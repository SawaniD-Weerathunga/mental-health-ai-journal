from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import os

app = Flask(__name__)
CORS(app)  # Allows your future frontend to talk to this server

# --- Load the Model and Vectorizer ---
print("Loading model and vectorizer...")
try:
    # We load these once when the app starts so it's fast!
    with open('model/emotion_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('model/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("❌ Error: Model files not found. Make sure you are in the 'backend' folder!")
    model = None

# --- Coping Suggestions (Step 10) ---
suggestions = {
    "positive": "Keep doing what makes you happy! 🌱",
    "negative": "Try deep breathing or journaling your thoughts. 💙",
    # If the model predicts something else (like 'neutral'), we need a default:
    "neutral": "Reflect on your day and set small goals. 🌤️"
}

# --- Routes (Step 9) ---
@app.route('/')
def home():
    return "Emotion Journal API is running! 🚀"

@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    if not model:
        return jsonify({"error": "Model is not loaded"}), 500

    # 1. Get the text from the user's request
    data = request.get_json()
    user_text = data.get('text', '')

    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    # 2. Prepare the text (Vectorize)
    # The model expects numbers, not words!
    text_vectorized = vectorizer.transform([user_text])
    
    # 3. Predict Emotion
    prediction = model.predict(text_vectorized)[0]

    # 4. Get Suggestion
    suggestion_text = suggestions.get(prediction, "Take a moment to breathe.")

    # 5. Send JSON response
    return jsonify({
        "emotion": prediction,
        "suggestion": suggestion_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)