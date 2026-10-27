"""Creates a fresh hospital.db with all tables, indexes and the latest_checkup view."""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "hospital.db")

SCHEMA = """
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    age        INTEGER,
    gender     TEXT,
    phone      TEXT
);

CREATE TABLE doctors (
    doctor_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    specialization TEXT,
    phone          TEXT
);

CREATE TABLE appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(patient_id),
    doctor_id      INTEGER NOT NULL REFERENCES doctors(doctor_id),
    appt_date      TEXT,
    reason         TEXT,
    status         TEXT DEFAULT 'Scheduled'
);

CREATE TABLE checkups (
    checkup_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id),
    pregnancies      INTEGER,
    glucose          REAL,
    blood_pressure   REAL,
    skin_thickness   REAL,
    insulin          REAL,
    bmi              REAL,
    pedigree         REAL,
    age              INTEGER,
    risk_prediction  INTEGER,
    risk_probability REAL,
    diabetes_actual  INTEGER
);

CREATE INDEX idx_chk_patient  ON checkups(patient_id);
CREATE INDEX idx_chk_risk     ON checkups(risk_prediction);
CREATE INDEX idx_appt_patient ON appointments(patient_id);
CREATE INDEX idx_appt_doctor  ON appointments(doctor_id);

CREATE VIEW latest_checkup AS
SELECT * FROM checkups c
WHERE c.checkup_id = (SELECT MAX(checkup_id) FROM checkups WHERE patient_id = c.patient_id);
"""

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    print("hospital.db created at", DB_PATH)
