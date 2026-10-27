"""Evaluates model.pkl on a held-out split and saves confusion_matrix.png and feature_importance.png."""
import os
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             roc_auc_score)
from sklearn.model_selection import train_test_split

BASE = os.path.dirname(os.path.abspath(__file__))
FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
ZERO_IS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]

df = pd.read_csv(os.path.join(BASE, "diabetes.csv"))
df[ZERO_IS_MISSING] = df[ZERO_IS_MISSING].replace(0, float("nan"))
X, y = df[FEATURES], df["Outcome"]
# Same split settings as train_model.py, so this is the held-out 20%
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = joblib.load(os.path.join(BASE, "model.pkl"))
pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]

print("Accuracy:", round(accuracy_score(y_test, pred), 3))
print("ROC AUC :", round(roc_auc_score(y_test, proba), 3))
print(classification_report(y_test, pred, target_names=["No diabetes", "Diabetes"]))

fig, ax = plt.subplots(figsize=(5, 4))
ConfusionMatrixDisplay.from_predictions(y_test, pred, display_labels=["No", "Yes"],
                                        cmap="Blues", ax=ax)
ax.set_title("Confusion matrix (test set)")
fig.tight_layout()
fig.savefig(os.path.join(BASE, "confusion_matrix.png"), dpi=150)

imp = pd.Series(model.named_steps["rf"].feature_importances_, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(6, 4))
imp.plot.barh(ax=ax, color="#2a9d8f")
ax.set_title("Feature importance")
fig.tight_layout()
fig.savefig(os.path.join(BASE, "feature_importance.png"), dpi=150)
print("saved confusion_matrix.png and feature_importance.png")
