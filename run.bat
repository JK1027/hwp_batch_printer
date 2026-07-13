@echo off
chcp 65001 > nul
echo [INFO] HWP Batch Printer 실행 환경을 검증하는 중입니다...

:: 가상환경 활성화 시도 (.venv 또는 venv가 있는 경우)
if exist .venv\Scripts\activate.bat (
    echo [INFO] 가상환경(.venv)을 활성화합니다.
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo [INFO] 가상환경(venv)을 활성화합니다.
    call venv\Scripts\activate.bat
)

:: 의존성 라이브러리 검증 및 자동 설치
python -c "import PySide6, win32com" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] 필요한 라이브러리(PySide6, pywin32)가 누락되었습니다.
    echo [INFO] requirements.txt를 기반으로 패키지 설치를 시작합니다...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

echo [OK] 애플리케이션을 구동합니다.
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 프로그램이 비정상 종료되었습니다. 위 오류 메시지를 확인하세요.
    pause
)
