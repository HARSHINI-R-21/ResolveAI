"""
ResolveAI - Main Application Server

Serves both the single-page web frontend and the REST API backend from http://localhost:8000.
Requires no second terminal or separate frontend build process.
"""

import http.server
import socketserver
import os
import json
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

class ResolveAIHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP Request Handler serving static frontend assets and API endpoints.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        # API Routes
        if self.path.startswith("/api/customers/"):
            customer_id = self.path.split("/")[-1]
            self._handle_get_customer(customer_id)
            return

        # Default static file serving (index.html, style.css, script.js)
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/resolve":
            self._handle_resolve_request()
            return
        
        self.send_error(404, "API endpoint not found")

    def _handle_get_customer(self, customer_id: str):
        """
        Placeholder API handler for customer retrieval.
        """
        customers_file = BASE_DIR / "data" / "customers.json"
        if customers_file.exists():
            try:
                with open(customers_file, "r", encoding="utf-8") as f:
                    customers = json.load(f)
                for cust in customers:
                    if cust.get("customer_id") == customer_id:
                        self._send_json_response(200, cust)
                        return
            except Exception as e:
                self._send_json_response(500, {"error": f"Failed to load customers data: {str(e)}"})
                return

        self._send_json_response(404, {"error": f"Customer '{customer_id}' not found."})

    def _handle_resolve_request(self):
        """
        Placeholder API handler for processing support query resolution.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON body"})
            return

        # Placeholder resolution response structure
        response_payload = {
            "status": "success",
            "decision": "ASK",
            "reasoning": "Placeholder decision engine: Additional customer information required.",
            "response_text": f"Placeholder: Received query '{payload.get('query')}' for category '{payload.get('category')}'. Resolution logic is being implemented.",
            "evidence": [
                {"type": "account_check", "detail": f"Customer ID: {payload.get('customer_id', 'Unknown')}"}
            ],
            "cited_articles": [
                {"title": "Broadband & Mobile Billing Guide", "file": "data/articles/billing.md"}
            ]
        }
        self._send_json_response(200, response_payload)

    def _send_json_response(self, statusCode: int, data: dict):
        self.send_response(statusCode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def run_server():
    print(f"==================================================")
    print(f"  Starting ResolveAI Assistant Server             ")
    print(f"  Serving UI & API at: http://localhost:{PORT}   ")
    print(f"==================================================")
    
    with socketserver.TCPServer(("", PORT), ResolveAIHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run_server()
