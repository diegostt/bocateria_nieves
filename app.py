import os
import sqlite3
from datetime import datetime
from flask import Flask, request, render_template, redirect, abort, url_for
from email.mime.text import MIMEText
import smtplib
import requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "pedidos.db")
SMTP_USER = os.getenv("SMTP_USER") or None
SMTP_PASS = os.getenv("SMTP_PASS") or None
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL") or None
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or None
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or None
ADMIN_KEY = os.getenv("ADMIN_KEY", "cambiame")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT,
        direccion TEXT,
        items TEXT,
        total REAL,
        estado TEXT,
        creado TEXT
    )
    """)
    conn.commit()
    conn.close()

def enviar_email(destino, subject, cuerpo):
    if not SMTP_USER or not SMTP_PASS or not destino:
        print("Email no configurado — salto envío")
        return
    msg = MIMEText(cuerpo)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = destino
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print("Email enviado a", destino)
    except Exception as e:
        print("Error enviando email:", e)

def enviar_telegram(chat_id, token, texto):
    if not chat_id or not token:
        print("Telegram no configurado — salto envío")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": texto})
        if r.status_code != 200:
            print("Error Telegram:", r.status_code, r.text)
        else:
            print("Notificación Telegram enviada")
    except Exception as e:
        print("Error enviando Telegram:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pedir", methods=["POST"])
def pedir():
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    direccion = request.form.get("direccion", "").strip()
    items = request.form.get("items", "").strip()
    try:
        total = float(request.form.get("total", "0").strip() or 0)
    except:
        total = 0.0
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (nombre, telefono, direccion, items, total, estado, creado) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (nombre, telefono, direccion, items, total, "nuevo", datetime.utcnow().isoformat()))
    conn.commit()
    pedido_id = c.lastrowid
    conn.close()

    texto = f"Nuevo pedido #{pedido_id}\\nNombre: {nombre}\\nTel: {telefono}\\nDirección: {direccion}\\nItems:\\n{items}\\nTotal: {total}€"

    if NOTIFY_EMAIL:
        enviar_email(NOTIFY_EMAIL, f"Nuevo pedido #{pedido_id} - {nombre}", texto)
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        enviar_telegram(TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, texto)

    return render_template("pedido_recibido.html", pedido_id=pedido_id)

@app.route("/admin")
def admin():
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        return abort(401)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, nombre, telefono, direccion, items, total, estado, creado FROM pedidos ORDER BY id DESC")
    filas = c.fetchall()
    conn.close()
    return render_template("admin.html", pedidos=filas, key=key)

@app.route("/admin/update", methods=["POST"])
def admin_update():
    key = request.form.get("key", "")
    if key != ADMIN_KEY:
        return abort(401)
    pedido_id = request.form.get("id")
    nuevo_estado = request.form.get("estado", "preparado")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin") + f"?key={key}")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)