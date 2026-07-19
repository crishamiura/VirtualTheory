# -*- coding: utf-8 -*-
"""Vital Theory — store backend.

A small Flask storefront on top of the static landing page:
  * dynamic checkout (demo payment by default; Stripe Checkout when keys set)
  * order database — Supabase (Postgres) if configured, else local SQLite
  * invoice / receipt (HTML + PDF)
  * secure ebook download links
  * a Gumroad webhook that records real sales
  * a password-protected admin dashboard: revenue, orders, who bought

Run:  python app.py
"""
import csv
import io
import os
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, send_file, send_from_directory, session, url_for)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

import store_db as store   # noqa: E402  (after dotenv so env is loaded)

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
COOKBOOK = os.path.join(SITE, "cookbook")

PRODUCT = {
    "name": "Vital Theory's Secret Recipes",
    "desc": "200 chef-inspired recipes - PDF, ePub & Kindle",
    "price": float(os.environ.get("PRICE", "9.99")),
    "list_price": float(os.environ.get("LIST_PRICE", "29.99")),
    "currency": os.environ.get("CURRENCY", "USD"),
}
SELLER = {
    "name": os.environ.get("SELLER_NAME", "Vital Theory"),
    "email": os.environ.get("SELLER_EMAIL", "hello@vitaltheory.shop"),
    "site": os.environ.get("SELLER_SITE", "vitaltheory.shop"),
}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

app = Flask(__name__, static_folder=os.path.join(HERE, "static"),
            static_url_path="/store-static")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def next_order_no():
    year = datetime.now(timezone.utc).strftime("%Y")
    return f"VT-{year}-{store.count() + 1:05d}"


def money(v):
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return v


app.jinja_env.filters["money"] = money


def _fmt(iso):
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %Y  %H:%M UTC")
    except Exception:
        return iso


# ---------------- static site passthrough ----------------
@app.route("/")
def home():
    return send_from_directory(SITE, "index.html")


@app.route("/<path:fname>")
def site_assets(fname):
    full = os.path.realpath(os.path.join(SITE, fname))
    if os.path.isfile(full) and os.path.commonpath([SITE, full]) == SITE:
        return send_from_directory(SITE, fname)
    abort(404)


# ---------------- checkout ----------------
@app.route("/checkout")
def checkout():
    return render_template("checkout.html", p=PRODUCT, seller=SELLER, stripe=bool(STRIPE_KEY))


@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    country = (request.form.get("country") or "").strip()
    if not name or "@" not in email:
        flash("Please enter your name and a valid email.", "err")
        return redirect(url_for("checkout"))

    token = secrets.token_urlsafe(24)
    order = {
        "order_no": next_order_no(), "name": name, "email": email, "country": country,
        "product": PRODUCT["name"], "amount": PRODUCT["price"], "currency": PRODUCT["currency"],
        "status": "pending", "method": None, "token": token, "ref": None,
        "created_at": now_iso(), "paid_at": None,
    }

    if STRIPE_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_KEY
            sess = stripe.checkout.Session.create(
                mode="payment", customer_email=email,
                line_items=[{"price_data": {
                    "currency": PRODUCT["currency"].lower(),
                    "product_data": {"name": PRODUCT["name"], "description": PRODUCT["desc"]},
                    "unit_amount": int(round(PRODUCT["price"] * 100))}, "quantity": 1}],
                success_url=f"{BASE_URL}/success?token={token}",
                cancel_url=f"{BASE_URL}/checkout",
                metadata={"order_no": order["order_no"]})
            order["ref"] = sess.id
            order["method"] = "stripe"
            store.insert_order(order)
            return redirect(sess.url, code=303)
        except Exception as e:
            flash(f"Payment setup failed: {e}", "err")
            return redirect(url_for("checkout"))

    # Demo mode: simulate a successful payment
    order["status"] = "paid"
    order["method"] = "demo"
    order["paid_at"] = now_iso()
    store.insert_order(order)
    return redirect(url_for("success", token=token))


@app.route("/success")
def success():
    token = request.args.get("token", "")
    o = store.by_token(token)
    if not o:
        abort(404)
    if o.get("status") != "paid":
        store.update_status("token", token, "paid", paid_at=now_iso())
        o = store.by_token(token)
    return render_template("success.html", o=o, p=PRODUCT, seller=SELLER)


# ---------------- Gumroad webhook (real sales -> your dashboard) ----------------
@app.route("/webhook/gumroad", methods=["POST"])
def gumroad_webhook():
    """Records real Gumroad sales. Configure in Gumroad: Settings > Advanced > Ping
    (or the product Webhook) pointing to  https://YOUR-DOMAIN/webhook/gumroad"""
    f = request.form if request.form else (request.get_json(silent=True) or {})
    sale_id = f.get("sale_id") or f.get("order_number")
    if not sale_id:
        return ("ignored", 200)

    email = (f.get("email") or "").strip()
    name = (f.get("full_name") or f.get("purchaser")
            or (email.split("@")[0] if email else "Gumroad customer"))
    cents = str(f.get("price") or "")
    amount = int(cents) / 100 if cents.isdigit() else PRODUCT["price"]
    currency = (f.get("currency") or PRODUCT["currency"]).upper()
    country = f.get("country") or f.get("ip_country") or ""
    product = f.get("product_name") or PRODUCT["name"]
    refunded = str(f.get("refunded", "false")).lower() == "true"
    disputed = str(f.get("disputed", "false")).lower() == "true"
    status = "refunded" if (refunded or disputed) else "paid"

    if store.by_ref(sale_id):
        store.update_status("ref", sale_id, status)
        return ("ok", 200)

    store.insert_order({
        "order_no": next_order_no(), "name": name, "email": email, "country": country,
        "product": product, "amount": amount, "currency": currency, "status": status,
        "method": "gumroad", "token": secrets.token_urlsafe(24), "ref": sale_id,
        "created_at": now_iso(), "paid_at": now_iso()})
    return ("ok", 200)


# ---------------- receipt / invoice ----------------
def _order_or_404(order_no):
    o = store.by_order_no(order_no)
    if not o:
        abort(404)
    return o


@app.route("/receipt/<order_no>")
def receipt(order_no):
    o = _order_or_404(order_no)
    return render_template("receipt.html", o=o, p=PRODUCT, seller=SELLER,
                           dt=_fmt(o.get("paid_at") or o.get("created_at")))


@app.route("/receipt/<order_no>.pdf")
def receipt_pdf(order_no):
    o = _order_or_404(order_no)
    return send_file(io.BytesIO(build_receipt_pdf(o)), mimetype="application/pdf",
                     as_attachment=True, download_name=f"receipt-{order_no}.pdf")


# ---------------- secure downloads ----------------
@app.route("/download/<token>/<kind>")
def download(token, kind):
    if not store.by_token_paid(token):
        abort(403)
    files = {"pdf": "Vital_Theory_Secret_Recipes.pdf",
             "epub": "Vital_Theory_Secret_Recipes.epub"}
    if kind not in files:
        abort(404)
    path = os.path.join(COOKBOOK, files[kind])
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=files[kind])


# ---------------- admin ----------------
def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*a, **k)
    return w


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong password.", "err")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin():
    rows = store.list_all()
    paid = [r for r in rows if r.get("status") == "paid"]
    revenue = sum(float(r.get("amount") or 0) for r in paid)
    stats = {
        "revenue": revenue,
        "orders": len(paid),
        "customers": len(set(r.get("email") for r in paid)),
        "aov": (revenue / len(paid)) if paid else 0,
        "currency": PRODUCT["currency"],
    }
    orders = [dict(r, created=_fmt(r.get("created_at"))) for r in rows]
    return render_template("admin.html", stats=stats, orders=orders, seller=SELLER,
                           backend=store.backend())


@app.route("/admin/refund/<order_no>", methods=["POST"])
@login_required
def admin_refund(order_no):
    store.update_status("order_no", order_no, "refunded")
    flash(f"Order {order_no} marked refunded.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/orders.csv")
@login_required
def admin_csv():
    rows = store.list_all()
    cols = ["order_no", "name", "email", "country", "amount", "currency",
            "status", "method", "created_at", "paid_at"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c) for c in cols])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=vital-theory-orders.csv"})


# ---------------- receipt PDF ----------------
def build_receipt_pdf(o):
    from fpdf import FPDF
    fonts = r"C:\Windows\Fonts"
    pdf = FPDF(format="A4", unit="mm")
    pdf.add_page()
    pdf.add_font("S", "", os.path.join(fonts, "arial.ttf"))
    pdf.add_font("S", "B", os.path.join(fonts, "arialbd.ttf"))
    BLUE, CYAN, INK, SLATE = (37, 99, 235), (6, 182, 212), (15, 23, 42), (100, 116, 139)

    pdf.set_fill_color(*BLUE); pdf.rect(0, 0, 210, 42, "F")
    pdf.set_fill_color(*CYAN); pdf.rect(0, 42, 210, 2.5, "F")
    pdf.set_xy(16, 13); pdf.set_font("S", "B", 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "Vital Theory")
    pdf.set_xy(16, 25); pdf.set_font("S", "", 12); pdf.cell(0, 7, "Payment receipt / invoice")
    pdf.set_xy(120, 15); pdf.set_font("S", "B", 13); pdf.cell(74, 7, o["order_no"], align="R")
    pdf.set_xy(120, 24); pdf.set_font("S", "", 10)
    pdf.cell(74, 6, _fmt(o.get("paid_at") or o.get("created_at")), align="R")

    pdf.set_text_color(*SLATE); pdf.set_xy(16, 56); pdf.set_font("S", "B", 9)
    pdf.cell(0, 6, "BILLED TO", ln=1)
    pdf.set_x(16); pdf.set_font("S", "", 11); pdf.set_text_color(*INK)
    pdf.multi_cell(90, 6, f"{o['name']}\n{o['email']}\n{o.get('country') or ''}")

    pdf.set_xy(120, 56); pdf.set_font("S", "B", 9); pdf.set_text_color(*SLATE)
    pdf.cell(74, 6, "FROM", ln=1)
    pdf.set_xy(120, 62); pdf.set_font("S", "", 11); pdf.set_text_color(*INK)
    pdf.multi_cell(74, 6, f"{SELLER['name']}\n{SELLER['email']}\n{SELLER['site']}")

    y = 95
    pdf.set_fill_color(240, 247, 255); pdf.rect(16, y, 178, 10, "F")
    pdf.set_xy(20, y + 2.5); pdf.set_font("S", "B", 9); pdf.set_text_color(*BLUE)
    pdf.cell(120, 5, "DESCRIPTION"); pdf.cell(54, 5, "AMOUNT", align="R")
    y += 14
    pdf.set_xy(20, y); pdf.set_font("S", "", 11); pdf.set_text_color(*INK)
    pdf.cell(120, 6, PRODUCT["name"])
    pdf.cell(50, 6, f"{o['currency']} {money(o['amount'])}", align="R")
    pdf.set_xy(20, y + 7); pdf.set_font("S", "", 9); pdf.set_text_color(*SLATE)
    pdf.cell(120, 5, PRODUCT["desc"])

    y += 22
    pdf.set_draw_color(*CYAN); pdf.set_line_width(0.5); pdf.line(120, y, 194, y)
    pdf.set_xy(120, y + 3); pdf.set_font("S", "B", 13); pdf.set_text_color(*INK)
    pdf.cell(40, 8, "Total paid")
    pdf.cell(34, 8, f"{o['currency']} {money(o['amount'])}", align="R")

    pdf.set_xy(16, y + 4); pdf.set_font("S", "B", 11)
    pdf.set_text_color(*((16, 163, 74) if o.get("status") == "paid" else SLATE))
    pdf.cell(0, 8, f"Status: {str(o.get('status','')).upper()}   -   Method: {str(o.get('method') or '').upper()}")

    pdf.set_xy(16, 250); pdf.set_font("S", "", 9); pdf.set_text_color(*SLATE)
    pdf.multi_cell(178, 5,
        "Thank you for your purchase! Your download includes PDF, ePub and Kindle-ready "
        "formats with lifetime updates. This receipt confirms payment for the item above. "
        f"Questions? Contact {SELLER['email']}.")
    return bytes(pdf.output())


if __name__ == "__main__":
    print("Vital Theory store")
    store.init()
    print("  Storefront : http://127.0.0.1:5000/")
    print("  Checkout   : http://127.0.0.1:5000/checkout")
    print("  Admin      : http://127.0.0.1:5000/admin")
    print("  Payments   :", "STRIPE" if STRIPE_KEY else "DEMO mode (simulated)")
    app.run(host="127.0.0.1", port=5000, debug=False)
