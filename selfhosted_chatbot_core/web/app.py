import os
import json
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
from functools import wraps

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

app = Flask(__name__)
app.secret_key = os.environ.get("WEB_SECRET_KEY", "devsecret")

def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET","POST"])
def login():
    settings = load_json(os.path.join(CONFIG_DIR, "settings.json"))
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == settings.get("admin_password"):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        flash("Sai mật khẩu")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@require_login
def dashboard():
    # Basic status from logs
    log_path = os.path.join(BASE_DIR, "logs", "bot.log")
    last_lines = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-50:]
    except FileNotFoundError:
        pass
    settings = load_json(os.path.join(CONFIG_DIR, "settings.json"))
    return render_template("dashboard.html", logs=last_lines, settings=settings)

@app.route("/config/replies", methods=["GET","POST"])
@require_login
def config_replies():
    path = os.path.join(CONFIG_DIR, "replies.json")
    if request.method == "POST":
        data = request.form.get("content", "")
        try:
            parsed = json.loads(data)
            save_json(path, parsed)
            flash("Lưu replies.json thành công!")
        except Exception as e:
            flash(f"Lỗi JSON: {e}")
    content = json.dumps(load_json(path), ensure_ascii=False, indent=2)
    return render_template("config_editor.html", title="replies.json", content=content, filename="replies.json")

@app.route("/config/settings", methods=["GET","POST"])
@require_login
def config_settings():
    path = os.path.join(CONFIG_DIR, "settings.json")
    if request.method == "POST":
        data = request.form.get("content", "")
        try:
            parsed = json.loads(data)
            save_json(path, parsed)
            flash("Lưu settings.json thành công!")
        except Exception as e:
            flash(f"Lỗi JSON: {e}")
    content = json.dumps(load_json(path), ensure_ascii=False, indent=2)
    return render_template("config_editor.html", title="settings.json", content=content, filename="settings.json")

@app.route("/config/credentials", methods=["GET","POST"])
@require_login
def config_credentials():
    path = os.path.join(CONFIG_DIR, "credentials.json")
    if request.method == "POST":
        data = request.form.get("content", "")
        try:
            parsed = json.loads(data)
            save_json(path, parsed)
            flash("Lưu credentials.json thành công!")
        except Exception as e:
            flash(f"Lỗi JSON: {e}")
    content = json.dumps(load_json(path), ensure_ascii=False, indent=2)
    return render_template("config_editor.html", title="credentials.json", content=content, filename="credentials.json")

@app.route("/download/log")
@require_login
def download_log():
    path = os.path.join(BASE_DIR, "logs", "bot.log")
    if not os.path.exists(path):
        return "No log yet", 404
    return send_file(path, as_attachment=True)
