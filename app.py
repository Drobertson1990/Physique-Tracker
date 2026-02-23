import streamlit as st
import pandas as pd
import datetime
import os
from database.database import Session, init_db, User, Dose, Cycle, Meal, Workout, Bloodwork, Photo
from utils.utils import weekly_dose_chart, weekly_meals_chart, weekly_workout_chart, bloodwork_chart

from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------
# INIT
# ------------------------------
init_db()
session = Session()

st.set_page_config(page_title="Physique Tracker", layout="wide")

# ------------------------------
# COMPOUND DATABASE
# ------------------------------
COMPOUNDS = {
    "BPC-157": {"category": "Peptide", "description": "Investigational peptide for tissue healing.", "male_range":"Not clinically established","female_range":"Not clinically established"},
    "TB-500": {"category": "Peptide", "description": "Research peptide for tissue repair.", "male_range":"Not clinically established","female_range":"Not clinically established"},
    "CJC-1295": {"category": "Peptide", "description": "Stimulates growth hormone release.", "male_range":"Clinical use varies","female_range":"Clinical use varies"},
    "Ipamorelin": {"category": "Peptide", "description": "Growth hormone secretagogue.", "male_range":"Clinical use varies","female_range":"Clinical use varies"},
    "Tesamorelin": {"category": "Peptide", "description": "FDA-approved for visceral fat in HIV patients.", "male_range":"2 mg daily","female_range":"2 mg daily"},
    "Semaglutide": {"category": "GLP-1 agonist", "description": "Glucose control/weight management.", "male_range":"0.25–2.4 mg weekly","female_range":"0.25–2.4 mg weekly"},
    "Testosterone (Prescription)": {"category":"Hormone","description":"Primary male androgen, prescription only.","male_range":"Physician prescribed","female_range":"Rare clinical use"},
    "Nandrolone (Prescription)": {"category":"Anabolic Steroid","description":"Prescription anabolic agent.","male_range":"Physician prescribed","female_range":"Physician prescribed"},
    "Oxandrolone (Prescription)": {"category":"Anabolic Steroid","description":"Used medically for muscle wasting.","male_range":"Physician prescribed","female_range":"Physician prescribed"}
}

# ------------------------------
# AUTH FUNCTIONS
# ------------------------------
def register():
    st.subheader("Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if password != confirm:
            st.error("Passwords do not match")
            return None
        if session.query(User).filter_by(email=email).first():
            st.error("Email already registered")
            return None
        user = User(email=email)
        user.set_password(password)
        session.add(user)
        session.commit()
        st.success("Account created! Please login.")

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = session.query(User).filter_by(email=email).first()
        if user and user.check_password(password):
            st.session_state['user'] = user.id
            st.success(f"Logged in as {email}")
        else:
            st.error("Invalid email or password")

def logout():
    if st.button("Logout"):
        st.session_state['user'] = None
        st.success("Logged out")

# ------------------------------
# MAIN
# ------------------------------
if 'user' not in st.session_state:
    st.session_state['user'] = None

if st.session_state['user'] is None:
    st.sidebar.title("Account")
    choice = st.sidebar.radio("Login/Register", ["Login", "Register"])
    if choice == "Login":
        login()
    else:
        register()
else:
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard","Log Dose","Cycle Planner","Log Meal","Log Workout","Bloodwork","Progress Photos","Account"])
    user_id = st.session_state['user']

    # ---------------- Dashboard ----------------
    if page == "Dashboard":
        st.header("📊 Dashboard Overview")

        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, session.bind)
        meals = pd.read_sql(session.query(Meal).filter_by(user_id=user_id).statement, session.bind)
        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, session.bind)
        blood = pd.read_sql(session.query(Bloodwork).filter_by(user_id=user_id).statement, session.bind)
        photos = pd.read_sql(session.query(Photo).filter_by(user_id=user_id).statement, session.bind)

        col1,col2,col3 = st.columns(3)
        with col1: st.metric("Doses Logged", len(doses))
        with col2: st.metric("Meals Logged", len(meals))
        with col3: st.metric("Workouts Logged", len(workouts))

        fig_dose = weekly_dose_chart(user_id)
        if fig_dose: st.plotly_chart(fig_dose)

        fig_meals = weekly_meals_chart(user_id)
        if fig_meals: st.plotly_chart(fig_meals)

        fig_workouts = weekly_workout_chart(user_id)
        if fig_workouts: st.plotly_chart(fig_workouts)

        fig_blood = bloodwork_chart(user_id)
        if fig_blood: st.plotly_chart(fig_blood)

    # ---------------- Log Dose ----------------
    elif page == "Log Dose":
        st.header("💊 Log Compound Dose")

        compound_list = list(COMPOUNDS.keys()) + ["Custom"]
        compound = st.selectbox("Select Compound", compound_list)

        if compound == "Custom":
            compound_name = st.text_input("Enter Compound Name")
            description = st.text_area("Description")
            male_range = st.text_input("Typical Male Range")
            female_range = st.text_input("Typical Female Range")
        else:
            info = COMPOUNDS[compound]
            compound_name = compound
            description = info['description']
            male_range = info['male_range']
            female_range = info['female_range']

        st.subheader("Compound Info")
        st.markdown(f"**Description:** {description}")
        st.markdown(f"**Male Range:** {male_range}")
        st.markdown(f"**Female Range:** {female_range}")
        st.warning("⚠ For tracking purposes only. Not medical advice.")

        amount = st.number_input("Amount Used (mg)", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Dose"):
            new_dose = Dose(user_id=user_id, compound=compound_name, amount_mg=amount, date=date)
            session.add(new_dose)
            session.commit()
            st.success("Dose logged successfully!")

        fig_dose = weekly_dose_chart(user_id)
        if fig_dose: st.plotly_chart(fig_dose)

    # ---------------- Cycle Planner ----------------
    elif page == "Cycle Planner":
        st.header("📅 Cycle Planner")
        cycles = pd.read_sql(session.query(Cycle).filter_by(user_id=user_id).statement, session.bind)
        st.subheader("Add Cycle")
        compound = st.selectbox("Compound", list(COMPOUNDS.keys()) + ["Custom"])
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        weekly_dose = st.number_input("Weekly Dose (mg)", min_value=0.0)
        if st.button("Add Cycle"):
            if compound == "Custom":
                compound_name = st.text_input("Custom Compound Name")
            else:
                compound_name = compound
            new_cycle = Cycle(user_id=user_id, compound=compound_name, start_date=start_date, end_date=end_date, weekly_dose=weekly_dose)
            session.add(new_cycle)
            session.commit()
            st.success("Cycle added!")

        if not cycles.empty:
            st.subheader("Your Cycles")
            st.dataframe(cycles)

    # ---------------- Log Meal ----------------
    elif page == "Log Meal":
        st.header("🥗 Log Meal")
        meal_name = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0)
        protein = st.number_input("Protein (g)", min_value=0)
        carbs = st.number_input("Carbs (g)", min_value=0)
        fats = st.number_input("Fats (g)", min_value=0)
        date = st.date_input("Date", datetime.date.today())
        if st.button("Save Meal"):
            new_meal = Meal(user_id=user_id, meal_name=meal_name, calories=calories, protein=protein, carbs=carbs, fats=fats, date=date)
            session.add(new_meal)
            session.commit()
            st.success("Meal logged successfully!")

        fig_meals = weekly_meals_chart(user_id)
        if fig_meals: st.plotly_chart(fig_meals)

    # ---------------- Log Workout ----------------
    elif page == "Log Workout":
        st.header("🏋️ Log Workout")
        exercise = st.text_input("Exercise")
        sets = st.number_input("Sets", min_value=1)
        reps = st.number_input("Reps", min_value=1)
        weight = st.number_input("Weight", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())
        if st.button("Save Workout"):
            new_workout = Workout(user_id=user_id, exercise=exercise, sets=sets, reps=reps, weight=weight, date=date)
            session.add(new_workout)
            session.commit()
            st.success("Workout logged successfully!")

        fig_workouts = weekly_workout_chart(user_id)
        if fig_workouts: st.plotly_chart(fig_workouts)

    # ---------------- Bloodwork ----------------
    elif page == "Bloodwork":
        st.header("🩸 Bloodwork Tracker")
        test_name = st.text_input("Test Name (e.g., Testosterone, Estradiol)")
        value = st.number_input("Value", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())
        if st.button("Save Bloodwork"):
            new_test = Bloodwork(user_id=user_id, test_name=test_name, value=value, date=date)
            session.add(new_test)
            session.commit()
            st.success("Bloodwork logged!")

        fig_blood = bloodwork_chart(user_id)
        if fig_blood: st.plotly_chart(fig_blood)

    # ---------------- Progress Photos ----------------
    elif page == "Progress Photos":
        st.header("📸 Progress Photos")
        if not os.path.exists("photos"):
            os.makedirs("photos")

        uploaded_file = st.file_uploader("Upload Photo", type=["png","jpg","jpeg"])
        date = st.date_input("Date", datetime.date.today())
        if uploaded_file and st.button("Save Photo"):
            file_path = f"photos/{user_id}_{date}_{uploaded_file.name}"
            with open(file_path,"wb") as f:
                f.write(uploaded_file.getbuffer())
            new_photo = Photo(user_id=user_id, file_path=file_path, date=date)
            session.add(new_photo)
            session.commit()
            st.success("Photo saved!")

        photos = session.query(Photo).filter_by(user_id=user_id).order_by(Photo.date).all()
        for p in photos:
            st.image(p.file_path, caption=str(p.date), use_column_width=True)

    # ---------------- Account ----------------
    elif page == "Account":
        st.header("Account Management")
        user_obj = session.query(User).get(user_id)
        st.write(f"Logged in as: {user_obj.email}")
        logout()
