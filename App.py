from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# - FOLDER
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# - DATABASE
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user TEXT,
        message TEXT
    )
    """)

    db.commit()

init_db()

# - LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        result = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (user, pw)
        ).fetchone()

        if result:
            session["user"] = user
            return redirect("/dashboard")

    return render_template("login.html")

# - REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        db.execute(
            "INSERT INTO users (username, password) VALUES (?,?)",
            (user, pw)
        )
        db.commit()

        return redirect("/")

    return render_template("register.html")

# - DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    user_folder = os.path.join(UPLOAD_FOLDER, user)
    os.makedirs(user_folder, exist_ok=True)

    # upload
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(user_folder, filename))

    # list files
    files = os.listdir(user_folder)
    file_data = []

    for file in files:
        path = os.path.join(user_folder, file)
        size = os.path.getsize(path)
        size_kb = size / 1024

        if size_kb > 1024:
            size = round(size_kb / 1024, 2)
            size = str(size) + " MB"
        else:
            size = round(size_kb, 2)
            size = str(size) + " KB"

        file_data.append((file, size))

    return render_template("dashboard.html", files=file_data, user=user)

# - DOWNLOAD 
@app.route("/download/<filename>")
def download(filename):
    if "user" not in session:
        return redirect("/")

    user_folder = os.path.join(UPLOAD_FOLDER, session["user"])
    return send_from_directory(user_folder, filename, as_attachment=True)
    
# - view 
@app.route("/view/<filename>")
def view(filename):
    if "user" not in session:
        return redirect("/")
          
          
    user_folder = os.path.join(UPLOAD_FOLDER,session["user"])
    return send_from_directory(user_folder,
      filename)

# DELETE 
@app.route("/delete/<filename>")
def delete(filename):
    if "user" not in session:
        return redirect("/")

    user_folder = os.path.join(UPLOAD_FOLDER, session["user"])
    path = os.path.join(user_folder, filename)

    if os.path.exists(path):
        os.remove(path)

    return redirect("/dashboard")

# - CHAT
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        msg = request.form["message"]
        db.execute(
            "INSERT INTO messages (user, message) VALUES (?,?)",
            (session["user"], msg)
        )
        db.commit()

    messages = db.execute("SELECT * FROM messages").fetchall()

    return render_template("chat.html", messages=messages, user=session["user"])

# - LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# - RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)