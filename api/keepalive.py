# -*- coding: utf-8 -*-
"""Vercel serverless function — keeps the Supabase project from auto-pausing.

Supabase free-tier projects pause after ~7 days of inactivity. A Vercel Cron Job
(see vercel.json) calls this endpoint a couple of times a week; it writes a
timestamp to a tiny `keepalive` table, which counts as database activity and
resets the inactivity timer.

Uses only the Python standard library (no dependencies). Reads SUPABASE_URL and
SUPABASE_KEY from the Vercel environment variables.

NOTE: this PREVENTS pausing — it cannot restore a project that is already paused
(that requires a manual "Restore" in the Supabase dashboard). Keep the schedule
comfortably under 7 days.
"""
import datetime
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
CRON_SECRET = os.environ.get("CRON_SECRET", "").strip()


def ping():
    if not (SUPABASE_URL and SUPABASE_KEY):
        return False, "SUPABASE_URL / SUPABASE_KEY are not set"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/keepalive?id=eq.1"
    body = json.dumps({"last_ping": now}).encode()
    req = urllib.request.Request(url, data=body, method="PATCH", headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return True, f"Supabase pinged at {now} (HTTP {r.status})"
    except Exception as e:
        return False, f"ping failed: {e}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # If CRON_SECRET is set, Vercel Cron sends it as a Bearer token; verify it.
        if CRON_SECRET:
            if self.headers.get("Authorization", "") != f"Bearer {CRON_SECRET}":
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
        ok, msg = ping()
        self._json(200 if ok else 500, {"ok": ok, "message": msg})

    def _json(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
