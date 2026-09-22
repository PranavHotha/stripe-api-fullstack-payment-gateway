import sys
import subprocess
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(ROOT_DIR, "backend", "venv", "Scripts", "python.exe")
PYTHON_EXE = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

def start_backend():
    print("Starting Backend Server on http://127.0.0.1:8001 ...")
    cmd = [PYTHON_EXE, os.path.join(ROOT_DIR, "stripegateway", "manage.py"), "runserver", "8001"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nBackend server stopped.")

def start_frontend():
    print("Starting Frontend Server on http://127.0.0.1:5500 ...")
    cmd = [PYTHON_EXE, "-m", "http.server", "5500", "--directory", os.path.join(ROOT_DIR, "frontend")]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nFrontend server stopped.")

def start_all():
    print("Starting Backend and Frontend servers concurrently...")
    p1 = subprocess.Popen([PYTHON_EXE, os.path.join(ROOT_DIR, "stripegateway", "manage.py"), "runserver", "8001"])
    p2 = subprocess.Popen([PYTHON_EXE, "-m", "http.server", "5500", "--directory", os.path.join(ROOT_DIR, "frontend")])
    
    print("\n" + "=" * 50)
    print("🚀 Both servers are running!")
    print("🌐 Frontend: http://127.0.0.1:5500")
    print("⚙️  Backend:  http://127.0.0.1:8001")
    print("Press Ctrl+C to stop both servers.")
    print("=" * 50 + "\n")
    
    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        p1.terminate()
        p2.terminate()

if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if mode == "backend":
        start_backend()
    elif mode == "frontend":
        start_frontend()
    elif mode in ("all", "both"):
        start_all()
    else:
        print("Usage: python run.py [backend|frontend|all]")
