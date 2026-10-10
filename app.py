from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from functools import wraps
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "studygo.db")
app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("STUDYGO_SECRET", "cambiar-esta-clave-antes-de-publicar")

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
          course TEXT DEFAULT '', specialty TEXT DEFAULT '', color TEXT DEFAULT '#1688e8',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          subject TEXT NOT NULL, title TEXT NOT NULL, due_date TEXT DEFAULT '',
          status TEXT DEFAULT 'Pendiente', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          title TEXT NOT NULL, event_date TEXT DEFAULT '', description TEXT DEFAULT '',
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS notices(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          title TEXT NOT NULL, body TEXT DEFAULT '', is_read INTEGER DEFAULT 0,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("uid"):
            return jsonify({"error":"Iniciá sesión para continuar."}), 401
        return fn(*args, **kwargs)
    return wrapped

def user_dict(row):
    return {k: row[k] for k in ("id","name","email","course","specialty","color")}

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.post("/api/register")
def register():
    d = request.get_json(silent=True) or {}
    name, email, password = (str(d.get(k,"")).strip() for k in ("name","email","password"))
    if not name or not email or len(password) < 8:
        return jsonify({"error":"Ingresá nombre, correo y una contraseña de al menos 8 caracteres."}), 400
    try:
        with connect() as c:
            cur = c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                            (name, email.lower(), generate_password_hash(password)))
            uid = cur.lastrowid
            c.execute("INSERT INTO notices(user_id,title,body) VALUES(?,?,?)",
                      (uid, "¡Bienvenido a StudyGO!", "Completá tu perfil y agregá tu primera tarea."))
        session["uid"] = uid
        return jsonify({"ok":True})
    except sqlite3.IntegrityError:
        return jsonify({"error":"Ya existe una cuenta con ese correo."}), 409

@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    with connect() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (str(d.get("email","")).strip().lower(),)).fetchone()
    if not u or not check_password_hash(u["password"], str(d.get("password",""))):
        return jsonify({"error":"Correo o contraseña incorrectos."}), 401
    session["uid"] = u["id"]
    return jsonify({"ok":True})

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok":True})

@app.get("/api/me")
@login_required
def me():
    with connect() as c:
        u = c.execute("SELECT id,name,email,course,specialty,color FROM users WHERE id=?", (session["uid"],)).fetchone()
    return jsonify(user_dict(u))

@app.put("/api/me")
@login_required
def update_me():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name","")).strip()
    if not name:
        return jsonify({"error":"El nombre es obligatorio."}), 400
    color = str(d.get("color","#1688e8"))
    if color not in ("#1688e8","#16a36b","#7955d9","#e98920"):
        color = "#1688e8"
    with connect() as c:
        c.execute("UPDATE users SET name=?,course=?,specialty=?,color=? WHERE id=?",
          (name, str(d.get("course","")).strip(), str(d.get("specialty","")).strip(), color, session["uid"]))
    return jsonify({"ok":True})

@app.get("/api/tasks")
@login_required
def get_tasks():
    with connect() as c:
        rows = c.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY CASE WHEN status='Completada' THEN 1 ELSE 0 END, due_date, id DESC", (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/tasks")
@login_required
def add_task():
    d = request.get_json(silent=True) or {}
    subject, title = str(d.get("subject","")).strip(), str(d.get("title","")).strip()
    if not subject or not title:
        return jsonify({"error":"La materia y el nombre de la tarea son obligatorios."}), 400
    with connect() as c:
        cur = c.execute("INSERT INTO tasks(user_id,subject,title,due_date) VALUES(?,?,?,?)",
          (session["uid"], subject[:100], title[:200], str(d.get("due_date",""))[:20]))
        c.execute("INSERT INTO notices(user_id,title,body) VALUES(?,?,?)",
          (session["uid"], "Tarea agregada", f"{subject}: {title}"))
        row = c.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.patch("/api/tasks/<int:task_id>")
@login_required
def update_task(task_id):
    d = request.get_json(silent=True) or {}
    status = str(d.get("status",""))
    if status not in ("Pendiente","En proceso","Completada"):
        return jsonify({"error":"Estado no válido."}), 400
    with connect() as c:
        cur = c.execute("UPDATE tasks SET status=? WHERE id=? AND user_id=?", (status, task_id, session["uid"]))
    if not cur.rowcount: return jsonify({"error":"Tarea no encontrada."}), 404
    return jsonify({"ok":True})

@app.delete("/api/tasks/<int:task_id>")
@login_required
def delete_task(task_id):
    with connect() as c:
        cur = c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, session["uid"]))
    if not cur.rowcount: return jsonify({"error":"Tarea no encontrada."}), 404
    return jsonify({"ok":True})

@app.get("/api/events")
@login_required
def get_events():
    with connect() as c:
        rows = c.execute("SELECT * FROM events WHERE user_id=? ORDER BY event_date", (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/events")
@login_required
def add_event():
    d = request.get_json(silent=True) or {}
    title = str(d.get("title","")).strip()
    if not title: return jsonify({"error":"El título es obligatorio."}), 400
    with connect() as c:
        cur = c.execute("INSERT INTO events(user_id,title,event_date,description) VALUES(?,?,?,?)",
          (session["uid"], title[:200], str(d.get("event_date",""))[:20], str(d.get("description",""))[:500]))
        row = c.execute("SELECT * FROM events WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.get("/api/notices")
@login_required
def get_notices():
    with connect() as c:
        rows = c.execute("SELECT * FROM notices WHERE user_id=? ORDER BY id DESC LIMIT 50", (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/notices/read-all")
@login_required
def read_notices():
    with connect() as c:
        c.execute("UPDATE notices SET is_read=1 WHERE user_id=?", (session["uid"],))
    return jsonify({"ok":True})

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"service":"StudyGO Web API"})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
