# -*- coding: utf-8 -*-
"""Pluggable order store for the Vital Theory shop.

Backend is chosen from the environment:
  * If SUPABASE_URL and SUPABASE_KEY are set  -> Supabase (Postgres via PostgREST)
  * Otherwise                                 -> local SQLite (store.db)

The rest of the app talks to this module only, so switching backends needs no
route changes. Uses the stdlib (urllib) — no extra dependency.
"""
import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

FIELDS = ["order_no", "name", "email", "country", "product", "amount", "currency",
          "status", "method", "token", "ref", "created_at", "paid_at"]

SUPA_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.environ.get("SUPABASE_KEY", "").strip()
USE_SUPA = bool(SUPA_URL and SUPA_KEY)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store.db")


def backend():
    return "supabase" if USE_SUPA else "sqlite"


# ----------------------------------------------------------------- SQLite
def _sq():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _sqlite_init():
    con = _sq()
    con.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT UNIQUE, name TEXT, email TEXT, country TEXT,
        product TEXT, amount REAL, currency TEXT,
        status TEXT DEFAULT 'pending', method TEXT,
        token TEXT UNIQUE, ref TEXT, created_at TEXT, paid_at TEXT)""")
    con.commit()
    con.close()


# ----------------------------------------------------------------- Supabase
def _supa(method, path, body=None, prefer=None, extra=None):
    url = f"{SUPA_URL}/rest/v1/{path}"
    headers = {"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
               "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    if extra:
        headers.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return r.status, dict(r.headers), (json.loads(raw) if raw else None)


def check_supabase():
    """Return (ok, message) describing whether the Supabase orders table is ready."""
    if not USE_SUPA:
        return False, "Supabase not configured."
    try:
        _supa("GET", "orders?select=order_no&limit=1")
        return True, "Supabase 'orders' table reachable."
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")
        if e.code == 404 or "PGRST205" in detail:
            return False, "Supabase reachable, but the 'orders' table is missing - run supabase_schema.sql."
        if e.code in (401, 403):
            return False, "Supabase rejected the key (check SUPABASE_KEY / RLS policy)."
        return False, f"Supabase error {e.code}: {detail[:120]}"
    except Exception as e:
        return False, f"Could not reach Supabase: {e}"


# ----------------------------------------------------------------- public API
def init():
    if USE_SUPA:
        ok, msg = check_supabase()
        print("  DB backend : Supabase ->", msg)
    else:
        _sqlite_init()
        print("  DB backend : SQLite (store.db)")


def insert_order(o):
    if USE_SUPA:
        _supa("POST", "orders", body={k: o.get(k) for k in FIELDS}, prefer="return=minimal")
    else:
        con = _sq()
        cols = ",".join(FIELDS)
        ph = ",".join(["?"] * len(FIELDS))
        con.execute(f"INSERT INTO orders({cols}) VALUES({ph})", [o.get(f) for f in FIELDS])
        con.commit()
        con.close()


def _get(col, val):
    if USE_SUPA:
        _, _, rows = _supa("GET", f"orders?{col}=eq.{urllib.parse.quote(str(val))}&select=*&limit=1")
        return rows[0] if rows else None
    con = _sq()
    row = con.execute(f"SELECT * FROM orders WHERE {col}=?", (val,)).fetchone()
    con.close()
    return dict(row) if row else None


def by_token(t):
    return _get("token", t)


def by_token_paid(t):
    o = _get("token", t)
    return o if o and o.get("status") == "paid" else None


def by_order_no(n):
    return _get("order_no", n)


def by_ref(r):
    return _get("ref", r)


def update_status(col, val, status, paid_at=None):
    if USE_SUPA:
        body = {"status": status}
        if paid_at:
            body["paid_at"] = paid_at
        _supa("PATCH", f"orders?{col}=eq.{urllib.parse.quote(str(val))}",
              body=body, prefer="return=minimal")
    else:
        con = _sq()
        if paid_at:
            con.execute(f"UPDATE orders SET status=?, paid_at=? WHERE {col}=?", (status, paid_at, val))
        else:
            con.execute(f"UPDATE orders SET status=? WHERE {col}=?", (status, val))
        con.commit()
        con.close()


def count():
    if USE_SUPA:
        try:
            _, hdrs, _ = _supa("GET", "orders?select=id", prefer="count=exact",
                               extra={"Range-Unit": "items", "Range": "0-0"})
            cr = hdrs.get("Content-Range", "0")
            return int(cr.split("/")[-1])
        except Exception:
            return 0
    con = _sq()
    n = con.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    con.close()
    return n


def list_all():
    if USE_SUPA:
        try:
            _, _, rows = _supa("GET", "orders?select=*&order=id.desc")
            return rows or []
        except Exception as e:
            print("  [warn] Supabase list failed:", e)
            return []
    con = _sq()
    rows = [dict(r) for r in con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()]
    con.close()
    return rows
