#!/usr/bin/env python3
"""
Bootstrap script for wiki-trends environment.
Creates virtual environment and installs required dependencies.
Usage: python setup.py
"""
import os
import subprocess
import sys

def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, ".venv")
    req_file = os.path.join(script_dir, "requirements.txt")
    
    print(f"[SETUP] Python executable: {sys.executable}")
    print(f"[SETUP] Python version: {sys.version.split()[0]}")
    
    # 1. Create venv if not present
    if not os.path.exists(venv_dir):
        print(f"[SETUP] Creating virtual environment at {venv_dir}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
    else:
        print(f"[SETUP] Virtual environment already exists at {venv_dir}")
        
    # 2. Determine venv binaries
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")
        
    # 3. Upgrade pip and install requirements
    print(f"[SETUP] Installing dependencies from {req_file}...")
    subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    subprocess.check_call([pip_path, "install", "-r", req_file, "-q"])
    
    # 4. Verify imports
    print("[SETUP] Verifying installed packages...")
    verify_cmd = [
        python_path,
        "-c",
        "import requests, matplotlib, numpy, scipy, reportlab; print('All dependencies imported successfully!')"
    ]
    subprocess.check_call(verify_cmd)
    
    print("\n[SETUP] Environment ready!")
    print(f"[SETUP] You can now run:\n  {python_path} {os.path.join(script_dir, 'wiki_trends.py')} --help\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
