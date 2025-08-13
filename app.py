"""
Railway entry point - imports the FastAPI app from apps/api
"""
import sys
import os
from pathlib import Path

# Add apps/api to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)