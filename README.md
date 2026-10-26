# Discord.py CMWorld Embed loader

코믹월드 홈페이지의 행사정보를 주기적으로 확인하고, 변경되면 Discord 채널에 임베드로 전송합니다.

## 실행

1. 가상환경에서 의존성을 설치합니다.

```powershell
pip install -r requirements.txt
```

2. 프로젝트 폴더의 `.env`에 아래 값을 설정합니다.

```env
DISCORD_TOKEN=디스코드_봇_토큰
DISCORD_CHANNEL_ID=전송할_채널_ID
POLL_MINUTES=30
```

`DISCORD_CHANNEL_ID`는 Discord 개발자 모드에서 채널을 우클릭해 복사할 수 있습니다. 봇에는 해당 채널의 `View Channel`과 `Send Messages` 권한이 필요합니다.

3. 봇을 실행합니다.

```powershell
python Index.py
```

첫 실행 후 행사정보가 변경될 때만 메시지가 전송되며, 마지막 응답의 해시는 `.event_cache.json`에 저장됩니다. 이 파일은 자동으로 생성되므로 Git에 올리지 않는 것을 권장합니다.

봇이 실행되면 다음 슬래시 명령어를 사용할 수 있습니다.

- `/코믹인포`: 가장 가까운 행사 1건을 표시합니다.
- `/코믹스케줄 count:1~10`: 원하는 개수의 행사 일정을 표시합니다.
- `/메뉴추가 menu:메뉴명`: 현재 서버에 점심 메뉴를 등록합니다.
- `/점메추`: 현재 서버에 등록된 메뉴 중 하나를 랜덤으로 추천합니다.

메뉴 데이터는 `menus.db` SQLite 파일에 서버별로 저장되며, 같은 서버에 같은 메뉴를 중복 등록할 수 없습니다.

명령어는 Discord 전역에 동기화되므로 봇이 들어가 있는 모든 서버에서 사용할 수 있습니다. Discord 전역 명령어의 반영에는 최대 약 1시간이 걸릴 수 있습니다.
