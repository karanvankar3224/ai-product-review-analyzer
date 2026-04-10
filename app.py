# ------------------------------
# IMPORTS
# ------------------------------
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import pandas as pd
from transformers import pipeline
import joblib
import certifi
from pymongo import MongoClient
import bcrypt
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ------------------------------
# APP INIT
# ------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_123'

# ------------------------------
# LOAD ENV VARIABLES
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")

load_dotenv(env_path)

mongo_uri = os.environ.get("MONGO_URI")
print("MONGO URI:", mongo_uri)

if not mongo_uri:
    raise ValueError("❌ MONGO_URI not found. Check your .env file")

# ------------------------------
# RATE LIMITER (FIXED)
# ------------------------------
limiter = Limiter(get_remote_address, app=app)

# ------------------------------
# MONGODB CONNECTION
# ------------------------------
client = MongoClient(mongo_uri, tlsCAfile=certifi.where())
db = client['ai_product_app']

# Collections
users_collection = db['users']
search_collection = db['search_history']
intrest_collection = db['users_intrests']

# ------------------------------
# LOAD DATASET
# ------------------------------
df = pd.read_csv("Reviews.csv")
df = df.sample(frac=1).reset_index(drop=True)
df["name"] = df["name"].astype(str)

# ------------------------------
# LOAD AI MODELS
# ------------------------------
sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

fake_model = joblib.load("models/fake_review_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

# ------------------------------
# ROUTES
# ------------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/home")
    return redirect("/login-page")

@app.route("/home")
def main_page():
    if "user_id" not in session:
        return redirect("/login-page")
    return render_template("index.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

# TEST DB:-
@app.route("/test-db")
def test_db():
    users_collection.insert_one({"test": "working"})
    return {"message": "MongoDB Connected Successfully"}
# ------------------------------
# PROFILE
# ------------------------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login-page')
    
    user_data = users_collection.find_one({'_id': ObjectId(session['user_id'])})

    joined_date = user_data.get('created_at')
    if joined_date:
        joined_date = joined_date.strftime("%d %b %Y")
    else:
        joined_date = "N/A"

    user = {
        'name': user_data['name'],
        'email': user_data['email'],
        'joined': joined_date
    }

    return render_template("profile.html", user=user)

# ------------------------------
# LOGOUT
# ------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login-page')

# ------------------------------
# SIGNUP
# ------------------------------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    name = data['name']
    email = data['email']
    password = data['password']

    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'User already exists'})

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    users_collection.insert_one({
        'name': name,
        'email': email,
        'password': hashed_password,
        'created_at': datetime.now()   # ✅ FIXED
    })

    return jsonify({'message': 'User registered successfully'})

# ------------------------------
# LOGIN
# ------------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = users_collection.find_one({'email': data['email']})

    if not user:
        return jsonify({'error': 'User not found'})
    
    if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        session['user_id'] = str(user['_id'])

        return jsonify({
            'message': 'Login successful',
            'userId': str(user['_id']),
            'name': user['name']
        })

    return jsonify({'error': 'Invalid password'})

# ------------------------------
# ANALYZE
# ------------------------------
@app.route("/analyze", methods=["POST"])
@limiter.limit("10 per minute")
def analyze():

    if "user_id" not in session:
        return jsonify({"error": "Please log in first"})

    data = request.json
    keyword = data.get("product", "")[:50].strip().lower()
    user_id = data.get('userId')

    reviews = df[df["name"].str.lower().str.contains(keyword, na=False)]

    if reviews.empty:
        return jsonify({"error": "No matching product reviews found"})

    texts = reviews["reviews.text"].dropna().sample(n=min(120, len(reviews))).tolist()
    texts = [t[:512] for t in texts]

    real_reviews = []
    fake_count = 0

    for review in texts:
        vec = vectorizer.transform([review])
        prediction = fake_model.predict(vec)[0]

        if prediction == "fake":
            fake_count += 1
        else:
            real_reviews.append(review)

    if not real_reviews:
        return jsonify({"error": "All reviews detected as fake"})

    results = sentiment_model(real_reviews)

    positive = sum(1 for r in results if r["label"] == "POSITIVE")
    negative = len(results) - positive

    total = positive + negative

    positive_percent = int((positive / total) * 100)
    negative_percent = int((negative / total) * 100)

    if user_id:
        search_collection.insert_one({
            'userId': user_id,
            'product': keyword,
            'searchedAt': datetime.now()
        })

        intrest_collection.update_one(
            {'userId': user_id},
            {'$addToSet': {'keywords': keyword}},
            upsert=True
        )

    return jsonify({
        "trust": positive_percent,
        "positive": positive_percent,
        "negative": negative_percent,
        "total_reviews": total,
        "fake_reviews": fake_count,
        "real_reviews": len(real_reviews)
    })

# ------------------------------
# RUN
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)