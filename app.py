from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = "test.db"
LOG_FILE = "logs/injection_logs.txt"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("CREATE TABLE users (username TEXT, password TEXT)")
    c.execute("INSERT INTO users VALUES ('admin', 'admin123')")
    conn.commit()
    conn.close()

    # Make sure logs directory exists
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        f.write("SQL Injection Log\n" + "-"*40 + "\n")

init_db()

# Logging function
def log_injection(query):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] Suspicious Query: {query}\n")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Safe registration using parameterized query
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    
    return render_template("register.html", message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Unsafe query (vulnerable)
        query = f"SELECT * FROM users WHERE username = '{user}' AND password = '{pwd}'"
        print("Executed Query:", query)

        try:
            cursor.execute(query)
            result = cursor.fetchone()
        except Exception as e:
            message = f"SQL Error: {e}"
            result = None

        conn.close()

        if result:
            message = "✅ Login successful!"
        else:
            message = "❌ Login failed!"
            if "'" in user or "--" in user or " OR " in user.upper():
                log_injection(query)

    return render_template("login.html", message=message)

@app.route('/testing', methods=['GET', 'POST'])
def testing():
    output = ""
    query = ""
    if request.method == 'POST':
        query = request.form['query']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()
            output = f"✅ Result: {result}"
        except Exception as e:
            output = f"❌ Error: {e}"
            log_injection(query)

        conn.close()

    return render_template("testing.html", output=output, query=query)

if __name__ == '__main__':
    app.run(debug=True)
