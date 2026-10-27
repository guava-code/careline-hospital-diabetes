"""Trains the diabetes risk model on diabetes.csv (Pima dataset) and saves model.pkl."""
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

BASE = os.path.dirname(os.path.abspath(__file__))
FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
# In this dataset a 0 in these columns means "not measured"
ZERO_IS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]

df = pd.read_csv(os.path.join(BASE, "diabetes.csv"))
df[ZERO_IS_MISSING] = df[ZERO_IS_MISSING].replace(0, float("nan"))

X, y = df[FEATURES], df["Outcome"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

model = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("rf", RandomForestClassifier(n_estimators=300, max_depth=6,
                                  class_weight="balanced", random_state=42)),
])
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test),
                            target_names=["No diabetes", "Diabetes"]))

joblib.dump(model, os.path.join(BASE, "model.pkl"))
print("saved model.pkl")
