"""Fills hospital.db with sample patients, doctors, appointments and real checkups from diabetes.csv.
Run order:  train_model.py -> init_db.py -> seed_data.py
"""
import os
import random
import sqlite3

import pandas as pd

from predict import FEATURES, predict_many

BASE = os.path.dirname(os.path.abspath(__file__))
random.seed(1)

NAMES = ["Aisha Khan", "Priya Sharma", "Meera Patel", "Sara Ali", "Neha Gupta",
         "Anita Rao", "Fatima Sheikh", "Kavya Iyer", "Riya Desai", "Sneha Joshi",
         "Pooja Nair", "Zoya Mirza", "Divya Menon", "Isha Kulkarni", "Tara Singh"]
DOCTORS = [("Dr. Rao", "Endocrinology"), ("Dr. Mehta", "General Medicine"),
           ("Dr. Iyer", "Cardiology"), ("Dr. Nair", "Gynecology"), ("Dr. Shah", "Nutrition")]

df = pd.read_csv(os.path.join(BASE, "diabetes.csv"))
chk = df.sample(len(NAMES) * 3, random_state=1).reset_index(drop=True)  # 3 checkups each

con = sqlite3.connect(os.path.join(BASE, "hospital.db"))

for i, name in enumerate(NAMES):
    con.execute("INSERT INTO patients (name, age, gender, phone) VALUES (?,?,?,?)",
                (name, int(chk.loc[i * 3, "Age"]), "Female", f"98{random.randint(10000000, 99999999)}"))

for name, spec in DOCTORS:
    con.execute("INSERT INTO doctors (name, specialization, phone) VALUES (?,?,?)",
                (name, spec, f"97{random.randint(10000000, 99999999)}"))

for _ in range(25):
    con.execute("""INSERT INTO appointments (patient_id, doctor_id, appt_date, reason, status)
                   VALUES (?,?,?,?,?)""",
                (random.randint(1, len(NAMES)), random.randint(1, len(DOCTORS)),
                 f"2026-10-{random.randint(1, 28):02d}",
                 random.choice(["Routine checkup", "Follow-up", "Blood test review"]),
                 random.choice(["Scheduled", "Completed", "Cancelled"])))

labels, probs = predict_many(chk[FEATURES].values.tolist())
for i, r in chk.iterrows():
    con.execute("""INSERT INTO checkups
        (patient_id, pregnancies, glucose, blood_pressure, skin_thickness, insulin,
         bmi, pedigree, age, risk_prediction, risk_probability, diabetes_actual)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (i // 3 + 1, int(r.Pregnancies), float(r.Glucose), float(r.BloodPressure),
         float(r.SkinThickness), float(r.Insulin), float(r.BMI),
         float(r.DiabetesPedigreeFunction), int(r.Age),
         int(labels[i]), float(probs[i]), int(r.Outcome)))

con.commit()
for t in ("patients", "doctors", "appointments", "checkups"):
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
con.close()
