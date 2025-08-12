import os
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "provider": os.getenv("PROVIDER", "alpaca_paper"),
            "orders_enabled": os.getenv("ORDERS_ENABLED", "true").lower() == "true",
            "database": "connected" if os.getenv("SUPABASE_URL") else "disconnected"
        }
        
        self.wfile.write(json.dumps(response).encode())