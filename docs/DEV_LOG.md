# DEV_LOG.md — 개발 일지

> 이 문서는 시간순 개발 기록이다.
> 날짜별 작업 내용, 의사결정 기록, 변경 사항을 기록한다.

---

## 2026-05-21 — 1단계: 뼈대 세우기

### 작업 내용

**PRD/RULES 분석 완료**
- PRD.pdf: 프로젝트 목표, MVP 범위, 기술 스택, 개발 로드맵 확인
- RULES.md: 아키텍처 원칙, COM 안정성, 스레드 규칙, 파일 무결성 규칙 확인

**프로젝트 구조 설계 및 생성**
- 5개 레이어: Core / UI / Service / Worker / Utility
- 총 19개 Python 파일 + 1개 QSS + 1개 requirements.txt
- 4개 프로젝트 문서 (ARCHITECTURE / CURRENT_STATUS / DEV_LOG / BUGS)

**Core Layer 구현**
- `AppState` 싱글톤 — Signal 기반 상태 통지
- `FileTask`, `PrintOptions`, `JobResult` dataclass 모델
- `FileStatus`, `JobStatus`, `DuplexMode`, `NupMode` 열거형
- 전역 상수 (`constants.py`)

**UI Layer 구현**
- `MainWindow` — 4개 패널 조립 + Signal/Slot 연결
- `DropZone` — 드래그앤드롭 수신 (시각적 피드백 포함)
- `FileListPanel` — 테이블 위젯 + 상태 표시 + 선택/전체 삭제
- `ControlPanel` — 매수/양면/모아찍기 옵션 + PDF/인쇄/취소 버튼
- `ProgressPanel` — 프로그레스 바 + 상태 레이블 + 로그 영역

**Service/Worker Layer (Stub)**
- 클래스 선언 + 메서드 시그니처만 정의
- 2단계에서 구현 예정

### 의사결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| 상태 관리 | Singleton AppState + Signal | Frame 간 직접 공유 금지 규칙 준수 |
| 데이터 모델 | dataclass | RULES.md에서 Pydantic 사용 금지 |
| Worker 구조 | QThread 상속 | PySide6 스레드 규칙 준수 |
| 레이어 분리 | 5-Layer | SoC 원칙 강화 (Core 레이어 분리) |

---

## 2026-05-21 — 2단계: 내용 채우기

### 작업 내용

**Service Layer 구현**
- `log_service.py` — 4개 분리 로거 (app/convert/print/error), Singleton, UTF-8 파일 핸들러
- `hwp_service.py` — COM 인스턴스 생성/해제, 문서 열기(읽기 전용)/닫기, 보안 모듈 등록
- `pdf_service.py` — PDF 변환 (Safe Save: temp→검증→rename), PDF_OUTPUT/ 자동 생성
- `print_service.py` — HWP Action API 기반 인쇄 (매수/양면/모아찍기), 프린터 목록 조회

**Worker Layer 구현**
- `pdf_worker.py` — COM in Thread, pythoncom.CoInitialize/CoUninitialize, 순차 변환
- `print_worker.py` — COM in Thread, 순차 인쇄, 옵션 로깅

**UI ↔ Worker 연결** (main_window.py 수정)
- PdfWorker / PrintWorker 생성 및 Signal 연결
- progress / file_done / finished_all / log_message 4개 시그널 연결
- 취소 기능 구현
- PDF 변환 완료 후 출력 폴더 열기 대화상자
- 작업 중 중복 실행 방지

### 의사결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| COM 인스턴스 수명 | 배치 전체에서 1개 재사용 | 파일마다 생성/해제하면 느리고 불안정 |
| COM 스레드 초기화 | pythoncom.CoInitialize | Worker Thread에서 COM 사용 필수 |
| PDF 저장 | temp.pdf → 검증 → rename | RULES §4-2 Safe Save 원칙 |
| 에러 격리 | per-file try/except | RULES §5-3 실패 파일이 전체 중단하면 안 됨 |
| 보안 모듈 | RegisterModule 호출 | HWP COM 자동화 시 보안 경고 차단 |

### 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| services/log_service.py | 전체 구현 |
| services/hwp_service.py | 전체 구현 |
| services/pdf_service.py | 전체 구현 |
| services/print_service.py | 전체 구현 |
| workers/pdf_worker.py | 전체 구현 |
| workers/print_worker.py | 전체 구현 |
| ui/main_window.py | Worker 연결 + 취소 + 폴더 열기 + 레이아웃 미세조정 |

---

## 2026-05-21 — 3단계: 디자인 적용

### 작업 내용

**프리미엄 QSS 테마 설계 및 적용**
- `assets/styles/main.qss`에 딥 인디고(Indigo 600)를 주 색상으로 하고 에머랄드(Emerald), 로즈(Rose)를 보조/상태 피드백 컬러로 하는 세련된 모던 테마 구축.
- 드롭존(`DropZone`) 마우스 드래그 진입(`dragOver="true"`) 시 보더 하이라이팅 및 배경색 변경 시각 효과 적용.
- 컨트롤 패널 내 `QPushButton`들의 테두리 둥글기(border-radius: 6px), 패딩, 비활성화(disabled) 비주얼 폴리싱.
- 로그 뷰어(`logArea`)를 어두운 테두리와 다크 슬레이트 배경, 오프 화이트 텍스트가 조화된 터미널 감성 스타일로 변경하여 업무 일지 가독성 개선.
- 스크롤바(`QScrollBar`)를 얇고 둥근 형태로 커스텀 디자인하여 공간 활용도 극대화.

**테이블 개별 행 진행 상태별 스타일링**
- `ui/file_list_panel.py`에서 `QTableWidgetItem`의 `setBackground()` 및 `setForeground()`를 제어하는 `_style_row()` 헬퍼 구현.
- 각 파일별 상태(`FileStatus`) 변화에 따른 시각 피드백 연결:
  - 대기 중 (Pending): 기본 흰색 배경
  - 처리 중 (Processing): 연한 파란색 배경 (`#eff6ff`), 파란색 글씨 (`#1d4ed8`)
  - 성공 (Success): 연한 녹색 배경 (`#ecfdf5`), 초록색 글씨 (`#047857`)
  - 실패 (Failed): 연한 빨간색 배경 (`#fef2f2`), 빨간색 글씨 (`#b91c1c`)
  - 건너뜀 (Skipped): 연한 회색 배경 (`#f3f4f6`), 어두운 회색 글씨 (`#4b5563`)

**UI 레이아웃 미세 조정**
- `ui/main_window.py` 메인 레이아웃의 패딩을 16px, 간격을 10px로 확대하여 요소 간의 시각적 답답함을 해소하고 여백의 미 확보.

### 의사결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| 상태별 배경 지정 방식 | `QTableWidgetItem` 직접 스타일 설정 | QSS만으로는 테이블 개별 셀 내용/상태에 따른 동적 배경 매핑 처리가 까다로우며 성능 저하를 야기하므로, Qt API로 직접 브러시 객체를 주입하는 방식이 안전하고 직관적임 |

### 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| assets/styles/main.qss | QSS 테마 설계 및 전체 리팩토링 |
| ui/file_list_panel.py | 상태별 색상 헬퍼 추가 및 테이블 스타일링 반영 |
| ui/main_window.py | 레이아웃 마진/간격 조정 |

---

## 2026-05-21 — 4단계: 마무리 점검

### 작업 내용

**COM 생성 안정성 보강 및 Dispatch 폴백**
- `services/hwp_service.py` 내의 `create_hwp_instance()` 리팩토링.
- `EnsureDispatch` 실패 시 레지스트리 상태나 캐시 오염 등으로 인한 오류 방지를 위해 `win32com.client.Dispatch`로 2차 시도(Fallback) 하도록 안정성 추가.
- `hwp.XHwpWindows.Item(0).Visible = False`를 안전하게 감싸서, 윈도우 핸들이 사전에 초기화되지 않은 상태에서 COM 연결 시 발생하는 인덱스 예외 처리 추가.
- 한글 문서 자동화 시의 보안 모듈 등록 예외 또한 try-except로 분리 격리하여 COM의 부분적 장애가 전체 시작 중단으로 확장되는 것을 방지.

**PyInstaller 단일 파일 패키징 자동화**
- `build_exe.py` 자동 빌드 파이썬 스크립트 작성.
- CP949 인코딩을 기본으로 사용하는 한글 Windows 콘솔 환경에서도 예외 없이 인코딩 출력이 진행되도록 print문 내 특수 이모티콘을 모두 텍스트 테그(`[OK]`, `[INFO]`)로 표준화.
- 스타일시트 리소스 누락을 원천 차단하기 위해 `--add-data "assets;assets"` 추가하여 최종 exe에서 테마가 유실되지 않도록 빌드 인수 설정.
- 이전 빌드 산출물(`build`, `dist` 디렉토리) 자동 정리 코드 통합.

### 의사결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| COM 실패 폴백 | EnsureDispatch -> Dispatch 폴백 | PC 환경에 따라 win32com 캐시(gen_py)가 손상되었거나 사전 빌드가 비활성화되어 있는 경우, EnsureDispatch가 크래시되는 경우가 잦음. 이 때 Dispatch로 폴백하면 즉시 해결 가능 |
| 리소스 번들링 방식 | PyInstaller `--add-data` | QSS 등의 설정 파일을 외부 참조 경로로 남겨두면 배포 시 사용자가 실수로 빼먹을 확률이 높으므로 단일 exe에 완전히 포팅하여 무결성 유지 |

### 변경된 파일

| 파일 | 변경 유형 |
|------|-----------|
| services/hwp_service.py | COM 생성 안정성 예외 보강 및 폴백 로직 추가 |
| build_exe.py | PyInstaller 자동화 빌드 스크립트 신규 구현 |
