import os
import re
import time
import sqlite3
import secrets
import hashlib
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, jsonify, request, send_from_directory, session, redirect

BASE = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.getenv("DB_FILE", os.path.join(BASE, "data", "site.db"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@ROVKQPKC")\nTELEGRAM_CHANNEL_USERNAME = os.getenv("TELEGRAM_CHANNEL_USERNAME", "@ROVKQPKC").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
ADMIN_URL = os.getenv("ADMIN_URL", "/admin.html").strip()

MAX_BODY = 64 * 1024
RATE_WINDOW = 60
RATE_MAX = 12
rate_cache = {}

app = Flask(__name__, static_folder=BASE)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "1") != "0",
    MAX_CONTENT_LENGTH=MAX_BODY,
)

os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def db():
    c = sqlite3.connect(DB_FILE, timeout=6)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS reports(
          id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          name TEXT NOT NULL DEFAULT '',
          phone TEXT NOT NULL DEFAULT '',
          category TEXT NOT NULL DEFAULT 'سایر',
          place TEXT NOT NULL DEFAULT '',
          text TEXT NOT NULL,
          anonymous INTEGER NOT NULL DEFAULT 0,
          telegram_sent INTEGER NOT NULL DEFAULT 0,
          telegram_error TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS donations(
          id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          name TEXT NOT NULL DEFAULT '',
          amount TEXT NOT NULL,
          phone TEXT NOT NULL DEFAULT '',
          note TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS visits(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT NOT NULL,
          visitor_hash TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_visits_created ON visits(created_at DESC);
        """)

def clean(v, limit):
    v = "" if v is None else str(v)
    v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
    return v.strip()[:limit]

def client_hash():
    # No raw IP is stored. Salt is server-side.
    raw = (request.headers.get("X-Forwarded-For","").split(",")[0].strip()
           or request.remote_addr or "unknown")
    salt = os.getenv("VISITOR_HASH_SALT", app.secret_key)
    return hashlib.sha256((salt + "|" + raw).encode()).hexdigest()

def rate_limit():
    now = time.time()
    key = client_hash()
    arr = [x for x in rate_cache.get(key, []) if now-x < RATE_WINDOW]
    if len(arr) >= RATE_MAX:
        return False
    arr.append(now)
    rate_cache[key] = arr
    if len(rate_cache) > 5000:
        for k in list(rate_cache)[:1000]:
            rate_cache.pop(k, None)
    return True

def tg_escape(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def telegram_target():
    target = (TELEGRAM_CHAT_ID or TELEGRAM_CHANNEL_USERNAME or "@ROVKQPKC").strip()
    return target

def send_telegram_report(r):
    if not BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Telegram environment variables are not configured."
    label = "ناشناس" if r["anonymous"] else (r["name"] or "ثبت نشده")
    phone = "" if r["anonymous"] else (r["phone"] or "ثبت نشده")
    msg = (
        "🚨 <b>گزارش جدید سایت</b>\n\n"
        f"<b>کد پیگیری:</b> {tg_escape(r['id'])}\n"
        f"<b>زمان:</b> {tg_escape(r['created_at'])}\n"
        f"<b>نام:</b> {tg_escape(label)}\n"
        f"<b>تلفن:</b> {tg_escape(phone)}\n"
        f"<b>دسته:</b> {tg_escape(r['category'])}\n"
        f"<b>محدوده:</b> {tg_escape(r['place'] or 'ثبت نشده')}\n\n"
        f"<b>شرح:</b>\n{tg_escape(r['text'])}"
    )
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": telegram_target(), "text": msg, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        data = resp.json()
        if not resp.ok or not data.get("ok"):
            return False, clean(data.get("description","Telegram error"), 500)
        return True, ""
    except Exception as e:
        return False, clean(str(e), 500)

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="نیاز به ورود مدیر است."), 401
        return f(*args, **kwargs)
    return wrapper

@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' data:; "
        "img-src 'self' data: blob:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'self';"
    )
    return resp

@app.get("/")
def home():
    return send_from_directory(BASE, "index.html")

@app.get("/admin.html")
def admin_page():
    return send_from_directory(BASE, "admin.html")

@app.get("/health")
def health():
    return jsonify(ok=True, time=datetime.now(timezone.utc).isoformat())

@app.get("/api/config")
def config():
    return jsonify(adminUrl=ADMIN_URL)

@app.post("/api/reports")
def create_report():
    if not rate_limit():
        return jsonify(error="تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."), 429
    data = request.get_json(silent=True) or {}
    if data.get("website"):
        return jsonify(error="درخواست نامعتبر است."), 400
    text = clean(data.get("text"), 5000)
    if len(text) < 8:
        return jsonify(error="شرح گزارش کوتاه است."), 400
    category = clean(data.get("category"), 40) or "سایر"
    allowed = {"فرهنگی","اجتماعی","آموزشی","احکام","سایر"}
    if category not in allowed:
        category = "سایر"
    anonymous = bool(data.get("anonymous"))
    rid = clean(data.get("id"), 50)
    if not re.fullmatch(r"VR-[A-Z0-9-]{8,45}", rid or ""):
        rid = "VR-" + secrets.token_hex(8).upper()
    created = datetime.now(timezone.utc).astimezone().strftime("%Y/%m/%d %H:%M:%S")
    name = "" if anonymous else clean(data.get("name"), 100)
    phone = "" if anonymous else clean(data.get("phone"), 40)
    place = clean(data.get("place"), 120)
    row = dict(id=rid, created_at=created, name=name, phone=phone,
               category=category, place=place, text=text, anonymous=anonymous)
    try:
        with db() as c:
            c.execute("""INSERT INTO reports
              (id,created_at,name,phone,category,place,text,anonymous)
              VALUES(?,?,?,?,?,?,?,?)""",
              (rid,created,name,phone,category,place,text,int(anonymous)))
    except sqlite3.IntegrityError:
        return jsonify(error="کد گزارش تکراری است؛ دوباره ارسال کنید."), 409

    sent, err = send_telegram_report(row)
    with db() as c:
        c.execute("UPDATE reports SET telegram_sent=?, telegram_error=? WHERE id=?",
                  (int(sent), err, rid))
    return jsonify(ok=True, id=rid, telegram="sent" if sent else "queued")

@app.post("/api/donations")
def create_donation():
    if not rate_limit():
        return jsonify(error="تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."), 429
    data = request.get_json(silent=True) or {}
    amount = clean(data.get("amount"), 80)
    if not amount:
        return jsonify(error="مبلغ را وارد کنید."), 400
    rid = "NZ-" + secrets.token_hex(7).upper()
    created = datetime.now(timezone.utc).astimezone().strftime("%Y/%m/%d %H:%M:%S")
    with db() as c:
        c.execute("INSERT INTO donations(id,created_at,name,amount,phone,note) VALUES(?,?,?,?,?,?)",
                  (rid,created,clean(data.get("name"),100),amount,clean(data.get("phone"),40),clean(data.get("note"),1000)))
    return jsonify(ok=True, id=rid)

@app.post("/api/visit")
def visit():
    if not rate_limit():
        return jsonify(ok=False), 429
    with db() as c:
        c.execute("INSERT INTO visits(created_at,visitor_hash) VALUES(?,?)",
                  (datetime.now(timezone.utc).isoformat(), client_hash()))
    return jsonify(ok=True)

@app.post("/api/admin/login")
def admin_login():
    if not rate_limit():
        return jsonify(error="تعداد تلاش‌ها زیاد است."), 429
    data = request.get_json(silent=True) or {}
    user = clean(data.get("username"), 80)
    pw = str(data.get("password") or "")
    if not ADMIN_PASSWORD or not secrets.compare_digest(user, ADMIN_USERNAME) or not secrets.compare_digest(pw, ADMIN_PASSWORD):
        time.sleep(0.35)
        return jsonify(error="نام کاربری یا رمز عبور نادرست است."), 401
    session.clear()
    session["admin"] = True
    session.permanent = True
    return jsonify(ok=True)

@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/api/admin/me")
def admin_me():
    return jsonify(authenticated=bool(session.get("admin")))

@app.get("/api/admin/reports")
@admin_required
def admin_reports():
    limit = min(max(int(request.args.get("limit", "100")), 1), 200)
    with db() as c:
        rows = [dict(x) for x in c.execute(
            "SELECT id,created_at,name,phone,category,place,text,anonymous,telegram_sent FROM reports ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()]
    return jsonify(reports=rows)

@app.get("/api/admin/donations")
@admin_required
def admin_donations():
    with db() as c:
        rows = [dict(x) for x in c.execute(
            "SELECT id,created_at,name,amount,phone,note FROM donations ORDER BY created_at DESC LIMIT 200").fetchall()]
    return jsonify(donations=rows)

@app.get("/api/admin/stats")
@admin_required
def admin_stats():
    with db() as c:
        r = c.execute("SELECT COUNT(*) n FROM reports").fetchone()["n"]
        d = c.execute("SELECT COUNT(*) n FROM donations").fetchone()["n"]
        v = c.execute("SELECT COUNT(*) n FROM visits").fetchone()["n"]
        pending = c.execute("SELECT COUNT(*) n FROM reports WHERE telegram_sent=0").fetchone()["n"]
    return jsonify(reports=r, donations=d, visits=v, telegram_pending=pending)

@app.post("/api/admin/retry-telegram/<rid>")
@admin_required
def retry_telegram(rid):
    with db() as c:
        row = c.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    if not row:
        return jsonify(error="گزارش پیدا نشد."), 404
    sent, err = send_telegram_report(dict(row))
    with db() as c:
        c.execute("UPDATE reports SET telegram_sent=?, telegram_error=? WHERE id=?",
                  (int(sent), err, rid))
    return jsonify(ok=sent, error=err)

init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
