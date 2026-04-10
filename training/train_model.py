import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

#load dataset
df = pd.read_csv("Reviews.csv")

#features and labels
X = df["reviews.text"]
y = df["review_label"]

#convert text into numerical features
vectorizer = TfidfVectorizer(stop_words="english")
X_vec = vectorizer.fit_transform(X)

#split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

#train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

#test accuracy
y_pred = model.predict(X_test)
print("model accuracy:", accuracy_score(y_test, y_pred))

#save model and vectorized
joblib.dump(model, "models/fake_review_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

print("model trained and saved successfully")

review = ["battery life is good and camera is sharp"]
vec = vectorizer.transform(review)
print(model.predict(vec))
