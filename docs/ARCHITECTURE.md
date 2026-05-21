# ARCHITECTURE.md — HWP Batch Printer 기술 아키텍처

> 이 문서는 프로젝트의 기술 구조를 정의한다.
> 레이어 구조, 파일별 책임, 상태 흐름, 기술 스택, 금지 사항을 기록한다.

---

## 기술 스택

| 항목 | 기술 | 목적 |
|------|------|------|
| 언어 | Python 3.11+ | 빠른 개발 및 유지보수 |
| GUI | PySide6 (Qt6) | 안정적인 Windows GUI |
| COM | Hancom Office COM (pywin32) | 실제 한글 엔진 활용 |
| 배포 | PyInstaller | exe 단일 파일 배포 |
| 경로 | pathlib | 안전한 경로 처리 |
| 스레드 | QThread | COM 처리 / PDF 변환 / 인쇄 |

---

## 레이어 구조

```text
┌─────────────────────────────────────────┐
│              UI Layer                   │
│  main_window / drop_zone / file_list    │
│  control_panel / progress_panel         │
│  (화면 렌더링만 담당)                     │
├─────────────────────────────────────────┤
│            Service Layer                │
│  file_manager / hwp_service             │
│  pdf_service / print_service            │
│  log_service                            │
│  (비즈니스 로직)                          │
├─────────────────────────────────────────┤
│            Worker Layer                 │
│  pdf_worker / print_worker              │
│  (QThread 백그라운드 처리)                │
├─────────────────────────────────────────┤
│             Core Layer                  │
│  app_state / models / constants         │
│  signals                                │
│  (데이터/상태/설정)                       │
├─────────────────────────────────────────┤
│            Utility Layer                │
│  file_utils / com_utils                 │
│  (공통 헬퍼)                             │
└─────────────────────────────────────────┘
```

---

## 상태 관리

- **AppState** (Singleton) — 모든 공유 상태의 단일 진입점
- 상태 변경 → Qt Signal → UI 자동 갱신
- Frame ↔ Frame 직접 상태 공유 금지
- Worker Thread → Signal/Slot으로만 UI 업데이트

---

## 핵심 원칙

### COM 안정성
- COM 객체는 반드시 생성/해제 명시 (try/finally)
- Quit() 누락 금지
- 병렬 COM 작업 금지 — 큐 기반 순차 처리만 허용
- COM 작업은 Worker Thread 내부에서만 수행

### UI 응답성
- 0.5초 이상 걸리는 작업 → 반드시 QThread 사용
- UI Thread에서 COM 직접 접근 금지
- Worker Thread에서 UI 직접 수정 금지

### 파일 무결성
- 원본 HWP/HWPX 파일 수정 금지 (읽기 전용)
- PDF 생성: temp → 확인 → rename (Safe Save)
- 출력 폴더: 원본폴더/PDF_OUTPUT/

### 로그
- 로그 분리: app.log / convert.log / print.log / error.log
- 필수 기록: 파일명, 작업 시간, 결과, 에러, traceback, 프린터 옵션

---

## 금지 사항

- UI Thread COM 호출
- 병렬 HWP 처리
- 원본 파일 수정
- 하드코딩 경로
- 긴 함수 (200줄 이상)
- God Object 클래스
- try-except 없는 COM 처리
- 로그 없는 예외 처리
