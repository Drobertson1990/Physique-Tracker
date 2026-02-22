import streamlit as st
import pandas as pd
from database import Session, init_db, Dose, Meal, Workout
import datetime
import plotly.express as px

init_db()
session = Session()

st.set_page_config(page_title="Physique Tracker", layout="wide")

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
    st.header("Log Peptide / Steroid Dose")

    compound = st.text_input("Compound Name")
    amount = st.number_input("Amount (mg)", min_value=0.0)
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
    weight = st.number_input("Weight (lbs or kg)", min_value=0.0)
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
