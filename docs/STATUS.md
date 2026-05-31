# STATUS (프로젝트 상태 및 배포 가이드)

본 문서는 **HWP Batch Printer** 프로젝트의 현재 개발 진행 상태, 각 파일별 구현 여부, 배포 패키징 안내 및 발견된 버그 현황을 통합하여 추적하는 문서입니다.

---

## 1. 현재 진행 상태

- **현재 단계**: **4단계: 마무리 점검** ✅ 완료 (프로젝트 전체 개발 완료)
- **최종 업데이트**: 2026-05-31

### 마일스톤 완료 내역

#### 1단계: 뼈대 세우기 ✅
- 5-Layer 기반 프로젝트 디렉토리 구조 생성
- **Core Layer**: AppState, models, signals, constants 구현 완료
- **UI Layer**: MainWindow, DropZone, FileListPanel, ControlPanel, ProgressPanel 구현 완료
- **Service/Worker/Utils Layer**: 기초 클래스 선언 및 Stub 정의 완료

#### 2단계: 내용 채우기 ✅
- **Service Layer**: file_manager, hwp_service, pdf_service, print_service, log_service 비즈니스 핵심 로직 구현 완료
- **Worker Layer**: 백그라운드 스레드 제어를 위한 pdf_worker, print_worker 구현 완료
- UI와 Worker 간의 비동기 Signal/Slot 이벤트 연동 완료 및 취소 처리 지원
- PDF 변환 종료 후 결과 출력 디렉토리 열기 편의 기능 반영

#### 3단계: 디자인 적용 ✅
- `assets/styles/main.qss` 모던 인디고/에머랄드/로즈 프리미엄 테마 설계 및 스타일시트 반영 완료
- 드롭존 마우스 드래그 진입 시 시각적 하이라이트(보더 및 배경색 변경) 적용 완료
- 개별 작업 파일들의 실시간 상태(`FileStatus`)에 따른 테이블 행 동적 스타일링(배경색 및 텍스트 색상 차별화) 구현 완료
- 윈도우 레이아웃 마진 및 패딩의 미세 튜닝 완료

#### 4단계: 마무리 점검 ✅
- 한글 자동화 기기별 환경 호환성 보강을 위해 `XHwpWindows.Item(0)` try-except 격리 및 `EnsureDispatch` 실패 시 `Dispatch` 자동 2차 시도 폴백(Fallback) 구조 구축 완료
- CP949 인코딩용 ASCII 텍스트 빌드 상태 로그 및 에셋 리소스를 자동 번들링하는 `build_exe.py` 패키징 빌드 자동화 스크립트 작성 완료
- PyInstaller 단일 실행 파일 빌드 및 최종 Windows 10/11 환경 작동 검증 테스트 통과

---

## 2. 파일별 구현 명세

현재 프로젝트를 구성하는 소스 코드들의 개발 완료 현황입니다.

| 폴더 | 파일명 | 상태 | 상세 비고 및 연동 내용 |
|:---|:---|:---:|:---|
| **Root** | `main.py` | ✅ 완료 | 프로그램 진입점. QApplication 생성 및 스타일시트 로드, 메인 윈도우 팝업 |
| | `build_exe.py` | ✅ 완료 | PyInstaller 자동화 빌드 스크립트. 이전 산출물 자동 클리닝 및 리소스 포팅 |
| **Core** | `core/constants.py` | ✅ 완료 | UI 마진값, 최대 매수 제한 등 전역 상수 데이터 정의 |
| | `core/models.py` | ✅ 완료 | FileTask, PrintOptions, JobResult 등 표준 데이터 구조체 정의 |
| | `core/signals.py` | ✅ 완료 | Worker ↔ UI 연동용 전역 Qt Signals 정의 |
| | `core/app_state.py` | ✅ 완료 | 전역 파일 큐 및 옵션 관리를 위한 싱글톤 AppState 클래스 |
| **UI** | `ui/main_window.py` | ✅ 완료 | 전체 레이아웃 조립, UI-Worker 시그널 바인딩 및 예외 다이얼로그 처리 |
| | `ui/drop_zone.py` | ✅ 완료 | 드래그 앤 드롭 파일 탐색기 연동 및 시각 피드백 기능 |
| | `ui/file_list_panel.py` | ✅ 완료 | 테이블 위젯 제어 및 개별 상태(`Pending`/`Processing`/`Success`/`Failed`) 컬러링 |
| | `ui/control_panel.py` | ✅ 완료 | 매수 선택 스핀박스, 양면/단면 선택 콤보박스, 모아찍기 라디오 그룹 및 액션 버튼 |
| | `ui/progress_panel.py` | ✅ 완료 | 일괄 작업 진척률 프로그레스 바 및 터미널 스타일 로그 뷰어 |
| **Services**| `services/file_manager.py` | ✅ 완료 | 드롭된 파일 중 유효한 한글(hwp, hwpx) 확장자 검사 및 목록 정합성 검증 |
| | `services/hwp_service.py` | ✅ 완료 | 한글 COM 연동, 읽기 전용 열기, 보안 승인 모듈 처리 및 인스턴스 자동 소멸 |
| | `services/pdf_service.py` | ✅ 완료 | 임시 저장 후 검증 통과 시 목적지 변경하는 Safe Save 기반 PDF 변환 로직 |
| | `services/print_service.py` | ✅ 완료 | HWP Action API를 매핑하여 양면/모아찍기 등의 시스템 인쇄 명령 제어 |
| | `services/log_service.py` | ✅ 완료 | UTF-8 호환 4개 영역(app, convert, print, error) 분리 로깅 엔진 |
| **Workers** | `workers/pdf_worker.py` | ✅ 완료 | QThread 상속 백그라운드 스레드. pythoncom 초기화 및 순차 PDF 변환 |
| | `workers/print_worker.py` | ✅ 완료 | QThread 상속 백그라운드 스레드. 순차 인쇄 명령 및 옵션 파라미터 로깅 |
| **Utils** | `utils/file_utils.py` | ✅ 완료 | 경로 정상성 및 임시 파일 처리를 돕는 유틸리티 함수군 |
| | `utils/com_utils.py` | ✅ 완료 | win32com 관련 Dispatch 핸들러 및 프로세스 잔류 보완 유틸리티 |

---

## 3. 배포 및 실행 안내

1. **사전 준비**:
   - Python 3.11 이상 및 pywin32, PySide6 패키지가 가상환경에 설치되어 있는지 확인합니다.
   - 실제 HWP 제어를 위해 대상 Windows PC에 **한글 2018 이상**의 프로그램이 정식 설치되어 있어야 합니다.
2. **빌드 명령**:
   프로젝트 루트 디렉토리에서 다음 명령을 실행합니다.
   ```bash
   python build_exe.py
   ```
3. **빌드 산출물**:
   빌드가 성공적으로 완료되면 `dist/HWP_Batch_Printer.exe` 단일 독립 실행 파일이 생성됩니다.

---

## 4. 버그 및 결함 관리 (Bug Tracker)

### 4-1. 버그 통계
현재 등록된 활성 버그는 없으며, 시스템은 안정화 상태입니다.

| ID | 심각도 | 상태 | 제목 | 발견일 | 해결일 |
|:---|:---:|:---:|:---|:---:|:---:|
| - | - | - | 현재 발견되거나 열려 있는 결함이 없습니다. | - | - |

### 4-2. 심각도 기준 정의
- 🔴 **Critical**: 앱 크래시, 데이터 파손 유발, 백그라운드 한글 COM 프로세스가 해제되지 않고 지속해서 누적되는 현상.
- 🟠 **High**: 인쇄 혹은 PDF 변환 오작동으로 핵심 기능을 정상 수행할 수 없거나, UI 스레드가 멈추어 반응이 없는 현상.
- 🟡 **Medium**: 세부 옵션(양면, 모아찍기 등)이 특정 하드웨어 환경에서 미세하게 누락되거나 예상치 못한 예외가 로그에만 잡히는 현상.
- 🟢 **Low**: 화면 레이아웃의 어긋남, 단순 타이포그래피 오류 및 부적절한 로그 메시지 형식 등 사소한 오류.

### 4-3. 결함 처리 상태 기준
- 🆕 **Open**: 사용자 또는 개발자에 의해 감지되었으나 아직 수정을 시작하지 않은 상태.
- 🔧 **In Progress**: 원인을 파악 중이거나 코드를 수정 중인 상태.
- ✅ **Fixed**: 수정 코드가 반영되었으며 Hell Validation 검증을 마친 상태.
- ❌ **Won't Fix**: 재현이 불가능하거나 타사 프린터 드라이버 자체 오류 등으로 수정에서 제외하기로 결정된 상태.

### 4-4. 버그 상세 기록 (템플릿)
*향후 오류 발견 시 아래 포맷을 복사하여 기록을 추가합니다.*

<!--
#### BUG-001: [결함 제목을 기록합니다]
- **심각도**: 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low
- **상태**: 🆕 Open / 🔧 In Progress / ✅ Fixed
- **발견일**: YYYY-MM-DD
- **영향 파일**: `file:///services/hwp_service.py`
- **재현 방법**:
  1. 프로그램 실행 후 HWPX 형식의 파일 3개 업로드
  2. 일괄 인쇄 도중 취소 버튼 연타
- **예상 동작**: 즉각적인 작업 취소와 함께 백그라운드 HWP COM 프로세스도 함께 클리어 되어야 함.
- **실제 동작**: UI는 취소 처리되나 Hwp.exe 프로세스가 Windows 작업관리자에 여전히 잔류함.
- **원인 분석**: Cancel Signal 수신 시 `Quit()`을 즉시 호출하지 않고 스레드만 루프를 탈출하여 finally 절이 스킵됨.
- **해결 방안**: Worker 스레드 종료 시그널 소멸자에 COM 인스턴스 Quit 로직 강제 연동.
-->

---

## 5. 알려진 제약 사항 (Known Limitations)

- **블로킹 COM API 연동으로 인한 작업 취소 제약**:
  한글 COM의 문서 저장(`SaveAs`) 및 인쇄(`PrintOut`) API 호출은 전적으로 동기식 블로킹(Blocking) 동작입니다. 이로 인해 하나의 파일을 처리(변환/인쇄)하고 있는 중간에는 즉각적인 취소 요청이 적용되지 않습니다. 현재 구현된 취소 기능은 파일 단위 처리 루프 시작 시점에 상태 플래그(`_cancelled`)를 체크하는 협조적 취소(Cooperative Cancel) 방식이므로, 진행 중인 파일 처리가 완전히 완료된 후에 중단 및 취소 처리가 완료됩니다.

