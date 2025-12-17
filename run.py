import subprocess
import time
import os
import sys

def main():
    print("💎 Gemscap Quant Analytics Launcher")
    print("-----------------------------------")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ingestion_script = os.path.join(base_dir, "backend", "ingestion.py")
    frontend_script = os.path.join(base_dir, "frontend", "app.py")
    
    # Start Ingestion (Background)
    print("🚀 Starting Data Ingestion Service...")
    ingestion_process = subprocess.Popen([sys.executable, ingestion_script])
    
    # Wait a moment for DB to initialize
    time.sleep(2)
    
    # Start Frontend
    print("📊 Starting Streamlit Dashboard...")
    try:
        # We run Streamlit using the 'streamlit run' command module
        subprocess.run([sys.executable, "-m", "streamlit", "run", frontend_script], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        ingestion_process.terminate()
        ingestion_process.wait()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
