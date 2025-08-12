import os
import json
import sys
from http.server import BaseHTTPRequestHandler

# Add the source directory to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from src.data.glide_path_allocations import GLIDE_PATH_ALLOCATIONS
except ImportError:
    GLIDE_PATH_ALLOCATIONS = {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            user_id = data.get('user_id')
            age = data.get('age', 35)
            risk_bucket = data.get('risk_bucket', 'Moderate')
            
            # Get allocation from existing glide path data
            bucket_data = GLIDE_PATH_ALLOCATIONS.get(risk_bucket, {})
            allocation = {}
            
            # Find appropriate age range
            for (age_from, age_to), alloc in bucket_data.items():
                if age_from <= age <= age_to:
                    allocation = alloc
                    break
            
            # Build targets
            targets = {}
            for symbol, weight in allocation.items():
                if symbol.upper() in ["VTI", "VEA", "VWO", "BND", "BNDX", "VNQ", "VNQI", "VTIP", "VBR", "VUG", "VSS"]:
                    targets[symbol] = weight * 100
            
            # Simple rationale
            rationale = f"Based on your {risk_bucket} risk profile and age {age}, this allocation balances growth potential with appropriate diversification."
            
            response = {
                "id": f"proposal_{user_id}",
                "targets": targets,
                "rationale": rationale,
                "risk_bucket": risk_bucket,
                "status": "awaiting_user"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')
        self.end_headers()