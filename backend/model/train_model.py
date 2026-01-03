import pandas as pd
import pickle
import nltk
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# --- Setup NLTK ---
print("Downloading NLTK data...")
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    cleaned_words = [w for w in words if w not in stop_words]
    return " ".join(cleaned_words)

# 1. Load Dataset
print("Loading dataset...")
data = pd.read_csv('../../dataset/train.csv')

# Fix Labels
print("Fixing labels...")
label_mapping = {0: 'negative', 1: 'positive'}
data['sentiment'] = data['sentiment'].map(label_mapping)
data = data.dropna(subset=['sentiment'])

# 2. Preprocess
print("Cleaning text (this might take a minute)...")
X = data['sentence'].apply(clean_text)
y = data['sentiment']

# 3. Vectorization
print("Vectorizing text...")
vectorizer = TfidfVectorizer(max_features=5000)
X_vectorized = vectorizer.fit_transform(X)

# --- NEW STEP: Split Data ---
# We split the data: 80% for training, 20% for testing
print("Splitting data for evaluation...")
X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)

# 4. Train the Model
print("Training model...")
model = LogisticRegression(n_jobs=-1)
model.fit(X_train, y_train)

# --- NEW STEP: Evaluate ---
print("\n--- MODEL REPORT CARD ---")
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
print(f"✅ Accuracy Score: {accuracy:.2%}") # formats as percentage (e.g., 85.20%)

print("\nDetailed Report:")
print(classification_report(y_test, predictions))
print("-------------------------\n")

# 5. Save the Model
print("Saving model files...")
with open('emotion_model.pkl', 'wb') as model_file:
    pickle.dump(model, model_file)
with open('vectorizer.pkl', 'wb') as vec_file:
    pickle.dump(vectorizer, vec_file)

print("✅ Success! Model trained, evaluated, and saved!")