"""
Railway entry point - imports the FastAPI app from apps/api
"""
import sys
import os
from pathlib import Path

# Add apps/api to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

try:
    from main import app
    print("✅ FastAPI app imported successfully")
except Exception as e:
    print(f"❌ Error importing FastAPI app: {e}")
    # Create a minimal backup app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"error": "Main app failed to import", "details": str(e)}
    
    @app.get("/health")
    def health():
        return {"status": "error", "message": "Main app import failed"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)