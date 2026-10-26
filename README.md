# Suro Discord App

슈로 Discord 봇의 코드와 공개 문의를 관리하는 저장소입니다.

- **개발 중인 버전:** 기본 브랜치의 `GA2.0-S`. 아직 Release로 배포하지 않습니다.
- **이전 버전:** [Releases](https://github.com/Nikuyi-cnst/Suro-DiscordApp/releases)의 `GA1.0-S (Restored)` ~ `OB2.0-U.E (Restored)`에서 받습니다.
- **공개 문의:** Discord의 `/문의` 또는 [GitHub Issues](https://github.com/Nikuyi-cnst/Suro-DiscordApp/issues)를 사용합니다.

## 설치와 실행

Python 3.10 이상이 필요합니다. 아래는 Windows PowerShell 기준입니다.

```powershell
git clone https://github.com/Nikuyi-cnst/Suro-DiscordApp.git
Set-Location Suro-DiscordApp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

로컬 `.env`를 편집하여 아래 값을 설정한 다음 실행합니다. `.env.example`에는 실제 토큰을 넣지 마세요. 환경변수로 직접 주입해도 되며, 이미 주입한 환경변수가 `.env`보다 우선합니다.

| 변수 | 설정 |
|---|---|
| `DISCORD_TOKEN` | Discord Developer Portal에서 발급한 봇 토큰 |
| `GITHUB_TOKEN` | 아래 권한으로 발급한 GitHub fine-grained PAT |
| `GITHUB_REPOSITORY` | `Nikuyi-cnst/Suro-DiscordApp` |
| `DISCORD_CHANNEL_ID` | 선택. 정기 코믹월드 알림을 보낼 채널 ID. 비우면 해당 알림을 비활성화합니다 |

```powershell
.\.venv\Scripts\python.exe Index.py
```

Discord Developer Portal에서 봇이 사용하는 **Message Content Intent**를 활성화하고, 서버에 `bot` 및 `applications.commands` 권한으로 초대하세요. 명령 동기화에는 시간이 걸릴 수 있습니다.

기존 알림/관리자 기능의 환경변수(`ADMIN_IDS`, `AUTO_MESSAGE_TIME`, `AUTO_MESSAGE_TEXT`, `AUTO_MESSAGE_TEXTS`, `AUTO_MESSAGE_CHANNEL_IDS`, `POLL_MINUTES`)는 계속 사용할 수 있습니다.

### GitHub 인증 설정

1. GitHub의 **Settings → Developer settings → Personal access tokens → Fine-grained tokens**에서 토큰을 만듭니다.
2. Resource owner는 `Nikuyi-cnst`, Repository access는 **Only select repositories → Suro-DiscordApp**으로 제한합니다.
3. Repository permissions에서 **Issues: Read and write**를 허용합니다. 기본 **Metadata: Read-only**는 저장소 공개 여부 확인에 사용합니다. 코드 쓰기나 전체 저장소 접근 권한은 필요하지 않습니다.
4. 만료일을 지정하고 로컬 `.env`의 `GITHUB_TOKEN` 또는 봇 실행 환경의 시크릿에만 저장합니다. 만료·폐기된 토큰은 교체하세요.

이 봇의 문의는 지정된 공개 저장소에만 생성됩니다. 저장소가 비공개이거나 Issues가 비활성화되거나 토큰 권한이 부족하면 등록하지 않고 오류를 안내합니다. 다른 봇 기능은 문의용 토큰 없이도 사용할 수 있습니다.

GitHub Actions의 Secrets에 저장하는 것만으로 로컬 봇에 적용되지는 않습니다. 실행 환경에서 환경변수로 명시적으로 주입해야 합니다. 이 저장소에는 자동 배포를 구성하지 않았습니다.

## `/문의` 사용법과 공개 범위

`/문의 content:문의 내용`으로 접수합니다. **이미지 첨부는 선택 사항**이며, 첨부할 때는 이미지 파일만 허용합니다. 공백만 있는 내용은 접수하지 않으며, 앞뒤 공백을 제거한 후 최대 1,000자입니다.

명령을 제출하면 다음 항목이 **공개 GitHub 이슈**로 등록됩니다.

- 문의 내용
- 작성자의 Discord 표시 이름
- 이미지를 첨부한 경우 해당 이미지 링크

Discord 사용자 ID, 서버 이름, 서버 ID는 별도 정보로 추가하지 않습니다. 다만 사용자가 내용/이미지에 직접 포함한 정보와 이미지 URL 자체의 식별 정보는 공개됩니다. **개인정보, 비밀번호, 봇 토큰 등 비밀 정보는 보내지 마세요.** 비공개 문의 기능은 없습니다.

기존 개발자 DM/관리자 채널 전달을 대신하며, 성공하면 명령 사용자에게만 이슈 링크를 안내합니다. 봇이 사용자에게 보내는 응답은 비공개여도 **GitHub 이슈 자체는 누구나 볼 수 있습니다.**

이미지를 GitHub에 별도 업로드하지 않고 Discord 첨부 링크를 기록하므로, 링크가 만료되거나 원본이 삭제되면 이미지가 표시되지 않을 수 있습니다. 영구 보관이 필요하면 민감 정보를 확인한 뒤 관리자가 GitHub 이슈에서 직접 첨부하세요.

연결 오류로 생성 여부를 확인하지 못하면 재접수 전에 Issues 목록을 확인하세요. 중복 이슈 방지를 위해 봇은 생성 요청을 자동 재시도하지 않습니다. GitHub 등록에는 성공했지만 Discord 응답 전달이 실패한 경우에도 먼저 Issues를 확인하세요.

## 버전 복원 안내

이전 버전의 로컬 소스 백업에서 다음 순서로 코드 상태를 복원했습니다.

| Release 이름 | 코드 태그 |
|---|---|
| GA1.0-S (Restored) | `GA1.0-S` |
| GA1.1-S (Restored) | `GA1.1-S` |
| GA1.2-S (Restored) | `GA1.2-S` |
| GA1.3-S (Restored) | `GA1.3-S` |
| OB2.0-U.E (Restored) | `OB2.0-U.E` |

Release의 제목은 왼쪽 이름 그대로입니다. 오른쪽 태그는 GitHub가 Release의 기준 코드를 가리키는 데 쓰는 별도 식별자입니다.

기존 Git 기록이나 과거 출시일을 재현한 것이 아닌 **소스 스냅샷 복원**입니다. 과거 코드에는 최신 문의 연동을 소급 적용하지 않았습니다. Releases에서 **Source code (zip)**을 내려받아 해당 시점의 코드를 확인할 수 있습니다. 실행하려면 각 버전의 의존성과 별도 로컬 환경 설정이 필요합니다.

최신 `GA2.0-S`는 별도 최신 원본에서 가져온 개발 코드입니다. GA2.0-S 자체와 이후 문의 연동은 커밋으로만 관리하며, GA2.0-S 태그나 Release는 만들지 않습니다.

원본 실행 폴더와 백업은 수정하지 않습니다. 따라서 이미 실행 중인 봇에는 이 변경이 자동 적용되지 않습니다. 새 저장소를 별도 폴더에 받은 뒤 로컬에서 토큰을 설정하고, 운영자가 기존 프로세스를 중지한 다음 새 코드로 실행하세요. DB를 옮길 경우 봇을 중지하고 로컬에서 별도로 백업·이전하며, Git에는 올리지 마세요.

## 비밀 파일 보호

모든 복원 커밋과 릴리즈를 포함해 `.env` 및 환경별 변형, 기존 `.git` 기록, DB, 로그, 가상환경, 캐시는 업로드하지 않습니다. `.env.example`은 비밀값 없는 설정 예제만 제공합니다.

`.gitignore`는 **이미 추적된 파일이나 과거 기록에서 비밀을 제거하지는 않습니다.** 이전 저장소 등에 토큰이 커밋된 적이 있다면 Discord Developer Portal에서 봇 토큰을 재발급하고, GitHub 토큰도 폐기·재발급하세요. 새 저장소로 옮겼다고 과거 노출이 해소되는 것은 아닙니다. 이 이전 작업은 기존 저장소의 기록을 수정하거나 저장소를 삭제하지 않습니다.

커밋 전에 아래 명령으로 파일 목록을 확인하세요. 실제 토큰이 들어 있는 파일을 `git add -f`로 강제로 추가하지 마세요.

```powershell
git status --short
git ls-files
git check-ignore .env
```

## GitHub에서 자주 쓰는 용어

| 용어 | 뜻 |
|---|---|
| 저장소 / Repository | 코드, 변경 기록, 문의 이슈를 모아두는 프로젝트 공간 |
| 커밋 / Commit | 특정 시점의 코드 변경을 저장한 기록 |
| 브랜치 / Branch | 다른 코드에 바로 영향을 주지 않고 작업하는 갈래. `main`은 기본 코드 |
| PR / Pull Request | 브랜치의 변경을 검토하고 합치기 위한 요청 |
| 병합 / Merge | 작업한 변경을 다른 브랜치에 합치는 것 |
| 이슈 / Issue | 버그, 질문, 기능 요청을 기록하고 논의하는 게시글 |
| 태그 / Tag | 특정 커밋에 붙이는 고정 버전 이름 |
| 릴리즈 / Release | 태그의 코드에 설명과 다운로드를 붙이는 배포 페이지 |
| Clone | 저장소와 기록을 내 컴퓨터에 처음 복사하기 |
| Push / Pull | 로컬 커밋을 GitHub에 올리기 / GitHub 변경을 로컬로 가져와 합치기 |
| `.gitignore` | Git에 새로 추가하지 않을 파일과 폴더를 지정하는 목록 |

## 테스트

문의 테스트는 GitHub와 Discord를 mock으로 대체하므로 실제 이슈나 메시지를 만들지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_inquiry.py"
.\.venv\Scripts\python.exe -m unittest discover -s tests
```
