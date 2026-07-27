# Anime Expedition macro

This repository contains a simple, downloadable macro runner for Anime Expedition-style matchmaking.

## What it does
- Lets you choose a configured gamemode from the command line.
- Supports separate enter-matchmaking and leave-match actions for each mode.
- Can run a default action sequence, or explicitly use the enter/leave sequence.

## Setup
1. Install Python 3.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Edit [config.json](config.json) and replace the placeholder coordinates with the actual positions for your game UI.

## Usage
List the configured modes:
```bash
python3 anime_expedition_macro.py --list-modes
```

Run a mode's default sequence:
```bash
python3 anime_expedition_macro.py --mode story
```

Run the matchmaking enter sequence:
```bash
python3 anime_expedition_macro.py --mode story --enter
```

Run the leave-match sequence:
```bash
python3 anime_expedition_macro.py --mode story --leave
```

Preview the action sequence without clicking:
```bash
python3 anime_expedition_macro.py --mode pvp --dry-run
```

## Notes
- The default coordinates in [config.json](config.json) are placeholders and will not work until you replace them with your own screen positions.
- For best results, use the game window at 1920x1080 or adjust the coordinates to match your resolution.
- If your game uses slightly different UI positions, change the `x` and `y` values in [config.json](config.json) to match your screen.
