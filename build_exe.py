# file: build_exe.py
"""
HWP Batch Printer — PyInstaller 패키징 빌드 스크립트.
assets 디렉토리를 포함하여 단일 실행 파일(.exe)로 빌드합니다.
"""

import os
import sys
import subprocess
import shutil


def check_and_install_pyinstaller():
    """PyInstaller 설치 여부 확인 및 설치"""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller is already installed. (Version: {PyInstaller.__version__})")
    except ImportError:
        print("[INFO] PyInstaller is not installed. Installing...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                check=True
            )
            print("[OK] PyInstaller installation completed.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install PyInstaller: {e}")
            sys.exit(1)


def build():
    """패키징 작업 실행"""
    check_and_install_pyinstaller()

    # 이전 빌드 아티팩트 정리
    print("[INFO] Cleaning up previous build folders (build, dist)...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  - {folder} folder deleted.")
            except Exception as e:
                print(f"  - Failed to clean {folder} folder: {e}")

    # 빌드 옵션 구성
    # Windows 환경이므로 세미콜론(;)을 구분자로 사용합니다.
    add_data_param = "assets;assets"

    args = [
        "main.py",
        "--name=HWP_Batch_Printer",
        "--onefile",
        "--noconsole",
        f"--add-data={add_data_param}",
        "--clean",
    ]

    print(f"[INFO] Starting PyInstaller build...")
    print(f"Command: pyinstaller {' '.join(args)}")

    try:
        import PyInstaller.__main__
        PyInstaller.__main__.run(args)
        print("\n[OK] Build completed successfully!")
        print(f"Generated file: {os.path.abspath('dist/HWP_Batch_Printer.exe')}")
    except Exception as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Windows 콘솔에서 인코딩 문제 방지를 위해 sys.stdout의 인코딩을 UTF-8 또는 적절하게 설정 시도
    try:
        if sys.platform.startswith('win'):
            import io
            # stdout/stderr를 utf-8로 강제설정하지는 않되, print 시 예외 방지를 위해 emoji 제거
            pass
    except Exception:
        pass

    build()
