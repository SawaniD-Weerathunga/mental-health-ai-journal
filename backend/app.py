from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# --- Database Setup (Phase 6) ---
def init_db():
    conn = sqlite3.connect('journal.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            emotion TEXT,
            suggestion TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the DB when the app starts
init_db()

# --- Load the Best Model ---
print("Loading model...")
try:
    with open('model/emotion_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('model/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("❌ Error: Model files not found.")
    model = None

suggestions = {
    "positive": "Keep doing what makes you happy! 🌱",
    "negative": "Try deep breathing or journaling your thoughts. 💙",
    "neutral": "Reflect on your day and set small goals. 🌤️"
}

@app.route('/')
def home():
    return "Emotion Journal API is running!"

@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    if not model:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.get_json()
    user_text = data.get('text', '')

    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    # 1. Predict
    text_vectorized = vectorizer.transform([user_text])
    prediction = model.predict(text_vectorized)[0]
    suggestion = suggestions.get(prediction, "Take care of yourself.")

    # 2. Save to Database
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        c.execute("INSERT INTO entries (content, emotion, suggestion) VALUES (?, ?, ?)",
                  (user_text, prediction, suggestion))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

    return jsonify({
        "emotion": prediction,
        "suggestion": suggestion
    })

# --- NEW ROUTE: Get History ---
@app.route('/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect('journal.db')
        c = conn.cursor()
        # Get the last 10 entries, newest first
        c.execute("SELECT content, emotion, suggestion, timestamp FROM entries ORDER BY id DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()

        # Convert database rows to a list of dictionaries (JSON)
        history = []
        for row in rows:
            history.append({
                "content": row[0],
                "emotion": row[1],
                "suggestion": row[2],
                "timestamp": row[3]
            })
        
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)