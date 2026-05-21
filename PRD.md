# PRD — Supertone CLI (Phase 1)

**Version**: 1.1
**Date**: 2026-04-03
**Status**: Draft

---

## Background

Supertone은 AI 음성 합성(TTS) API를 제공하며, Python SDK(`supertone`)를 통해 개발자가 접근할 수 있다. 그러나 CLI 도구가 없어 매번 Python 코드를 작성해야 하고, 콘텐츠 제작 워크플로에 통합하기 번거롭다.

Phase 1은 Supertone Python SDK를 래핑하는 Unix 파이프 친화적 CLI를 만들어, 한 줄 명령으로 TTS를 실행하고 기존 도구들과 자연스럽게 조합할 수 있게 한다.

### 관련 문서
- [Brainstorm Notes](docs/brainstorm_notes.md)
- [Business Analysis](docs/business_analysis.md)

---

## Goals

1. **코드 없는 TTS** — Python 코드 작성 없이 터미널에서 바로 음성 생성
2. **파이프라인 통합** — stdin/stdout, 배치 처리, JSON 출력으로 기존 도구와 조합 가능
3. **빠른 시작** — `pip install` 후 API 키 설정만으로 즉시 사용 가능
4. **SDK 전체 기능 노출** — TTS, 보이스 관리, 음성 클로닝, 사용량 조회까지 CLI에서 접근 가능

---

## Non-Goals (Phase 1 범위 밖)

- 감정 스타일 시스템 (Phase 2)
- 비언어 태그 자동 삽입 (Phase 2)
- 보이스 가이딩 (Phase 2)
- 대본 포맷 파서 (Phase 2)
- 워크플로/파이프라인 YAML 오케스트레이션 (Phase 2)
- 프로필/프리셋 (`--profile narrator` 등) (Phase 2)
- GUI/TUI 인터페이스

---

## Target User

### 주 사용자: 콘텐츠 크리에이터
- 유튜브 나레이션, 숏폼 보이스오버, 오디오북, 게임 에셋 등 다양한 유형
- 터미널 기본 사용은 가능하지만 Python 코딩에 익숙하지 않을 수 있음
- 반복적인 TTS 작업을 자동화하고 싶음

### 부 사용자: 자동화 파이프라인 구축자
- 셸 스크립트/CI에서 TTS를 호출하는 개발자
- LLM → 번역 → TTS → 편집 같은 워크플로를 구축하는 사람

---

## User Stories

### 기본 TTS
- **US-1**: 사용자로서, 터미널에서 텍스트를 입력하면 음성 파일이 생성되길 원한다. 매번 Python 스크립트를 작성하지 않기 위해.
- **US-2**: 사용자로서, 텍스트 파일을 입력으로 주면 음성 파일로 변환되길 원한다. 긴 대본을 처리하기 위해.
- **US-3**: 사용자로서, 보이스/모델/언어/스타일/포맷을 선택할 수 있길 원한다. 콘텐츠에 맞는 음성을 만들기 위해.
- **US-4**: 사용자로서, TTS 전에 예상 길이를 확인할 수 있길 원한다. 크레딧을 절약하기 위해.

### 파이프라인 통합
- **US-5**: 사용자로서, 다른 명령의 출력을 파이프로 TTS에 넘길 수 있길 원한다. (예: `echo "text" | supertone tts`) 자동화 파이프라인에 끼워 넣기 위해.
- **US-6**: 사용자로서, 음성을 stdout으로 출력할 수 있길 원한다. (예: `supertone tts "text" > output.wav`) 다른 도구로 전달하기 위해.
- **US-7**: 사용자로서, 여러 파일을 한 번에 변환할 수 있길 원한다. 대량의 콘텐츠를 일괄 처리하기 위해.
- **US-8**: 사용자로서, `--format json` 으로 메타데이터를 JSON으로 받을 수 있길 원한다. 스크립트에서 파싱하기 위해.

### 보이스 관리
- **US-9**: 사용자로서, 사용 가능한 보이스 목록을 조회할 수 있길 원한다. 어떤 보이스를 쓸 수 있는지 알기 위해.
- **US-10**: 사용자로서, 언어/성별/나이/용도로 보이스를 검색할 수 있길 원한다. 원하는 보이스를 빠르게 찾기 위해.
- **US-11**: 사용자로서, 내 음성 샘플로 커스텀 보이스를 만들 수 있길 원한다. 고유한 브랜드 음성을 사용하기 위해.
- **US-12**: 사용자로서, 프리셋과 커스텀 보이스를 구분해서 볼 수 있길 원한다. 내가 만든 보이스를 관리하기 위해.

### 설정 & 모니터링
- **US-13**: 사용자로서, API 키를 한 번 설정하면 매번 입력하지 않아도 되길 원한다. 편의를 위해.
- **US-14**: 사용자로서, 자주 쓰는 설정(보이스, 모델, 언어 등)을 기본값으로 저장하길 원한다. 반복 입력을 줄이기 위해.
- **US-15**: 사용자로서, API 사용량을 확인할 수 있길 원한다. 비용을 관리하기 위해.

---

## Functional Requirements

### FR-1: `supertone tts` — 텍스트→음성 변환

| 입력 방식 | 예시 |
|-----------|------|
| 인라인 텍스트 | `supertone tts "안녕하세요"` |
| 파일 입력 | `supertone tts --input script.txt` |
| stdin 파이프 | `echo "안녕하세요" \| supertone tts` |

| 출력 방식 | 예시 |
|-----------|------|
| 파일 출력 | `supertone tts "text" --output hello.wav` |
| stdout | `supertone tts "text" > hello.wav` |
| 자동 파일명 | `supertone tts "text"` → `output.wav` (기본값) |

**옵션**:

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--voice` | 보이스 ID | config 기본값 또는 필수 |
| `--model` | 모델 선택 (sona_speech_1, supertonic_api_1, supertonic_api_3, sona_speech_2, sona_speech_2_flash, sona_speech_2t) | sona_speech_2 |
| `--lang` | 언어 코드 (ko, en, ja 등 31개; `supertonic_api_3` 사용 시 확장 언어 지원) | ko |
| `--style` | 음성 스타일 | 모델 기본값 |
| `--output-format` | 출력 오디오 포맷 (wav, mp3, ogg, flac, aiff) | wav |
| `--speed` | 말하기 속도 | 모델 기본값 |
| `--pitch` | 피치 조절 | 모델 기본값 |
| `--pitch-variance` | 피치 변화량 | 모델 기본값 |
| `--similarity` | 유사도 (sona_speech_2_flash 미지원) | 모델 기본값 |
| `--text-guidance` | 텍스트 가이던스 (sona_speech_2_flash 미지원) | 모델 기본값 |
| `--stream` | 스트리밍 모드 — 실시간 오디오 재생 (sona_speech_1만 지원) | false |
| `--include-phonemes` | 음소 정보 포함 | false |

### FR-2: `supertone tts predict` — 음성 길이 예측

```bash
supertone tts predict "긴 텍스트를 넣으면 예상 길이를 알려줍니다"
supertone tts predict --input script.txt
cat script.txt | supertone tts predict
supertone tts predict "text" --format json    # JSON 출력
```

- Predict Duration API 호출 (크레딧 차감 없음)
- 예상 시간(초), 예상 크레딧 비용 표시
- 배치 처리 전 비용 확인 용도

### FR-3: `supertone tts` — 배치 처리

| 입력 방식 | 예시 |
|-----------|------|
| 디렉토리 입력 | `supertone tts --input ./scripts/ --outdir ./audio/` |
| glob 패턴 | `supertone tts --input "scripts/*.txt" --outdir ./audio/` |

- 입력 파일명 기반으로 출력 파일명 자동 생성 (예: `script1.txt` → `script1.wav`)
- 진행률 표시 (stderr, 파이프 시 자동 비활성화)
- 에러 발생 시 나머지 파일 계속 처리 (`--fail-fast`로 중단 가능)

### FR-4: `supertone voices list` — 보이스 목록 조회

```bash
supertone voices list                          # 전체 보이스 목록
supertone voices list --type preset            # 프리셋 보이스만
supertone voices list --type custom            # 커스텀 보이스만
supertone voices list --format json            # JSON 출력
```

- SDK의 `list_voices` 호출
- 테이블 형식 기본 출력 (이름, ID, 타입, 지원 언어)
- `--format json`으로 JSON 출력

### FR-5: `supertone voices search` — 보이스 검색

```bash
supertone voices search --lang ko              # 한국어 지원 보이스
supertone voices search --gender female        # 여성 보이스
supertone voices search --age young            # 젊은 보이스
supertone voices search --use-case narration   # 나레이션용
supertone voices search --query "밝은"          # 키워드 검색
supertone voices search --lang ko --gender female --format json
```

- Search Voices API 호출
- 필터 조합 가능 (언어 + 성별 + 나이 + 용도)
- 키워드 검색 지원

### FR-6: `supertone voices clone` — 보이스 클로닝

```bash
supertone voices clone --name "my-narrator" --sample ./voice_sample.wav
supertone voices clone --name "my-narrator" --sample ./sample.wav --format json
```

- 음성 샘플 파일 업로드 (~10초)
- 지원 오디오 포맷 검증 (업로드 전)
- 등록 완료 후 voice_id 출력
- 등록된 커스텀 보이스는 `supertone tts --voice <id>`로 즉시 사용 가능

### FR-7: `supertone usage` — 사용량 조회

```bash
supertone usage                                # 현재 사용량 요약
supertone usage --format json                  # JSON 출력
```

- Get Voice Usage API 호출
- 사용량, 잔여 크레딧, 요금제 정보 표시

### FR-8: `supertone config` — 설정 관리

```bash
supertone config init               # 대화형 초기 설정 (API 키 + 기본값)
supertone config set api_key <key>  # 개별 설정
supertone config set default_voice <id>
supertone config set default_model sona_speech_2
supertone config set default_lang ko
supertone config get api_key        # 설정 조회
supertone config list               # 전체 설정 출력
```

- 설정 파일 위치: `~/.config/supertone/config.toml`
- API 키는 환경변수 `SUPERTONE_API_KEY`로도 지원 (환경변수 우선)
- `config init`은 대화형으로 API 키, 기본 보이스, 모델, 언어를 설정

### FR-9: 출력 & 에러 처리

- **일반 출력**: 사람이 읽기 쉬운 형태 (테이블, 진행률 등) → stderr
- **오디오 데이터**: stdout 또는 파일
- **`--format json`**: 모든 명령에서 JSON 출력 지원
- **종료 코드**: 0=성공, 1=일반 에러, 2=인증 에러, 3=입력 에러
- **에러 메시지**: stderr로 출력, 원인과 해결 방법 포함
- **파이프 감지**: stdout이 터미널이 아닌 경우 진행률/컬러 자동 비활성화

---

## Non-Functional Requirements

### NFR-1: 설치 용이성
- `pip install supertone-cli` 한 줄로 설치
- Python 3.11+ 지원
- 의존성 최소화 (supertone SDK, typer, rich)

### NFR-2: 응답 속도
- CLI 시작 시간 < 500ms (import 최적화)
- TTS 변환 시간은 Supertone API 응답에 의존 (CLI 자체 오버헤드 최소화)

### NFR-3: 보안
- API 키는 config 파일에 저장 시 파일 퍼미션 600 적용
- API 키를 로그/에러 메시지에 노출하지 않음
- 환경변수 `SUPERTONE_API_KEY` 지원

### NFR-4: 테스트
- pytest 기반 테스트
- API 호출은 mock 처리 (단위 테스트), 통합 테스트는 `-m integration`으로 분리
- 주요 명령어별 최소 1개 테스트

---

## Technical Notes

### 기술 스택
- **언어**: Python 3.11+
- **패키지 관리**: uv
- **CLI 프레임워크**: Typer (Click 기반, 타입 힌트 활용, Rich 통합)
- **TTS 엔진**: supertone Python SDK
- **설정 관리**: TOML (`~/.config/supertone/config.toml`)
- **테스트**: pytest + pytest-cov
- **배포**: PyPI (`supertone-cli`)

### SDK 의존성
- `supertone` 패키지의 `Supertone` 클라이언트 사용
- 주요 메서드:
  - `text_to_speech.create_speech()` — TTS 생성
  - `text_to_speech.stream_speech()` — 스트리밍 TTS
  - `list_voices()` — 보이스 목록
  - Search Voices API — 보이스 검색
  - Voice Cloning Registration API — 음성 클로닝
  - Predict Duration API — 길이 예측
  - Get Voice Usage API — 사용량 조회
- 에러 처리: `SupertoneError` 및 하위 클래스 활용

### CLI 명령어 구조

```
supertone
├── tts <text>           # 텍스트→음성 변환
│   └── predict <text>   # 음성 길이 예측
├── voices
│   ├── list             # 보이스 목록 조회
│   ├── search           # 보이스 검색
│   └── clone            # 보이스 클로닝
├── usage                # 사용량 조회
└── config
    ├── init             # 대화형 초기 설정
    ├── set <key> <val>  # 설정 변경
    ├── get <key>        # 설정 조회
    └── list             # 전체 설정 출력
```

### 패키지 구조

```
supertone-cli/
├── src/
│   └── supertone_cli/
│       ├── __init__.py
│       ├── cli.py            # 메인 CLI 엔트리포인트
│       ├── commands/
│       │   ├── tts.py        # tts, tts predict 명령
│       │   ├── voices.py     # voices list, search, clone 명령
│       │   ├── usage.py      # usage 명령
│       │   └── config.py     # config 명령
│       ├── config.py         # 설정 관리
│       └── client.py         # SDK 래핑 레이어
├── tests/
├── pyproject.toml
└── README.md
```

---

## Success Metrics

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 설치 → 첫 TTS 생성 | < 3분 | 사용자 테스트 |
| CLI 시작 시간 | < 500ms | 벤치마크 |
| 테스트 커버리지 | > 80% | pytest-cov |
| PyPI 설치 성공률 | > 95% | PyPI 통계 |

---

## Decisions

| # | 결정 | 근거 |
|---|------|------|
| 1 | **CLI 프레임워크: Typer** | Click 기반이라 안정적이면서, 타입 힌트 활용으로 코드 간결. Rich 통합. 2025-2026 신규 프로젝트 트렌드 |
| 2 | **프로필/프리셋은 Phase 2로** | Phase 1은 핵심 기능에 집중. 커스텀 프리셋은 사용 패턴 파악 후 설계 |
| 3 | **스트리밍은 실시간 오디오 재생 포함** | `--stream` 시 터미널에서 바로 오디오 재생. 파일 저장과 병행 가능 |
| 4 | **`models` 명령 제거** | 모델 4개로 고정적. `supertone tts --help`에서 충분히 커버 |
| 5 | **보이스 클로닝 Phase 1에 포함** | SDK API에서 지원 확인됨. `voices clone` 서브커맨드로 제공 |
| 6 | **`--style` 옵션 추가** | SDK v1.1.0+ 에서 style이 voice_id와 분리됨 |
