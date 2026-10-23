"""
Unified launcher for Render deployment.
Starts FastAPI in the background and Streamlit in the foreground.
"""
import os
import subprocess
import sys
import time

def main():
    port = os.environ.get("PORT", "8501")
    
    print("[1/2] Starting FastAPI backend on port 8000...")
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    # Give backend a moment to bind port 8000
    time.sleep(3)
    
    print(f"[2/2] Starting Streamlit frontend on port {port}...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    
    try:
        subprocess.run(frontend_cmd)
    finally:
        backend.terminate()

if __name__ == "__main__":
    main()
