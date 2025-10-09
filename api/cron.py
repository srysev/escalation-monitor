# api/cron.py
from http.server import BaseHTTPRequestHandler
import os
import asyncio
from src.pipeline import run_daily_pipeline

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Sicherheit: Vercel sendet automatisch Authorization: Bearer <CRON_SECRET>
        # (wenn CRON_SECRET als Env gesetzt ist)
        auth = self.headers.get("Authorization", "")
        secret = os.environ.get("CRON_SECRET", "")
        if not secret or auth != f"Bearer {secret}":
            self.send_response(401); self.end_headers()
            self.wfile.write(b"unauthorized"); return

        result = asyncio.run(run_daily_pipeline())  # fetch -> process -> store
        self.send_response(200); self.end_headers()
        self.wfile.write(f"ok: {result}".encode("utf-8"))