from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
import os, threading, logging
from functools import wraps

from config import (
    BOT_TOKEN, ADMIN_ID, DASHBOARD_PASSWORD,
    SECRET_KEY, TMP_DIR
)
from database import (
    init_db, get_stats, get_channels, add_channel,
    remove_channel, set_setting, get_setting,
    load_fatwas_from_json, get_fatwas
)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ============ تهيئة ============
db_ready = False

def ensure_db():
    global db_ready
    if not db_ready:
        init_db()
        db_ready = True
        # تشغيل البوت
        try:
            from bot import build_application
            from worker import start_worker
            build_application()
            start_worker()
            logging.info("✅ Bot & Worker started")
        except Exception as e:
            logging.error(f"startup err: {e}")

@app.before_request
def before():
    ensure_db()

# ============ Auth ============
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == DASHBOARD_PASSWORD:
            login_user(User("admin"))
            return redirect(url_for("dashboard"))
        flash("كلمة السر خاطئة", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ============ Dashboard ============
@app.route("/")
@login_required
def dashboard():
    stats = get_stats()
    state = get_setting("state", "stopped")
    chans = get_channels()
    recent = get_fatwas(limit=20)
    return render_template(
        "dashboard.html", stats=stats, state=state,
        channels=chans, recent=recent
    )

# ============ Actions ============
@app.route("/start", methods=["POST"])
@login_required
def start_processing():
    set_setting("state", "running")
    return jsonify({"ok": True, "state": "running"})

@app.route("/pause", methods=["POST"])
@login_required
def pause_processing():
    set_setting("state", "paused")
    return jsonify({"ok": True, "state": "paused"})

@app.route("/stop", methods=["POST"])
@login_required
def stop_processing():
    set_setting("state", "stopped")
    return jsonify({"ok": True, "state": "stopped"})

@app.route("/stats")
@login_required
def stats_api():
    return jsonify({
        "stats": get_stats(),
        "state": get_setting("state", "stopped")
    })

@app.route("/load-data", methods=["POST"])
@login_required
def load_data():
    try:
        n = load_fatwas_from_json("fatwas.json")
        return jsonify({"ok": True, "inserted": n})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# ============ Channels ============
@app.route("/channels")
@login_required
def channels_page():
    return render_template("channels.html", channels=get_channels())

@app.route("/channels/add", methods=["POST"])
@login_required
def add_channel_route():
    cid = request.form.get("chat_id", "").strip()
    title = request.form.get("title", "").strip()
    if not cid:
        flash("chat_id مطلوب", "error")
    else:
        add_channel(cid, title)
        flash("✅ تمت الإضافة", "success")
    return redirect(url_for("channels_page"))

@app.route("/channels/remove/<int:cid>", methods=["POST"])
@login_required
def remove_channel_route(cid):
    chans = get_channels()
    for c in chans:
        if c["id"] == cid:
            remove_channel(c["chat_id"])
            break
    return redirect(url_for("channels_page"))

# ============ Logs ============
@app.route("/logs")
@login_required
def logs_page():
    logs = []
    for status in ["sent", "failed", "pending"]:
        logs.extend(get_fatwas(limit=30, status=status))
    return render_template("logs.html", logs=logs)

# ============ Keep alive ============
@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)