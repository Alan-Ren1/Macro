#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - optional dependency
    Image = None
    ImageTk = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "f6",
    "click_delay": 0.25,
    "queue_wait_seconds": 5.0,
    "repeat": 1,
    "selected_mode": "story",
    "webhook_url": "",
    "webhook_events": ["started", "finished"],
    "followup": {
        "after_match": {
            "action": "none",
            "profile": "",
        }
    },
    "profiles": {
        "villain_invasion": {
            "enter": [{"action": "wait", "seconds": 1.0}],
            "leave": [{"action": "press", "key": "esc"}],
        },
        "expeditions": {
            "enter": [{"action": "wait", "seconds": 1.0}],
            "leave": [{"action": "press", "key": "esc"}],
        },
    },
    "modes": {
        "story": {
            "enter": [{"action": "wait", "seconds": 1.0}],
            "leave": [{"action": "press", "key": "esc"}],
            "default": [{"action": "wait", "seconds": 1.0}],
        },
        "pvp": {
            "enter": [{"action": "wait", "seconds": 1.0}],
            "leave": [{"action": "press", "key": "esc"}],
            "default": [{"action": "wait", "seconds": 1.0}],
        },
    },
}


class MacroError(RuntimeError):
    """Raised when the macro cannot be executed."""


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    config_path = path or os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        return json.loads(json.dumps(DEFAULT_CONFIG))

    with open(config_path, "r", encoding="utf-8") as handle:
        user_data = json.load(handle)

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(user_data)
    if "modes" in user_data:
        merged["modes"] = {**merged["modes"], **user_data["modes"]}
    return merged


def save_config(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def send_discord_webhook(webhook_url: str, message: str) -> None:
    if not webhook_url:
        return

    payload = json.dumps({"content": message}).encode("utf-8")
    request = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as response:  # type: ignore[call-arg]
        response.read()


def list_modes(config: Dict[str, Any]) -> List[str]:
    return sorted(config.get("modes", {}).keys())


def get_steps(config: Dict[str, Any], mode: str, section: str) -> List[Dict[str, Any]]:
    mode_config = config.get("modes", {}).get(mode, {})
    if isinstance(mode_config, dict):
        if section in mode_config:
            steps = mode_config[section]
            if isinstance(steps, list):
                return steps
        if "steps" in mode_config:
            return mode_config["steps"]
        if "enter" in mode_config and section == "enter":
            return mode_config["enter"]
        if "leave" in mode_config and section == "leave":
            return mode_config["leave"]
        if "default" in mode_config:
            return mode_config["default"]
    if isinstance(mode_config, list):
        return mode_config
    return []


def select_followup_action(config: Dict[str, Any]) -> Optional[str]:
    followup = config.get("followup", {})
    if isinstance(followup, dict):
        after_match = followup.get("after_match", {})
        if isinstance(after_match, dict) and after_match.get("action") == "run_profile":
            return str(after_match.get("profile", ""))
    return None


def resolve_mode(config: Dict[str, Any], mode: Optional[str]) -> str:
    modes = list_modes(config)
    if not modes:
        raise MacroError("No modes were configured.")
    if mode is None:
        raise MacroError(f"Choose one of: {', '.join(modes)}")
    if mode not in modes:
        raise MacroError(f"Unknown mode '{mode}'. Choose one of: {', '.join(modes)}")
    return mode


def run_sequence(config: Dict[str, Any], mode: str, repeats: int = 1, dry_run: bool = False, section: str = "default") -> None:
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:
        raise MacroError("Install dependencies first: pip install -r requirements.txt") from exc

    webhook_url = str(config.get("webhook_url", ""))
    steps = get_steps(config, mode, section)
    if not steps:
        raise MacroError(f"No steps found for mode '{mode}' in section '{section}'.")

    if dry_run:
        print(f"Dry run for mode '{mode}' section '{section}' with {repeats} cycle(s):")
        for index, step in enumerate(steps, 1):
            print(f"  {index}. {step}")
        return

    if "started" in config.get("webhook_events", []) and webhook_url:
        send_discord_webhook(webhook_url, f"Anime Expedition macro started for {mode} ({section})")

    for cycle in range(1, repeats + 1):
        print(f"Starting cycle {cycle}/{repeats} for mode '{mode}' section '{section}'.")
        for step in steps:
            action = step.get("action")
            if action == "wait":
                seconds = float(step.get("seconds", 0.0))
                time.sleep(seconds)
            elif action == "click":
                x = int(step.get("x", 0))
                y = int(step.get("y", 0))
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                time.sleep(float(config.get("click_delay", 0.25)))
            elif action == "press":
                key = str(step.get("key", ""))
                pyautogui.press(key)
            else:
                raise MacroError(f"Unsupported action '{action}'.")
        time.sleep(float(config.get("queue_wait_seconds", 0.0)))

    if "finished" in config.get("webhook_events", []) and webhook_url:
        send_discord_webhook(webhook_url, f"Anime Expedition macro finished for {mode} ({section})")

    followup_profile = select_followup_action(config)
    if followup_profile and followup_profile in config.get("profiles", {}):
        print(f"Match complete. Running follow-up profile '{followup_profile}'.")
        run_sequence(config, followup_profile, repeats=1, dry_run=dry_run, section="enter")


def build_gui() -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError:
        print("Tkinter is not available on this system.", file=sys.stderr)
        return

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)

    root = tk.Tk()
    root.title("Anime Expedition Macro")
    root.geometry("620x480")
    root.resizable(False, False)

    bg_image_path = os.path.join(os.path.dirname(__file__), "MacroImage.png")
    if Image is not None and ImageTk is not None and os.path.exists(bg_image_path):
        try:
            img = Image.open(bg_image_path)
            img = img.resize((620, 480))
            photo = ImageTk.PhotoImage(img)
            background = tk.Label(root, image=photo)
            background.place(x=0, y=0, relwidth=1, relheight=1)
            background.image = photo
        except Exception:
            pass

    frame = tk.Frame(root, bg="#0f172a")
    frame.place(relx=0.05, rely=0.08, relwidth=0.9, relheight=0.82)

    title = tk.Label(frame, text="Anime Expedition Macro", fg="#f8fafc", bg="#0f172a", font=("Segoe UI", 20, "bold"))
    title.pack(pady=(18, 6))
    subtitle = tk.Label(frame, text="Open Roblox, choose a mode, and start the flow.", fg="#cbd5e1", bg="#0f172a")
    subtitle.pack(pady=(0, 12))

    mode_var = tk.StringVar(value=config.get("selected_mode", "story"))
    webhook_var = tk.StringVar(value=config.get("webhook_url", ""))
    section_var = tk.StringVar(value="enter")

    ttk.Label(frame, text="Mode", background="#0f172a", foreground="#f8fafc").pack(anchor="w", padx=28)
    ttk.Combobox(frame, textvariable=mode_var, values=list_modes(config), state="readonly", width=32).pack(padx=28, pady=(0, 10), anchor="w")

    ttk.Label(frame, text="Action", background="#0f172a", foreground="#f8fafc").pack(anchor="w", padx=28)
    ttk.Combobox(frame, textvariable=section_var, values=["enter", "leave", "default"], state="readonly", width=32).pack(padx=28, pady=(0, 10), anchor="w")

    ttk.Label(frame, text="Discord Webhook URL", background="#0f172a", foreground="#f8fafc").pack(anchor="w", padx=28)
    ttk.Entry(frame, textvariable=webhook_var, width=58).pack(padx=28, pady=(0, 12), anchor="w")

    def run_from_gui() -> None:
        config["selected_mode"] = mode_var.get()
        config["webhook_url"] = webhook_var.get()
        save_config(config_path, config)
        try:
            run_sequence(config, mode_var.get(), repeats=max(1, int(config.get("repeat", 1))), section=section_var.get())
        except MacroError as exc:
            messagebox.showerror("Macro Error", str(exc))

    button_frame = tk.Frame(frame, bg="#0f172a")
    button_frame.pack(pady=10)
    ttk.Button(button_frame, text="Start", command=run_from_gui).pack(side="left", padx=6)
    ttk.Button(button_frame, text="Exit", command=root.destroy).pack(side="left", padx=6)

    root.mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Anime Expedition macro runner")
    parser.add_argument("--config", default=None, help="Path to your JSON config file")
    parser.add_argument("--mode", default=None, help="Mode to run (must exist in the config)")
    parser.add_argument("--list-modes", action="store_true", help="Show the configured modes")
    parser.add_argument("--repeat", type=int, default=1, help="How many times to run the sequence")
    parser.add_argument("--dry-run", action="store_true", help="Print the sequence without clicking")
    parser.add_argument("--enter", action="store_true", help="Run the enter sequence for the selected mode")
    parser.add_argument("--leave", action="store_true", help="Run the leave sequence for the selected mode")
    return parser


def main() -> int:
    parser = build_parser()
    parser.add_argument("--gui", action="store_true", help="Open the desktop launcher window")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.gui:
        build_gui()
        return 0
    if args.list_modes:
        print("Configured modes:")
        for mode in list_modes(config):
            print(f"- {mode}")
        return 0

    mode = resolve_mode(config, args.mode)
    if args.leave:
        run_sequence(config, mode, repeats=max(1, args.repeat), dry_run=args.dry_run, section="leave")
    elif args.enter:
        run_sequence(config, mode, repeats=max(1, args.repeat), dry_run=args.dry_run, section="enter")
    else:
        run_sequence(config, mode, repeats=max(1, args.repeat), dry_run=args.dry_run, section="default")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MacroError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
