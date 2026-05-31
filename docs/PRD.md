# PRD (Product Requirements Document) — HWP Batch Printer

## 프로젝트 개요

- **프로젝트명**: HWP Batch Printer
- **프로젝트 목적**: 여러 개의 한글(HWP/HWPX) 파일을 한 번에 인쇄하거나 PDF로 변환할 수 있는 Windows 데스크톱 업무 자동화 프로그램 개발
- **핵심 문제**:
  - 반복적인 수동 인쇄/PDF 변환 작업
  - 대량 문서 처리 비효율
  - PDF 저장 위치 관리 문제
  - 인쇄 옵션 반복 설정
- **타겟 사용자**:
  - 개인 사무 사용자
  - 학교 교사
  - 행정 업무 담당자
- **핵심 가치 제안**:
  - 드래그앤드롭 기반 빠른 작업
  - 여러 파일 동시 처리
  - 반복 업무 시간 절약
  - 최소 클릭 기반 UX

---

## MVP 범위

### 핵심 기능
- HWP/HWPX 드래그앤드롭
- 다중 파일 등록
- 일괄 인쇄
- 일괄 PDF 변환
- PDF_OUTPUT 자동 생성
- 진행률 표시
- 파일별 상태 표시
- 성공/실패 로그
- 인쇄 매수 설정
- 단면/양면 선택
- 모아찍기 설정

### 제외 기능
- 로그인 기능
- 클라우드 저장
- 웹 버전
- 사용자 계정 관리
- Mac/Linux 지원

### 향후 기능 (Backlog)
- 최근 작업 기록
- 작업 프리셋 저장
- 다크모드
- 워드(docx) 지원
- OCR/PDF 병합

---

## 사용자 흐름 (User Flow)

### PDF 변환 흐름
1. 프로그램 실행
2. 파일 드래그앤드롭
3. PDF 변환 버튼 클릭
4. 진행 상태 확인
5. 완료 후 폴더 자동 열기

### 일괄 인쇄 흐름
1. 프로그램 실행
2. 파일 드래그앤드롭
3. 인쇄 옵션 설정 (매수, 단면/양면, 모아찍기 등)
4. 인쇄 버튼 클릭
5. 진행 상태 확인

---

## 기술 설계 (Technical Specifications)

### 기술 스택
- **언어**: Python 3.11+
- **GUI**: PySide6 (Qt6)
- **COM**: Hancom Office COM (pywin32)
- **배포**: PyInstaller
- **경로**: pathlib
- **스레드**: QThread

### 기술 스택 선택 이유
- **Python**: 빠른 개발 및 유지보수
- **PySide6**: 안정적인 Windows GUI
- **Hancom COM**: 실제 설치된 한글 엔진 활용
- **PyInstaller**: exe 단일 파일 배포

### 시스템 구조
- **GUI Layer**
  - Drag & Drop UI
  - File List UI
  - Progress UI
  - Print/PDF Controls
- **Service Layer**
  - File Manager
  - HWP Automation Service
  - PDF Converter
  - Print Service
  - Logger
- **System Layer**
  - Hancom Office COM
  - Windows Printer API
  - File System

---

## 개발 로드맵

### 1단계 [뼈대 세우기]
- 프로젝트 구조 생성
- GUI 구성
- 드래그앤드롭 구현
- 파일 목록 테이블 구현

### 2단계 [내용 채우기]
- COM 연결
- PDF 변환 구현
- 일괄 인쇄 구현
- 진행 상태 처리

### 3단계 [디자인 입히기]
- UI 스타일링
- UX 개선
- 상태 표시 개선

### 4단계 [마무리 점검]
- 예외 처리
- 메모리 점검
- exe 패키징
- 실제 프린터 테스트

---

## 개발 리스크 (Risks)

- **COM 자동화 불안정성**: 한글 COM 객체 누수 및 예외 대처 필요
- **프린터 드라이버 의존성**: 시스템에 설치된 특정 프린터 드라이버와의 호환성 문제
- **대량 파일 처리 속도 문제**: 파일 개수가 많아질 때의 성능 지연 및 메모리 누적 현상
- **PyInstaller 백신 오탐 가능성**: 단일 파일 패키징 시 Windows Defender 등에서의 백신 오탐 이슈

---

## 추천 개발 순서

1. GUI 구조 설계 및 구현
2. 드래그앤드롭 수신 처리
3. 단일 PDF 변환 연동
4. 다중 PDF 변환 처리 루프 구현
5. 기본 인쇄 기능 연동
6. 상세 인쇄 옵션 (양면, 모아찍기) 처리
7. 진행률 및 개별 파일 상태 표시 UI 연동
8. PyInstaller 기반 exe 패키징 환경 구성

---

## 추천 프로젝트 구조

```text
project/
  ├── main.py
  ├── ui/
  ├── services/
  ├── workers/
  ├── utils/
  ├── assets/
  └── dist/
```
