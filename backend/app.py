from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime  # Moved to top for better organization
import pickle
import sqlite3
import os

# Initialize Flask
app = Flask(__name__)
app.secret_key = 'super_secret_key_123' 
CORS(app)

# --- Security Setup ---
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page' 

# --- Database Setup ---
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

@app.route('/')
@login_required
def home():
    return render_template('index.html', username=current_user.username)

@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home')) 
    return render_template('login.html')

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

# --- UPDATED HISTORY ENDPOINT (WITH DATE FILTERING) ---
@app.route('/history', methods=['GET'])
@login_required
def get_history():
    # 1. Check if user wants a specific month
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')
    
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()

    if selected_month and selected_year:
        # CASE A: User selected a specific month
        date_filter = f"{selected_year}-{selected_month}"
        c.execute("""
            SELECT content, emotion, suggestion, timestamp 
            FROM entries 
            WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ? 
            ORDER BY timestamp DESC
        """, (current_user.id, date_filter))
    else:
        # CASE B: Default view (No month selected) -> Last 20 entries
        c.execute("""
            SELECT content, emotion, suggestion, timestamp 
            FROM entries 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT 20
        """, (current_user.id,))
        
    rows = c.fetchall()
    conn.close()
    
    return jsonify([{"content": r[0], "emotion": r[1], "suggestion": r[2], "timestamp": r[3]} for r in rows])


# --- STATS ENDPOINT FOR CHART (WITH DATE FILTERING) ---
@app.route('/api/stats')
@login_required
def get_stats():
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    # If no date is sent, default to the current month/year
    if not selected_month or not selected_year:
        now = datetime.now()
        selected_month = now.strftime('%m') 
        selected_year = now.strftime('%Y')

    date_filter = f"{selected_year}-{selected_month}"

    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE user_id = ? AND emotion = 'positive' AND strftime('%Y-%m', timestamp) = ?
    """, (current_user.id, date_filter))
    positive_count = c.fetchone()[0]
    
    c.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE user_id = ? AND emotion = 'negative' AND strftime('%Y-%m', timestamp) = ?
    """, (current_user.id, date_filter))
    negative_count = c.fetchone()[0]
    
    c.execute("""
        SELECT COUNT(*) FROM entries 
        WHERE user_id = ? AND emotion = 'neutral' AND strftime('%Y-%m', timestamp) = ?
    """, (current_user.id, date_filter))
    neutral_count = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count,
        'period': f"{selected_year}-{selected_month}"
    })

# --- ADD THIS TO app.py ---
from collections import Counter
import re

@app.route('/api/wordcloud')
@login_required
def get_wordcloud_data():
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    # Get all text content from the user's history
    c.execute("SELECT content FROM entries WHERE user_id = ?", (current_user.id,))
    rows = c.fetchall()
    conn.close()

    # 1. Combine all entries into one big string
    all_text = " ".join([r[0] for r in rows]).lower()

    # 2. Remove special characters (keep only letters and spaces)
    # This regex replaces anything that isn't a-z or 0-9 with a space
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text)

    # 3. Split into individual words
    words = clean_text.split()

    # 4. Define "Stop Words" (words to ignore)
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
        'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
        'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
        'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    }

    # 5. Filter out stop words and short words
    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

    # 6. Count frequency and get the top 50 common words
    # Format required by wordcloud2.js is: [['word', size], ['word', size]]
    word_counts = Counter(filtered_words).most_common(50)

    return jsonify(word_counts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)