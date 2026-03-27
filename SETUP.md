# AI Handover 셋업 가이드

## 사전 요구사항

| 항목 | 최소 버전 | 확인 방법 |
|------|-----------|-----------|
| Node.js | 19.0.0 이상 | `node -v` |
| Python | 3.10 이상 | `python --version` |
| pip | 최신 권장 | `pip --version` |
| Git | 최신 권장 | `git --version` |

---

## 1. 저장소 클론

```bash
git clone <저장소 URL>
cd ai-handover
```

---

## 2. Node.js 의존성 설치

```bash
npm install
```

> `postinstall` 스크립트가 자동으로 `electron-builder install-app-deps`를 실행합니다.

---

## 3. Python 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

로컬 임베딩(sentence-transformers)을 사용하려면 추가 설치:

```bash
pip install sentence-transformers
```

> **참고:** 앱을 `npm run dev`로 실행하면, `fastapi`가 import되지 않을 경우 자동으로 `pip install -r requirements.txt`를 실행합니다. 하지만 처음에는 수동 설치를 권장합니다.

---

## 4. AI 프로바이더 API 키 준비

앱 내 Settings 패널에서 설정하지만, 사전에 준비해두세요.

| 프로바이더 | 필요한 키 | 용도 |
|-----------|-----------|------|
| **OpenAI** | `OPENAI_API_KEY` | 임베딩 + 채팅 (GPT 모델) |
| **Anthropic** | `ANTHROPIC_API_KEY` | 채팅 (Claude 모델) + 로컬 임베딩 사용 |

> OpenAI는 임베딩과 채팅 모두 지원, Anthropic은 채팅에는 Claude를 사용하고 임베딩에는 로컬 `sentence-transformers`를 사용합니다.

---

## 5. 개발 모드 실행

```bash
# 프로젝트 루트에서 실행
npm run dev
```

- Electron 앱이 실행되며 내부적으로 Python 백엔드(`uvicorn`)가 포트 **8932**에서 자동 시작됩니다.
- 백엔드 헬스체크(`http://127.0.0.1:8932/health`) 응답 후 앱 창이 열립니다.
- 최초 실행 시 백엔드 기동까지 수십 초가 걸릴 수 있습니다.

---

## 6. 앱 사용 시작

1. **Settings** 패널에서 AI 프로바이더와 API 키, 모델명 입력
2. **+ Add Project** 버튼으로 분석할 로컬 폴더 선택
3. 프로젝트 선택 후 **Index** 버튼으로 코드 인덱싱 시작
4. 인덱싱 완료(`ready` 상태) 후 채팅 시작

---

## 7. 데이터 저장 위치

앱 데이터는 OS별 `userData` 경로 하위에 저장됩니다:

| OS | 경로 |
|----|------|
| Windows | `%APPDATA%\ai-handover\data\` |
| macOS | `~/Library/Application Support/ai-handover/data/` |
| Linux | `~/.config/ai-handover/data/` |

- `app.db` — SQLite (프로젝트 목록, 채팅 기록, 암호화된 API 키)
- `chroma/` — ChromaDB 벡터 인덱스

---

## 8. 백엔드 단독 실행 (선택)

Electron 없이 백엔드만 테스트할 경우:

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8932 --reload
```

API 문서: `http://127.0.0.1:8932/docs`

---

## 9. 테스트 실행

```bash
cd backend
pytest tests/ -v

# 특정 테스트만
pytest tests/test_rag.py -v
pytest tests/test_chunker.py -v
```

---

## 10. 프로덕션 빌드 (Windows)

```bash
npm run build:win
```

- `dist/` 폴더에 NSIS 설치 파일(`.exe`) 생성
- Python 백엔드(`backend/*.py`)는 `resources/backend/`에 번들링됨
- 배포된 앱은 사용자 환경의 Python + pip를 사용해 의존성을 자동 설치

---

## 트러블슈팅

### 백엔드가 시작되지 않는 경우 (Windows)
- Electron은 bash/터미널 PATH와 무관하게 **Windows 시스템에 등록된 `python`** 을 호출합니다.
- `pyenv`, `conda` 등 가상환경을 사용 중이라면, Electron이 실제로 어떤 Python을 쓰는지 확인 후 그 Python에 패키지를 설치해야 합니다:
  ```
  # 앱 실행 후 로그에서 python 경로 확인 (예시)
  # [Backend] C:\Users\...\Python\pythoncore-3.14-64\python.exe: No module named uvicorn

  # 해당 Python으로 직접 설치
  "C:\Users\...\Python\pythoncore-3.14-64\python.exe" -m pip install -r backend\requirements.txt
  ```
- 포트 8932가 다른 프로세스에 의해 사용 중인지 확인: `netstat -ano | findstr 8932`

### ChromaDB 오류
- Python 버전이 3.10 이상인지 확인
- `pip install --upgrade chromadb`로 업그레이드 시도

### Anthropic + 임베딩 오류
- `sentence-transformers` 패키지가 설치되어 있는지 확인
- 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있음

### npm install 실패
- Node.js 버전 확인 (`node -v`, 19.0.0 이상 필요)
- `node_modules` 삭제 후 재시도: `rm -rf node_modules && npm install`
