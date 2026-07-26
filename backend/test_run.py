import os
import uvicorn
from app.main import app
from app.core.config import settings

def update_env_local(port: int):
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    
    
    env_local_path = os.path.join(project_root, ".env.local")
    env_content = ""
    if os.path.exists(env_local_path):
        with open(env_local_path, "r") as f:
            lines = f.readlines()
        env_content = "".join([line for line in lines if not line.startswith("NEXT_PUBLIC_API_URL=")])
    
    with open(env_local_path, "w") as f:
        f.write(env_content.strip() + f"\nNEXT_PUBLIC_API_URL=http://localhost:{port}\n")
        
    
    frontend_env_local = os.path.join(project_root, "frontend", ".env.local")
    env_content = ""
    if os.path.exists(frontend_env_local):
        with open(frontend_env_local, "r") as f:
            lines = f.readlines()
        env_content = "".join([line for line in lines if not line.startswith("NEXT_PUBLIC_API_URL=")])
    
    with open(frontend_env_local, "w") as f:
        f.write(env_content.strip() + f"\nNEXT_PUBLIC_API_URL=http://localhost:{port}\n")
    
    print(f"[INFO] Updated NEXT_PUBLIC_API_URL to http://localhost:{port} in .env.local")

if __name__ == "__main__":
    import time
    import subprocess
    import sys
    import os
    port = settings.PORT
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    while True:
        print(f"[INFO] Attempting to start backend server on port {port} (IPv6)...")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = backend_dir + os.pathsep + env.get("PYTHONPATH", "")
        env["ANONYMIZED_TELEMETRY"] = "False"
        
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            env=env,
            cwd=backend_dir
        )
        
        
        time.sleep(10)
        
        if process.poll() is not None:
            print(f"[WARN] Uvicorn failed to start on port {port}, trying port {port + 1}...")
            port += 1
        else:
            
            print(f"[INFO] Backend successfully bound to port {port}.")
            update_env_local(port)
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
            break
