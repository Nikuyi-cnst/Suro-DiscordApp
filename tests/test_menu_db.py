import os
import sqlite3
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any, cast

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
            self.assertTrue(Index.is_menu_admin(cast(Any, types.SimpleNamespace(id=9001))))
            self.assertTrue(Index.is_menu_admin(cast(Any, types.SimpleNamespace(id=9002))))
            self.assertFalse(Index.is_menu_admin(cast(Any, types.SimpleNamespace(id=1234))))
        finally:
            if old_value is None:
                os.environ.pop("ADMIN_IDS", None)
            else:
                os.environ["ADMIN_IDS"] = old_value

    def test_menu_list_embed_is_paginated_in_groups_of_twenty(self):
        menus = [f"메뉴 {index}" for index in range(1, 22)]

        first_page = Index.make_menu_list_embed(menus, page=0)
        second_page = Index.make_menu_list_embed(menus, page=1)

        self.assertEqual(len(first_page.fields), 20)
        self.assertEqual(len(second_page.fields), 1)
        self.assertTrue(all(field.inline for field in first_page.fields))
        self.assertEqual(first_page.fields[0].value, "메뉴 1")
        self.assertEqual(second_page.fields[0].value, "메뉴 21")
        self.assertIn("페이지 1 / 2", first_page.footer.text or "")

    def test_random_menu_only_uses_the_selected_category(self):
        Index.initialize_menu_db()
        self.assertTrue(Index.add_menu(1, "김치찌개", 101, "일반 음식"))
        self.assertTrue(Index.add_menu(1, "케이크", 102, "디저트"))
        self.assertTrue(Index.add_menu(1, "민트초코 라면", 103, "괴랄한 음식"))

        self.assertEqual(Index.get_random_menu(1, "디저트"), ("케이크", 1))
        self.assertEqual(Index.get_random_menu(1, "괴랄한 음식"), ("민트초코 라면", 1))
        self.assertEqual(Index.get_random_menu(1), ("김치찌개", 1))
        self.assertEqual(Index.get_random_menu(1, "없는 분류"), (None, 0))

    def test_initialize_menu_db_migrates_existing_menus_to_regular_food(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute(
            """
            CREATE TABLE menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL DEFAULT 0,
                menu TEXT NOT NULL,
                UNIQUE(guild_id, menu)
            )
            """
        )
        connection.execute(
            "INSERT INTO menus (guild_id, owner_id, menu) VALUES (?, ?, ?)",
            (1, 101, "기존 메뉴"),
        )
        connection.commit()
        connection.close()

        Index.initialize_menu_db()

        self.assertEqual(Index.get_random_menu(1), ("기존 메뉴", 1))
        self.assertEqual(Index.get_random_menu(1, "디저트"), (None, 0))


class MenuCategoryCommandTests(unittest.TestCase):
    def test_add_and_recommend_commands_expose_all_menu_categories(self):
        command_categories = (
            (Index.add_menu_command, Index.MENU_CATEGORIES),
            (Index.recommend_menu_command, Index.MENU_RECOMMEND_CATEGORIES),
        )
        for command, expected_categories in command_categories:
            with self.subTest(command=command.name):
                category_option = next(
                    option for option in command.parameters if option.name == "category"
                )
                self.assertEqual(
                    [choice.value for choice in category_option.choices],
                    list(expected_categories),
                )


class CommandLoggingTests(unittest.TestCase):
    def test_command_log_helper_uses_consistent_fields(self):
        user = types.SimpleNamespace(id=12345, __str__=lambda self: "TestUser")

        with self.assertLogs(Index.logger, level="INFO") as captured:
            Index.log_command_trigger("테스트", cast(Any, user))

        self.assertIn("CommandTriggered: command=테스트", captured.output[0])
        self.assertIn("user_id=12345", captured.output[0])


class BotRegistrationTests(unittest.TestCase):
    def test_tig_command_is_registered(self):
        old_time = os.environ.pop("AUTO_MESSAGE_TIME", None)
        old_text = os.environ.pop("AUTO_MESSAGE_TEXT", None)
        try:
            bot = Index.ComicWorldBot(None)
            import asyncio
            asyncio.run(bot.setup_hook())
            self.assertIsNotNone(bot.get_command("티그"))
            self.assertIsNotNone(bot.get_command("cnst:suro!saveLog"))
            self.assertIsNotNone(bot.get_command("saveLog"))
            self.assertIsNotNone(bot.tree.get_command("레벨"))
            self.assertIsNotNone(bot.tree.get_command("인벤토리"))
            self.assertIsNotNone(bot.tree.get_command("골디상점"))
            self.assertIsNotNone(bot.tree.get_command("유저레벨초기화"))
            self.assertIsNotNone(bot.tree.get_command("레벨초기화"))
            self.assertIsNotNone(bot.tree.get_command("레벨차감"))
        finally:
            if old_time is not None:
                os.environ["AUTO_MESSAGE_TIME"] = old_time
            if old_text is not None:
                os.environ["AUTO_MESSAGE_TEXT"] = old_text


class StatusHelpersTests(unittest.TestCase):
    def test_get_auto_message_time(self):
        old_value = os.environ.get("AUTO_MESSAGE_TIME")
        try:
            os.environ["AUTO_MESSAGE_TIME"] = "09:05"
            self.assertEqual(Index.get_auto_message_time(), (9, 5))
            os.environ["AUTO_MESSAGE_TIME"] = "25:00"
            self.assertIsNone(Index.get_auto_message_time())
        finally:
            if old_value is None:
                os.environ.pop("AUTO_MESSAGE_TIME", None)
            else:
                os.environ["AUTO_MESSAGE_TIME"] = old_value

    def test_get_auto_message_times_supports_multiple_times(self):
        old_value = os.environ.get("AUTO_MESSAGE_TIME")
        try:
            os.environ["AUTO_MESSAGE_TIME"] = "19:17, 19:18"
            self.assertEqual(Index.get_auto_message_times(), [(19, 17), (19, 18)])
        finally:
            if old_value is None:
                os.environ.pop("AUTO_MESSAGE_TIME", None)
            else:
                os.environ["AUTO_MESSAGE_TIME"] = old_value

    def test_get_auto_message_text_uses_time_specific_messages(self):
        old_value = os.environ.get("AUTO_MESSAGE_TEXTS")
        try:
            os.environ["AUTO_MESSAGE_TEXTS"] = '{"19:17":"첫 번째", "19:18":"두 번째"}'
            self.assertEqual(Index.get_auto_message_text((19, 17)), "첫 번째")
            self.assertEqual(Index.get_auto_message_text((19, 18)), "두 번째")
        finally:
            if old_value is None:
                os.environ.pop("AUTO_MESSAGE_TEXTS", None)
            else:
                os.environ["AUTO_MESSAGE_TEXTS"] = old_value

    def test_get_auto_message_channel_ids_uses_both_servers(self):
        old_value = os.environ.pop("AUTO_MESSAGE_CHANNEL_IDS", None)
        try:
            self.assertEqual(
                Index.get_auto_message_channel_ids(),
                [1549321583384862730],
            )
        finally:
            if old_value is not None:
                os.environ["AUTO_MESSAGE_CHANNEL_IDS"] = old_value

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
