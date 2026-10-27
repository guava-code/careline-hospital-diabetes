"""Prediction helper. Import it (app.py does) or run it from the command line (main.cpp does):

    python predict.py <pregnancies> <glucose> <bp> <skin> <insulin> <bmi> <pedigree> <age>

The command-line form prints:  <label> <probability>
"""
import os
import sys

import joblib
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "model.pkl")

FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
ZERO_IS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]

_model = None


def model_exists():
    return os.path.exists(MODEL_PATH)


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def build_frame(rows):
    """rows: list of 8-value lists in FEATURES order."""
    X = pd.DataFrame(rows, columns=FEATURES)
    X[ZERO_IS_MISSING] = X[ZERO_IS_MISSING].replace(0, float("nan"))
    return X


def predict_many(rows):
    """Returns (labels, probabilities) for a list of 8-value rows."""
    m = _get_model()
    X = build_frame(rows)
    return m.predict(X), m.predict_proba(X)[:, 1]


def predict_one(pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age):
    labels, probs = predict_many([[pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age]])
    return int(labels[0]), float(probs[0])


if __name__ == "__main__":
    if len(sys.argv) != 9:
        sys.exit("usage: python predict.py preg glucose bp skin insulin bmi pedigree age")
    label, prob = predict_one(*[float(a) for a in sys.argv[1:]])
    print(label, f"{prob:.4f}")
