#!/usr/bin/env python3
"""
Anesthesia Success Predictor (Final Version)
--------------------------------------------
Dataset: Anesthesia_Cleaned.csv (columns as shown in screenshot)

Features used:
  Age, Gender, BMI, SurgeryType, SurgeryDuration,
  AnesthesiaType, PainLevel, Complications, Notes

Target:
  Outcome (0/1)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

# ========== LOAD DATA ==========
print(" Loading dataset...")
df = pd.read_csv("Anesthesia_Cleaned.csv")

# Drop PatientID if present
if "PatientID" in df.columns:
    df = df.drop(columns=["PatientID"])

# ========== SEPARATE FEATURES AND TARGET ==========
y = df["Outcome"]
X = df.drop(columns=["Outcome"])

# Identify column types
categorical_cols = ["Gender", "SurgeryType", "AnesthesiaType", "Complications"]
numeric_cols = ["Age", "BMI", "SurgeryDuration", "PainLevel"]
text_cols = ["Notes"]

# ========== PREPROCESSING PIPELINE ==========
from sklearn.preprocessing import OneHotEncoder

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

text_transformer = Pipeline(steps=[
    ("tfidf", TfidfVectorizer(max_features=50, stop_words="english"))
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_cols),
        ("cat", categorical_transformer, categorical_cols),
        ("txt", text_transformer, "Notes")
    ],
    remainder="drop"
)


# ========== SPLIT DATA ==========
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ========== DEFINE MODELS ==========
models = {
    "Logistic Regression": LogisticRegression(max_iter=500),
    "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42),
    "XGBoost": XGBClassifier(
        n_estimators=300, learning_rate=0.05, max_depth=6,
        subsample=0.9, colsample_bytree=0.9, random_state=42, eval_metric="logloss"
    ),
}

best_model = None
best_acc = 0

# ========== TRAIN & EVALUATE ==========
for name, model in models.items():
    print(f"\n Training {name}...")
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f" {name} Accuracy: {acc*100:.2f}%")
    print(classification_report(y_test, y_pred))

    if acc > best_acc:
        best_acc = acc
        best_model = pipeline

# ========== SAVE BEST MODEL ==========
print(f"\n Best Model Accuracy: {best_acc*100:.2f}%")
joblib.dump(best_model, "best_anesthesia_model.pkl")
print("Saved best model to best_anesthesia_model.pkl\n")

# ========== PREDICT FROM TERMINAL ==========
print(" Enter new patient details for prediction:\n")
input_data = {}

for col in X.columns:
    if col == "Notes":
        val = input(f"Enter {col} (short summary): ")
    else:
        val = input(f"Enter {col}: ")
    input_data[col] = val

input_df = pd.DataFrame([input_data])

# Predict
prediction = best_model.predict(input_df)[0]
print(f"\n Predicted Outcome: {prediction}")
print(f"\n0 means No complications and 1 Means Complications present")