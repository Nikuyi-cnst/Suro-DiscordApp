import asyncio, hashlib, json, logging, math, os, random, re, shutil, sqlite3, subprocess, sys, threading, time, uuid
from datetime import date, datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord
import requests
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from github_inquiries import InquiryError, create_inquiry_issue

ClientBuild = "OpenBeta-UnderEvaluation"
ClientVersion = "GA2.0-S"
ClientBuildDate = "KOO20261024124437-%Nan"

Help_Message_KOR = """# 슈로 봇 사용안내 (For Korean)
-# {mention}
# ✧ ----------≺ **메인** ≻---------- ✧
> 안녕하세요! 봇 개발자인 **<@924576483333259294>(Aren/아렌)**입니다.
> 이 문서는 해당 봇을 사용하는 방법을 알려드려요.
# ✧ ----------≺ **기능** ≻---------- ✧
> ### - `/코믹인포`
> `/코믹인포`는 **대한민국의 행사인 코믹월드의 정보**를 불러와줘요.
> _단, **10분마다 1번씩 **보낼 수 있어요._
> ### - `/코믹스케줄`
> `/코믹스케줄`은 **대한민국의 행사인 코믹월드의 정보를 원하는 많큼** 불러올 수 있어요.
> ### - `/메뉴추천`
> `/메뉴추천`은 **분류별 메뉴 추천을 받고 엘리프를 얻을 수 있**어요.
> ### - `/레벨`
> `/레벨`은 **현재 레벨과 다음 레벨까지 필요한 엘리프를 확인**할 수 있어요.
> ### - `/랭킹 type:레벨`
> `/랭킹`은 **서버의 레벨과 엘리프 랭킹**을 확인할 수 있어요.
> `type:퀴즈랭킹`을 선택하면 **정답을 맞힌 문제 수 순위**를 확인할 수 있어요.
> ### - `/퀴즈`
> `/퀴즈`는 **기본 문제 또는 서버에 출제된 문제를 시작**해요. 힌트 보기, 정답 입력, 포기는 문제 아래 버튼을 사용해주세요.
> 한 사람은 문제마다 정답을 3회까지 입력할 수 있고, 누구든 정답을 맞히거나 포기하면 전체 풀이가 종료돼요. 정답을 맞히면 5~20엘리프를 받아요.
> `/퀴즈`는 서버 전체에서 4시간마다 한 번만 시작할 수 있어요.
> 힌트는 첫 번 무료로 10초간 볼 수 있으며, 두 번째는 15엘리프를 사용해 10초간 볼 수 있어요.
> ### - `/문제출제`
> `/문제출제`에 문제, 정답, 힌트를 입력하면 바로 진행하지 않고 문제 은행에 저장해요. `/퀴즈`를 실행하면 저장된 문제도 출제돼요.
> ### - `/인벤토리`
> `/인벤토리`는 **보유 아이템과 엘리프**를 확인할 수 있어요.
> ### - `/골디상점`
> `/골디상점`에서 **엘리프로 아이템을 구매**할 수 있어요.
> ### - `/메뉴등록`
> `/메뉴등록`은 **식사 메뉴를 등록**할 수 있어요. 
> ### - `/메뉴삭제`
> `/메뉴삭제`는 **본인이 등록한 메뉴를 삭제**할 수 있어요.
> ### - `/문의`
> `/문의`는 **피드백, 버그재보, 질문등의 모든것**을 받습니다.
> 문의 내용과 작성자 표시 이름은 **GitHub 공개 이슈로 등록**됩니다.
> 이미지는 **선택 사항**이며 첨부하면 이미지 링크도 공개됩니다.
> __개인정보나 토큰 등 비밀 정보는 내용과 이미지에 넣지 마세요.__
> ### - `/상태`
> `/상태`는 말 그대로 봇의 상태를 볼 수 있어요.
> ### - `/도움말`
> `/도움말`은 이 문서를 볼 수 있어요.
# ✧ ----------≺ **기타 정보** ≻---------- ✧
> 추가 질문 사항이 있다면, `/문의`를 사용해보세요! 문의는 공개되며 사진 첨부는 선택입니다.
> 다음 업데이트(GA1.4-S)에선 무엇이 추가될까요? 원하는 기능이 있다면, `/문의`를 통해서 말씀해보세요.
-# C-Build: {ClientBuild} / ClientVersion: {ClientVersion} / C-BuildDate: {ClientBuildDate}"""

Help_Message_JPN = """# 슈로「シュロ」ボット使用案内 (For Japanese)
-# {mention}
その文書は翻訳者を使用して書かれています。
誤解を招く可能性がある文があるかもしれません。参考にしてください！
# ✧ ----------≺ **メイン** ≻---------- ✧
> こんにちは！ボット開発者である**<@924576483333259294>(Aren/アレン)**です
> この記事では、そのボットの使い方を教えてくれます。
# ✧ ----------≺ **機能** ≻---------- ✧
> ### - `/코믹인포`
> `/코믹인포`(コミックインフォ)は**大韓民国のイベントであるコミックワールドの情報**を呼んでくれます。
> _ただし、**10分ごとに1回ずつ**送信できます。_
> ### - `/코믹스케줄`
> `/코믹스케줄`(コミックスケジュール)は **大韓民国のイベントであるコミックワールドの情報を欲しがる多く**呼べます。
> ### - `/메뉴추천`
> `/메뉴추천`(メニューおすすめ)は**分類別のメニューをおすすめし、エリフを獲得できます。**
> ### - `/레벨`
> `/레벨`(レベル)は**現在のレベルと次のレベルまでのエリフを確認できます。**
> ### - `/랭킹 type:레벨`
> `/랭킹`(ランキング)は**サーバーのレベルとエリフのランキング**を確認できます。
> `type:퀴즈랭킹`を選ぶと**正解した問題数のランキング**を確認できます。
> ### - `/퀴즈`
> `/퀴즈`(クイズ)は**基本問題またはサーバーに出題された問題を開始**します。ヒント、回答、あきらめる操作は問題の下のボタンを使用してください。
> 一人につき問題ごとに3回まで回答でき、誰かが正解するか、あきらめると全体の問題が終了します。正解すると5～20エリフを獲得します。
> `/퀴즈`はサーバー全体で4時間に1回だけ開始できます。
> ヒントは最初の1回が無料で10秒間、2回目は15エリフを使って10秒間表示されます。
> ### - `/문제출제`
> `/문제출제`に問題、答え、ヒントを入力すると、すぐには開始せず問題集に保存されます。`/퀴즈`を実行すると保存された問題も出題されます。
> ### - `/인벤토리`
> `/인벤토리`(インベントリ)は**所持アイテムとエリフを確認できます。**
> ### - `/골디상점`
> `/골디상점`(ゴルディショップ)で**エリフを使ってアイテムを購入できます。**
> ### - `/메뉴등록`
> `/메뉴등록`(メニュー登録)は**食事メニューを登録**できます。
> ### - `/메뉴삭제`
> `/메뉴삭제`(メニュー削除)は**本人が登録したメニューを削除**できます。
> ### - `/문의`
> `/문의`(お問い合わせ)は**フィードバック、バグ再報、質問などのすべてを受け取ります。
> 内容と投稿者の表示名は **GitHubの公開Issueに登録**されます。
> 画像の添付は **任意**です。添付すると画像リンクも公開されます。
> __個人情報やトークンなどの秘密情報を内容や画像に含めないでください。__
> ### - `/상태`
> `/상태`(状態)は文字通りボットの状態を見ることができます。
> ### - `/도움말`
> `/도움말`(ヘルプ)はこの記事を見ることができます。
# ✧ ----------≺ **その他の情報** ≻---------- ✧
> 質問は`/문의`（お問い合わせ）へ！内容は公開され、画像の添付は任意です。
> 次のアップデート(GA1.4-S)では何が追加されますか？必要な機能がある場合は、`/문의`（お問い合わせ）を通して教えてください。
-# C-Build: {ClientBuild} / ClientVersion: {ClientVersion} / C-BuildDate: {ClientBuildDate}"""

Notification_Message1_PM08 = """# <@1548636045615304755> 는 오류신고 기능이 있어요!
오류가 발생한다면 `/문의`를 통해 오류신고를 해주세요.
-# _신고하면 포상금(칭찬)줌_
"""

Notification_Message1_PM03 = """# <@1548636045615304755> 의 /메뉴등록 기능에는 규정이 있어요!
<@1548636045615304755>의 [위키 페이지](https://app.notion.com/p/3e31e98a441d8052b17ff0d257d78537?v=3e31e98a441d80518ebc000cc886c8b5&source=copy_link)를 확인해주세요.
규정을 지키지 않거나, 읽지 않아서 생긴 불이익은 이용에 제한이 생겨요."""

BASE_URL = "https://comicw.net"
EVENTS_URL = f"{BASE_URL}/bbs/ajax.main.php"
COMICWORLD_EMOJI_URL = "https://cdn.discordapp.com/emojis/1549042252322439258.png"
CACHE_FILE = Path(__file__).with_name(".event_cache.json")
MENU_DB_FILE = Path(__file__).with_name("menus.db")
LEVEL_DB_FILE = Path(__file__).with_name("levels.db")

LOG_DIRECTORY = Path(__file__).with_name("logs")
LOG_FILE = LOG_DIRECTORY / "suro.log"
LOG_SNAPSHOT_DIRECTORY = LOG_DIRECTORY / "saved"
DEVELOPER_USER_ID = 924576483333259294
SCHEDULE_COOLDOWN_SECONDS = 600
TIG_COOLDOWN_SECONDS = 21600
MENU_PAGE_SIZE = 20
MENU_CATEGORIES = ("일반 음식", "디저트", "괴랄한 음식")
MENU_RECOMMEND_CATEGORIES = (*MENU_CATEGORIES, "연회장 특식")
MAX_USER_LEVEL = 150
LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL = 20
QUIZ_HINT_COST = 15
QUIZ_MAX_ATTEMPTS = 3
QUIZ_REWARD_MIN = 5
QUIZ_REWARD_MAX = 20
QUIZ_COOLDOWN_SECONDS = 4 * 60 * 60
LOTTERY_CRYSTAL_LEAF_CHANCE = 0.0001
BANQUET_SPECIAL_MIN_LEVEL = 15
BANQUET_SPECIAL_PREFERRED_WEIGHT = 1.2
KST = timezone(timedelta(hours=9))
DEFAULT_AUTO_MESSAGE_CHANNEL_IDS = (
	1549321583384862730,
	# 1548640303337046138,
)
schedule_cooldown_until: float | None = None
tig_cooldown_until: float | None = None
last_auto_message_dates: dict[int, date] = {}

quizs: dict[str, dict[str, str]] = {
	"	1": {
		"<출제자>": "슈로 봇",
		"<문제내용>": "대한민국의 수도는 어디일까요?",
		"<정답>": "서울",
		"<힌트>": "대한민국에서 가장 인구가 많은 도시예요.",
	},
	"2": {
		"<출제자>": "슈로 봇",
		"<문제내용>": "태양계에서 가장 큰 행성은 무엇일까요?",
		"<정답>": "목성",
		"<힌트>": "영어 이름은 Jupiter예요.",
	},
	"3": {
		"<출제자>": "슈로 봇",
		"<문제내용>": "물의 화학식은 무엇일까요?",
		"<정답>": "H2O",
		"<힌트>": "수소 원자 두 개와 산소 원자 한 개로 이루어져 있어요.",
	},
}

BOT_NAME = "Suro"
BOT_ON_MESSAGE = f"""
----------------------------------------------------                                                                           
Wellcome to {BOT_NAME} app log channel!

새 버전 출시! -  [KST]2026년 x월 x일 x시 x분
GA2.0-S - 버전이 출시되었스빈다.
자세한 내용은 '/도움말'을 참고하세요.

다음 업대이트는 GA2.1-S로 예정되어 있습니다.(아마도)
----------------------------------------------------
build: {ClientBuild}
version: {ClientVersion}
build date: {ClientBuildDate}
System Load Time: {time.ctime()}
------------------------------------------------"""

Activitys = {1: "아침공기 마시는중",# 8:00 ~ 11:00
             2: "연회장에서 식사중",# 11:00 ~ 13:00, 18:00 ~ 20:00
             3: "밥 먹는중",# 11:00 ~ 13:00, 18:00 ~ 20:00
             4: "밥 씹는중",# 11:00 ~ 13:00 / 0.5%의 확률로 나타나게
             5: "티그랑 훈련중",# 13:00 ~ 18:00
             6: "교주님 따라 침략중",# 13:00 ~ 18:00
             7: "추천할 메뉴 생각중",# 13:00 ~ 18:00
             8: "산책하는중",# 13:00 ~ 18:00, 18:00 ~ 20:00
             9: "밤 하늘 보는중"# 18:00 ~ 20:00
             }


ITEM_LIST = {
	"소화제": {
		"price": 20,
		"description": "연회장 특식을 추가로 먹을 떄 사용해요.",
		"daily_limit": 1,
	},
	"집문서": {
		"price": 2990,
		"description": "누군가의 집문서다. 한으로 시작하는 모회사 대표가 생각난다.",
		"daily_limit": 1,
	},
}


# Lv 25 이상
eliasFoodsP60 = ["트리플 민트초코 아이스크림", "해적 만화 곡 구이", "머스크 멜론 보코치니", "보물 타르트", "1급 비밀의 포도주스", "찹쌀밥 한 공기", "악령푸딩",
              "딥다크 초콜릿 아이스크림", "에심당 딸기 케이크", "우주 차원 식량", "꿀꿀꿀단지", "용감한 사탕", "UFC 모둠 튀김", "파팝! 카라멜 팝콘",
              "홍삼맛 건강 알사탕", "빵실 마시멜로 마카롱", "VIP 캔 사료", "질소 커틀릿", "3단 매듭 빵", "스파클링 레몬차", "세입초 쌈",
			  "코코넛 산뜻 녹즙", "솔티 크림 브륄레", "보석 탕후루", "앗뜨거 앗차거 아메리카노", "석류석 빙수", "스페셜 허니갈릭 살몬", "해초 도시락",
			  "호박죽", "얼음 가득 미숫가루", "킹짱비타K"]# 개쩜
# Lv 20 이상
eliasFoodsP50 = ["초콜릿 아이스크림", "만화 고기 구이", "비밀의 포도주스", "멜론 보코치니", "유령 푸팅", "보석 타르트",
                 "민트 초코 아이스크림", "쌀밥 한 공기", "뜨거운 냉동 아메리카노", "927곡 미숫가루", "석류석 화채", "해초 포케",
				 "로얄 허니갈릭 살몬", "호박 스튜", "얌얌비타C", "송편"]# 전설
# Lv 15 이상
eliasFoodsP40 = ["허니갈릭 살몬", "따뜻한 아이스 아메리카노", "해초 샐러드", "호박 스프", "석류석 열매", "미숫가루",
                  "수소 커틀릿", "백금탕후루", "유기농 레몬차", "하트 메듭 빵", "코코넛 만능 녹즙",
				  "소프트 크림 브륄레", "두입초 쌈", "새콤비타F", "부쉬 드 노엘", "아몬드 로쉐", "떡국", "에심당 뽈사탕"]# 희귀
# Lv 10 이상
eliasFoodsP30 = ["크림 브륄레", "메듭 빵", "레몬차", "한입초 쌈", "공기 커틀릿", "금탕후루",
                 "코코넛 솔잎죽", "UFC 야채 튀김", "계피맛 건강 알사탕", "꿀꿀단지", "와앙 딸기 케이크", "저당 마시멜로 마카롱",
				 "용족 세공 사탕", "ANSA 우주식량", "고급 캔 사료", "엘플릭스 카라멜 팝콘"]# 고급
#모든 레벨
eliasFoodsP20 = ["딸기 케이크", "카라멜 팝콘", "캔 사료", "우주식량", "꿀단지", "계피맛 알사탕",
                 "용족 사탕", "UFC 당근 튀김", "마시멜로 마카롱"]# 일반


def get_banquet_special_tiers(level: int) -> list[list[str]]:
	tiers = [eliasFoodsP20]
	if level >= 10:
		tiers.append(eliasFoodsP30)
	if level >= BANQUET_SPECIAL_MIN_LEVEL:
		tiers.append(eliasFoodsP40)
	if level >= 20:
		tiers.append(eliasFoodsP50)
	if level >= 25:
		tiers.append(eliasFoodsP60)
	return tiers


def get_banquet_specials(level: int) -> list[str]:
	return [food for tier in get_banquet_special_tiers(level) for food in tier]


def choose_banquet_special_reward(level: int) -> tuple[str, int]:
	tiers = get_banquet_special_tiers(level)
	weights = [1.0] * len(tiers)
	weights[-1] = BANQUET_SPECIAL_PREFERRED_WEIGHT
	preferred_tier = random.choices(tiers, weights=weights, k=1)[0]
	base_crystal_leaf = 20 + 10 * tiers.index(preferred_tier)
	return random.choice(preferred_tier), base_crystal_leaf


def choose_banquet_special(level: int) -> str:
	menu, _ = choose_banquet_special_reward(level)
	return menu


def roll_banquet_special_crystal_leaf(base_crystal_leaf: int) -> int:
	return base_crystal_leaf + random.randint(-5, 5)

ACTIVITY_SCHEDULE = (
	(8, 11, (1,)),	
	(11, 13, (2, 3, 4)),
	(13, 18, (5, 6, 7, 8)),
	(18, 20, (2, 3, 8, 9)),
)


def get_activity_period(now: datetime) -> tuple[tuple[int, ...], datetime] | None:
	for start_hour, end_hour, activity_ids in ACTIVITY_SCHEDULE:
		if start_hour <= now.hour < end_hour:
			period_end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
			return activity_ids, period_end
	return None


def choose_activity_id(
	activity_ids: tuple[int, ...],
	previous_activity_id: int | None = None,
) -> int: 
	if 4 in activity_ids and previous_activity_id != 4 and random.random() < 0.005:
		return 4

	choices = [
		activity_id
		for activity_id in activity_ids
		if activity_id != 4 and activity_id != previous_activity_id
	]
	if not choices:
		choices = [activity_id for activity_id in activity_ids if activity_id != 4]
	return random.choice(choices)

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
)
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
file_log_handler = RotatingFileHandler(
	LOG_FILE,
	maxBytes=4 * 1024 * 1024,
	backupCount=3,
	encoding="utf-8",
)
file_log_handler.setFormatter(
	logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
logging.getLogger().addHandler(file_log_handler)
logger = logging.getLogger("tooAwesomeCommandDetector")
def log_command_trigger(command_name: str, user: discord.abc.User) -> None:
	logger.info(
		"CommandTriggered: command=%s, user_id=%s, username=%s",
		command_name,
		user.id,
		str(user),
	)


def save_log_snapshot() -> Path:
	for handler in logging.getLogger().handlers:
		handler.flush()
	LOG_SNAPSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)
	timestamp = datetime.now(KST).strftime("%Y%m%d-%H%M%S-%f")
	snapshot_path = LOG_SNAPSHOT_DIRECTORY / f"suro-log-{timestamp}.log"
	if LOG_FILE.exists():
		shutil.copy2(LOG_FILE, snapshot_path)
	else:
		snapshot_path.write_text("아직 기록된 로그가 없습니다.\n", encoding="utf-8")
	return snapshot_path


class LogErrorNotificationHandler(logging.Handler):
	def __init__(self, bot) -> None:
		super().__init__(level=logging.ERROR)
		self.bot = bot

	def emit(self, record: logging.LogRecord) -> None:
		loop = getattr(self.bot, "log_event_loop", None)
		if loop is None or not loop.is_running():
			return
		try:
			location = f"{Path(record.pathname).name}:{record.lineno}"
			message = (
				"오류 로그가 자동 전송되었습니다.\n"
				f"발생 위치: `{location}`"
			)
			loop.call_soon_threadsafe(self._schedule_notification, message, True)
		except Exception:
			self.handleError(record)

	def _schedule_notification(self, message: str, automatic_error: bool = False) -> None:
		asyncio.create_task(
			self.bot.save_logs_and_notify(message, automatic_error=automatic_error)
		)


def console_log_listener(bot) -> None:
	while True:
		command = sys.stdin.readline()
		if not command:
			return
		if command.strip().casefold() not in {"savelog", "cnst:suro!savelog"}:
			continue
		if not bot.log_loop_ready.wait(timeout=120):
			print("봇이 준비되지 않아 로그를 저장하지 못했습니다.")
			continue
		loop = bot.log_event_loop
		if loop is None or not loop.is_running():
			print("봇 이벤트 루프가 실행 중이 아니어서 로그를 저장하지 못했습니다.")
			continue
		future = asyncio.run_coroutine_threadsafe(
			bot.save_logs_and_notify("콘솔에서 로그 저장을 요청했습니다."),
			loop,
		)
		try:
			snapshot_path, sent_to_developer = future.result()
			if snapshot_path is None:
				print("로그 파일 저장에 실패했습니다.")
			elif sent_to_developer:
				print(f"로그 저장 및 개발자 DM 전송 완료: {snapshot_path}")
			else:
				print(f"로그는 저장했지만 개발자 DM 전송에 실패했습니다: {snapshot_path}")
		except Exception as error:
			print(f"로그 저장 처리 실패: {error}", file=sys.stderr)


def required_env(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"환경변수 {name}이(가) 설정되지 않았습니다.")
	return value


def get_auto_message_times() -> list[tuple[int, int]]:
	value = os.getenv("AUTO_MESSAGE_TIME", "").strip()
	if not value:
		return []

	times = []
	for item in value.split(","):
		try:
			hour, minute = (int(part) for part in item.strip().split(":", 1))
		except (TypeError, ValueError):
			logger.warning("AUTO_MESSAGE_TIME은 HH:MM 형식이어야 합니다: %s", item)
			continue
		if not (0 <= hour <= 23 and 0 <= minute <= 59):
			logger.warning("AUTO_MESSAGE_TIME이 올바른 시간이 아닙니다: %s", item)
			continue
		if (hour, minute) not in times:
			times.append((hour, minute))
	return times


def get_auto_message_time() -> tuple[int, int] | None:
	times = get_auto_message_times()
	return times[0] if times else None


def get_auto_message_text(current_time: tuple[int, int]) -> str | None:
	message_map = os.getenv("AUTO_MESSAGE_TEXTS", "").strip()
	if message_map:
		try:
			payload = json.loads(message_map)
		except json.JSONDecodeError:
			logger.warning("AUTO_MESSAGE_TEXTS는 JSON 형식이어야 합니다.")
			payload = {}
		if isinstance(payload, dict):
			key = f"{current_time[0]:02d}:{current_time[1]:02d}"
			message = payload.get(key)
			if isinstance(message, str) and message.strip():
				return message.strip()

	message = os.getenv("AUTO_MESSAGE_TEXT", "").strip()
	return message or None


def get_auto_message_channel_ids() -> list[int]:
	value = os.getenv("AUTO_MESSAGE_CHANNEL_IDS")
	if value is None:
		return list(DEFAULT_AUTO_MESSAGE_CHANNEL_IDS)

	channel_ids = []
	for item in value.split(","):
		candidate = item.strip()
		if not candidate:
			continue
		try:
			channel_id = int(candidate)
		except ValueError:
			logger.warning("AUTO_MESSAGE_CHANNEL_IDS에 잘못된 값이 포함되어 있습니다: %s", candidate)
			continue
		if channel_id > 0 and channel_id not in channel_ids:
			channel_ids.append(channel_id)
	return channel_ids


def fetch_events() -> list[dict[str, str]]:
	response = requests.post(
		EVENTS_URL,
		data={"type": "comic"},
		headers={"User-Agent": "ComicWorldDiscordBot/1.0"},
		timeout=15,
	)
	response.raise_for_status()
	data = response.json()
	if not isinstance(data, list):
		raise ValueError("코믹월드 행사 API가 예상과 다른 형식의 응답을 반환했습니다.")
	return data


def events_fingerprint(events: list[dict[str, str]]) -> str:
	payload = json.dumps(events, ensure_ascii=False, sort_keys=True)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cached_fingerprint() -> str | None:
	try:
		return json.loads(CACHE_FILE.read_text(encoding="utf-8")).get("fingerprint")
	except (FileNotFoundError, json.JSONDecodeError, AttributeError):
		return None


def save_cached_fingerprint(fingerprint: str) -> None:
	CACHE_FILE.write_text(
		json.dumps({"fingerprint": fingerprint}, ensure_ascii=False),
		encoding="utf-8",
	)


def initialize_menu_db() -> None:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS menus (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				guild_id INTEGER NOT NULL,
				owner_id INTEGER NOT NULL DEFAULT 0,
				menu TEXT NOT NULL,
				category TEXT NOT NULL DEFAULT '일반 음식',
				UNIQUE(guild_id, menu)
			)
			"""
		)
		try:
			connection.execute("SELECT owner_id FROM menus LIMIT 1")
		except sqlite3.OperationalError:
			connection.execute(
				"ALTER TABLE menus ADD COLUMN owner_id INTEGER NOT NULL DEFAULT 0"
			)
		try:
			connection.execute("SELECT category FROM menus LIMIT 1")
		except sqlite3.OperationalError:
			connection.execute(
				"ALTER TABLE menus ADD COLUMN category TEXT NOT NULL DEFAULT '일반 음식'"
			)
		connection.commit()
	finally:
		connection.close()


def add_menu(
	guild_id: int,
	menu: str,
	owner_id: int,
	category: str = "일반 음식",
) -> bool:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		cursor = connection.execute(
			"INSERT OR IGNORE INTO menus (guild_id, menu, owner_id, category) VALUES (?, ?, ?, ?)",
			(guild_id, menu, owner_id, category),
		)
		connection.commit()
		return cursor.rowcount == 1
	finally:
		connection.close()


def get_menu_entries(guild_id: int) -> list[str]:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		menus = connection.execute(
			"SELECT menu FROM menus WHERE guild_id = ? ORDER BY menu COLLATE NOCASE",
			(guild_id,),
		).fetchall()
		return [menu for (menu,) in menus]
	finally:
		connection.close()


def initialize_level_db() -> None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		columns = {
			column[1]
			for column in connection.execute("PRAGMA table_info(user_levels)").fetchall()
		}
		if columns and "guild_id" not in columns:
			legacy_crystal_leaf_column = "crystal_leaf" if "crystal_leaf" in columns else "points"
			connection.execute("ALTER TABLE user_levels RENAME TO user_levels_legacy")
			connection.execute(
				"""
				CREATE TABLE user_levels (
					guild_id INTEGER NOT NULL,
					user_id INTEGER NOT NULL,
					level INTEGER NOT NULL DEFAULT 1,
					crystal_leaf INTEGER NOT NULL DEFAULT 0,
					PRIMARY KEY (guild_id, user_id)
				)
				"""
			)
			connection.execute(
				f"""
				INSERT INTO user_levels (guild_id, user_id, level, crystal_leaf)
				SELECT 0, user_id, level, {legacy_crystal_leaf_column} FROM user_levels_legacy
				"""
			)
			connection.execute("DROP TABLE user_levels_legacy")
		elif not columns:
			connection.execute(
				"""
				CREATE TABLE user_levels (
					guild_id INTEGER NOT NULL,
					user_id INTEGER NOT NULL,
					level INTEGER NOT NULL DEFAULT 1,
					crystal_leaf INTEGER NOT NULL DEFAULT 0,
					PRIMARY KEY (guild_id, user_id)
				)
				"""
			)
		else:
			if "crystal_leaf" not in columns:
				if "points" in columns:
					connection.execute(
						"ALTER TABLE user_levels RENAME COLUMN points TO crystal_leaf"
					)
				else:
					connection.execute(
						"ALTER TABLE user_levels ADD COLUMN crystal_leaf INTEGER NOT NULL DEFAULT 0"
					)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS user_inventory (
				guild_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				item_name TEXT NOT NULL,
				quantity INTEGER NOT NULL DEFAULT 0,
				PRIMARY KEY (guild_id, user_id, item_name)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS banquet_special_uses (
				guild_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				use_date TEXT NOT NULL,
				uses INTEGER NOT NULL DEFAULT 1,
				PRIMARY KEY (guild_id, user_id, use_date)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS user_item_daily_purchases (
				guild_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				item_name TEXT NOT NULL,
				purchase_date TEXT NOT NULL,
				purchase_count INTEGER NOT NULL DEFAULT 0,
				PRIMARY KEY (guild_id, user_id, item_name, purchase_date)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS quiz_questions (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				guild_id INTEGER NOT NULL,
				creator_id INTEGER NOT NULL,
				question TEXT NOT NULL,
				answer TEXT NOT NULL,
				hint TEXT NOT NULL,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS quiz_sessions (
				session_id TEXT PRIMARY KEY,
				guild_id INTEGER NOT NULL,
				creator_id INTEGER NOT NULL,
				question TEXT NOT NULL,
				answer TEXT NOT NULL,
				hint TEXT NOT NULL,
				status TEXT NOT NULL DEFAULT 'active',
				winner_id INTEGER,
				channel_id INTEGER,
				message_id INTEGER,
				created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
			)
			"""
		)
		connection.execute(
			"""
			CREATE UNIQUE INDEX IF NOT EXISTS idx_quiz_one_active_per_guild
			ON quiz_sessions (guild_id) WHERE status = 'active'
			"""
		)
		connection.execute(
			"""
			CREATE INDEX IF NOT EXISTS idx_quiz_solved_winners
			ON quiz_sessions (guild_id, winner_id)
			WHERE status = 'solved' AND winner_id IS NOT NULL
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS quiz_attempts (
				session_id TEXT NOT NULL,
				user_id INTEGER NOT NULL,
				attempts INTEGER NOT NULL DEFAULT 0,
				PRIMARY KEY (session_id, user_id)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS quiz_hints (
				session_id TEXT NOT NULL,
				user_id INTEGER NOT NULL,
				free_used INTEGER NOT NULL DEFAULT 0,
				paid_used INTEGER NOT NULL DEFAULT 0,
				PRIMARY KEY (session_id, user_id)
			)
			"""
		)
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS quiz_guild_cooldowns (
				guild_id INTEGER PRIMARY KEY,
				session_id TEXT NOT NULL,
				started_at REAL NOT NULL
			)
			"""
		)
		connection.commit()
	finally:
		connection.close()


def claim_legacy_user_level(connection: sqlite3.Connection, guild_id: int, user_id: int) -> None:
	if guild_id == 0:
		return
	connection.execute(
		"""
		INSERT OR IGNORE INTO user_levels (guild_id, user_id, level, crystal_leaf)
		SELECT ?, user_id, level, crystal_leaf FROM user_levels WHERE guild_id = 0 AND user_id = ?
		""",
		(guild_id, user_id),
	)
	connection.execute(
		"DELETE FROM user_levels WHERE guild_id = 0 AND user_id = ?",
		(user_id,),
	)


def get_user_level(guild_id: int, user_id: int) -> tuple[int, int]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		claim_legacy_user_level(connection, guild_id, user_id)
		row = connection.execute(
			"SELECT level, crystal_leaf FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		).fetchone()
		connection.commit()
		return row if row else (1, 0)
	finally:
		connection.close()


def get_level_leaderboard(guild_id: int, limit: int = 10) -> list[tuple[int, int, int]]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		rows = connection.execute(
			"""
			SELECT user_id, level, crystal_leaf
			FROM user_levels
			WHERE guild_id = ?
			ORDER BY level DESC, crystal_leaf DESC, user_id ASC
			LIMIT ?
			""",
			(guild_id, limit),
		).fetchall()
		return rows
	finally:
		connection.close()


def get_quiz_leaderboard(guild_id: int, limit: int = 10) -> list[tuple[int, int]]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		return connection.execute(
			"""
			SELECT winner_id, COUNT(*) AS solved_count
			FROM quiz_sessions
			WHERE guild_id = ? AND status = 'solved' AND winner_id IS NOT NULL
			GROUP BY winner_id
			ORDER BY solved_count DESC, winner_id ASC
			LIMIT ?
			""",
			(guild_id, limit),
		).fetchall()
	finally:
		connection.close()


def get_quiz_question_bank(guild_id: int) -> list[tuple[int, str, str, str]]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		return connection.execute(
			"""
			SELECT creator_id, question, answer, hint
			FROM quiz_questions
			WHERE guild_id = ?
			ORDER BY id
			""",
			(guild_id,),
		).fetchall()
	finally:
		connection.close()


def save_quiz_question(
	guild_id: int,
	creator_id: int,
	question: str,
	answer: str,
	hint: str,
) -> None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute(
			"""
			INSERT INTO quiz_questions (guild_id, creator_id, question, answer, hint)
			VALUES (?, ?, ?, ?, ?)
			""",
			(guild_id, creator_id, question, answer, hint),
		)
		connection.commit()
	finally:
		connection.close()


def get_active_quiz_session(guild_id: int) -> str | None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		row = connection.execute(
			"SELECT session_id FROM quiz_sessions WHERE guild_id = ? AND status = 'active'",
			(guild_id,),
		).fetchone()
		return row[0] if row else None
	finally:
		connection.close()


def create_quiz_session(
	guild_id: int,
	creator_id: int,
	question: str,
	answer: str,
	hint: str,
) -> str | None:
	session_id = uuid.uuid4().hex
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		active_session = connection.execute(
			"SELECT 1 FROM quiz_sessions WHERE guild_id = ? AND status = 'active'",
			(guild_id,),
		).fetchone()
		if active_session:
			connection.rollback()
			return None
		connection.execute(
			"""
			INSERT INTO quiz_sessions (
				session_id, guild_id, creator_id, question, answer, hint
			) VALUES (?, ?, ?, ?, ?, ?)
			""",
			(session_id, guild_id, creator_id, question, answer, hint),
		)
		connection.commit()
		return session_id
	finally:
		connection.close()


def start_quiz_session(
	guild_id: int,
	creator_id: int,
	question: str,
	answer: str,
	hint: str,
	now: float | None = None,
) -> tuple[str, str | None, float]:
	current_time = time.time() if now is None else now
	session_id = uuid.uuid4().hex
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		cooldown = connection.execute(
			"SELECT started_at FROM quiz_guild_cooldowns WHERE guild_id = ?",
			(guild_id,),
		).fetchone()
		if cooldown:
			remaining = cooldown[0] + QUIZ_COOLDOWN_SECONDS - current_time
			if remaining > 0:
				connection.rollback()
				return "cooldown", None, remaining

		active_session = connection.execute(
			"SELECT 1 FROM quiz_sessions WHERE guild_id = ? AND status = 'active'",
			(guild_id,),
		).fetchone()
		if active_session:
			connection.rollback()
			return "active", None, 0

		connection.execute(
			"""
			INSERT INTO quiz_sessions (
				session_id, guild_id, creator_id, question, answer, hint
			) VALUES (?, ?, ?, ?, ?, ?)
			""",
			(session_id, guild_id, creator_id, question, answer, hint),
		)
		connection.execute(
			"""
			INSERT INTO quiz_guild_cooldowns (guild_id, session_id, started_at)
			VALUES (?, ?, ?)
			ON CONFLICT(guild_id) DO UPDATE SET
				session_id = excluded.session_id,
				started_at = excluded.started_at
			""",
			(guild_id, session_id, current_time),
		)
		connection.commit()
		return "started", session_id, 0
	finally:
		connection.close()


def save_quiz_message_id(session_id: str, channel_id: int, message_id: int) -> None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		cursor = connection.execute(
			"""
			UPDATE quiz_sessions SET channel_id = ?, message_id = ?
			WHERE session_id = ? AND status = 'active'
			""",
			(channel_id, message_id, session_id),
		)
		connection.commit()
		if cursor.rowcount != 1:
			raise ValueError(f"퀴즈 메시지를 저장할 활성 세션이 없습니다: {session_id}")
	finally:
		connection.close()


def get_active_quiz_messages() -> list[tuple[str, int, int]]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		return connection.execute(
			"""
			SELECT session_id, channel_id, message_id
			FROM quiz_sessions
			WHERE status = 'active' AND channel_id IS NOT NULL AND message_id IS NOT NULL
			"""
		).fetchall()
	finally:
		connection.close()


def cancel_quiz_session(session_id: str) -> None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		connection.execute(
			"UPDATE quiz_sessions SET status = 'cancelled' WHERE session_id = ? AND status = 'active'",
			(session_id,),
		)
		connection.execute(
			"DELETE FROM quiz_guild_cooldowns WHERE session_id = ?",
			(session_id,),
		)
		connection.commit()
	finally:
		connection.close()


def get_quiz_session(session_id: str) -> tuple[int, int, str, str] | None:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		return connection.execute(
			"""
			SELECT guild_id, creator_id, status, answer
			FROM quiz_sessions WHERE session_id = ?
			""",
			(session_id,),
		).fetchone()
	finally:
		connection.close()


def submit_quiz_answer(
	session_id: str,
	user_id: int,
	answer: str,
) -> tuple[str, int, int]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		session = connection.execute(
			"SELECT status, answer, guild_id FROM quiz_sessions WHERE session_id = ?",
			(session_id,),
		).fetchone()
		if session is None or session[0] != "active":
			connection.commit()
			return "inactive", 0, 0

		attempt_row = connection.execute(
			"SELECT attempts FROM quiz_attempts WHERE session_id = ? AND user_id = ?",
			(session_id, user_id),
		).fetchone()
		attempts = attempt_row[0] if attempt_row else 0
		if attempts >= QUIZ_MAX_ATTEMPTS:
			connection.commit()
			return "exhausted", 0, 0

		normalized_answer = " ".join(answer.casefold().split())
		expected_answer = " ".join(session[1].casefold().split())
		if normalized_answer == expected_answer:
			guild_id = session[2]
			crystal_leaf_awarded = random.randint(QUIZ_REWARD_MIN, QUIZ_REWARD_MAX)
			connection.execute(
				"""
				UPDATE quiz_sessions SET status = 'solved', winner_id = ?
				WHERE session_id = ? AND status = 'active'
				""",
				(user_id, session_id),
			)
			claim_legacy_user_level(connection, guild_id, user_id)
			connection.execute(
				"INSERT OR IGNORE INTO user_levels (guild_id, user_id) VALUES (?, ?)",
				(guild_id, user_id),
			)
			level, current_crystal_leaf = connection.execute(
				"SELECT level, crystal_leaf FROM user_levels WHERE guild_id = ? AND user_id = ?",
				(guild_id, user_id),
			).fetchone()
			if level >= MAX_USER_LEVEL:
				current_crystal_leaf += crystal_leaf_awarded
			elif current_crystal_leaf + crystal_leaf_awarded >= (
				level * LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL
			):
				level += 1
				current_crystal_leaf = 0
			else:
				current_crystal_leaf += crystal_leaf_awarded
			connection.execute(
				"""
				UPDATE user_levels SET level = ?, crystal_leaf = ?
				WHERE guild_id = ? AND user_id = ?
				""",
				(level, current_crystal_leaf, guild_id, user_id),
			)
			connection.commit()
			return "correct", QUIZ_MAX_ATTEMPTS - attempts - 1, crystal_leaf_awarded

		connection.execute(
			"""
			INSERT INTO quiz_attempts (session_id, user_id, attempts) VALUES (?, ?, 1)
			ON CONFLICT(session_id, user_id) DO UPDATE SET attempts = attempts + 1
			""",
			(session_id, user_id),
		)
		connection.commit()
		return "incorrect", QUIZ_MAX_ATTEMPTS - attempts - 1, 0
	finally:
		connection.close()


def consume_quiz_hint(
	guild_id: int,
	session_id: str,
	user_id: int,
) -> tuple[str, str | None, int]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		session = connection.execute(
			"SELECT status, hint FROM quiz_sessions WHERE session_id = ? AND guild_id = ?",
			(session_id, guild_id),
		).fetchone()
		if session is None or session[0] != "active":
			connection.commit()
			return "inactive", None, 0

		hint_row = connection.execute(
			"SELECT free_used, paid_used FROM quiz_hints WHERE session_id = ? AND user_id = ?",
			(session_id, user_id),
		).fetchone()
		free_used, paid_used = hint_row if hint_row else (0, 0)
		if not free_used:
			connection.execute(
				"""
				INSERT INTO quiz_hints (session_id, user_id, free_used)
				VALUES (?, ?, 1)
				ON CONFLICT(session_id, user_id) DO UPDATE SET free_used = 1
				""",
				(session_id, user_id),
			)
			connection.commit()
			return "free", session[1], 0
		if paid_used:
			connection.commit()
			return "used", None, 0

		claim_legacy_user_level(connection, guild_id, user_id)
		balance_row = connection.execute(
			"SELECT crystal_leaf FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		).fetchone()
		balance = balance_row[0] if balance_row else 0
		if balance < QUIZ_HINT_COST:
			connection.commit()
			return "insufficient", None, balance

		connection.execute(
			"""
			UPDATE user_levels SET crystal_leaf = crystal_leaf - ?
			WHERE guild_id = ? AND user_id = ?
			""",
			(QUIZ_HINT_COST, guild_id, user_id),
		)
		connection.execute(
			"""
			INSERT INTO quiz_hints (session_id, user_id, free_used, paid_used)
			VALUES (?, ?, 1, 1)
			ON CONFLICT(session_id, user_id) DO UPDATE SET paid_used = 1
			""",
			(session_id, user_id),
		)
		connection.commit()
		return "paid", session[1], balance - QUIZ_HINT_COST
	finally:
		connection.close()


def give_up_quiz(session_id: str, user_id: int) -> tuple[str, str | None]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		session = connection.execute(
			"SELECT status, answer FROM quiz_sessions WHERE session_id = ?",
			(session_id,),
		).fetchone()
		if session is None or session[0] != "active":
			connection.commit()
			return "inactive", None
		connection.execute(
			"""
			UPDATE quiz_sessions SET status = 'abandoned', winner_id = ?
			WHERE session_id = ? AND status = 'active'
			""",
			(user_id, session_id),
		)
		connection.commit()
		return "abandoned", session[1]
	finally:
		connection.close()


def award_user_crystal_leaf(
	guild_id: int,
	user_id: int,
	crystal_leaf_awarded: int,
) -> tuple[int, int, bool]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		claim_legacy_user_level(connection, guild_id, user_id)
		connection.execute(
			"INSERT OR IGNORE INTO user_levels (guild_id, user_id) VALUES (?, ?)",
			(guild_id, user_id),
		)
		level, current_crystal_leaf = connection.execute(
			"SELECT level, crystal_leaf FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		).fetchone()
		if level >= MAX_USER_LEVEL:
			connection.execute(
				"UPDATE user_levels SET crystal_leaf = 0 WHERE guild_id = ? AND user_id = ?",
				(guild_id, user_id),
			)
			connection.commit()
			return MAX_USER_LEVEL, 0, False

		levelled_up = current_crystal_leaf + crystal_leaf_awarded >= level * LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL
		if levelled_up:
			level += 1
			current_crystal_leaf = 0
		else:
			current_crystal_leaf += crystal_leaf_awarded
		connection.execute(
			"UPDATE user_levels SET level = ?, crystal_leaf = ? WHERE guild_id = ? AND user_id = ?",
			(level, current_crystal_leaf, guild_id, user_id),
		)
		connection.commit()
		return level, current_crystal_leaf, levelled_up
	finally:
		connection.close()


def reset_user_level(guild_id: int, user_id: int) -> bool:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		claim_legacy_user_level(connection, guild_id, user_id)
		cursor = connection.execute(
			"DELETE FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		)
		connection.commit()
		return cursor.rowcount == 1
	finally:
		connection.close()


def reset_guild_levels(guild_id: int) -> int:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		cursor = connection.execute(
			"DELETE FROM user_levels WHERE guild_id = ?",
			(guild_id,),
		)
		connection.commit()
		return cursor.rowcount
	finally:
		connection.close()


def subtract_user_levels(guild_id: int, user_id: int, levels_to_subtract: int) -> tuple[int, int]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		claim_legacy_user_level(connection, guild_id, user_id)
		connection.execute(
			"INSERT OR IGNORE INTO user_levels (guild_id, user_id) VALUES (?, ?)",
			(guild_id, user_id),
		)
		current_level = connection.execute(
			"SELECT level FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		).fetchone()[0]
		new_level = max(1, current_level - levels_to_subtract)
		connection.execute(
			"UPDATE user_levels SET level = ?, crystal_leaf = 0 WHERE guild_id = ? AND user_id = ?",
			(new_level, guild_id, user_id),
		)
		connection.commit()
		return current_level, new_level
	finally:
		connection.close()


def buy_shop_item(guild_id: int, user_id: int, item_name: str) -> tuple[bool, int, bool, int]:
	item = ITEM_LIST.get(item_name)
	if item is None:
		raise ValueError(f"상점에 없는 아이템입니다: {item_name}")
	price = item["price"]
	daily_limit = item.get("daily_limit", 0)
	purchase_date = datetime.now(KST).date().isoformat()

	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		claim_legacy_user_level(connection, guild_id, user_id)
		connection.execute(
			"INSERT OR IGNORE INTO user_levels (guild_id, user_id) VALUES (?, ?)",
			(guild_id, user_id),
		)
		crystal_leaf_balance = connection.execute(
			"SELECT crystal_leaf FROM user_levels WHERE guild_id = ? AND user_id = ?",
			(guild_id, user_id),
		).fetchone()[0]
		row = connection.execute(
			"""
			SELECT purchase_count FROM user_item_daily_purchases
			WHERE guild_id = ? AND user_id = ? AND item_name = ? AND purchase_date = ?
			""",
			(guild_id, user_id, item_name, purchase_date),
		).fetchone()
		purchases_today = row[0] if row else 0
		if daily_limit > 0 and purchases_today >= daily_limit:
			connection.commit()
			return False, crystal_leaf_balance, True, purchases_today
		if crystal_leaf_balance < price:
			connection.commit()
			return False, crystal_leaf_balance, False, purchases_today

		connection.execute(
			"UPDATE user_levels SET crystal_leaf = crystal_leaf - ? WHERE guild_id = ? AND user_id = ?",
			(price, guild_id, user_id),
		)
		connection.execute(
			"""
			INSERT INTO user_inventory (guild_id, user_id, item_name, quantity)
			VALUES (?, ?, ?, 1)
			ON CONFLICT(guild_id, user_id, item_name)
			DO UPDATE SET quantity = quantity + 1
			""",
			(guild_id, user_id, item_name),
		)
		connection.execute(
			"""
			INSERT INTO user_item_daily_purchases (
				guild_id, user_id, item_name, purchase_date, purchase_count
			) VALUES (?, ?, ?, ?, 1)
			ON CONFLICT(guild_id, user_id, item_name, purchase_date)
			DO UPDATE SET purchase_count = purchase_count + 1
			""",
			(guild_id, user_id, item_name, purchase_date),
		)
		connection.commit()
		return True, crystal_leaf_balance - price, False, purchases_today + 1
	finally:
		connection.close()


def consume_banquet_special_use(
	guild_id: int,
	user_id: int,
	use_date: date | None = None,
) -> tuple[bool, bool]:
	date_key = (use_date or datetime.now(KST).date()).isoformat()
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		connection.execute("BEGIN IMMEDIATE")
		row = connection.execute(
			"SELECT uses FROM banquet_special_uses WHERE guild_id = ? AND user_id = ? AND use_date = ?",
			(guild_id, user_id, date_key),
		).fetchone()
		if row is None:
			connection.execute(
				"INSERT INTO banquet_special_uses (guild_id, user_id, use_date, uses) VALUES (?, ?, ?, 1)",
				(guild_id, user_id, date_key),
			)
			connection.commit()
			return True, False

		inventory_row = connection.execute(
			"SELECT quantity FROM user_inventory WHERE guild_id = ? AND user_id = ? AND item_name = ?",
			(guild_id, user_id, "소화제"),
		).fetchone()
		if inventory_row is None or inventory_row[0] < 1:
			connection.commit()
			return False, False

		connection.execute(
			"UPDATE user_inventory SET quantity = quantity - 1 WHERE guild_id = ? AND user_id = ? AND item_name = ?",
			(guild_id, user_id, "소화제"),
		)
		connection.execute(
			"UPDATE banquet_special_uses SET uses = uses + 1 WHERE guild_id = ? AND user_id = ? AND use_date = ?",
			(guild_id, user_id, date_key),
		)
		connection.commit()
		return True, True
	finally:
		connection.close()


def get_user_inventory(guild_id: int, user_id: int) -> list[tuple[str, int]]:
	connection = sqlite3.connect(LEVEL_DB_FILE)
	try:
		return connection.execute(
			"""
			SELECT item_name, quantity FROM user_inventory
			WHERE guild_id = ? AND user_id = ? AND quantity > 0
			ORDER BY item_name COLLATE NOCASE
			""",
			(guild_id, user_id),
		).fetchall()
	finally:
		connection.close()


def format_inventory_items(items: list[tuple[str, int]]) -> str:
	if not items:
		return "보유한 아이템이 없습니다. `/골디상점`에서 아이템을 구매해보세요."
	return "\n".join(
		f"**{name}** × {quantity} · {ITEM_LIST.get(name, {}).get('description', "(설명 없음)")}\n"
		for name, quantity in items
	)


def roll_menu_reward_crystal_leaf() -> int:
	if random.random() < LOTTERY_CRYSTAL_LEAF_CHANCE:
		return 100
	return random.randint(1, 10)


def make_menu_list_embed(menus: list[str], page: int = 0) -> discord.Embed:
	page_count = max(1, math.ceil(len(menus) / MENU_PAGE_SIZE))
	page = min(max(page, 0), page_count - 1)
	start = page * MENU_PAGE_SIZE
	embed = discord.Embed(
		title="등록된 메뉴 목록",
		color=discord.Color.green(),
	)
	for index, menu in enumerate(menus[start : start + MENU_PAGE_SIZE], start=start + 1):
		embed.add_field(name=f"{index}.", value=menu, inline=True)
	embed.set_footer(text=f"페이지 {page + 1} / {page_count} · 전체 {len(menus)}개")
	return embed


def delete_menu(guild_id: int, menu: str, user_id: int, is_admin: bool = False) -> bool:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		if is_admin:
			cursor = connection.execute(
				"DELETE FROM menus WHERE guild_id = ? AND menu = ?",
				(guild_id, menu),
			)
		else:
			cursor = connection.execute(
				"DELETE FROM menus WHERE guild_id = ? AND menu = ? AND owner_id = ?",
				(guild_id, menu, user_id),
			)
		connection.commit()
		return cursor.rowcount == 1
	finally:
		connection.close()


class MenuListView(discord.ui.View):
	def __init__(self, menus: list[str], requester_id: int) -> None:
		super().__init__(timeout=120)
		self.menus = menus
		self.requester_id = requester_id
		self.page = 0
		self.page_count = max(1, math.ceil(len(menus) / MENU_PAGE_SIZE))
		self._update_buttons()

	def _update_buttons(self) -> None:
		self.previous_button.disabled = self.page == 0
		self.next_button.disabled = self.page >= self.page_count - 1

	async def _change_page(self, interaction: discord.Interaction, page: int) -> None:
		if interaction.user.id != self.requester_id:
			await interaction.response.send_message(
				"이 메뉴 목록을 실행한 사용자만 페이지를 넘길 수 있습니다.",
				ephemeral=True,
			)
			return

		self.page = page
		self._update_buttons()
		await interaction.response.edit_message(
			embed=make_menu_list_embed(self.menus, self.page),
			view=self,
		)

	@discord.ui.button(label="이전", style=discord.ButtonStyle.secondary)
	async def previous_button(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button,
	) -> None:
		await self._change_page(interaction, self.page - 1)

	@discord.ui.button(label="다음", style=discord.ButtonStyle.primary)
	async def next_button(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button,
	) -> None:
		await self._change_page(interaction, self.page + 1)


def clear_menus(guild_id: int) -> int:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		cursor = connection.execute(
			"DELETE FROM menus WHERE guild_id = ?",
			(guild_id,),
		)
		connection.commit()
		return cursor.rowcount
	finally:
		connection.close()


def get_random_menu(
	guild_id: int,
	category: str = "일반 음식",
) -> tuple[str | None, int]:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		menus = connection.execute(
			"SELECT menu FROM menus WHERE guild_id = ? AND category = ?",
			(guild_id, category),
		).fetchall()
		return (random.choice(menus)[0], len(menus)) if menus else (None, 0)
	finally:
		connection.close()


def format_menu_recommendation(menu: str) -> str:
	if random.random() < 0.001:
		return "# _난 마들렌이야_"

	return random.choice(
		[
			f"오늘의 추천 메뉴, **{menu}**을(를) 먹어보세요!",
			f"오늘 메뉴는 고민할 것도 없이 **{menu}**을(를) 먹어봐요.",
			f"오늘의 메뉴는 **{menu}**인거사와요.",
		]
	)


def format_menu_recommendation_response(
	category: str,
	menu: str,
	progress_message: str | None = None,
	is_banquet_special: bool = False,
) -> str:
	recommendation = format_menu_recommendation(menu)
	if is_banquet_special:
		return f"{recommendation}\n{progress_message}" if progress_message else recommendation
	message = f"**{category} 추천:** {recommendation}"
	return f"{message}\n{progress_message}" if progress_message else message


def get_admin_ids() -> set[int]:
	value = os.getenv("ADMIN_IDS") or os.getenv("MENU_ADMIN_IDS", "")
	admins: set[int] = set()
	for item in value.split(","):
		candidate = item.strip()
		if not candidate:
			continue
		try:
			admins.add(int(candidate))
		except ValueError:
			logger.warning("ADMIN_IDS에 잘못된 값이 포함되어 있습니다: %s", candidate)
	return admins


def get_admin_channel_id() -> int | None:
	channel_id = os.getenv("ADMIN_CHANNEL_ID")
	if not channel_id:
		return None
	try:
		return int(channel_id)
	except ValueError:
		logger.warning("ADMIN_CHANNEL_ID가 올바른 숫자가 아닙니다: %s", channel_id)
		return None


def parse_ping_latency(raw_output: str) -> str:
	match = re.search(r"time=(\d+(?:\.\d+)?)\s*ms", raw_output, re.IGNORECASE)
	if match:
		return f"{match.group(1)}ms"
		
	match = re.search(r"round-trip min/avg/max/stddev = .*?/((?:\d+(?:\.\d+)?)) ms", raw_output, re.IGNORECASE)
	if match:
		return f"{match.group(1)}ms"
	
	match = re.search(r"\b(\d+(?:\.\d+)?)\s*ms\b", raw_output, re.IGNORECASE)
	if match:
		return f"{match.group(1)}ms"
	
	return "측정 실패"


def format_uptime_seconds(total_seconds: float | int) -> str:
	total = int(total_seconds)
	days, remainder = divmod(total, 86400)
	hours, remainder = divmod(remainder, 3600)
	minutes, seconds = divmod(remainder, 60)
	parts = []
	if days:
		parts.append(f"{days}일")
	if hours or days:
		parts.append(f"{hours}시간")
	if minutes or hours or days:
		parts.append(f"{minutes}분")
	parts.append(f"{seconds}초")
	return " ".join(parts)


def parse_uptime_text(uptime_text: str) -> str:
	units = {
		"week": 604800,
		"weeks": 604800,
		"day": 86400,
		"days": 86400,
		"hour": 3600,
		"hours": 3600,
		"minute": 60,
		"minutes": 60,
		"second": 1,
		"seconds": 1,
	}
	total_seconds = 0
	for value, unit in re.findall(r"(\d+)\s+(weeks?|days?|hours?|minutes?|seconds?)", uptime_text.lower()):
		total_seconds += int(value) * units[unit]
	return format_uptime_seconds(total_seconds) if total_seconds else "-"


def read_text_file(path: str) -> str:
	try:
		return Path(path).read_text(encoding="utf-8", errors="replace")
	except OSError:
		return ""


def android_command_candidates(command: list[str]) -> list[list[str]]:
	if command[0] == "termux-battery-status":
		return [
			command,
			["/data/data/com.termux/files/usr/bin/termux-battery-status"],
		]
	if command[0] in {"dumpsys", "cmd"}:
		return [command, [f"/system/bin/{part}" if index == 0 else part for index, part in enumerate(command)]]
	return [command]


def get_android_device_model() -> str:
	for cmd in (["getprop", "ro.product.model"], ["cat", "/system/build.prop"]):
		try:
			result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=2)
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
		if result.returncode == 0:
			output = result.stdout.strip()
			if not output:
				continue
			for line in output.splitlines():
				if "ro.product.model" in line:
					value = line.split("=", 1)[1].strip()
					if value:
						return value
			if output and "model" not in output.lower():
				return output.splitlines()[0].strip()
	return "SM-F731N"


def get_battery_status() -> tuple[str, str]:
	android_battery_states = {
		"1": "알 수 없음",
		"2": "충전 중",
		"3": "방전 중",
		"4": "충전 안 함",
		"5": "완전 충전",
	}
	results = [
		["termux-battery-status"],
		["dumpsys", "battery"],
	]
	for command in results:
		for candidate in android_command_candidates(command):
			try:
				result = subprocess.run(candidate, capture_output=True, text=True, check=False, timeout=3)
			except (FileNotFoundError, subprocess.TimeoutExpired):
				logger.debug("배터리 조회 명령을 사용할 수 없습니다: %s", candidate[0])
				continue
			if result.returncode != 0:
				logger.debug("배터리 조회 명령 실패: %s, stderr=%s", candidate[0], result.stderr.strip())
				continue
			output = result.stdout.strip()
			if not output:
				continue

			if command[0] == "termux-battery-status":
				try:
					payload = json.loads(output)
					percentage = payload.get("percentage")
					status = payload.get("status")
					if percentage is not None:
						status_text = android_battery_states.get(str(status), str(status or "알 수 없음"))
						return f"{int(percentage)}%", status_text
				except (json.JSONDecodeError, TypeError, ValueError):
					pass

			match_level = re.search(r"(?:level|percentage)\s*[:=]\s*(\d+)", output, re.IGNORECASE)
			match_status = re.search(r"(?:status)\s*[:=]\s*([A-Za-z_]+|\d+)", output, re.IGNORECASE)
			if match_level:
				status_value = match_status.group(1) if match_status else "알 수 없음"
				status_text = android_battery_states.get(status_value, status_value)
				return f"{match_level.group(1)}%", status_text

	# Android 12+에서도 cmd battery가 dumpsys보다 허용되는 경우가 있습니다.
	for command in (["cmd", "battery", "get-level"], ["cmd", "battery", "get-status"]):
		for candidate in android_command_candidates(command):
			try:
				result = subprocess.run(candidate, capture_output=True, text=True, check=False, timeout=2)
			except (FileNotFoundError, subprocess.TimeoutExpired):
				continue
			if result.returncode != 0:
				continue
			output = result.stdout.strip()
			if command[-1] == "get-level" and output.isdigit():
				return f"{int(output)}%", "알 수 없음"

	power_supply_dir = Path("/sys/class/power_supply")
	if power_supply_dir.is_dir():
		for capacity_path in power_supply_dir.glob("*/capacity"):
			capacity = capacity_path.read_text(encoding="utf-8", errors="replace").strip()
			if not capacity.isdigit():
				continue
			status_path = capacity_path.with_name("status")
			try:
				battery_state = status_path.read_text(encoding="utf-8", errors="replace").strip()
			except OSError:
				battery_state = "알 수 없음"
			return f"{int(capacity)}%", battery_state or "알 수 없음"

	logger.warning("배터리 정보를 찾지 못했습니다. Termux:API 또는 Android power_supply 경로를 확인하세요.")
	return "-", "-"


def get_ram_usage() -> tuple[str, str, str]:
	meminfo = read_text_file("/proc/meminfo")
	if meminfo:
		values: dict[str, int] = {}
		for line in meminfo.splitlines():
			if not line.strip():
				continue
			key, value = line.split(":", 1)
			if key.strip() in {"MemTotal", "MemAvailable", "MemFree"}:
				try:
					values[key.strip()] = int(value.strip().split()[0])
				except (IndexError, ValueError):
					continue
		if "MemTotal" in values and "MemAvailable" in values:
			total_kb = values["MemTotal"]
			available_kb = values["MemAvailable"]
			used_kb = max(0, total_kb - available_kb)
			percent = 0 if total_kb == 0 else round((used_kb / total_kb) * 100)
			return f"{used_kb / 1024:.0f}MB", f"{total_kb / 1024:.0f}MB", f"{percent}%"

	for cmd in (["free", "-m"], ["free", "-k"]):
		try:
			result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=3)
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
		if result.returncode != 0:
			continue
		lines = result.stdout.splitlines()
		if len(lines) < 2:
			continue
		parts = lines[1].split()
		if len(parts) < 3:
			continue
		total = int(parts[1])
		used = int(parts[2])
		percent = 0 if total == 0 else round((used / total) * 100)
		if cmd[1] == "-m":
			return f"{used:.0f}MB", f"{total:.0f}MB", f"{percent}%"
		return f"{used / 1024:.0f}MB", f"{total / 1024:.0f}MB", f"{percent}%"

	return "-", "-", "-"


def get_cpu_usage() -> str:
	try:
		stat_before = read_text_file("/proc/stat").splitlines()[0]
		before_fields = stat_before.split()[1:]
		before_total = sum(int(value) for value in before_fields)
		before_idle = int(before_fields[3])
		time.sleep(1.0)
		stat_after = read_text_file("/proc/stat").splitlines()[0]
		after_fields = stat_after.split()[1:]
		after_total = sum(int(value) for value in after_fields)
		after_idle = int(after_fields[3])
		delta_total = after_total - before_total
		delta_idle = after_idle - before_idle
		if delta_total <= 0:
			return "-"
		usage = max(0.0, 100.0 * (1.0 - (delta_idle / delta_total)))
		return f"{usage:.1f}%"
	except (IndexError, ValueError, OSError):
		try:
			loadavg = read_text_file("/proc/loadavg").split()
			if loadavg:
				cpu_count = os.cpu_count() or 1
				return f"{min(100.0, max(0.0, float(loadavg[0]) / cpu_count * 100)):.1f}%"
			get_loadavg = getattr(os, "getloadavg", None)
			if get_loadavg is None:
				return "-"
			load_1m = get_loadavg()[0]
			cpu_count = os.cpu_count() or 1
			return f"{min(100.0, max(0.0, load_1m / cpu_count * 100)):.1f}%"
		except (AttributeError, OSError):
			pass
	try:
		result = subprocess.run(
			["top", "-b", "-n", "1"],
			capture_output=True,
			text=True,
			check=False,
			timeout=3,
		)
		cpu_match = re.search(r"(?:Cpu\(s\)|CPU):\s*(?:[\d.]+\s*us,\s*)?([\d.]+)\s*id", result.stdout, re.IGNORECASE)
		if result.returncode == 0 and cpu_match:
			return f"{max(0.0, 100.0 - float(cpu_match.group(1))):.1f}%"
		cpu_match = re.search(r"(?:CPU usage|CPU):\s*([\d.]+)%\s*(?:user|us).*?([\d.]+)%\s*idle", result.stdout, re.IGNORECASE)
		if result.returncode == 0 and cpu_match:
			return f"{max(0.0, 100.0 - float(cpu_match.group(2))):.1f}%"
	except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
		pass
	for command in (["dumpsys", "cpuinfo"], ["/system/bin/dumpsys", "cpuinfo"]):
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=3)
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
		if result.returncode != 0:
			continue
		cpu_match = re.search(r"Total CPU usage:\s*([\d.]+)%", result.stdout, re.IGNORECASE)
		if cpu_match:
			return f"{float(cpu_match.group(1)):.1f}%"
	logger.warning("CPU 사용량을 계산하지 못했습니다. /proc/stat 또는 top 출력을 확인하세요.")
	return "-"


def get_ping_latency() -> str:
	for command in (["ping", "-c", "1", "-W", "2", "8.8.8.8"], ["ping", "-c", "1", "1.1.1.1"], ["ping", "-c", "1", "localhost"]):
		try:
			result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=3)
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
		output = (result.stdout or "") + (result.stderr or "")
		if not output:
			continue
		parsed = parse_ping_latency(output)
		if parsed != "측정 실패":
			return parsed
	return "측정 실패"


def get_uptime() -> str:
	uptime_text = read_text_file("/proc/uptime")
	if uptime_text:
		try:
			return format_uptime_seconds(float(uptime_text.split()[0]))
		except (IndexError, ValueError):
			pass
	try:
		result = subprocess.run(["uptime", "-p"], capture_output=True, text=True, check=False, timeout=2)
		if result.returncode == 0 and result.stdout.strip():
			parsed = parse_uptime_text(result.stdout)
			if parsed != "-":
				return parsed
	except (FileNotFoundError, subprocess.TimeoutExpired):
		pass
	try:
		clock_boottime = getattr(time, "CLOCK_BOOTTIME", None)
		get_clock_time = getattr(time, "clock_gettime", None)
		if clock_boottime is not None and get_clock_time is not None:
			return format_uptime_seconds(get_clock_time(clock_boottime))
	except (AttributeError, OSError):
		pass
	return "-"


def get_storage_usage() -> tuple[str, str, str]:
	for path in ["/data", "/", "/storage/emulated/0"]:
		try:
			usage = shutil.disk_usage(path)
			total_bytes = usage.total
			used_bytes = usage.used
			percent = 0 if total_bytes == 0 else round((used_bytes / total_bytes) * 100)
			return f"{used_bytes / (1024 ** 3):.1f}GB", f"{total_bytes / (1024 ** 3):.1f}GB", f"{percent}%"
		except OSError:
			pass

		try:
			result = subprocess.run(["df", "-k", path], capture_output=True, text=True, check=False, timeout=2)
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
		if result.returncode != 0:
			continue
		lines = result.stdout.strip().splitlines()
		if len(lines) < 2:
			continue
		columns = lines[1].split()
		if len(columns) < 4:
			continue
		try:
			total_kb = int(columns[1])
			used_kb = int(columns[2])
		except ValueError:
			continue
		percent = 0 if total_kb == 0 else round((used_kb / total_kb) * 100)
		return f"{used_kb / 1024:.1f}GB", f"{total_kb / 1024:.1f}GB", f"{percent}%"
	return "-", "-", "-"


def get_system_status_snapshot(uptime_override: str | None = None) -> dict[str, str]:
	device_model = get_android_device_model()
	ram_used, ram_total, ram_percent = get_ram_usage()
	ping_latency = get_ping_latency()
	uptime = uptime_override or get_uptime()
	storage_used, storage_total, storage_percent = get_storage_usage()
	return {
		"device_model": device_model,
		"ram_used": ram_used,
		"ram_total": ram_total,
		"ram_percent": ram_percent,
		"ping": ping_latency,
		"uptime": uptime,
		"storage_used": storage_used,
		"storage_total": storage_total,
		"storage_percent": storage_percent,
	}


def is_menu_admin(user: discord.abc.User | discord.User | discord.Member | None) -> bool:
	if user is None:
		return False
	if isinstance(user, discord.Member) and user.guild_permissions.administrator:
		return True
	return user.id in get_admin_ids()


class HelpLanguageSelect(discord.ui.Select):
	def __init__(self, requester_id: int) -> None:
		super().__init__(
			placeholder="도움말 언어를 선택하세요 / 言語を選択してください",
			options=[
				discord.SelectOption(label="한국어", value="kor", description="한국어 도움말"),
				discord.SelectOption(label="日本語", value="jpn", description="日本語のヘルプ"),
			],
		)
		self.requester_id = requester_id

	async def callback(self, interaction: discord.Interaction) -> None:
		if interaction.user.id != self.requester_id:
			await interaction.response.send_message(
				"이 도움말 선택 메뉴를 실행한 사용자만 사용할 수 있습니다.",
				ephemeral=True,
			)
			return

		help_message = Help_Message_KOR if self.values[0] == "kor" else Help_Message_JPN
		help_message = help_message.format(
			mention=interaction.user.mention,
			ClientBuild=ClientBuild,
			ClientVersion=ClientVersion,
			ClientBuildDate=ClientBuildDate,
		)
		try:
			await interaction.user.send(help_message)
		except discord.Forbidden:
			await interaction.response.send_message(
				"DM을 보낼 수 없습니다. 사용자 설정에서 서버 멤버의 DM 수신을 허용해주세요.",
				ephemeral=True,
			)
			return
		except discord.HTTPException:
			logger.exception("도움말 DM 전송 실패: user_id=%s", interaction.user.id)
			await interaction.response.send_message(
				"도움말을 DM으로 보내지 못했습니다. 잠시 후 다시 시도해주세요.",
				ephemeral=True,
			)
			return

		view = self.view
		if view is not None:
			view.stop()
			for child in view.children:
				child.disabled = True
		await interaction.response.edit_message(
			content="도움말을 DM으로 보냈습니다.",
			view=view,
		)


class HelpLanguageView(discord.ui.View):
	def __init__(self, requester_id: int) -> None:
		super().__init__(timeout=120)
		self.add_item(HelpLanguageSelect(requester_id))


@app_commands.command(
	name="도움말",
	description="원하는 언어로 도움말을 DM으로 받을 수 있어요.",
)
async def help_command(interaction: discord.Interaction) -> None:
	log_command_trigger("도움말", interaction.user)
	await interaction.response.send_message(
		"도움말을 받을 언어를 선택해주세요.",
		view=HelpLanguageView(interaction.user.id),
		ephemeral=True,
	)


@commands.command(name="버터")
async def butter_command(ctx: commands.Context) -> None:
	log_command_trigger("버터", ctx.author)
	message = (
		"각그랜저다!!!"
		if ctx.author.id in get_admin_ids()
		else "안녕하세요 저는 버터애요!"
	)
	await ctx.send(message)

@commands.command(name="티그")
async def tig_command(ctx: commands.Context) -> None:
	log_command_trigger("티그", ctx.author)
	global tig_cooldown_until
	now = time.monotonic()
	if tig_cooldown_until is not None:
		remaining = tig_cooldown_until - now
		if remaining > 0:
			#remaining_minutes = math.ceil(remaining / 60)
			#await ctx.send(
			#	f"이 명령어는 2시간 쿨타임이 있습니다. {remaining_minutes}분 후 다시 시도해주세요."
			#)
			# 터질듯한 쿨타임안내?
			#터져서 없어짐 수고하세요ㅋ
			return
	tig_cooldown_until = now + TIG_COOLDOWN_SECONDS
	message = random.choice(
		[
			"허~졉♡ 이딴게 좋은거야~? 최악♡최저♡ 저질이네♡ 역겨워...♡",
			"허졉 이딴말을 듣고싶어서 그런 글이나 싸지르고 정말한심하네♡",
			"허접~ 주제를 알아야지♡ 역겨우니까 말 걸지 마♡",
			"시끄러워♡ 허접 주제에 울기나 하고...♡",
			"허접... 이예요오...",
		]
	)
	await ctx.send(message)
	


@commands.command(name="cnstSuro:stop")
async def stop_command(ctx: commands.Context) -> None:
	log_command_trigger("cnstSuro:stop", ctx.author)
	if ctx.author.id not in get_admin_ids():
		await ctx.send("# _난 마들렌이야_")
		return
	await ctx.bot.close()


@commands.command(name="cnst:suro!saveLog", aliases=["saveLog"])
async def save_log_command(ctx: commands.Context) -> None:
	log_command_trigger("cnst:suro!saveLog", ctx.author)
	if ctx.author.id not in get_admin_ids():
		await ctx.reply("이 명령어는 관리자만 사용할 수 있사와요.")
		return

	logger.info("로그 수동 저장 요청: user_id=%s", ctx.author.id)
	snapshot_path, sent_to_developer = await ctx.bot.save_logs_and_notify(
		f"Discord 명령어로 로그 저장 요청 (user_id={ctx.author.id})"
	)
	if snapshot_path is None:
		message = "서버 로그 파일 저장에 실패했습니다."
	elif sent_to_developer:
		message = f"로그를 서버에 저장하고 개발자 DM으로 전송했습니다: `{snapshot_path.name}`"
	else:
		message = f"로그는 서버에 저장했지만 개발자 DM 전송에 실패했습니다: `{snapshot_path.name}`"
	await ctx.reply(message)


@app_commands.command(
	name="상태",
	description="서버의 상태를 확인할 수 있어요.",
)
async def status_command(interaction: discord.Interaction) -> None:
	log_command_trigger("상태", interaction.user)
	interaction_age = max(0.0, time.time() - interaction.created_at.timestamp())
	logger.info(
		"상태 명령어 수신: interaction_id=%s, age=%.3fs, latency=%sms",
		interaction.id,
		interaction_age,
		getattr(interaction.client.ws, "latency", 0) * 1000,
	)
	try:
		await interaction.response.send_message("서버 상태를 조회하고 있습니다...", ephemeral=True)
	except discord.NotFound:
		logger.warning(
			"상태 명령어의 초기 응답이 만료되었습니다: interaction_id=%s, age=%.3fs",
			interaction.id,
			interaction_age,
		)
		return
	except discord.HTTPException as error:
		logger.exception("상태 명령어 초기 응답 실패: status=%s", error.status)
		return

	try:
		login_started_at = getattr(interaction.client, "login_started_at", None)
		uptime_override = (
			format_uptime_seconds(time.monotonic() - login_started_at)
			if login_started_at is not None
			else None
		)
		status = await asyncio.wait_for(
			asyncio.to_thread(get_system_status_snapshot, uptime_override),
			timeout=12,
		)
	except Exception as error:
		logger.exception("상태 조회 실패: %s", error)
		try:
			await interaction.edit_original_response(
				content="서버 상태를 불러오지 못했습니다ㅋ. 서버 환경이 정상인지 확인해주세요."
			)
		except discord.NotFound:
			logger.warning("상태 명령어 오류 안내가 만료되었습니다: interaction_id=%s", interaction.id)
		return

	embed = discord.Embed(
		title=f"서버 상태",
		color=discord.Color.green(),
	)
	embed.add_field(
		name="RAM 사용량",
		value=f"{status['ram_used']} / {status['ram_total']} ({status['ram_percent']})",
		inline=True,
	)
	embed.add_field(
		name="통신속도(핑)",
		value=status['ping'],
		inline=True,
	)
	embed.add_field(
		name="가동시간",
		value=status['uptime'],
		inline=True,
	)
	embed.add_field(
		name="스토리지",
		value=f"{status['storage_used']} / {status['storage_total']} ({status['storage_percent']})",
		inline=True,
	)
	embed.set_footer(text="Powered by Nikuyi")
	try:
		await interaction.edit_original_response(content=None, embed=embed)
	except discord.NotFound:
		logger.warning("상태 명령어 결과 전송이 만료되었습니다: interaction_id=%s", interaction.id)


def make_event_embed(event: dict[str, str]) -> discord.Embed:
	embed = discord.Embed(
		title=event.get("title", "행사명 없음"),
		url=event.get("submitLink") or BASE_URL,
		color=discord.Color.blue(),
	)
	embed.set_author(name="ComicWorld", icon_url=COMICWORLD_EMOJI_URL)
	embed.add_field(
		name="기간",
		value=f"{event.get('startDate', '-')} ~ {event.get('endDate', '-')}",
		inline=False,
	)
	embed.add_field(name="장소", value=event.get("place", "-"), inline=False)
	if event.get("tag"):
		embed.add_field(name="태그", value=f"#{event['tag']}", inline=True)
	embed.set_footer(text="Comic World 행사정보")
	return embed


def get_nearest_events(events: list[dict[str, str]]) -> list[dict[str, str]]:
	today = date.today()
	upcoming = []
	for event in events:
		try:
			start_date = date.fromisoformat(event["startDate"])
		except (KeyError, ValueError):
			continue
		if start_date >= today:
			upcoming.append((start_date, event))

	if upcoming:
		return [event for _, event in sorted(upcoming, key=lambda item: item[0])]
	return events



@app_commands.command(
	name="메뉴추가",# 아 줴줴이야
	description="카테고리별로 메뉴를 만들 수 있어요.",
)
@app_commands.describe(menu="등록할 메뉴 문자열", category="메뉴 분류")
@app_commands.choices(
	category=[
		app_commands.Choice(name="일반 음식", value="일반 음식"),
		app_commands.Choice(name="디저트", value="디저트"),
		app_commands.Choice(name="괴랄한 음식", value="괴랄한 음식"),
	]
)
async def add_menu_command(
	interaction: discord.Interaction,
	menu: str,
	category: app_commands.Choice[str],
) -> None:
	log_command_trigger("메뉴추가", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	menu = menu.strip()
	if not menu:
		await interaction.response.send_message(
			"등록할 메뉴를 입력해주세요.",
			ephemeral=True,
		)
		return
	if len(menu) > 100:
		await interaction.response.send_message(
			"메뉴는 100자 이내로 입력해주세요.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	was_added = await asyncio.to_thread(
		add_menu,
		interaction.guild_id,
		menu,
		interaction.user.id,
		category.value,
	)
	logger.info(
		"메뉴 등록: guild_id=%s, user_id=%s, username=%s, category=%s, menu=%s, added=%s",
		interaction.guild_id,
		interaction.user.id,
		str(interaction.user),
		category.value,
		menu,
		was_added,
	)
	message = (
		f"`{menu}` 메뉴를 **{category.name}** 분류로 등록했습니다."
		if was_added
		else f"`{menu}` 메뉴는 이미 등록되어 있습니다."
	)
	await interaction.response.send_message(message, ephemeral=True)


@app_commands.command(
	name="메뉴목록",
	description="등록된 메뉴를 목록으로 보여줍니다.",
)
async def list_menus_command(interaction: discord.Interaction) -> None:
	log_command_trigger("메뉴목록", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	menus = await asyncio.to_thread(get_menu_entries, interaction.guild_id)
	if not menus:
		await interaction.response.send_message(
			"등록된 메뉴가 없습니다. `/메뉴추가`로 메뉴를 먼저 등록해주세요.",
			ephemeral=True,
		)
		return
	view = MenuListView(menus, interaction.user.id)
	await interaction.response.send_message(
		embed=make_menu_list_embed(menus),
		view=view,
		ephemeral=True,
	)


class MenuDeleteModal(discord.ui.Modal, title="메뉴 삭제"):
	def __init__(self, guild_id: int) -> None:
		super().__init__()
		self.guild_id = guild_id
		self.menu_name = discord.ui.TextInput(
			label="삭제할 메뉴 이름",
			placeholder="정확한 메뉴 이름을 입력하세요",
			max_length=100,
		)
		self.add_item(self.menu_name)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		menu = self.menu_name.value.strip()
		if not menu:
			await interaction.response.send_message(
				"삭제할 메뉴 이름을 입력해주세요.",
				ephemeral=True,
			)
			return
		is_admin = is_menu_admin(interaction.user)
		deleted = await asyncio.to_thread(
			delete_menu,
			self.guild_id,
			menu,
			interaction.user.id,
			is_admin,
		)
		if deleted:
			message = f"`{menu}` 메뉴를 삭제했습니다."
		else:
			message = (
				f"`{menu}` 메뉴를 찾을 수 없거나, 본인이 등록한 메뉴만 삭제할 수 있습니다."
				if not is_admin
				else f"`{menu}` 메뉴를 찾을 수 없습니다."
			)
		await interaction.response.send_message(message, ephemeral=True)


@app_commands.command(
	name="메뉴삭제",
	description="선택한 메뉴를 완전히 삭제해요. 본인이 등록한것 외에는 삭제, 수정할 수 없어요.",
)
async def delete_menu_command(interaction: discord.Interaction) -> None:
	log_command_trigger("메뉴삭제", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	menus = await asyncio.to_thread(get_menu_entries, interaction.guild_id)
	if not menus:
		await interaction.response.send_message(
			"등록된 메뉴가 없습니다. `/메뉴추가`로 메뉴를 먼저 등록해주세요.",
			ephemeral=True,
		)
		return

	menu_list = "\n".join(f"- {menu}" for menu in menus)
	view = discord.ui.View(timeout=120)

	async def open_delete_modal(interaction: discord.Interaction) -> None:
		await interaction.response.send_modal(MenuDeleteModal(interaction.guild_id or 0))

	button = discord.ui.Button(
		label="삭제할 메뉴 입력",
		style=discord.ButtonStyle.danger,
	)
	button.callback = open_delete_modal
	view.add_item(button)

	await interaction.response.send_message(
		f"현재 등록된 메뉴입니다:\n{menu_list}\n\n삭제할 메뉴를 입력하려면 아래 버튼을 눌러주세요.",
		view=view,
		ephemeral=True,
	)


@app_commands.command(
	name="메뉴초기화",
	description="존제하는 모든 메뉴들을 보여줘요.",
)
async def reset_menus_command(interaction: discord.Interaction) -> None:
	log_command_trigger("메뉴초기화", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	if not is_menu_admin(interaction.user):
		await interaction.response.send_message(
			"관리자만 사용할 수 있는 명령어입니다. (서버 관리자 또는 MENU_ADMIN_IDS 설정 사용자)",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	removed_count = await asyncio.to_thread(clear_menus, interaction.guild_id)
	await interaction.response.send_message(
		f"서버의 등록 메뉴 {removed_count}개를 삭제했습니다.",
		ephemeral=True,
	)


@app_commands.command(
	name="메뉴추천",
	description="원하는 카테고리에서 메뉴를 추천해요.",
)
@app_commands.describe(category="추천받을 메뉴 카테고리")
@app_commands.choices(
	category=[
		app_commands.Choice(name="일반 음식", value="일반 음식"),
		app_commands.Choice(name="디저트", value="디저트"),
		app_commands.Choice(name="괴랄한 음식", value="괴랄한 음식"),
		app_commands.Choice(name="연회장 특식", value="연회장 특식"),
	]
)
async def recommend_menu_command(
	interaction: discord.Interaction,
	category: app_commands.Choice[str],
) -> None:
	log_command_trigger("메뉴추천", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	await asyncio.to_thread(initialize_level_db)
	current_level, _ = await asyncio.to_thread(
		get_user_level,
		interaction.guild_id,
		interaction.user.id,
	)
	is_banquet_special = category.value == "연회장 특식"
	banquet_base_crystal_leaf: int | None = None
	if is_banquet_special:
		was_used, _ = await asyncio.to_thread(
			consume_banquet_special_use,
			interaction.guild_id,
			interaction.user.id,
		)
		if not was_used:
			await interaction.response.send_message(
				"해당 코스는 이미 먹었어요. 내일 다시 찾아와주세요! 더 먹고싶으면 소화제를 먹어보는건 어떨까요?",
				ephemeral=True,
			)
			return
		menu, banquet_base_crystal_leaf = choose_banquet_special_reward(current_level)
	else:
		menu, _ = await asyncio.to_thread(
			get_random_menu,
			interaction.guild_id,
			category.value,
		)
		if menu is None:
			await interaction.response.send_message(
				f"**{category.name}** 카테고리에 등록된 메뉴가 없습니다. `/메뉴추가`로 등록해주세요.",
				ephemeral=True,
			)
			return

	if current_level >= MAX_USER_LEVEL:
		await interaction.response.send_message(
			format_menu_recommendation_response(
				category.name,
				menu,
				f"최대 레벨 Lv.{MAX_USER_LEVEL}에 도달해 엘리프는 더 쌓이지 않아요.",
				is_banquet_special,
			)
		)
		return

	reward_crystal_leaf = (
		roll_banquet_special_crystal_leaf(banquet_base_crystal_leaf)
		if banquet_base_crystal_leaf is not None
		else roll_menu_reward_crystal_leaf()
	)
	new_level, current_crystal_leaf, levelled_up = await asyncio.to_thread(
		award_user_crystal_leaf,
		interaction.guild_id,
		interaction.user.id,
		reward_crystal_leaf,
	)
	reward_label = (
		f"로또 당첨! +{reward_crystal_leaf}엘리프"
		if reward_crystal_leaf == 100
		else f"+{reward_crystal_leaf}엘리프"
	)
	if levelled_up:
		progress_message = f"{reward_label}로 Lv.{new_level} 레벨업 되었어요."
	else:
		next_level_crystal_leaf = new_level * LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL
		progress_message = (
			f"-# {reward_label} (Lv.{new_level} 엘리프: "
			f"{current_crystal_leaf}/{next_level_crystal_leaf})"
		)
	await interaction.response.send_message(
		format_menu_recommendation_response(
			category.name,
			menu,
			progress_message,
			is_banquet_special,
		),
	)
	logger.info(
		"메뉴 추천 보상: user_id=%s, crystal_leaf=%s, level=%s",
		interaction.user.id,
		reward_crystal_leaf,
		new_level,
	)


@app_commands.command(
	name="레벨",
	description="자신의 레벨을 볼 수 있어요.",
)
async def level_command(interaction: discord.Interaction) -> None:
	log_command_trigger("레벨", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	level, crystal_leaf = await asyncio.to_thread(
		get_user_level,
		interaction.guild_id,
		interaction.user.id,
	)
	if level >= MAX_USER_LEVEL:
		message = f"{interaction.user.mention} 현재 레벨은 **Lv.{MAX_USER_LEVEL}**입니다. 최대 레벨에 도달했습니다."
	else:
		next_level_crystal_leaf = level * LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL
		message = (
			f"{interaction.user.mention} 현재 레벨은 **Lv.{level}**입니다.\n"
			f"다음 레벨까지: **{crystal_leaf}/{next_level_crystal_leaf}엘리프**"
		)
	await interaction.response.send_message(message, ephemeral=True)


@app_commands.command(
	name="랭킹",
	description="원하는 유형의 랭킹을 확인할 수 있어요.",
)
@app_commands.describe(type="확인할 랭킹 유형")
@app_commands.choices(
	type=[
		app_commands.Choice(name="레벨", value="level"),
		app_commands.Choice(name="퀴즈랭킹", value="quiz"),
	]
)
async def ranking_command(
	interaction: discord.Interaction,
	type: app_commands.Choice[str],
) -> None:
	log_command_trigger("랭킹", interaction.user)
	if interaction.guild_id is None or interaction.guild is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	if type.value == "quiz":
		rows = await asyncio.to_thread(get_quiz_leaderboard, interaction.guild_id)
		if not rows:
			await interaction.response.send_message(
				"아직 이 서버의 퀴즈 정답 기록이 없습니다.",
				ephemeral=True,
			)
			return

		lines = []
		for rank, (user_id, solved_count) in enumerate(rows, start=1):
			member = interaction.guild.get_member(user_id)
			name = member.mention if member is not None else f"<@{user_id}>"
			lines.append(f"**{rank}위** {name} · 정답 **{solved_count}문제**")

		embed = discord.Embed(
			title="퀴즈 랭킹",
			description="\n".join(lines),
			color=discord.Color.gold(),
		)
		embed.set_footer(text="퀴즈 정답을 맞힌 문제 수가 많은 순으로 정렬되요.")
		await interaction.response.send_message(embed=embed)
		return

	if type.value != "level":
		await interaction.response.send_message(
			"지원하지 않는 랭킹 유형입니다.",
			ephemeral=True,
		)
		return

	rows = await asyncio.to_thread(get_level_leaderboard, interaction.guild_id)
	if not rows:
		await interaction.response.send_message(
			"아직 이 서버의 레벨 랭킹 데이터가 없습니다.",
			ephemeral=True,
		)
		return

	lines = []
	for rank, (user_id, level, crystal_leaf) in enumerate(rows, start=1):
		member = interaction.guild.get_member(user_id)
		name = member.mention if member is not None else f"<@{user_id}>"
		progress = (
			"최대 레벨"
			if level >= MAX_USER_LEVEL
			else f"{crystal_leaf}/{level * LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL} 엘리프"
		)
		lines.append(f"**{rank}위** {name} · Lv.{level} · {progress}")

	embed = discord.Embed(
		title="레벨 랭킹",
		description="\n".join(lines),
		color=discord.Color.gold(),
	)
	embed.set_footer(text="랭킹 순위는 레벨이 높은 순으로 정해져요. 레벨이 같으면 엘리프가 많은 순으로 정해져요.")
	await interaction.response.send_message(embed=embed)


def make_quiz_embed(question: str, creator_id: int) -> discord.Embed:
	creator = f"<@{creator_id}>" if creator_id else "슈로 봇 기본 문제"
	embed = discord.Embed(
		title="퀴즈",
		description=discord.utils.escape_mentions(question),
		color=discord.Color.blurple(),
	)
	embed.set_footer(
		text=f"출제자: {creator} · 정답 입력 기회는 한 사람당 {QUIZ_MAX_ATTEMPTS}회예요."
	)
	return embed


class QuizAnswerModal(discord.ui.Modal, title="정답 입력"):
	def __init__(self, view: "QuizView") -> None:
		super().__init__()
		self.quiz_view = view
		self.answer_input = discord.ui.TextInput(
			label="정답",
			placeholder="정답을 입력하세요",
			max_length=200,
		)
		self.add_item(self.answer_input)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		answer = self.answer_input.value.strip()
		if not answer:
			await interaction.response.send_message(
				"정답을 입력해주세요.",
				ephemeral=True,
			)
			return

		status, remaining, reward = await asyncio.to_thread(
			submit_quiz_answer,
			self.quiz_view.session_id,
			interaction.user.id,
			answer,
		)
		if status == "incorrect":
			await interaction.response.send_message(
				f"틀렸습니다. 남은 기회: **{remaining}회**",
				ephemeral=True,
			)
			return
		if status == "exhausted":
			await interaction.response.send_message(
				"이 문제의 정답 입력 기회 3회를 모두 사용했습니다. 다른 참가자는 계속 풀 수 있어요.",
				ephemeral=True,
			)
			return
		if status == "inactive":
			await interaction.response.send_message(
				"이미 종료된 퀴즈입니다.",
				ephemeral=True,
			)
			return
		if status != "correct":
			raise RuntimeError(f"예상하지 못한 퀴즈 정답 처리 결과입니다: {status}")

		await interaction.response.send_message(
			f"정답입니다! 퀴즈 풀이를 종료하고 **{reward}엘리프**를 얻었어요.",
			ephemeral=True,
		)
		session = await asyncio.to_thread(get_quiz_session, self.quiz_view.session_id)
		if session is None:
			raise ValueError(f"종료된 퀴즈 세션을 찾을 수 없습니다: {self.quiz_view.session_id}")
		canonical_answer = session[3]
		result = (
			f"{interaction.user.mention}님이 정답을 맞혔습니다! "
			f"정답: ||{discord.utils.escape_mentions(discord.utils.escape_markdown(canonical_answer))}||"
		)
		try:
			await self.quiz_view.update_public_message(interaction, result)
		except discord.HTTPException:
			logger.exception(
				"퀴즈 종료 메시지를 갱신하지 못했습니다: session_id=%s",
				self.quiz_view.session_id,
			)
			try:
				await interaction.followup.send(
					f"{interaction.user.mention}님이 정답을 맞혀 퀴즈가 종료되었습니다.",
					allowed_mentions=discord.AllowedMentions.none(),
				)
			except discord.HTTPException:
				logger.exception(
					"퀴즈 종료 안내 전송도 실패했습니다: session_id=%s",
					self.quiz_view.session_id,
				)


class QuizView(discord.ui.View):
	def __init__(
		self,
		session_id: str,
		channel_id: int | None = None,
		message_id: int | None = None,
	) -> None:
		super().__init__(timeout=None)
		self.session_id = session_id
		self.channel_id = channel_id
		self.message_id = message_id

	async def update_public_message(
		self,
		interaction: discord.Interaction,
		content: str,
	) -> None:
		if interaction.message is not None:
			await interaction.message.edit(content=content, embed=None, view=None)
			return
		if self.channel_id is None or self.message_id is None:
			raise ValueError(f"퀴즈 메시지 정보가 없습니다: {self.session_id}")

		channel = interaction.client.get_channel(self.channel_id)
		if channel is None:
			channel = await interaction.client.fetch_channel(self.channel_id)
		if not isinstance(channel, discord.abc.Messageable):
			raise TypeError(f"퀴즈 채널에서 메시지를 가져올 수 없습니다: {self.channel_id}")
		message = await channel.fetch_message(self.message_id)
		await message.edit(content=content, embed=None, view=None)

	@discord.ui.button(
		label="힌트 보기",
		style=discord.ButtonStyle.primary,
		custom_id="quiz:hint:v1",
	)
	async def show_hint(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button,
	) -> None:
		if interaction.guild_id is None:
			await interaction.response.send_message(
				"서버에서만 사용할 수 있는 퀴즈입니다.",
				ephemeral=True,
			)	
			return

		status, hint, balance = await asyncio.to_thread(
			consume_quiz_hint,
			interaction.guild_id,
			self.session_id,
			interaction.user.id,
		)
		if status == "inactive":
			await interaction.response.send_message("이미 종료된 퀴즈입니다.", ephemeral=True)
			return
		if status == "used":
			await interaction.response.send_message(
				"이 문제의 힌트를 이미 두 번 확인했습니다.",
				ephemeral=True,
			)
			return
		if status == "insufficient":
			await interaction.response.send_message(
				f"엘리프가 부족합니다. 힌트에는 {QUIZ_HINT_COST}엘리프가 필요하고, "
				f"현재 {balance}엘리프를 보유하고 있습니다. 레벨은 차감되지 않았습니다.",
				ephemeral=True,
			)
			return
		if status not in {"free", "paid"} or hint is None:
			raise RuntimeError(f"예상하지 못한 퀴즈 힌트 처리 결과입니다: {status}")

		hint_text = f"힌트: {hint}"
		if status == "paid":
			hint_text += f"\n-# {QUIZ_HINT_COST}엘리프 사용 · 남은 엘리프: {balance}"
		else:
			hint_text += "\n-# 무료 힌트 · 이 메시지는 10초 후 사라집니다."
		await interaction.response.send_message(
			hint_text,
			ephemeral=True,
			delete_after=10,
		)

	@discord.ui.button(
		label="정답 입력",
		style=discord.ButtonStyle.success,
		custom_id="quiz:answer:v1",
	)
	async def enter_answer(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button,
	) -> None:
		await interaction.response.send_modal(QuizAnswerModal(self))

	@discord.ui.button(
		label="포기",
		style=discord.ButtonStyle.danger,
		custom_id="quiz:give-up:v1",
	)
	async def give_up(
		self,
		interaction: discord.Interaction,
		button: discord.ui.Button,
	) -> None:
		status, answer = await asyncio.to_thread(
			give_up_quiz,
			self.session_id,
			interaction.user.id,
		)
		if status == "inactive" or answer is None:
			await interaction.response.send_message(
				"이미 종료된 퀴즈입니다.",
				ephemeral=True,
			)
			return

		safe_answer = discord.utils.escape_mentions(discord.utils.escape_markdown(answer))
		await interaction.response.edit_message(
			content=(
				f"{interaction.user.mention}님이 포기하여 **모두의 퀴즈 풀이가 종료되었습니다.**\n"
				f"정답: ||{safe_answer}||"
			),
			embed=None,
			view=None,
			allowed_mentions=discord.AllowedMentions.none(),
		)


async def publish_quiz(
	interaction: discord.Interaction,
	guild_id: int,
	creator_id: int,
	question: str,
	answer: str,
	hint: str,
) -> None:
	status, session_id, remaining = await asyncio.to_thread(
		start_quiz_session,
		guild_id,
		creator_id,
		question,
		answer,
		hint,
	)
	if status == "cooldown":
		remaining_hours = max(1, math.ceil(remaining / 3600))
		await interaction.response.send_message(
			f"{remaining_hours}시간 뒤에 퀴즈를 풀 수 있어요.",
			ephemeral=True,
		)
		return
	if status == "active" or session_id is None:
		await interaction.response.send_message(
			"이 서버에는 이미 진행 중인 퀴즈가 있습니다. 현재 퀴즈가 끝난 뒤 다시 시도해주세요.",
			ephemeral=True,
		)
		return

	view = QuizView(session_id)
	try:
		await interaction.response.send_message(
			embed=make_quiz_embed(question, creator_id),
			view=view,
			allowed_mentions=discord.AllowedMentions.none(),
		)
		message = await interaction.original_response()
		view.channel_id = message.channel.id
		view.message_id = message.id
		await asyncio.to_thread(
			save_quiz_message_id,
			session_id,
			message.channel.id,
			message.id,
		)
	except (discord.HTTPException, sqlite3.Error, ValueError):
		await asyncio.to_thread(cancel_quiz_session, session_id)
		logger.exception("퀴즈 메시지를 만들거나 저장하지 못했습니다: session_id=%s", session_id)
		if interaction.response.is_done():
			await interaction.followup.send(
				"퀴즈 메시지를 준비하지 못했습니다. 잠시 후 다시 시도해주세요.",
				ephemeral=True,
			)
		else:
			await interaction.response.send_message(
				"퀴즈 메시지를 준비하지 못했습니다. 잠시 후 다시 시도해주세요.",
				ephemeral=True,
			)


@app_commands.command(
	name="퀴즈",
	description="퀴즈타임!",
)
async def start_quiz_command(interaction: discord.Interaction) -> None:
	log_command_trigger("퀴즈", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	bank = await asyncio.to_thread(get_quiz_question_bank, interaction.guild_id)
	candidates = [
		(0, data["<문제내용>"], data["<정답>"], data["<힌트>"])
		for data in quizs.values()
	]
	candidates.extend(bank)
	creator_id, question, answer, hint = random.choice(candidates)
	await publish_quiz(
		interaction,
		interaction.guild_id,
		creator_id,
		question,
		answer,
		hint,
	)


@app_commands.command(
	name="퀴즈내기",
	description="문제를 직접 낼 수 있어요.",
)
@app_commands.rename(question="문제", answer="정답", hint="힌트")
@app_commands.describe(
	question="출제할 문제 내용",
	answer="문제의 정답",
	hint="참가자에게 보여줄 힌트",
)
async def submit_quiz_question_command(
	interaction: discord.Interaction,
	question: str,
	answer: str,
	hint: str,
) -> None:
	log_command_trigger("문제출제", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	question = question.strip()
	answer = answer.strip()
	hint = hint.strip()
	if not question or not answer or not hint:
		await interaction.response.send_message(
			"문제 내용, 정답, 힌트를 모두 입력해주세요.",
			ephemeral=True,
		)
		return
	if len(question) > 1000 or len(answer) > 200 or len(hint) > 1000:
		await interaction.response.send_message(
			"문제와 힌트는 각각 1000자, 정답은 200자 이내로 입력해주세요.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(
		save_quiz_question,
		interaction.guild_id,
		interaction.user.id,
		question,
		answer,
		hint,
	)
	await interaction.response.send_message(
		"문제를 문제 은행에 저장했습니다. 바로 시작하지는 않았어요. "
		"나중에 `/퀴즈`를 사용해 서버에서 문제를 시작할 수 있습니다.",
		ephemeral=True,
	)


def make_goldy_shop_embed(selected_item: str | None = None) -> discord.Embed:
	lines = [
		f"**{name}**: {item['price']} 엘리프 · "
		f"{f'하루 {item.get("daily_limit", 0)}회 구메 가능' if item.get('daily_limit', 0) else '일일 제한 없음'}\n"
		f"{item['description']}\n"
		for name, item in ITEM_LIST.items()
	]
	embed = discord.Embed(
		title="골디 상점",
		description="\n".join(lines) or "현재 판매 중인 아이템이 없습니다.",
		color=discord.Color.gold(),
	)
	if selected_item is not None:
		embed.set_footer(text=f"선택한 아이템: {selected_item} · 구매 버튼을 눌러 확정하세요.")
	return embed


class GoldyShopView(discord.ui.View):
	def __init__(self, guild_id: int, user_id: int) -> None:
		super().__init__(timeout=180)
		self.guild_id = guild_id
		self.user_id = user_id
		self.selected_item: str | None = None
		self.item_select = discord.ui.Select(
			placeholder="구매할 아이템을 선택하세요",
			options=[
				discord.SelectOption(
					label=name[:100],
					value=name,
					description=(
						f"{item['price']} 엘리프 · "
						f"{f'하루 {item.get("daily_limit", 0)}회' if item.get('daily_limit', 0) else '제한 없음'} · "
						f"{item['description']}"
					)[:100],
				)
				for name, item in ITEM_LIST.items()
			],
			disabled=not ITEM_LIST,
		)
		self.item_select.callback = self.select_item
		self.add_item(self.item_select)
		self.purchase_button = discord.ui.Button(
			label="구매",
			style=discord.ButtonStyle.success,
			disabled=True,
		)
		self.purchase_button.callback = self.purchase_selected_item
		self.add_item(self.purchase_button)

	async def interaction_check(self, interaction: discord.Interaction) -> bool:
		if interaction.user.id != self.user_id:
			await interaction.response.send_message(
				"이 상점을 연 사용자만 구매할 수 있습니다.",
				ephemeral=True,
			)
			return False
		return True

	async def select_item(self, interaction: discord.Interaction) -> None:
		self.selected_item = self.item_select.values[0]
		self.purchase_button.disabled = False
		await interaction.response.edit_message(
			embed=make_goldy_shop_embed(self.selected_item),
			view=self,
		)

	async def purchase_selected_item(self, interaction: discord.Interaction) -> None:
		if self.selected_item is None:
			await interaction.response.send_message(
				"먼저 구매할 아이템을 선택해주세요.",
				ephemeral=True,
			)
			return

		item = ITEM_LIST.get(self.selected_item)
		if item is None:
			await interaction.response.send_message(
				"선택한 아이템은 현재 상점에서 판매하지 않습니다.",
				ephemeral=True,
			)
			return
		price = item["price"]

		was_purchased, remaining_crystal_leaf, daily_limit_reached, purchases_today = await asyncio.to_thread(
			buy_shop_item,
			self.guild_id,
			self.user_id,
			self.selected_item,
		)
		if daily_limit_reached:
			await interaction.response.send_message(
				f"오늘의 **{self.selected_item}** 구매 한도에 도달했습니다. "
				f"(하루 {item.get('daily_limit', 0)}개)",
				ephemeral=True,
			)
			return
		if not was_purchased:
			await interaction.response.send_message(
				f"엘리프가 부족합니다. 보유 엘리프: {remaining_crystal_leaf}, 필요 엘리프: {price}",
				ephemeral=True,
			)
			return

		self.item_select.disabled = True
		self.purchase_button.disabled = True
		daily_limit = item.get("daily_limit", 0)
		purchase_count_message = (
			f"오늘 {purchases_today}/{daily_limit}개 구매"
			if daily_limit
			else "일일 구매 제한 없음"
		)
		await interaction.response.edit_message(
			content=(
				f"**{self.selected_item}** 구매 완료! 엘리프 {price}개를 사용했습니다. "
				f"남은 엘리프: {remaining_crystal_leaf} · {purchase_count_message}"
			),
			embed=make_goldy_shop_embed(self.selected_item),
			view=self,
		)


@app_commands.command(
	name="인벤토리",
	description="인벤토리를 확인해요.",
)
async def inventory_command(interaction: discord.Interaction) -> None:
	log_command_trigger("인벤토리", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	items, (_, crystal_leaf) = await asyncio.gather(
		asyncio.to_thread(get_user_inventory, interaction.guild_id, interaction.user.id),
		asyncio.to_thread(get_user_level, interaction.guild_id, interaction.user.id),
	)
	description = format_inventory_items(items)
	embed = discord.Embed(title="인벤토리", description=description, color=discord.Color.blue())
	embed.set_footer(text=f"보유 엘리프: {crystal_leaf}")
	await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.command(
	name="골디상점",
	description="아이템을 엘리프로 구매합니다.",
)
async def goldy_shop_command(interaction: discord.Interaction) -> None:
	log_command_trigger("골디상점", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_level_db)
	view = GoldyShopView(interaction.guild_id, interaction.user.id)
	await interaction.response.send_message(
		embed=make_goldy_shop_embed(),
		view=view,
		ephemeral=True,
	)


@app_commands.command(
	name="유저레벨초기화",
	description="특정 유저의 레벨을 초기화할 수있어요.",
)
@app_commands.describe(user="레벨을 초기화할 유저")
async def reset_user_level_command(
	interaction: discord.Interaction,
	user: discord.Member,
) -> None:
	log_command_trigger("유저레벨초기화", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return
	if not is_menu_admin(interaction.user):
		await interaction.response.send_message(
			"관리자만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_level_db)
	await asyncio.to_thread(reset_user_level, interaction.guild_id, user.id)
	await interaction.response.send_message(
		f"{user.mention}님의 레벨 정보를 초기화했습니다. (Lv.1, 0엘리프)",
		ephemeral=True,
	)


@app_commands.command(
	name="레벨초기화",
	description="모든 유저의 레벨 정보를 초기화 합니다.",
)
async def reset_guild_levels_command(interaction: discord.Interaction) -> None:
	log_command_trigger("레벨초기화", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return
	if not is_menu_admin(interaction.user):
		await interaction.response.send_message(
			"관리자만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_level_db)
	reset_count = await asyncio.to_thread(reset_guild_levels, interaction.guild_id)
	await interaction.response.send_message(
		f"현재 서버의 레벨 정보 {reset_count}건을 초기화했습니다.",
		ephemeral=True,
	)


@app_commands.command(
	name="레벨차감",
	description="특정 유저의 레벨 정보를 수정합니다.",
)
@app_commands.describe(user="레벨을 차감할 유저", levels="차감할 레벨 수")
async def subtract_level_command(
	interaction: discord.Interaction,
	user: discord.Member,
	levels: int,
) -> None:
	log_command_trigger("레벨차감", interaction.user)
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return
	if not is_menu_admin(interaction.user):
		await interaction.response.send_message(
			"관리자만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return
	if levels <= 0:
		await interaction.response.send_message(
			"차감할 레벨은 1 이상의 정수여야 합니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_level_db)
	old_level, new_level = await asyncio.to_thread(
		subtract_user_levels,
		interaction.guild_id,
		user.id,
		levels,
	)
	removed_levels = old_level - new_level
	await interaction.response.send_message(
		f"{user.mention}님의 레벨을 Lv.{old_level}에서 Lv.{new_level}로 조정했습니다. "
		f"({removed_levels}레벨 차감, 엘리프 초기화)",
		ephemeral=True,
	)


@app_commands.command(
	name="문의",
	description="문의와 표시 이름을 GitHub 공개 이슈로 등록합니다. 이미지 선택, 개인정보 입력 금지.",
)
@app_commands.describe(
	content="공개할 문의 내용 (1000자 이내, 개인정보·토큰 입력 금지)",
	attachment="오류/화면 자료 이미지 (선택, 첨부한 이미지 링크도 공개됩니다)",
)
async def inquiry_command(
	interaction: discord.Interaction,
	content: str,
	attachment: discord.Attachment | None = None,
) -> None:
	log_command_trigger("문의", interaction.user)
	message = content.strip()
	if not message:
		await interaction.response.send_message(
			"문의 내용을 입력해주세요.",
			ephemeral=True,
		)
		return
	if len(message) > 1000:
		await interaction.response.send_message(
			"문의는 1000자 이내로 입력해주세요.",
			ephemeral=True,
		)
		return
	if attachment is not None and (not attachment.content_type or not attachment.content_type.startswith("image/")):
		await interaction.response.send_message(
			"첨부는 선택 사항이며 이미지 파일만 첨부할 수 있습니다.",
			ephemeral=True, 	
		)
		return
	await interaction.response.defer(ephemeral=True)
	try:
		issue_url = await asyncio.to_thread(
			create_inquiry_issue,
			message,
			interaction.user.display_name,
			attachment.url if attachment is not None else None,
		)
	except InquiryError as error:
		logger.warning("GitHub 문의 등록 실패: code=%s", error.code)
		await interaction.followup.send(str(error), ephemeral=True)
		return
	logger.info("GitHub 문의 등록 완료: %s", issue_url)
	await interaction.followup.send(
		f"문의가 GitHub 공개 이슈로 등록되었습니다.\n{issue_url}",
		ephemeral=True,
	)


@app_commands.command(
	name="코믹인포",
	description="코믹월드 행사정보를 보여줘요.",
)
async def comic_info_command(interaction: discord.Interaction) -> None:
	log_command_trigger("코믹인포", interaction.user)
	await interaction.response.defer()
	try:
		events = await asyncio.to_thread(fetch_events)
		nearest = get_nearest_events(events)[:1]
		if not nearest:
			await interaction.followup.send("현재 등록된 행사가 없습니다.")
			return
		await interaction.followup.send(embed=make_event_embed(nearest[0]))
	except (requests.RequestException, ValueError, KeyError) as error:
		logger.exception("코믹인포 명령어 처리 실패: %s", error)
		await interaction.followup.send(
			"행사정보를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.",
			ephemeral=True,
		)
	


@app_commands.command(
	name="코믹스케줄",
	description="원하는 만큼 코믹월드 일정을 보여줘요.",
)
@app_commands.describe(count="출력할 행사 개수 (1~10)")
async def comic_schedule_command(
	interaction: discord.Interaction,
	count: app_commands.Range[int, 1, 10],
) -> None:
	global schedule_cooldown_until
	log_command_trigger("코믹스케줄", interaction.user)
	now = time.monotonic()
	if schedule_cooldown_until is not None:
		remaining = schedule_cooldown_until - now
		if remaining > 0:
			try:
				remaining_minutes = math.ceil(remaining / 60)
				await interaction.response.send_message(
					f"이 명령어는 전체 10분 쿨타임이 있습니다. {remaining_minutes}분 후 다시 시도해주세요.",
					ephemeral=True,
				)
			except discord.NotFound:
				logger.warning("쿨타임 안내 전에 상호작용이 만료되었습니다.")
			return

	schedule_cooldown_until = now + SCHEDULE_COOLDOWN_SECONDS
	try:
		await interaction.response.defer()
	except discord.NotFound:
		logger.warning("코믹스케줄 상호작용이 응답 전에 만료되었습니다.")
		return
	try:
		events = await asyncio.to_thread(fetch_events)
		scheduled = get_nearest_events(events)[:count]
		if not scheduled:
			await interaction.followup.send("현재 등록된 행사가 없습니다.")
			return
		await interaction.followup.send(
			content=f"요청한 **{count}개**의 코믹월드 행사 목록입니다.\n-# _전체 {len(events)}개_",
			embeds=[make_event_embed(event) for event in scheduled],
		)
	except (requests.RequestException, ValueError, KeyError) as error:
		logger.exception("코믹스케줄 명령어 처리 실패: %s", error)
		try:
			await interaction.followup.send(
				"행사정보를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.",
				ephemeral=True,
			)
		except discord.NotFound:
			logger.warning("오류 안내 전에 코믹스케줄 상호작용이 만료되었습니다.")


class ComicWorldBot(commands.Bot):
	def __init__(self, channel_id: int | None) -> None:
		intents = discord.Intents.default()
		intents.message_content = True
		super().__init__(command_prefix="!", intents=intents)
		self.channel_id = channel_id
		self.login_started_at: float | None = None
		self.commands_synced = False
		self.quiz_views_restored = False
		self.activity_id: int | None = None
		self.activity_deadline: datetime | None = None
		self.activity_period_end: datetime | None = None
		self.activity_initialized = False
		self.log_event_loop: asyncio.AbstractEventLoop | None = None
		self.log_loop_ready = threading.Event()

	async def save_logs_and_notify(
		self,
		reason: str,
		automatic_error: bool = False,
	) -> tuple[Path | None, bool]:
		try:
			snapshot_path = await asyncio.to_thread(save_log_snapshot)
		except Exception as error:
			print(f"로그 파일 저장 실패: {error}", file=sys.stderr)
			return None, False

		try:
			developer = self.get_user(DEVELOPER_USER_ID)
			if developer is None:
				developer = await self.fetch_user(DEVELOPER_USER_ID)
			await developer.send(
				content=(
					reason[:1500]
					if automatic_error
					else f"로그 저장 알림: {reason[:1500]}"
				),
				file=discord.File(snapshot_path, filename=snapshot_path.name),
			)
		except Exception as error:
			print(f"개발자 DM 로그 전송 실패: {error}", file=sys.stderr)
			return snapshot_path, False
		return snapshot_path, True

	async def sync_commands_with_retry(self, max_retries: int = 3) -> None:
		for attempt in range(1, max_retries + 1):
			try:
				for guild in self.guilds:
					self.tree.clear_commands(guild=guild)
					self.tree.copy_global_to(guild=guild)
					await self.tree.sync(guild=guild)
					logger.info(
						"슬래시 명령어를 서버에 동기화했습니다: guild=%s (%s)",
						guild.name,
						guild.id,
					)
				self.tree.clear_commands(guild=None)
				await self.tree.sync()
				logger.info("중복을 방지하기 위해 전역 슬래시 명령어를 제거했습니다.")
				self.commands_synced = True
				return
			except discord.Forbidden:
				logger.error(
					"전역 슬래시 명령어 동기화 권한이 없습니다. "
					"봇 초대 URL에 'bot'과 'applications.commands' 권한 범위가 포함되어 있는지 확인하세요."
				)
				return
			except discord.HTTPException as error:
				status_code = getattr(error, "status", None)
				if status_code not in {500, 502, 503, 504}:
					raise
				if attempt == max_retries:
					logger.exception(
						"Discord API가 반복적으로 500 오류를 반환했습니다. 마지막 시도 후 명령어 동기화를 포기합니다.",
					)
					return
				logger.warning(
					"Discord 명령어 동기화에 일시적 %s 오류가 발생해 %d초 뒤 재시도합니다. (%d/%d)",
					status_code,
					attempt,
					attempt,
					max_retries,
				)
				await asyncio.sleep(attempt * 5)

	async def setup_hook(self) -> None:
		self.tree.add_command(comic_info_command)
		self.tree.add_command(comic_schedule_command)
		self.tree.add_command(add_menu_command)
		self.tree.add_command(list_menus_command)
		self.tree.add_command(delete_menu_command)
		self.tree.add_command(reset_menus_command)
		self.tree.add_command(recommend_menu_command)
		self.tree.add_command(level_command)
		self.tree.add_command(ranking_command)
		self.tree.add_command(start_quiz_command)
		self.tree.add_command(submit_quiz_question_command)
		self.tree.add_command(inventory_command)
		self.tree.add_command(goldy_shop_command)
		self.tree.add_command(reset_user_level_command)
		self.tree.add_command(reset_guild_levels_command)
		self.tree.add_command(subtract_level_command)
		self.tree.add_command(status_command)
		self.tree.add_command(inquiry_command)
		self.tree.add_command(help_command)
		self.add_command(butter_command)
		self.add_command(tig_command)
		self.add_command(stop_command)
		self.add_command(save_log_command)
		self.log_event_loop = asyncio.get_running_loop()
		self.log_loop_ready.set()
		root_logger = logging.getLogger()
		for handler in root_logger.handlers[:]:
			if isinstance(handler, LogErrorNotificationHandler):
				root_logger.removeHandler(handler)
		error_handler = LogErrorNotificationHandler(self)
		error_handler.setFormatter(
			logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
		)
		root_logger.addHandler(error_handler)
		initialize_menu_db()
		initialize_level_db()
		if self.channel_id is not None:
			self.update_events.start()
		else:
			logger.warning("DISCORD_CHANNEL_ID가 없어 주기 알림을 비활성화합니다.")
		if (
			get_auto_message_times()
			and any(get_auto_message_text(scheduled_time) for scheduled_time in get_auto_message_times())
			and get_auto_message_channel_ids()
		):
			self.send_auto_message.start()
		else:
			logger.info(
				"AUTO_MESSAGE_TIME, AUTO_MESSAGE_TEXTS 또는 AUTO_MESSAGE_CHANNEL_IDS가 없어 "
				"예약 메시지를 비활성화합니다."
			)

	async def on_ready(self) -> None:
		if self.login_started_at is None:
			self.login_started_at = time.monotonic()
		if not self.quiz_views_restored:
			for session_id, channel_id, message_id in await asyncio.to_thread(
				get_active_quiz_messages
			):
				self.add_view(
					QuizView(session_id, channel_id, message_id),
					message_id=message_id,
				)
			self.quiz_views_restored = True
		if not self.update_activity.is_running():
			self.update_activity.start()
		if not self.commands_synced:
			await self.sync_commands_with_retry()
		logger.info("로그인 완료: %s", self.user)
		print(BOT_ON_MESSAGE)

	async def on_command_error(
		self,
		ctx: commands.Context,
		error: commands.CommandError,
	) -> None:
		if isinstance(error, commands.CommandNotFound):
			return

		logger.exception("일반 명령어 처리 중 오류가 발생했습니다: %s", error)

	@tasks.loop(minutes=1)
	async def update_activity(self) -> None:
		now = datetime.now(KST)
		period = get_activity_period(now)
		if period is None:
			if not self.activity_initialized or self.activity_id is not None:
				await self.change_presence(activity=None)
			self.activity_id = None
			self.activity_deadline = None
			self.activity_period_end = None
			self.activity_initialized = True
			return

		activity_ids, period_end = period
		if (
			self.activity_deadline is None
			or now >= self.activity_deadline
			or self.activity_period_end != period_end
		):
			activity_id = choose_activity_id(activity_ids, self.activity_id)
			await self.change_presence(
				activity=discord.CustomActivity(name=Activitys[activity_id])
			)
			self.activity_id = activity_id
			self.activity_deadline = min(
				now + timedelta(hours=random.randint(1, 3)),
				period_end,
			)
			self.activity_period_end = period_end
			self.activity_initialized = True

	@tasks.loop(minutes=float(os.getenv("POLL_MINUTES", "30")))
	async def update_events(self) -> None:
		if self.channel_id is None:
			return
		channel = self.get_channel(self.channel_id)
		if not isinstance(channel, discord.abc.Messageable):
			logger.error("채널을 찾을 수 없습니다: %s", self.channel_id)
			return

		try:
			events = await asyncio.to_thread(fetch_events)
			fingerprint = events_fingerprint(events)
			if fingerprint == load_cached_fingerprint():
				logger.info("행사정보 변경 없음")
				return

			embeds = [make_event_embed(event) for event in events[:10]]
			if embeds:
				await channel.send(
					content="코믹월드 행사정보가 업데이트되었습니다.",
					embeds=embeds,
				)
			save_cached_fingerprint(fingerprint)
			logger.info("행사정보 %d건 전송 완료", len(embeds))
		except (requests.RequestException, ValueError, KeyError) as error:
			logger.exception("행사정보를 가져오지 못했습니다: %s", error)

	@tasks.loop(minutes=1)
	async def send_auto_message(self) -> None:
		scheduled_times = get_auto_message_times()
		channel_ids = get_auto_message_channel_ids()
		if not scheduled_times or not channel_ids:
			return

		now = datetime.now(KST)
		current_time = (now.hour, now.minute)
		if current_time not in scheduled_times:
			return
		message = get_auto_message_text(current_time)
		if message is None:
			return

		for channel_id in channel_ids:
			if last_auto_message_dates.get(channel_id) == now.date():
				continue
			channel = self.get_channel(channel_id)
			if not isinstance(channel, discord.abc.Messageable):
				logger.error("예약 메시지 채널을 찾을 수 없습니다: %s", channel_id)
				continue
			try:
				await channel.send(message)
				last_auto_message_dates[channel_id] = now.date()
				logger.info("예약 메시지를 전송했습니다: channel_id=%s, time=%s", channel_id, current_time)
			except discord.HTTPException as error:
				logger.exception("예약 메시지 전송 실패: channel_id=%s, error=%s", channel_id, error)

	@send_auto_message.before_loop
	async def before_send_auto_message(self) -> None:
		await self.wait_until_ready()

	@update_events.before_loop
	async def before_update_events(self) -> None:
		await self.wait_until_ready()


def main() -> None:
	token = required_env("DISCORD_TOKEN")
	channel_id_value = os.getenv("DISCORD_CHANNEL_ID")
	channel_id = int(channel_id_value) if channel_id_value else None
	bot = ComicWorldBot(channel_id)
	print("콘솔 로그 저장 명령: saveLog")
	threading.Thread(
		target=console_log_listener,
		args=(bot,),
		name="console-log-listener",
		daemon=True,
	).start()
	bot.run(token)


if __name__ == "__main__":
	main()