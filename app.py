import os
import random
import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from predict import FEATURES, model_exists, predict_many, predict_one

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "hospital.db")
CSV_PATH = os.path.join(BASE, "diabetes.csv")

st.set_page_config(page_title="CareLine", page_icon="🏥", layout="wide")

st.markdown("""
<style>
.hero {background:#0f2b33; border-radius:24px; padding:28px 36px; margin-bottom:24px;}
.hero h1 {margin:0; font-size:2.2rem;}
.hero p {margin:6px 0 0 0; color:#9fc7c7;}
div[data-testid="stMetric"] {background:#0f2b33; padding:16px 20px; border-radius:14px;}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Database helpers
# ----------------------------------------------------------------------------
def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def q(sql, params=()):
    """Run a SELECT and return a DataFrame."""
    con = connect()
    try:
        return pd.read_sql(sql, con, params=params)
    finally:
        con.close()


def run(sql, params=()):
    """Run an INSERT / UPDATE / DELETE."""
    con = connect()
    try:
        con.execute(sql, params)
        con.commit()
    finally:
        con.close()


def db_ready():
    if not os.path.exists(DB_PATH):
        return False
    try:
        q("SELECT 1 FROM patients LIMIT 1")
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# Predictions (model lives in predict.py)
# ----------------------------------------------------------------------------
def save_checkup(pid, pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age, actual=None):
    label, prob = predict_one(pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age)
    run("""INSERT INTO checkups
           (patient_id, pregnancies, glucose, blood_pressure, skin_thickness, insulin,
            bmi, pedigree, age, risk_prediction, risk_probability, diabetes_actual)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age,
         label, prob, actual))
    return label, prob


# ----------------------------------------------------------------------------
# Sample data (demo tools)
# ----------------------------------------------------------------------------
def load_sample():
    if not model_exists():
        st.error("model.pkl not found. Run train_model.py first.")
        return
    if not os.path.exists(CSV_PATH):
        st.error("diabetes.csv not found in the project folder.")
        return

    random.seed(1)
    df = pd.read_csv(CSV_PATH)
    names = ["Aisha Khan", "Priya Sharma", "Meera Patel", "Sara Ali", "Neha Gupta",
             "Anita Rao", "Fatima Sheikh", "Kavya Iyer", "Riya Desai", "Sneha Joshi",
             "Pooja Nair", "Zoya Mirza", "Divya Menon", "Isha Kulkarni", "Tara Singh"]
    chk = df.sample(len(names) * 3, random_state=1).reset_index(drop=True)

    con = connect()
    try:
        if con.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            for i, n in enumerate(names):
                con.execute("INSERT INTO patients (name, age, gender, phone) VALUES (?,?,?,?)",
                            (n, int(chk.loc[i * 3, "Age"]), "Female",
                             f"98{random.randint(10000000, 99999999)}"))
        if con.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
            for n, s in [("Dr. Rao", "Endocrinology"), ("Dr. Mehta", "General Medicine"),
                         ("Dr. Iyer", "Cardiology"), ("Dr. Nair", "Gynecology"),
                         ("Dr. Shah", "Nutrition")]:
                con.execute("INSERT INTO doctors (name, specialization, phone) VALUES (?,?,?)",
                            (n, s, f"97{random.randint(10000000, 99999999)}"))
        pids = [r[0] for r in con.execute("SELECT patient_id FROM patients")]
        dids = [r[0] for r in con.execute("SELECT doctor_id FROM doctors")]
        if con.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
            for _ in range(25):
                con.execute("""INSERT INTO appointments
                               (patient_id, doctor_id, appt_date, reason, status)
                               VALUES (?,?,?,?,?)""",
                            (random.choice(pids), random.choice(dids),
                             f"2026-10-{random.randint(1, 28):02d}",
                             random.choice(["Routine checkup", "Follow-up", "Blood test review"]),
                             random.choice(["Scheduled", "Completed", "Cancelled"])))

        labels, probs = predict_many(chk[FEATURES].values.tolist())
        for i, r in chk.iterrows():
            con.execute("""INSERT INTO checkups
                           (patient_id, pregnancies, glucose, blood_pressure, skin_thickness,
                            insulin, bmi, pedigree, age, risk_prediction, risk_probability,
                            diabetes_actual)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (pids[(i // 3) % len(pids)], int(r.Pregnancies), float(r.Glucose),
                         float(r.BloodPressure), float(r.SkinThickness), float(r.Insulin),
                         float(r.BMI), float(r.DiabetesPedigreeFunction), int(r.Age),
                         int(labels[i]), float(probs[i]), int(r.Outcome)))
        con.commit()
    finally:
        con.close()


def clear_checkups():
    run("DELETE FROM checkups")


# ----------------------------------------------------------------------------
# Queries
# ----------------------------------------------------------------------------
def overview_stats():
    return q("""SELECT
        (SELECT COUNT(*) FROM patients) AS patients,
        (SELECT COUNT(*) FROM doctors) AS doctors,
        (SELECT COUNT(*) FROM appointments) AS appts,
        (SELECT COUNT(*) FROM latest_checkup WHERE risk_prediction=1) AS high,
        (SELECT COUNT(*) FROM latest_checkup WHERE risk_prediction IS NOT NULL) AS predicted,
        (SELECT COUNT(*) FROM latest_checkup WHERE diabetes_actual=1) AS diabetes""").iloc[0]


def patient_options():
    df = q("SELECT patient_id, name FROM patients ORDER BY name")
    return {f"{r.name} (#{r.patient_id})": int(r.patient_id) for r in df.itertuples()}


def doctor_options():
    df = q("SELECT doctor_id, name, specialization FROM doctors ORDER BY name")
    return {f"{r.name} - {r.specialization}": int(r.doctor_id) for r in df.itertuples()}


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def page_overview():
    hero("📊 Hospital overview", "Patients, appointments and diabetes risk at a glance")
    sx = overview_stats()

    c1, c2, c3 = st.columns(3)
    c1.metric("Patients", int(sx.patients))
    c2.metric("Doctors", int(sx.doctors))
    c3.metric("Appointments", int(sx.appts))

    c4, c5, c6 = st.columns(3)
    c4.metric("High-risk (predicted)", int(sx.high))
    c5.metric("Patients with a prediction", int(sx.predicted))
    c6.metric("Diabetes (recorded)", int(sx.diabetes))

    left, right = st.columns(2)
    with left:
        st.subheader("Predicted risk")
        risk = q("""SELECT CASE risk_prediction WHEN 1 THEN 'High risk' ELSE 'Low risk' END AS risk,
                           COUNT(*) AS patients
                    FROM latest_checkup WHERE risk_prediction IS NOT NULL GROUP BY risk""")
        if risk.empty:
            st.info("No checkups yet.")
        else:
            st.bar_chart(risk.set_index("risk"))
    with right:
        st.subheader("Appointments by status")
        ap = q("SELECT status, COUNT(*) AS appointments FROM appointments GROUP BY status")
        if ap.empty:
            st.info("No appointments yet.")
        else:
            st.bar_chart(ap.set_index("status"))

    st.subheader("Most recent checkups")
    recent = q("""SELECT c.checkup_id, p.name AS patient, c.glucose, c.bmi, c.age,
                         ROUND(c.risk_probability*100, 1) AS risk_pct,
                         CASE c.risk_prediction WHEN 1 THEN 'High' ELSE 'Low' END AS risk
                  FROM checkups c JOIN patients p ON p.patient_id = c.patient_id
                  ORDER BY c.checkup_id DESC LIMIT 10""")
    st.dataframe(recent, use_container_width=True, hide_index=True)


def page_conditions():
    hero("🫀 Conditions", "Diabetes patterns across age, BMI and glucose (latest checkup per patient)")
    df = q("SELECT * FROM latest_checkup")
    if df.empty:
        st.info("No checkup data yet. Use Load sample data or add a checkup.")
        return

    df["bmi"] = df["bmi"].replace(0, float("nan"))
    df["age_group"] = pd.cut(df["age"], [0, 29, 39, 49, 59, 120],
                             labels=["<30", "30-39", "40-49", "50-59", "60+"])
    df["bmi_category"] = pd.cut(df["bmi"], [0, 18.5, 25, 30, 100],
                                labels=["Underweight", "Normal", "Overweight", "Obese"])

    left, right = st.columns(2)
    with left:
        st.subheader("High-risk share by age group")
        g = df.groupby("age_group", observed=True)["risk_prediction"].mean().mul(100).round(1)
        st.bar_chart(g.rename("% high risk"))
    with right:
        st.subheader("High-risk share by BMI category")
        g = df.groupby("bmi_category", observed=True)["risk_prediction"].mean().mul(100).round(1)
        st.bar_chart(g.rename("% high risk"))

    st.subheader("Average measurements: high vs low risk")
    avg = (df.assign(risk=df["risk_prediction"].map({1: "High risk", 0: "Low risk"}))
             .groupby("risk")[["glucose", "blood_pressure", "bmi", "insulin", "age"]]
             .mean().round(1))
    st.dataframe(avg, use_container_width=True)


def page_patients():
    hero("🧑 Patients", "Register patients and review their history")

    with st.expander("➕ Add a new patient"):
        with st.form("add_patient", clear_on_submit=True):
            name = st.text_input("Full name")
            c1, c2, c3 = st.columns(3)
            age = c1.number_input("Age", 1, 120, 30)
            gender = c2.selectbox("Gender", ["Female", "Male", "Other"])
            phone = c3.text_input("Phone")
            if st.form_submit_button("Save patient"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    run("INSERT INTO patients (name, age, gender, phone) VALUES (?,?,?,?)",
                        (name.strip(), int(age), gender, phone.strip()))
                    st.success(f"Added {name}.")
                    st.rerun()

    search = st.text_input("Search by name")
    df = q("""SELECT p.patient_id, p.name, p.age, p.gender, p.phone,
                     CASE lc.risk_prediction WHEN 1 THEN 'High' WHEN 0 THEN 'Low' ELSE '-' END AS latest_risk
              FROM patients p LEFT JOIN latest_checkup lc ON lc.patient_id = p.patient_id
              WHERE p.name LIKE ? ORDER BY p.name""", (f"%{search}%",))
    st.dataframe(df, use_container_width=True, hide_index=True)

    opts = patient_options()
    if opts:
        st.subheader("Patient history")
        label = st.selectbox("Select a patient", list(opts.keys()))
        pid = opts[label]
        hist = q("""SELECT checkup_id, pregnancies, glucose, blood_pressure, skin_thickness,
                           insulin, bmi, pedigree, age,
                           ROUND(risk_probability*100, 1) AS risk_pct,
                           CASE risk_prediction WHEN 1 THEN 'High' ELSE 'Low' END AS risk
                    FROM checkups WHERE patient_id=? ORDER BY checkup_id DESC""", (pid,))
        st.dataframe(hist, use_container_width=True, hide_index=True)

        with st.expander("🗑️ Delete this patient"):
            st.warning("This also deletes their checkups and appointments.")
            if st.button("Delete patient"):
                run("DELETE FROM checkups WHERE patient_id=?", (pid,))
                run("DELETE FROM appointments WHERE patient_id=?", (pid,))
                run("DELETE FROM patients WHERE patient_id=?", (pid,))
                st.rerun()


def page_doctors():
    hero("🩺 Doctors", "Hospital staff and their workload")

    with st.expander("➕ Add a new doctor"):
        with st.form("add_doctor", clear_on_submit=True):
            name = st.text_input("Name")
            c1, c2 = st.columns(2)
            spec = c1.text_input("Specialization")
            phone = c2.text_input("Phone")
            if st.form_submit_button("Save doctor"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    run("INSERT INTO doctors (name, specialization, phone) VALUES (?,?,?)",
                        (name.strip(), spec.strip(), phone.strip()))
                    st.success(f"Added {name}.")
                    st.rerun()

    df = q("""SELECT d.doctor_id, d.name, d.specialization, d.phone,
                     COUNT(a.appointment_id) AS appointments
              FROM doctors d LEFT JOIN appointments a ON a.doctor_id = d.doctor_id
              GROUP BY d.doctor_id ORDER BY d.name""")
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_appointments():
    hero("📅 Appointments", "Book and manage appointments")

    pats, docs = patient_options(), doctor_options()
    if not pats or not docs:
        st.info("Add at least one patient and one doctor first.")
    else:
        with st.expander("➕ Book an appointment"):
            with st.form("book_appt", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p = c1.selectbox("Patient", list(pats.keys()))
                d = c2.selectbox("Doctor", list(docs.keys()))
                c3, c4 = st.columns(2)
                when = c3.date_input("Date", date.today())
                reason = c4.text_input("Reason", "Routine checkup")
                if st.form_submit_button("Book"):
                    run("""INSERT INTO appointments (patient_id, doctor_id, appt_date, reason, status)
                           VALUES (?,?,?,?, 'Scheduled')""",
                        (pats[p], docs[d], when.isoformat(), reason))
                    st.success("Appointment booked.")
                    st.rerun()

    status = st.selectbox("Filter by status", ["All", "Scheduled", "Completed", "Cancelled"])
    sql = """SELECT a.appointment_id, p.name AS patient, d.name AS doctor,
                    a.appt_date, a.reason, a.status
             FROM appointments a
             JOIN patients p ON p.patient_id = a.patient_id
             JOIN doctors d ON d.doctor_id = a.doctor_id"""
    params = ()
    if status != "All":
        sql += " WHERE a.status = ?"
        params = (status,)
    sql += " ORDER BY a.appt_date DESC"
    df = q(sql, params)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        st.subheader("Update status")
        c1, c2, c3 = st.columns([1, 1, 1])
        appt_id = c1.selectbox("Appointment ID", df["appointment_id"].tolist())
        new_status = c2.selectbox("New status", ["Scheduled", "Completed", "Cancelled"])
        c3.write("")
        c3.write("")
        if c3.button("Update"):
            run("UPDATE appointments SET status=? WHERE appointment_id=?",
                (new_status, int(appt_id)))
            st.rerun()


def page_checkup():
    hero("🧪 Checkup & Risk", "Enter measurements and predict diabetes risk")

    if not model_exists():
        st.error("model.pkl not found. Run train_model.py first.")
        return
    pats = patient_options()
    if not pats:
        st.info("Add a patient first.")
        return

    with st.form("checkup_form"):
        label = st.selectbox("Patient", list(pats.keys()))
        c1, c2, c3, c4 = st.columns(4)
        preg = c1.number_input("Pregnancies", 0, 20, 1)
        glucose = c2.number_input("Glucose (mg/dL)", 0.0, 300.0, 110.0)
        bp = c3.number_input("Blood pressure (mm Hg)", 0.0, 200.0, 72.0)
        skin = c4.number_input("Skin thickness (mm)", 0.0, 100.0, 20.0)
        c5, c6, c7, c8 = st.columns(4)
        insulin = c5.number_input("Insulin (mu U/ml)", 0.0, 900.0, 80.0)
        bmi = c6.number_input("BMI", 0.0, 70.0, 27.0)
        pedigree = c7.number_input("Pedigree function", 0.0, 3.0, 0.4, step=0.01)
        age = c8.number_input("Age", 1, 120, 35)
        st.caption("A value of 0 for glucose, blood pressure, skin thickness, insulin or BMI "
                   "is treated as 'not measured'.")
        submitted = st.form_submit_button("Predict and save")

    if submitted:
        pid = pats[label]
        pred, prob = save_checkup(pid, int(preg), float(glucose), float(bp), float(skin),
                                  float(insulin), float(bmi), float(pedigree), int(age))
        if pred == 1:
            st.error(f"High risk of diabetes ({prob * 100:.1f}%)")
        else:
            st.success(f"Low risk of diabetes ({prob * 100:.1f}%)")
        st.caption("Educational project. Predictions are not medical advice.")

    st.subheader("Recent checkups")
    recent = q("""SELECT c.checkup_id, p.name AS patient, c.glucose, c.bmi, c.age,
                         ROUND(c.risk_probability*100, 1) AS risk_pct,
                         CASE c.risk_prediction WHEN 1 THEN 'High' ELSE 'Low' END AS risk
                  FROM checkups c JOIN patients p ON p.patient_id = c.patient_id
                  ORDER BY c.checkup_id DESC LIMIT 15""")
    st.dataframe(recent, use_container_width=True, hide_index=True)


def page_reports():
    hero("📝 Reports", "High-risk patients, exports and model evaluation")

    st.subheader("High-risk patients (latest checkup)")
    high = q("""SELECT p.name, p.phone, lc.age, lc.glucose, lc.bmi,
                       ROUND(lc.risk_probability*100, 1) AS risk_pct
                FROM latest_checkup lc JOIN patients p ON p.patient_id = lc.patient_id
                WHERE lc.risk_prediction = 1 ORDER BY lc.risk_probability DESC""")
    st.dataframe(high, use_container_width=True, hide_index=True)

    st.subheader("Export")
    full = q("""SELECT p.name AS patient, c.* FROM checkups c
                JOIN patients p ON p.patient_id = c.patient_id""")
    c1, c2 = st.columns(2)
    c1.download_button("Download all checkups (CSV)", full.to_csv(index=False),
                       "checkups.csv", "text/csv")
    c2.download_button("Download high-risk list (CSV)", high.to_csv(index=False),
                       "high_risk_patients.csv", "text/csv")

    st.subheader("Model evaluation")
    a, b = st.columns(2)
    if os.path.exists(os.path.join(BASE, "confusion_matrix.png")):
        a.image(os.path.join(BASE, "confusion_matrix.png"), caption="Confusion matrix")
    if os.path.exists(os.path.join(BASE, "feature_importance.png")):
        b.image(os.path.join(BASE, "feature_importance.png"), caption="Feature importance")
    if not (os.path.exists(os.path.join(BASE, "confusion_matrix.png")) or os.path.exists(os.path.join(BASE, "feature_importance.png"))):
        st.info("Run evaluate.py to generate the evaluation charts.")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
PAGES = {
    "📊 Overview": page_overview,
    "🫀 Conditions": page_conditions,
    "🧑 Patients": page_patients,
    "🩺 Doctors": page_doctors,
    "📅 Appointments": page_appointments,
    "🧪 Checkup & Risk": page_checkup,
    "📝 Reports": page_reports,
}

st.sidebar.markdown("## CareLine")

if not db_ready():
    st.error("hospital.db is missing or has no tables. Run `python init_db.py` first.")
    st.stop()

choice = st.sidebar.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

with st.sidebar.expander("Demo tools"):
    if st.button("Load sample data"):
        load_sample()
        st.rerun()
    if st.button("Clear all checkups"):
        clear_checkups()
        st.rerun()

st.sidebar.caption("Educational project. Predictions are not medical advice.")

if q("SELECT COUNT(*) AS n FROM patients").iloc[0, 0] == 0:
    st.sidebar.info("The database is empty.")

PAGES[choice]()
