from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import pickle
import sqlite3
import os

# Initialize Flask (It automatically finds 'templates' and 'static' folders now!)
app = Flask(__name__)
app.secret_key = 'super_secret_key_123' # Change this for production
CORS(app)

# --- Security Setup ---
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page' # If user isn't logged in, send them here

# --- Database Setup (Keep your existing init_db code) ---
def init_db():
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entries 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, content TEXT, emotion TEXT, suggestion TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# --- User Loader ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user: return User(id=user[0], username=user[1])
    return None

# --- Load AI Model ---
try:
    with open('model/emotion_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('model/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
except:
    model = None

suggestions = {
    "positive": "Keep doing what makes you happy! 🌱",
    "negative": "Try deep breathing or journaling your thoughts. 💙",
    "neutral": "Reflect on your day and set small goals. 🌤️"
}

# ==========================================
#  The Connecting Routes (Frontend <-> Backend)
# ==========================================

# 1. The Home Page (Protected)
@app.route('/')
@login_required
def home():
    # Only shows index.html if user is logged in
    return render_template('index.html', username=current_user.username)

# 2. The Login Page
@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home')) # If already logged in, go home
    return render_template('login.html')

# 3. The Register Page
@app.route('/register')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('register.html')

# ==========================================
#  API Endpoints (The Logic)
# ==========================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({"message": "Success"}), 201
    except:
        return jsonify({"error": "Username taken"}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    conn.close()
    if user_data and bcrypt.check_password_hash(user_data[2], password):
        user = User(id=user_data[0], username=user_data[1])
        login_user(user)
        return jsonify({"message": "Success"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_emotion():
    data = request.get_json()
    user_text = data.get('text', '')
    text_vectorized = vectorizer.transform([user_text])
    prediction = model.predict(text_vectorized)[0]
    suggestion = suggestions.get(prediction, "Take care.")
    
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("INSERT INTO entries (user_id, content, emotion, suggestion) VALUES (?, ?, ?, ?)",
              (current_user.id, user_text, prediction, suggestion))
    conn.commit()
    conn.close()
    return jsonify({"emotion": prediction, "suggestion": suggestion})

@app.route('/history', methods=['GET'])
@login_required
def get_history():
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT content, emotion, suggestion, timestamp FROM entries WHERE user_id = ? ORDER BY id DESC LIMIT 10", (current_user.id,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{"content": r[0], "emotion": r[1], "suggestion": r[2], "timestamp": r[3]} for r in rows])

if __name__ == '__main__':
    app.run(debug=True, port=5000)