import os
import tempfile
import types
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class MenuDbTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "menus.db"
        Index.MENU_DB_FILE = self.db_path

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_delete_menu_respects_owner_and_admin(self):
        Index.initialize_menu_db()
        self.assertTrue(Index.add_menu(1, "짜장면", 101))
        self.assertTrue(Index.add_menu(1, "짬뽕", 102))

        self.assertTrue(Index.delete_menu(1, "짜장면", 101, is_admin=False))
        self.assertFalse(Index.delete_menu(1, "짬뽕", 101, is_admin=False))
        self.assertTrue(Index.delete_menu(1, "짬뽕", 999, is_admin=True))

        remaining = Index.get_menu_entries(1)
        self.assertEqual(remaining, [])

    def test_menu_admin_list_allows_special_admins(self):
        old_value = os.environ.get("ADMIN_IDS")
        os.environ["ADMIN_IDS"] = "9001, 9002"
        try:
            self.assertTrue(Index.is_menu_admin(types.SimpleNamespace(id=9001)))
            self.assertTrue(Index.is_menu_admin(types.SimpleNamespace(id=9002)))
            self.assertFalse(Index.is_menu_admin(types.SimpleNamespace(id=1234)))
        finally:
            if old_value is None:
                os.environ.pop("ADMIN_IDS", None)
            else:
                os.environ["ADMIN_IDS"] = old_value


class StatusHelpersTests(unittest.TestCase):
    def test_parse_ping_latency(self):
        raw = (
            "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n"
            "64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=13.2 ms\n"
        )
        self.assertEqual(Index.parse_ping_latency(raw), "13.2ms")

    def test_format_uptime_seconds(self):
        self.assertEqual(Index.format_uptime_seconds(90061), "1일 1시간 1분 1초")

    def test_parse_android_uptime_text(self):
        self.assertEqual(
            Index.parse_uptime_text("up 1 week, 22 hours, 12 minutes"),
            "7일 22시간 12분 0초",
        )


if __name__ == "__main__":
    unittest.main()
