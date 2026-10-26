import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class LogSnapshotTests(unittest.TestCase):
	def test_save_log_snapshot_copies_live_log_to_saved_directory(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			root = Path(temporary_directory)
			log_file = root / "suro.log"
			snapshot_directory = root / "saved"
			log_file.write_text("test log entry\n", encoding="utf-8")
			old_log_file = Index.LOG_FILE
			old_snapshot_directory = Index.LOG_SNAPSHOT_DIRECTORY
			Index.LOG_FILE = log_file
			Index.LOG_SNAPSHOT_DIRECTORY = snapshot_directory
			try:
				snapshot_path = Index.save_log_snapshot()
				self.assertEqual(snapshot_path.read_text(encoding="utf-8"), "test log entry\n")
				self.assertEqual(snapshot_path.parent, snapshot_directory)
			finally:
				Index.LOG_FILE = old_log_file
				Index.LOG_SNAPSHOT_DIRECTORY = old_snapshot_directory


class LogNotificationTests(unittest.IsolatedAsyncioTestCase):
	async def test_save_log_command_allows_admin_ids_from_environment(self):
		bot = SimpleNamespace(
			save_logs_and_notify=AsyncMock(
				return_value=(Path("saved.log"), True),
			),
		)
		context = SimpleNamespace(
			author=SimpleNamespace(id=222),
			bot=bot,
			reply=AsyncMock(),
		)

		with patch.dict(os.environ, {"ADMIN_IDS": "111, 222"}):
			callback = cast(Any, Index.save_log_command.callback)
			await callback(context)

		bot.save_logs_and_notify.assert_awaited_once()
		context.reply.assert_awaited_once()

	async def test_save_log_command_denies_non_admin(self):
		bot = SimpleNamespace(save_logs_and_notify=AsyncMock())
		context = SimpleNamespace(
			author=SimpleNamespace(id=333),
			bot=bot,
			reply=AsyncMock(),
		)

		with patch.dict(os.environ, {"ADMIN_IDS": "111, 222"}):
			callback = cast(Any, Index.save_log_command.callback)
			await callback(context)

		bot.save_logs_and_notify.assert_not_awaited()
		context.reply.assert_awaited_once()

	async def test_saved_log_is_sent_to_developer_as_attachment(self):
		bot = Index.ComicWorldBot(None)
		developer = SimpleNamespace(send=AsyncMock())
		with tempfile.TemporaryDirectory() as temporary_directory:
			snapshot_path = Path(temporary_directory) / "snapshot.log"
			snapshot_path.write_text("test log entry\n", encoding="utf-8")
			with (
				patch.object(bot, "get_user", return_value=developer),
				patch.object(Index.asyncio, "to_thread", new=AsyncMock(return_value=snapshot_path)),
				patch.object(
					Index.discord,
					"File",
					return_value=SimpleNamespace(filename="snapshot.log"),
				),
			):
				result_path, sent_to_developer = await bot.save_logs_and_notify("manual request")

		self.assertEqual(result_path, snapshot_path)
		self.assertTrue(sent_to_developer)
		developer.send.assert_awaited_once()
		call = developer.send.await_args
		if call is None:
			self.fail("개발자 DM 전송이 호출되지 않았습니다.")
		self.assertEqual(call.kwargs["content"], "로그 저장 알림: manual request")
		self.assertEqual(call.kwargs["file"].filename, "snapshot.log")

	async def test_error_handler_schedules_log_notification(self):
		bot = SimpleNamespace(
			log_event_loop=asyncio.get_running_loop(),
			save_logs_and_notify=AsyncMock(),
		)
		handler = Index.LogErrorNotificationHandler(bot)
		record = Index.logging.LogRecord("test", Index.logging.ERROR, "test.py", 1, "failure", (), None)

		handler.emit(record)
		await asyncio.sleep(0)
		await asyncio.sleep(0)

		bot.save_logs_and_notify.assert_awaited_once_with(
			"오류 로그가 자동 전송되었습니다.\n발생 위치: `test.py:1`",
			automatic_error=True,
		)


if __name__ == "__main__":
	unittest.main()