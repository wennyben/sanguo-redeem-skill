#!/usr/bin/env python3

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import main


class LoadUsersTests(unittest.TestCase):
    def test_load_users_uses_sanguo_users_file_env(self):
        users = [{"player_id": "123456", "player_name": "玩家A", "region": "hk"}]

        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = Path(temp_dir) / "user.json"
            users_file.write_text(json.dumps(users, ensure_ascii=False), encoding="utf-8")

            original = os.environ.get("SANGUO_USERS_FILE")
            os.environ["SANGUO_USERS_FILE"] = str(users_file)
            try:
                self.assertEqual(main.load_users(), users)
            finally:
                if original is None:
                    os.environ.pop("SANGUO_USERS_FILE", None)
                else:
                    os.environ["SANGUO_USERS_FILE"] = original

    def test_monitor_mode_reports_missing_monitor_module(self):
        original_argv = sys.argv[:]
        sys.argv = ["main.py", "--monitor"]
        stderr = StringIO()

        try:
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                main.main()
        finally:
            sys.argv = original_argv

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("monitor mode requires monitor.py", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
