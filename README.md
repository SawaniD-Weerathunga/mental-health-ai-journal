
# 🧠 Mental Health AI Journal

A **privacy-first, AI-powered journaling platform** that helps users track their mental well-being. It uses state-of-the-art Natural Language Processing (RoBERTa) to analyze journal entries, detect emotions, and provide personalized coping suggestions.

> **Key Differentiator:** Unlike standard journals, this application features **Database-Level Encryption**, ensuring that even if the database file is stolen, user thoughts remain unreadable.

---

## 📸 Screenshots

*(Add screenshots here of your Dashboard, Dark Mode, or PDF Report)*

<div style="display: flex; gap: 10px;">
<img src="[https://via.placeholder.com/400x200?text=Dashboard+Analytics](https://www.google.com/search?q=https://via.placeholder.com/400x200%3Ftext%3DDashboard%2BAnalytics)" alt="Dashboard" width="45%">
<img src="[https://via.placeholder.com/400x200?text=PDF+Report](https://www.google.com/search?q=https://via.placeholder.com/400x200%3Ftext%3DPDF%2BReport)" alt="PDF Report" width="45%">
</div>

---

## ✨ Key Features

### 🤖 Advanced AI Analysis

* **RoBERTa Model:** Uses a Transformer-based model trained on millions of tweets for accurate sentiment detection (Positive/Negative/Neutral).
* **Context Aware:** Understands nuance (e.g., "I am not happy" is correctly identified as Negative).

### 🔒 Privacy & Security (HIPAA-Compliant Grade)

* **AES Encryption:** All journal entries are encrypted using `cryptography` (Fernet) **before** they are saved to the SQLite database.
* **Secure Auth:** User passwords are hashed using `Bcrypt`.

### 📊 Rich Analytics & Gamification

* **Interactive Dashboard:** View mood trends via **Chart.js** (Doughnut Charts) and a **Word Cloud** of recurring thoughts.
* **Mood Calendar:** Visual heatmap of your monthly emotional journey.
* **Gamification:** Earn badges (e.g., "Positivity Pro", "Night Owl") and track daily streaks.

### 📥 Export & Reporting

* **PDF Reports:** Generate and download professional A4 monthly reports with visual charts for personal reflection or therapy sessions.

---

## ⚙️ Tech Stack

* **Backend:** Python, Flask, Flask-Login, Flask-Bcrypt
* **AI/ML:** Hugging Face `transformers`, PyTorch, RoBERTa
* **Database:** SQLite (with `cryptography` encryption)
* **Frontend:** HTML5, CSS3 (Responsive), JavaScript
* **Visualization:** Chart.js, WordCloud2.js
* **Tools:** HTML2PDF (Report Generation), Dotenv

---

## 🚀 Installation & Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mental-health-ai-journal.git
cd mental-health-ai-journal/backend

```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

*(Note: First run may take time as it downloads the PyTorch/Transformer libraries)*

### 4. Configure Environment Variables

Create a file named `.env` in the `backend/` folder and add the following keys.
You can generate unique keys using a python script or terminal.

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_random_generated_secret_key

# Database Encryption Key (CRITICAL)
# Generate this using: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY=your_generated_fernet_key

```

### 5. Run the Application

```bash
python app.py

```

Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 📂 Project Structure

```
mental-health-ai-journal/
│
├── backend/
│   ├── app.py                 # Main Flask Application
│   ├── journal.db             # Encrypted SQLite Database
│   ├── .env                   # Environment Variables (Ignored by Git)
│   ├── requirements.txt       # Python Dependencies
│   │
│   ├── static/                # CSS, JS, Images
│   │   ├── style.css
│   │   └── script.js
│   │
│   └── templates/             # HTML Templates
│       ├── index.html
│       ├── login.html
│       └── register.html
│
└── README.md

```

---

## 🤝 Future Roadmap

* [ ] **Chatbot Integration:** A conversational AI therapist using LLMs (e.g., Llama 2).
* [ ] **Mobile App:** React Native wrapper for mobile access.
* [ ] **Bio-metrics:** Integration with wearable API data (sleep/heart rate).

---

## 🛡️ License

This project is open-source and available under the **MIT License**.

---

### 👤 Author

**Sawani Weerathunga**

* GitHub: https://github.com/SawaniD-Weerathunga
* LinkedIn: https://www.linkedin.com/in/sawani-weerathunga-507a55348/