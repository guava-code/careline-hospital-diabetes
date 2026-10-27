// CareLine - console hospital management with diabetes risk prediction.
// Shares hospital.db with the Streamlit website (app.py).
// Prediction is done by calling predict.py, so the C++ and web versions use the same model.
//
// Build:  gcc -c sqlite3.c -o sqlite3.o
//         g++ main.cpp sqlite3.o -o hospital.exe
// Run from the project folder:  hospital.exe

#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include "sqlite3.h"

#ifdef _WIN32
#define POPEN _popen
#define PCLOSE _pclose
#define PYTHON "python"
#else
#define POPEN popen
#define PCLOSE pclose
#define PYTHON "python3"
#endif

using namespace std;

static sqlite3 *db = nullptr;

// ---------- input helpers ----------
static string readLine(const string &prompt) {
    cout << prompt;
    string s;
    getline(cin, s);
    return s;
}

static int readInt(const string &prompt, int lo, int hi) {
    while (true) {
        string s = readLine(prompt);
        try {
            size_t pos;
            int v = stoi(s, &pos);
            if (pos == s.size() && v >= lo && v <= hi) return v;
        } catch (...) {}
        cout << "  Enter a whole number between " << lo << " and " << hi << ".\n";
    }
}

static double readDouble(const string &prompt, double lo, double hi) {
    while (true) {
        string s = readLine(prompt);
        try {
            size_t pos;
            double v = stod(s, &pos);
            if (pos == s.size() && v >= lo && v <= hi) return v;
        } catch (...) {}
        cout << "  Enter a number between " << lo << " and " << hi << ".\n";
    }
}

// ---------- database helpers ----------
static bool execSql(const string &sql) {
    char *err = nullptr;
    if (sqlite3_exec(db, sql.c_str(), nullptr, nullptr, &err) != SQLITE_OK) {
        cerr << "SQL error: " << err << "\n";
        sqlite3_free(err);
        return false;
    }
    return true;
}

static string col(sqlite3_stmt *st, int i) {
    const unsigned char *t = sqlite3_column_text(st, i);
    return t ? string(reinterpret_cast<const char *>(t)) : string("-");
}

static void printRows(sqlite3_stmt *st, const char *header) {
    cout << "\n" << header << "\n";
    int n = 0;
    while (sqlite3_step(st) == SQLITE_ROW) {
        int cols = sqlite3_column_count(st);
        for (int i = 0; i < cols; i++) cout << col(st, i) << (i + 1 < cols ? " | " : "\n");
        n++;
    }
    if (n == 0) cout << "(no records)\n";
    sqlite3_finalize(st);
}

static void query(const string &sql, const char *header) {
    sqlite3_stmt *st;
    if (sqlite3_prepare_v2(db, sql.c_str(), -1, &st, nullptr) != SQLITE_OK) {
        cerr << "SQL error: " << sqlite3_errmsg(db) << "\n";
        return;
    }
    printRows(st, header);
}

static bool exists(const string &table, const string &idCol, int id) {
    string sql = "SELECT 1 FROM " + table + " WHERE " + idCol + "=?";
    sqlite3_stmt *st;
    sqlite3_prepare_v2(db, sql.c_str(), -1, &st, nullptr);
    sqlite3_bind_int(st, 1, id);
    bool ok = sqlite3_step(st) == SQLITE_ROW;
    sqlite3_finalize(st);
    return ok;
}

// ---------- patients ----------
static void addPatient() {
    string name = readLine("Name: ");
    if (name.empty()) { cout << "Name is required.\n"; return; }
    int age = readInt("Age: ", 1, 120);
    string gender = readLine("Gender (Female/Male/Other): ");
    string phone = readLine("Phone: ");

    sqlite3_stmt *st;
    sqlite3_prepare_v2(db, "INSERT INTO patients (name, age, gender, phone) VALUES (?,?,?,?)",
                       -1, &st, nullptr);
    sqlite3_bind_text(st, 1, name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(st, 2, age);
    sqlite3_bind_text(st, 3, gender.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(st, 4, phone.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(st) == SQLITE_DONE)
        cout << "Patient added with ID " << sqlite3_last_insert_rowid(db) << ".\n";
    else
        cerr << "Failed: " << sqlite3_errmsg(db) << "\n";
    sqlite3_finalize(st);
}

static void listPatients() {
    query("SELECT patient_id, name, age, gender, phone FROM patients ORDER BY patient_id",
          "ID | Name | Age | Gender | Phone");
}

// ---------- doctors ----------
static void addDoctor() {
    string name = readLine("Name: ");
    if (name.empty()) { cout << "Name is required.\n"; return; }
    string spec = readLine("Specialization: ");
    string phone = readLine("Phone: ");

    sqlite3_stmt *st;
    sqlite3_prepare_v2(db, "INSERT INTO doctors (name, specialization, phone) VALUES (?,?,?)",
                       -1, &st, nullptr);
    sqlite3_bind_text(st, 1, name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(st, 2, spec.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(st, 3, phone.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(st) == SQLITE_DONE)
        cout << "Doctor added with ID " << sqlite3_last_insert_rowid(db) << ".\n";
    else
        cerr << "Failed: " << sqlite3_errmsg(db) << "\n";
    sqlite3_finalize(st);
}

static void listDoctors() {
    query("SELECT doctor_id, name, specialization, phone FROM doctors ORDER BY doctor_id",
          "ID | Name | Specialization | Phone");
}

// ---------- appointments ----------
static void bookAppointment() {
    int pid = readInt("Patient ID: ", 1, 1000000);
    if (!exists("patients", "patient_id", pid)) { cout << "No such patient.\n"; return; }
    int did = readInt("Doctor ID: ", 1, 1000000);
    if (!exists("doctors", "doctor_id", did)) { cout << "No such doctor.\n"; return; }
    string date = readLine("Date (YYYY-MM-DD): ");
    string reason = readLine("Reason: ");

    sqlite3_stmt *st;
    sqlite3_prepare_v2(db,
        "INSERT INTO appointments (patient_id, doctor_id, appt_date, reason, status) "
        "VALUES (?,?,?,?, 'Scheduled')", -1, &st, nullptr);
    sqlite3_bind_int(st, 1, pid);
    sqlite3_bind_int(st, 2, did);
    sqlite3_bind_text(st, 3, date.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(st, 4, reason.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(st) == SQLITE_DONE)
        cout << "Appointment booked (ID " << sqlite3_last_insert_rowid(db) << ").\n";
    else
        cerr << "Failed: " << sqlite3_errmsg(db) << "\n";
    sqlite3_finalize(st);
}

static void listAppointments() {
    query("SELECT a.appointment_id, p.name, d.name, a.appt_date, a.reason, a.status "
          "FROM appointments a JOIN patients p ON p.patient_id=a.patient_id "
          "JOIN doctors d ON d.doctor_id=a.doctor_id ORDER BY a.appt_date DESC",
          "ID | Patient | Doctor | Date | Reason | Status");
}

static void updateAppointmentStatus() {
    int id = readInt("Appointment ID: ", 1, 1000000);
    if (!exists("appointments", "appointment_id", id)) { cout << "No such appointment.\n"; return; }
    int c = readInt("New status (1=Scheduled, 2=Completed, 3=Cancelled): ", 1, 3);
    const char *status[] = {"", "Scheduled", "Completed", "Cancelled"};

    sqlite3_stmt *st;
    sqlite3_prepare_v2(db, "UPDATE appointments SET status=? WHERE appointment_id=?",
                       -1, &st, nullptr);
    sqlite3_bind_text(st, 1, status[c], -1, SQLITE_STATIC);
    sqlite3_bind_int(st, 2, id);
    sqlite3_step(st);
    sqlite3_finalize(st);
    cout << "Status updated.\n";
}

// ---------- checkups and prediction ----------
static bool runPrediction(double v[8], int &label, double &prob) {
    ostringstream cmd;
    cmd << PYTHON << " predict.py";
    for (int i = 0; i < 8; i++) cmd << " " << v[i];
#ifdef _WIN32
    cmd << " 2>nul";
#else
    cmd << " 2>/dev/null";
#endif
    FILE *pipe = POPEN(cmd.str().c_str(), "r");
    if (!pipe) return false;
    char buf[128];
    bool ok = false;
    if (fgets(buf, sizeof buf, pipe)) ok = sscanf(buf, "%d %lf", &label, &prob) == 2;
    PCLOSE(pipe);
    return ok;
}

static void recordCheckup() {
    int pid = readInt("Patient ID: ", 1, 1000000);
    if (!exists("patients", "patient_id", pid)) { cout << "No such patient.\n"; return; }

    double v[8];
    v[0] = readInt("Pregnancies (0-20): ", 0, 20);
    v[1] = readDouble("Glucose mg/dL (0 = not measured): ", 0, 300);
    v[2] = readDouble("Blood pressure mm Hg (0 = not measured): ", 0, 200);
    v[3] = readDouble("Skin thickness mm (0 = not measured): ", 0, 100);
    v[4] = readDouble("Insulin mu U/ml (0 = not measured): ", 0, 900);
    v[5] = readDouble("BMI (0 = not measured): ", 0, 70);
    v[6] = readDouble("Diabetes pedigree function (0-3): ", 0, 3);
    v[7] = readInt("Age: ", 1, 120);

    int label = 0;
    double prob = 0;
    if (!runPrediction(v, label, prob)) {
        cout << "Prediction failed. Check that model.pkl exists (run train_model.py) and that\n"
             << "'" << PYTHON << "' works, and run hospital.exe from the project folder.\n";
        return;
    }

    sqlite3_stmt *st;
    sqlite3_prepare_v2(db,
        "INSERT INTO checkups (patient_id, pregnancies, glucose, blood_pressure, skin_thickness, "
        "insulin, bmi, pedigree, age, risk_prediction, risk_probability) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", -1, &st, nullptr);
    sqlite3_bind_int(st, 1, pid);
    sqlite3_bind_int(st, 2, (int)v[0]);
    for (int i = 1; i <= 6; i++) sqlite3_bind_double(st, i + 2, v[i]);
    sqlite3_bind_int(st, 9, (int)v[7]);
    sqlite3_bind_int(st, 10, label);
    sqlite3_bind_double(st, 11, prob);
    if (sqlite3_step(st) != SQLITE_DONE) cerr << "Failed: " << sqlite3_errmsg(db) << "\n";
    sqlite3_finalize(st);

    cout << "\nResult: " << (label ? "HIGH risk" : "LOW risk") << " of diabetes ("
         << prob * 100 << "%)\n"
         << "Educational project. Predictions are not medical advice.\n";
}

static void patientHistory() {
    int pid = readInt("Patient ID: ", 1, 1000000);
    string sql =
        "SELECT checkup_id, glucose, bmi, age, ROUND(risk_probability*100,1) || '%', "
        "CASE risk_prediction WHEN 1 THEN 'High' ELSE 'Low' END "
        "FROM checkups WHERE patient_id=" + to_string(pid) + " ORDER BY checkup_id DESC";
    query(sql, "Checkup | Glucose | BMI | Age | Risk % | Risk");
}

static void highRiskReport() {
    query("SELECT p.patient_id, p.name, p.phone, ROUND(l.risk_probability*100,1) || '%' "
          "FROM latest_checkup l JOIN patients p ON p.patient_id=l.patient_id "
          "WHERE l.risk_prediction=1 ORDER BY l.risk_probability DESC",
          "ID | Name | Phone | Risk (latest checkup)");
}

static void summary() {
    sqlite3_stmt *st;
    sqlite3_prepare_v2(db,
        "SELECT (SELECT COUNT(*) FROM patients), (SELECT COUNT(*) FROM doctors), "
        "(SELECT COUNT(*) FROM appointments), "
        "(SELECT COUNT(*) FROM latest_checkup WHERE risk_prediction=1)", -1, &st, nullptr);
    if (sqlite3_step(st) == SQLITE_ROW)
        cout << "\nPatients: " << sqlite3_column_int(st, 0)
             << " | Doctors: " << sqlite3_column_int(st, 1)
             << " | Appointments: " << sqlite3_column_int(st, 2)
             << " | High-risk patients: " << sqlite3_column_int(st, 3) << "\n";
    sqlite3_finalize(st);
}

// ---------- menu ----------
static void menu() {
    cout << "\n===== CareLine Hospital Management =====\n"
         << " 1. Add patient            2. List patients\n"
         << " 3. Add doctor             4. List doctors\n"
         << " 5. Book appointment       6. List appointments\n"
         << " 7. Update appt status     8. Record checkup + predict risk\n"
         << " 9. Patient checkup history 10. High-risk patients\n"
         << "11. Summary                 0. Exit\n";
}

int main() {
    if (sqlite3_open("hospital.db", &db) != SQLITE_OK) {
        cerr << "Cannot open hospital.db: " << sqlite3_errmsg(db) << "\n";
        return 1;
    }
    execSql("PRAGMA foreign_keys = ON");

    // Make sure the schema exists (run init_db.py first if this fails)
    sqlite3_stmt *chk;
    sqlite3_prepare_v2(db, "SELECT 1 FROM sqlite_master WHERE name='checkups'", -1, &chk, nullptr);
    bool ready = sqlite3_step(chk) == SQLITE_ROW;
    sqlite3_finalize(chk);
    if (!ready) {
        cerr << "hospital.db has no tables. Run:  python init_db.py\n";
        sqlite3_close(db);
        return 1;
    }

    while (true) {
        menu();
        int c = readInt("Choice: ", 0, 11);
        switch (c) {
            case 1: addPatient(); break;
            case 2: listPatients(); break;
            case 3: addDoctor(); break;
            case 4: listDoctors(); break;
            case 5: bookAppointment(); break;
            case 6: listAppointments(); break;
            case 7: updateAppointmentStatus(); break;
            case 8: recordCheckup(); break;
            case 9: patientHistory(); break;
            case 10: highRiskReport(); break;
            case 11: summary(); break;
            case 0: sqlite3_close(db); cout << "Goodbye.\n"; return 0;
        }
    }
}
