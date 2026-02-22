import streamlit as st
import pandas as pd
from database import Session, init_db, Dose, Meal, Workout
import datetime
import plotly.express as px

init_db()
session = Session()

st.set_page_config(page_title="Physique Tracker", layout="wide")

# ------------------------------
# COMPOUND DATABASE
# ------------------------------

COMPOUNDS = {
    "BPC-157": {
        "category": "Peptide",
        "description": "Investigational peptide often discussed for tissue healing and gut repair.",
        "male_range": "Not clinically established",
        "female_range": "Not clinically established"
    },
    "TB-500 (Thymosin Beta-4)": {
        "category": "Peptide",
        "description": "Research peptide associated with tissue repair and recovery.",
        "male_range": "Not clinically established",
        "female_range": "Not clinically established"
    },
    "CJC-1295": {
        "category": "Growth Hormone Releasing Peptide",
        "description": "Stimulates growth hormone release.",
        "male_range": "Clinical dosing varies (prescription required)",
        "female_range": "Clinical dosing varies (prescription required)"
    },
    "Ipamorelin": {
        "category": "Growth Hormone Secretagogue",
        "description": "Stimulates natural growth hormone pulse release.",
        "male_range": "Clinical dosing varies",
        "female_range": "Clinical dosing varies"
    },
    "Tesamorelin": {
        "category": "Prescription Peptide",
        "description": "FDA-approved for reducing visceral fat in HIV patients.",
        "male_range": "2 mg daily (clinical use)",
        "female_range": "2 mg daily (clinical use)"
    },
    "Semaglutide": {
        "category": "GLP-1 Agonist",
        "description": "Used for glucose control and weight management.",
        "male_range": "0.25–2.4 mg weekly (clinical use)",
        "female_range": "0.25–2.4 mg weekly (clinical use)"
    },
    "Tirzepatide": {
        "category": "GLP-1/GIP Agonist",
        "description": "Dual incretin agonist for metabolic control.",
        "male_range": "2.5–15 mg weekly (clinical use)",
        "female_range": "2.5–15 mg weekly (clinical use)"
    },
    "Testosterone (Prescription)": {
        "category": "Hormone (Controlled)",
        "description": "Primary male androgen. Prescription only.",
        "male_range": "Clinical TRT varies (physician prescribed)",
        "female_range": "Rare clinical use (physician supervised)"
    },
    "Nandrolone (Prescription)": {
        "category": "Anabolic Steroid (Controlled)",
        "description": "Prescription anabolic agent used medically in limited cases.",
        "male_range": "Physician prescribed only",
        "female_range": "Physician prescribed only"
    },
    "Oxandrolone (Prescription)": {
        "category": "Anabolic Steroid (Controlled)",
        "description": "Used medically for muscle wasting and recovery.",
        "male_range": "Physician prescribed only",
        "female_range": "Physician prescribed only"
    }
}

# ------------------------------
# UI
# ------------------------------

st.title("💪 Physique Performance Tracker")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Log Dose", "Log Meal", "Log Workout"])

# ---------------- DASHBOARD ----------------

if menu == "Dashboard":
    st.header("Overview")

    doses = pd.read_sql(session.query(Dose).statement, session.bind)
    meals = pd.read_sql(session.query(Meal).statement, session.bind)
    workouts = pd.read_sql(session.query(Workout).statement, session.bind)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Doses Logged", len(doses))

    with col2:
        st.metric("Total Calories Logged", meals["calories"].sum() if not meals.empty else 0)

    with col3:
        st.metric("Workouts Logged", len(workouts))

    if not meals.empty:
        daily_cals = meals.groupby("date")["calories"].sum().reset_index()
        fig = px.line(daily_cals, x="date", y="calories", title="Daily Calories")
        st.plotly_chart(fig)

# ---------------- LOG DOSE ----------------

elif menu == "Log Dose":
    st.header("Log Compound Dose")

    compound = st.selectbox("Select Compound", list(COMPOUNDS.keys()))

    info = COMPOUNDS[compound]

    st.subheader("Compound Information")

    st.markdown(f"**Category:** {info['category']}")
    st.markdown(f"**Description:** {info['description']}")
    st.markdown(f"**Typical Male Clinical Range:** {info['male_range']}")
    st.markdown(f"**Typical Female Clinical Range:** {info['female_range']}")

    st.warning("⚠ This application is for tracking purposes only and does not provide medical advice. Consult a licensed medical professional before using any prescription or research compound.")

    amount = st.number_input("Amount Used (mg)", min_value=0.0)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Save Dose"):
        new_dose = Dose(compound=compound, amount_mg=amount, date=date)
        session.add(new_dose)
        session.commit()
        st.success("Dose Logged Successfully")

# ---------------- LOG MEAL ----------------

elif menu == "Log Meal":
    st.header("Log Meal")

    meal_name = st.text_input("Meal Name")
    calories = st.number_input("Calories", min_value=0)
    protein = st.number_input("Protein (g)", min_value=0)
    carbs = st.number_input("Carbs (g)", min_value=0)
    fats = st.number_input("Fats (g)", min_value=0)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Save Meal"):
        new_meal = Meal(
            meal_name=meal_name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats,
            date=date
        )
        session.add(new_meal)
        session.commit()
        st.success("Meal Logged Successfully")

# ---------------- LOG WORKOUT ----------------

elif menu == "Log Workout":
    st.header("Log Workout")

    exercise = st.text_input("Exercise")
    sets = st.number_input("Sets", min_value=1)
    reps = st.number_input("Reps", min_value=1)
    weight = st.number_input("Weight", min_value=0.0)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Save Workout"):
        new_workout = Workout(
            exercise=exercise,
            sets=sets,
            reps=reps,
            weight=weight,
            date=date
        )
        session.add(new_workout)
        session.commit()
        st.success("Workout Logged Successfully")
