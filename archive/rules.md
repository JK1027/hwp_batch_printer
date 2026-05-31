# 🚀 HWP Batch Printer 전용 AI 협업 바이브 코딩 지침 v1.0

> 대상 프로젝트:
> Windows 기반 HWP/HWPX 일괄 인쇄 및 PDF 변환 업무 자동화 프로그램

---

# 0. 프로젝트 운영 철학 (Operating Philosophy)

본 프로젝트는:

- 빠른 MVP 개발
- 실사용 가능한 업무 자동화
- 안정적인 HWP COM 제어
- GUI 응답성 유지
- 파일 무결성 보장

을 핵심 목표로 한다.

특히 다음을 최우선으로 한다:

1. COM 안정성
2. UI 멈춤 방지
3. 파일 손상 방지
4. 로그 기반 복구 가능성
5. 유지보수 가능한 구조

---

# 1. 핵심 아키텍처 원칙

## 1-1. 관심사 분리 (Separation of Concerns)

반드시 아래 구조를 유지한다.

```text
UI Layer
 └─ 화면 렌더링만 담당

Service Layer
 └─ HWP/PDF/Print 처리

Worker Layer
 └─ 백그라운드 작업 처리

System Layer
 └─ COM / Printer / FileSystem 접근
```

금지:

- UI에서 COM 직접 호출
- UI에서 파일 저장 직접 처리
- UI에서 긴 작업 수행

---

## 1-2. 단일 책임 원칙 (SRP)

하나의 클래스는 하나의 역할만 가진다.

예시:

```text
HwpService
 └─ HWP 열기/닫기

PdfService
 └─ PDF 변환

PrintService
 └─ 인쇄 처리

LogService
 └─ 로그 처리
```

---

# 2. Hancom COM 안정성 원칙

## 2-1. COM 객체 생명주기 강제

모든 COM 객체는 반드시 생성/해제를 명시한다.

```python
hwp = None

try:
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
finally:
    if hwp:
        hwp.Quit()
```

절대 금지:

- Quit() 누락
- 예외 시 COM 객체 방치
- 백그라운드 HWP 프로세스 잔류

---

## 2-2. 병렬 COM 작업 금지

HWP COM은 병렬 안정성이 낮다.

따라서:

```text
파일 큐 기반 순차 처리 ONLY
```

원칙을 강제한다.

금지:

- 멀티 HWP 동시 실행
- 병렬 PDF 변환
- 병렬 인쇄 작업

---

## 2-3. COM 작업 위치 제한

COM 작업은 반드시 Worker Thread 내부에서만 수행한다.

금지:

```text
UI Thread → COM 직접 접근
```

---

# 3. GUI 및 스레드 원칙

## 3-1. UI Freezing 금지

0.5초 이상 걸리는 작업은 반드시 Worker Thread 사용.

대상:

- PDF 변환
- HWP 열기
- 인쇄
- 대량 파일 처리

---

## 3-2. PySide6 스레드 구조 강제

```text
Main Thread
 └─ UI 렌더링

QThread
 └─ COM 처리
 └─ PDF 변환
 └─ 인쇄 처리
```

---

## 3-3. UI 업데이트 규칙

UI 갱신은 Signal/Slot만 사용한다.

예시:

```python
worker.progress_changed.connect(self.update_progress)
```

금지:

- Worker Thread에서 UI 직접 수정
- time.sleep()으로 UI 대기

---

# 4. 파일 무결성 원칙

## 4-1. 원본 파일 수정 금지

원본 HWP/HWPX는 절대 수정하지 않는다.

허용:

```text
읽기 전용 접근
```

---

## 4-2. 안전 저장 (Safe Save)

PDF 생성 시 temp 파일 기반 저장 사용.

```text
temp.pdf 생성
→ 생성 성공 확인
→ 최종 rename
```

---

## 4-3. 출력 폴더 정책

PDF는 반드시:

```text
원본 폴더/PDF_OUTPUT/
```

에 저장한다.

자동 생성 규칙:

```python
output_dir.mkdir(exist_ok=True)
```

---

# 5. 작업 큐 및 대량 처리 원칙

## 5-1. Queue 기반 처리

반드시 Queue 기반 순차 처리 사용.

```text
File Queue
 → 하나씩 처리
 → 상태 업데이트
 → 다음 파일 진행
```

---

## 5-2. 진행 상태 표시 의무화

대량 작업은 반드시:

- 진행률 바
- 현재 파일명
- 성공/실패 상태
- 로그 출력

을 제공한다.

---

## 5-3. 실패 파일 처리

하나의 파일 실패가 전체 작업 중단으로 이어지면 안 된다.

원칙:

```text
실패 기록
→ 다음 파일 계속 진행
```

---

# 6. 로그 및 Recovery 원칙

## 6-1. 로그 분리

```text
logs/
 ├─ app.log
 ├─ convert.log
 ├─ print.log
 └─ error.log
```

---

## 6-2. 로그 기록 항목

반드시 기록:

- 파일명
- 작업 시간
- 작업 결과
- 에러 메시지
- traceback
- 프린터 옵션

---

## 6-3. Recovery 원칙

예외 발생 시:

1. 로그 기록
2. COM 종료 시도
3. Worker 종료
4. UI 정상 유지
5. 다음 작업 가능 상태 복구

---

# 7. 데이터 구조 원칙

## 7-1. dataclass 우선 사용

Pydantic 사용 금지.

권장:

```python
from dataclasses import dataclass

@dataclass
class FileTask:
    path: str
    status: str
```

---

## 7-2. 상태 중앙 관리

공유 상태는 Controller 또는 StateManager에서만 관리.

금지:

```text
Frame ↔ Frame 직접 상태 공유
```

---

# 8. AI 코드 출력 규칙

## 8-1. 함수 단위 전체 출력

AI는 수정 함수 전체를 출력한다.

금지:

```python
# 기존 코드 동일
```

---

## 8-2. Diff 우선 원칙

작은 수정은 Diff 방식 우선.

```diff
- old
+ new
```

---

## 8-3. 파일명 및 위치 명시

반드시 포함:

```python
# file: services/pdf_service.py
# function: convert_to_pdf()
```

---

# 9. 검증 시스템

## Level 1 — Fast Patch

대상:

- UI 문구
- 색상
- 스타일 수정

검증:

- 코드 리뷰 1회

---

## Level 2 — Standard

대상:

- 상태 변경
- 파일 처리
- 이벤트 로직

검증:

- 실행 테스트
- 빈 데이터 테스트
- 실패 케이스 테스트

---

## Level 3 — Hell Validation

대상:

- COM 로직
- 멀티스레드
- 인쇄 처리
- PDF 저장 구조

검증:

- 실제 파일 테스트
- 대량 파일 테스트
- 예외 테스트
- 최대 3회 검증

---

# 10. 배포 원칙

## 10-1. exe 배포 기준

PyInstaller 사용.

예시:

```bash
pyinstaller --noconsole --onefile main.py
```

---

## 10-2. 배포 전 필수 점검

체크리스트:

- 한글 설치 여부
- PDF 변환 테스트
- 인쇄 테스트
- 로그 생성 확인
- COM 종료 확인

---

## 10-3. 백신 오탐 대응

권장:

- 버전 정보 명시
- 디지털 서명 고려
- dist 초기화 후 재빌드

---

# 11. 금지 사항

절대 금지:

- UI Thread COM 호출
- 병렬 HWP 처리
- 원본 파일 수정
- 하드코딩 경로
- 긴 함수
- God Object 클래스
- try-except 없는 COM 처리
- 로그 없는 예외 처리

---

# 12. 최종 원칙

1. 빠른 구현보다 안정성을 우선한다.
2. COM 객체는 반드시 정리한다.
3. UI는 절대 멈추지 않아야 한다.
4. 파일 무결성을 항상 보호한다.
5. 실패해도 다음 작업은 계속 가능해야 한다.
6. AI는 기존 구조를 존중하며 최소 수정 원칙을 따른다.
7. 업무 자동화 도구는 "신뢰성"이 핵심이다.
