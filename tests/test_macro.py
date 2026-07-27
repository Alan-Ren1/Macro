import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import anime_expedition_macro as macro


class MacroConfigTests(unittest.TestCase):
    def test_load_config_merges_defaults(self):
        config = macro.load_config(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        self.assertIn("story", config["modes"])
        self.assertIn("pvp", config["modes"])

    def test_list_modes_returns_sorted_names(self):
        config = macro.load_config(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        self.assertEqual(list(macro.list_modes(config)), ["pvp", "story"])

    def test_get_steps_supports_enter_and_leave_sections(self):
        config = {
            "modes": {
                "story": {
                    "enter": [{"action": "wait", "seconds": 1.0}],
                    "leave": [{"action": "press", "key": "esc"}],
                }
            }
        }
        self.assertEqual(macro.get_steps(config, "story", "enter")[0]["action"], "wait")
        self.assertEqual(macro.get_steps(config, "story", "leave")[0]["action"], "press")

    def test_save_config_persists_webhook_and_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "config.json")
            data = {"webhook_url": "https://example.test/hook", "selected_mode": "story"}
            macro.save_config(path, data)
            self.assertEqual(macro.load_config(path)["webhook_url"], "https://example.test/hook")
            self.assertEqual(macro.load_config(path)["selected_mode"], "story")

    def test_send_discord_webhook_posts_payload(self):
        with patch("anime_expedition_macro.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b"ok"
            macro.send_discord_webhook("https://example.test/hook", "hello")
            self.assertTrue(mock_urlopen.called)

    def test_select_followup_action_uses_configured_profile(self):
        config = {
            "followup": {
                "after_match": {
                    "action": "run_profile",
                    "profile": "villain_invasion",
                }
            }
        }
        self.assertEqual(macro.select_followup_action(config), "villain_invasion")


if __name__ == "__main__":
    unittest.main()
