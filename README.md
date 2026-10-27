# careline-hospital-diabetes[README.md](https://github.com/user-attachments/files/34003228/README.md)
# CareLine: Hospital Management with Diabetes Risk Prediction

CareLine is a DBMS course project that combines a small hospital database with a machine learning model that estimates a patient's risk of diabetes. It has two front ends that share the same database and the same model:

- **A Streamlit web app** (`app.py`) with pages for an overview, conditions, patients, doctors, appointments, checkups and risk prediction, and reports.
- **A C++ console app** (`main.cpp`) that uses SQLite directly for the same data and calls `predict.py` for risk predictions.

The database is a SQLite file (`hospital.db`) with four tables (`patients`, `doctors`, `appointments`, `checkups`), indexes, and a `latest_checkup` view. The risk model is a Random Forest classifier trained with scikit-learn.

> Predictions are for educational purposes only and are not medical advice.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit website |
| `main.cpp` | C++ console application |
| `init_db.py` | Creates an empty `hospital.db` with the schema |
| `seed_data.py` | Fills the database with sample patients, doctors, appointments and checkups |
| `train_model.py` | Trains the model and saves `model.pkl` |
| `evaluate.py` | Evaluates the model and saves `confusion_matrix.png` and `feature_importance.png` |
| `predict.py` | Prediction helper used by both front ends |
| `diabetes.csv` | Training and seed data (see below) |
| `run_all.bat` | One-time setup for Windows |
| `build.bat` | Builds the C++ app into `hospital.exe` |
| `sqlite3.c`, `sqlite3.h` | SQLite amalgamation, compiled into the C++ app |
| `requirements.txt` | Python dependencies |

## Requirements

- Python 3.9 or newer, with `python` available on the command line
- For the C++ app only: MinGW (`gcc` and `g++`) on the PATH

## How to run it (Windows)

### 1. Set up the project (once)

Open a terminal in the project folder and run:

```bat
run_all.bat
```

This installs the Python packages in `requirements.txt`, trains the model, creates `hospital.db`, fills it with sample data, and generates the evaluation charts. It only needs to run once, or again if you delete `hospital.db` or `model.pkl`.

### 2. Start the website

```bat
streamlit run app.py
```

Streamlit prints a local address (usually `http://localhost:8501`). Open it in your browser.

### 3. (Optional) Build and run the C++ console app

```bat
build.bat
hospital.exe
```

`build.bat` compiles `sqlite3.c` once into `sqlite3.o`, then builds `hospital.exe`. Run `hospital.exe` from the project folder so it can find `hospital.db` and `predict.py`. The app calls `python predict.py` to get predictions, so Python must be on the PATH.

## The dataset

The data comes from the **Pima Indians Diabetes Database**, originally collected by the National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK) and widely distributed through the UCI Machine Learning Repository and Kaggle. It contains 768 records of female patients aged 21 or older, of Pima Indian heritage, with these columns:

- `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age`
- `Outcome`: 1 if the patient has diabetes, 0 if not

In this dataset, a value of 0 in `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin` or `BMI` means the value was not recorded. The code treats these zeros as missing and fills them with the median during training.

The patient names, doctors, phone numbers and appointments in the database are randomly generated sample data. They are not real people.

## How the model works

- **Algorithm:** Random Forest (300 trees, maximum depth 6, balanced class weights)
- **Preprocessing:** zeros in the five measurement columns are replaced with missing values, then imputed with the median
- **Split:** 80% training, 20% testing, stratified by outcome, with a fixed random seed
- **Outputs:** a risk label (0 or 1) and a probability, both stored in the `checkups` table

Run `evaluate.py` to see accuracy, ROC AUC and the confusion matrix on the held-out test set.

## Notes

- `hospital.db` and `model.pkl` are generated files. You can delete them and rerun `run_all.bat` to start fresh.
- The `file.gitignore` file lists folders and files that should not be committed, such as virtual environments and `.env`.
