from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import sqlite3
import os

# --- Import Transformers (New AI) ---
from transformers import pipeline

# --- Import Dotenv (Security) ---
from dotenv import load_dotenv

# 1. Load environment variables from .env file
load_dotenv()

# Initialize Flask
app = Flask(__name__)

# 2. Get the secret key securely from .env
app.secret_key = os.getenv('SECRET_KEY') 

# Fallback in case .env is missing (prevents crash, but warns you)
if not app.secret_key:
    print("WARNING: No SECRET_KEY found in .env. Using unsafe default.")
    app.secret_key = 'unsafe-default-key'

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

# ==========================================
#  🧠 AI SETUP (TRANSFORMERS)
# ==========================================
print("🤖 Loading AI Brain... (This may take a moment on first run)")

# We use a RoBERTa model trained specifically for sentiment (Positive/Negative/Neutral)
# It will download automatically (~400MB) the first time you run this.
emotion_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

suggestions = {
    "positive": "Keep doing what makes you happy! 🌱",
    "negative": "Try deep breathing or journaling your thoughts. 💙",
    "neutral": "Reflect on your day and set small goals. 🌤️"
}

# ==========================================
#  Routes
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

# --- API Endpoints ---

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

# --- ANALYZE ENDPOINT ---
@app.route('/analyze', methods=['POST'])
@login_required
def analyze_emotion():
    data = request.get_json()
    user_text = data.get('text', '')
    
    # 1. Run the Transformer AI
    # Truncate text to 512 chars to prevent errors with long entries
    results = emotion_pipeline(user_text[:512]) 
    
    # The model returns labels like 'positive', 'negative', 'neutral'
    raw_label = results[0]['label']
    
    # Map model output to our database format (lowercase)
    prediction = raw_label.lower() 
    
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
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()

    if selected_month and selected_year:
        date_filter = f"{selected_year}-{selected_month}"
        c.execute("SELECT content, emotion, suggestion, timestamp FROM entries WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ? ORDER BY timestamp DESC", (current_user.id, date_filter))
    else:
        c.execute("SELECT content, emotion, suggestion, timestamp FROM entries WHERE user_id = ? ORDER BY id DESC LIMIT 20", (current_user.id,))
        
    rows = c.fetchall()
    conn.close()
    return jsonify([{"content": r[0], "emotion": r[1], "suggestion": r[2], "timestamp": r[3]} for r in rows])

@app.route('/api/stats')
@login_required
def get_stats():
    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    if not selected_month or not selected_year:
        now = datetime.now()
        selected_month = now.strftime('%m') 
        selected_year = now.strftime('%Y')

    date_filter = f"{selected_year}-{selected_month}"

    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM entries WHERE user_id = ? AND emotion = 'positive' AND strftime('%Y-%m', timestamp) = ?", (current_user.id, date_filter))
    positive_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM entries WHERE user_id = ? AND emotion = 'negative' AND strftime('%Y-%m', timestamp) = ?", (current_user.id, date_filter))
    negative_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM entries WHERE user_id = ? AND emotion = 'neutral' AND strftime('%Y-%m', timestamp) = ?", (current_user.id, date_filter))
    neutral_count = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'positive': positive_count,
        'negative': negative_count,
        'neutral': neutral_count,
        'period': f"{selected_year}-{selected_month}"
    })

@app.route('/api/wordcloud')
@login_required
def get_wordcloud_data():
    from collections import Counter
    import re
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT content FROM entries WHERE user_id = ?", (current_user.id,))
    rows = c.fetchall()
    conn.close()

    all_text = " ".join([r[0] for r in rows]).lower()
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text)
    words = clean_text.split()

    stop_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}

    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
    word_counts = Counter(filtered_words).most_common(50)
    return jsonify(word_counts)

@app.route('/api/calendar')
@login_required
def get_calendar_data():
    from collections import Counter
    month = request.args.get('month')
    year = request.args.get('year')
    
    if not month or not year:
        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%Y')

    date_filter = f"{year}-{month}"
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    
    c.execute("SELECT date(timestamp), emotion FROM entries WHERE user_id = ? AND strftime('%Y-%m', timestamp) = ?", (current_user.id, date_filter))
    rows = c.fetchall()
    conn.close()

    daily_emotions = {}
    temp_data = {}
    for r in rows:
        day_date = r[0]
        emotion = r[1]
        if day_date not in temp_data: temp_data[day_date] = []
        temp_data[day_date].append(emotion)

    for day, emotion_list in temp_data.items():
        most_common = Counter(emotion_list).most_common(1)[0][0]
        daily_emotions[day] = most_common

    return jsonify(daily_emotions)

@app.route('/api/day_stats')
@login_required
def get_day_stats():
    date_str = request.args.get('date')
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT emotion, COUNT(*) FROM entries WHERE user_id = ? AND date(timestamp) = ? GROUP BY emotion", (current_user.id, date_str))
    rows = c.fetchall()
    conn.close()
    stats = {'positive': 0, 'negative': 0, 'neutral': 0}
    for r in rows:
        stats[r[0]] = r[1]
    return jsonify(stats)

@app.route('/api/gamification')
@login_required
def get_gamification():
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, emotion FROM entries WHERE user_id = ? ORDER BY timestamp DESC", (current_user.id,))
    rows = c.fetchall()
    conn.close()

    streak = 0
    if rows:
        dates = []
        for r in rows:
            dt = datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
            dates.append(dt.date())
        
        unique_dates = sorted(list(set(dates)), reverse=True)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        if unique_dates[0] == today:
            streak = 1
            check_date = yesterday
        elif unique_dates[0] == yesterday:
            streak = 1
            check_date = yesterday - timedelta(days=1)
        else:
            streak = 0 
            
        if streak > 0:
            for d in unique_dates[1:]:
                if d == check_date:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break 

    badges = []
    if len(rows) >= 1: badges.append({'icon': '🌱', 'name': 'First Step', 'desc': 'Created your first entry'})
    if len(rows) >= 10: badges.append({'icon': '✍️', 'name': 'Journalist', 'desc': 'Created 10 entries'})
    
    is_positive_streak = False
    if len(rows) >= 5:
        recent_emotions = [r[1] for r in rows[:5]] 
        if all(e == 'positive' for e in recent_emotions):
            badges.append({'icon': '☀️', 'name': 'Positivity Pro', 'desc': '5 positive entries in a row'})

    is_night_owl = False
    for r in rows:
        dt = datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
        if dt.hour >= 23 or dt.hour < 4:
            is_night_owl = True
            break
    if is_night_owl:
        badges.append({'icon': '🦉', 'name': 'Night Owl', 'desc': 'Wrote an entry late at night'})

    return jsonify({'streak': streak, 'badges': badges})

if __name__ == '__main__':
    app.run(debug=True, port=5000)