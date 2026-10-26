"""
Unified launcher for Render deployment.
Starts FastAPI in the background and Streamlit in the foreground.
"""
import os
import subprocess
import sys
import time
import urllib.request

def main():
    port = os.environ.get("PORT", "8501")
    
    print("[1/2] Starting FastAPI backend on port 8000...")
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    # Wait for backend to be ready (up to 8 seconds)
    print("Waiting for FastAPI backend to bind port 8000...")
    backend_ready = False
    for i in range(8):
        if backend.poll() is not None:
            print(f"FastAPI backend exited with code {backend.returncode}")
            break
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as resp:
                if resp.status == 200:
                    print(f"FastAPI backend is ready on port 8000! (Took {i+1}s)")
                    backend_ready = True
                    break
        except Exception:
            time.sleep(1)
            
    if not backend_ready and backend.poll() is None:
        print("FastAPI startup pending; frontend will use resilient direct inference.")
    
    print(f"[2/2] Starting Streamlit frontend on port {port}...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    try:
        subprocess.run(frontend_cmd)
    finally:
        if backend.poll() is None:
            backend.terminate()

if __name__ == "__main__":
    main()
