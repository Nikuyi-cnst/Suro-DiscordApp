import asyncio, hashlib, json, logging, math, os, random, sqlite3, time, discord, requests
from datetime import date
from pathlib import Path
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv


BASE_URL = "https://comicw.net"
EVENTS_URL = f"{BASE_URL}/bbs/ajax.main.php"
COMICWORLD_EMOJI_URL = "https://cdn.discordapp.com/emojis/1549042252322439258.png"
CACHE_FILE = Path(__file__).with_name(".event_cache.json")
MENU_DB_FILE = Path(__file__).with_name("menus.db")
SCHEDULE_COOLDOWN_SECONDS = 600
COMMAND_GUILD_ID = 1534554345876754595
schedule_cooldown_until: float | None = None

BOT_NAME = "Suro"
ClientBuild = "GA-Stable"
ClientVersion = "GA1.0-S"
ClientBuildDate = "260913192906-260914230000"
BOT_ON_MESSAGE = f"""
----------------------------------------------------                                                                           
Wellcome to {BOT_NAME} app log channel!

새 버전 출시! - 2026.09.14 월요일 오전 23:00 KST
GA1.0 - 버전이 정식 출시되었스빈다.
자세한 내용은 '/도움말'을 참고하세요.

다음 업대이트는 GA1.1-S로 예정되어 있습니다.(아마도)
----------------------------------------------------
build: {ClientBuild}
version: {ClientVersion}
build date: {ClientBuildDate}
System Load Time: {time.ctime()}
------------------------------------------------"""


load_dotenv()

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("comicworld-loader")


def required_env(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"환경변수 {name}이(가) 설정되지 않았습니다.")
	return value


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
				menu TEXT NOT NULL,
				UNIQUE(guild_id, menu)
			)
			"""
		)
		connection.commit()
	finally:
		connection.close()


def add_menu(guild_id: int, menu: str) -> bool:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		cursor = connection.execute(
			"INSERT OR IGNORE INTO menus (guild_id, menu) VALUES (?, ?)",
			(guild_id, menu),
		)
		connection.commit()
		return cursor.rowcount == 1
	finally:
		connection.close()


def get_random_menu(guild_id: int) -> tuple[str | None, int]:
	connection = sqlite3.connect(MENU_DB_FILE)
	try:
		menus = connection.execute(
			"SELECT menu FROM menus WHERE guild_id = ?",
			(guild_id,),
		).fetchall()
		return (random.choice(menus)[0], len(menus)) if menus else (None, 0)
	finally:
		connection.close()


def make_event_embed(event: dict[str, str]) -> discord.Embed:
	status = "진행중" if str(event.get("status")) == "0" else "종료"
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
	name="메뉴추가",
	description="메뉴를 등록합니다.",
)
@app_commands.describe(menu="등록할 메뉴 문자열")
async def add_menu_command(
	interaction: discord.Interaction,
	menu: str,
) -> None:
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
	was_added = await asyncio.to_thread(add_menu, interaction.guild_id, menu)
	message = (
		f"`{menu}` 메뉴를 등록했습니다."
		if was_added
		else f"`{menu}` 메뉴는 이미 등록되어 있습니다."
	)
	await interaction.response.send_message(message, ephemeral=True)


@app_commands.command(
	name="메뉴추천",
	description="등록된 메뉴 중 하나를 랜덤으로 추천합니다.",
)
async def recommend_menu_command(interaction: discord.Interaction) -> None:
	if interaction.guild_id is None:
		await interaction.response.send_message(
			"서버에서만 사용할 수 있는 명령어입니다.",
			ephemeral=True,
		)
		return

	await asyncio.to_thread(initialize_menu_db)
	menu, menu_count = await asyncio.to_thread(
		get_random_menu,
		interaction.guild_id,
	)
	if menu is None:
		await interaction.response.send_message(
			"등록된 메뉴가 없습니다. `/메뉴추가`로 메뉴를 먼저 등록해주세요.",
			ephemeral=True,
		)
		return

	await interaction.response.send_message(
		f"오늘의 메뉴는 **{menu}** 입니다! (등록 메뉴 {menu_count}개 중 추천)",
	)


@app_commands.command(
	name="코믹인포",
	description="코믹월드 행사정보를 보여줍니다.",
)
async def comic_info_command(interaction: discord.Interaction) -> None:
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
	description="코믹월드 행사 일정을 원하는 개수만큼 보여 줍니다.",
)
@app_commands.describe(count="출력할 행사 개수 (1~10)")
async def comic_schedule_command(
	interaction: discord.Interaction,
	count: app_commands.Range[int, 1, 10],
) -> None:
	global schedule_cooldown_until
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
		super().__init__(command_prefix="!", intents=intents)
		self.channel_id = channel_id

	async def setup_hook(self) -> None:
		self.tree.add_command(comic_info_command)
		self.tree.add_command(comic_schedule_command)
		self.tree.add_command(add_menu_command)
		self.tree.add_command(recommend_menu_command)
		initialize_menu_db()
		guild = discord.Object(id=COMMAND_GUILD_ID)
		self.tree.copy_global_to(guild=guild)
		await self.tree.sync(guild=guild)
		logger.info("슬래시 명령어를 길드 %s에 동기화했습니다.", COMMAND_GUILD_ID)
		if self.channel_id is not None:
			self.update_events.start()
		else:
			logger.warning("DISCORD_CHANNEL_ID가 없어 주기 알림을 비활성화합니다.")

	async def on_ready(self) -> None:
		logger.info("로그인 완료: %s", self.user)
		print(BOT_ON_MESSAGE)

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

	@update_events.before_loop
	async def before_update_events(self) -> None:
		await self.wait_until_ready()


def main() -> None:
	token = required_env("DISCORD_TOKEN")
	channel_id_value = os.getenv("DISCORD_CHANNEL_ID")
	channel_id = int(channel_id_value) if channel_id_value else None
	bot = ComicWorldBot(channel_id)
	bot.run(token)


if __name__ == "__main__":
	main()

