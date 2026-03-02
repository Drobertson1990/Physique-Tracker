import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.express as px
from sqlalchemy import inspect, text

# ----------------------
# DATABASE SETUP
# ----------------------
DB_PATH = "/tmp/tracker.db"  # Streamlit Cloud writable path
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# ----------------------
# DATABASE MODELS
# ----------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dose(Base):
    __tablename__ = "doses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    compound = Column(String)
    amount = Column(Float)
    date = Column(Date)

class MealLog(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    meal = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    date = Column(Date)

class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)


class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    exercise = Column(String)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    rest_time = Column(Integer, default=60)
    goal = Column(String, default="Hypertrophy")
    date = Column(Date)

class Bloodwork(Base):
    __tablename__ = "bloodwork"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    test = Column(String)
    value = Column(Float)
    date = Column(Date)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    path = Column(String)
    date = Column(Date)

# ----------------------
# DATABASE MODELS (EXTENDED)
# ----------------------

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # Primary muscle group (Chest, Back, etc.)
    category = Column(String, nullable=False)

    # Equipment required (barbell, dumbbells, bodyweight, etc.)
    equipment = Column(String, default="")

    # Secondary muscles
    secondary_muscles = Column(String, default="")

    description = Column(String, default="")
    image_url = Column(String, default="")
class Routine(Base):
    __tablename__ = "routines"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # Null for prebuilt routines
    name = Column(String)
    goal = Column(String)

class RoutineExercise(Base):
    __tablename__ = "routine_exercises"
    id = Column(Integer, primary_key=True)
    routine_id = Column(Integer)
    exercise_id = Column(Integer)
    sets = Column(Integer)
    reps = Column(Integer)
    rest_time = Column(Integer)

# ----------------------
# CREATE TABLES
# ----------------------
Base.metadata.create_all(engine)
# ----------------------
# Ensure rest_time column exists in Workouts table
# ----------------------
inspector = inspect(engine)
columns = [col["name"] for col in inspector.get_columns("workouts")]

if "rest_time" not in columns:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE workouts ADD COLUMN rest_time INTEGER DEFAULT 60"))

# --------------------------------------------------------

# ----------------------
# PRELOAD EXERCISES
# ----------------------

preload_exercises = [

    # CHEST
    {"name": "Barbell Bench Press", "equipment": "barbell & bench", "category": "Chest", "secondary_muscles": "Triceps, Anterior Deltoids"},
    {"name": "Dumbbell Bench Press", "equipment": "dumbbells & bench", "category": "Chest", "secondary_muscles": "Triceps, Shoulders"},
    {"name": "Incline Barbell Bench Press", "equipment": "barbell & incline bench", "category": "Upper Chest", "secondary_muscles": "Shoulders, Triceps"},
    {"name": "Incline Dumbbell Press", "equipment": "dumbbells & incline bench", "category": "Upper Chest", "secondary_muscles": "Triceps"},
    {"name": "Decline Barbell Press", "equipment": "barbell & decline bench", "category": "Lower Chest", "secondary_muscles": "Triceps"},
    {"name": "Decline Dumbbell Press", "equipment": "dumbbells & decline bench", "category": "Lower Chest", "secondary_muscles": "Triceps"},
    {"name": "Smith Machine Bench Press", "equipment": "smith machine & bench", "category": "Chest", "secondary_muscles": "Triceps"},
    {"name": "Machine Chest Press", "equipment": "chest press machine", "category": "Chest", "secondary_muscles": "Triceps"},
    {"name": "Pec Deck Fly", "equipment": "pec deck machine", "category": "Chest", "secondary_muscles": "Anterior Deltoids"},
    {"name": "Cable Chest Fly", "equipment": "cable machine", "category": "Chest", "secondary_muscles": "Anterior Deltoids"},
    {"name": "Standing Cable Crossover", "equipment": "cable machine", "category": "Chest", "secondary_muscles": "Shoulders"},
    {"name": "Push-Ups", "equipment": "bodyweight", "category": "Chest", "secondary_muscles": "Triceps, Shoulders"},
    {"name": "Incline Push-Ups", "equipment": "bodyweight (elevated)", "category": "Upper Chest", "secondary_muscles": "Shoulders"},
    {"name": "Decline Push-Ups", "equipment": "bodyweight (feet elevated)", "category": "Lower Chest", "secondary_muscles": "Shoulders"},

    # BACK
    {"name": "Pull-Ups", "equipment": "pull-up bar", "category": "Lats", "secondary_muscles": "Biceps, Rear Delts"},
    {"name": "Chin-Ups", "equipment": "pull-up bar", "category": "Lats/Biceps", "secondary_muscles": "Chest"},
    {"name": "Lat Pulldown (Wide Grip)", "equipment": "cable machine", "category": "Lats", "secondary_muscles": "Biceps"},
    {"name": "Lat Pulldown (Close Grip)", "equipment": "cable machine", "category": "Lats", "secondary_muscles": "Biceps"},
    {"name": "Seated Cable Row", "equipment": "cable machine", "category": "Mid Back", "secondary_muscles": "Biceps"},
    {"name": "Bent-Over Barbell Row", "equipment": "barbell", "category": "Upper Back", "secondary_muscles": "Lats, Biceps"},
    {"name": "Dumbbell One-Arm Row", "equipment": "dumbbell", "category": "Upper Back", "secondary_muscles": "Lats, Biceps"},
    {"name": "T-Bar Row", "equipment": "barbell/T-bar", "category": "Upper Back", "secondary_muscles": "Lats, Biceps"},
    {"name": "Machine Row", "equipment": "row machine", "category": "Back", "secondary_muscles": "Biceps"},
    {"name": "Straight-Arm Cable Pulldown", "equipment": "cable machine", "category": "Lats", "secondary_muscles": ""},
    {"name": "Reverse Grip Pulldown", "equipment": "cable machine", "category": "Lats", "secondary_muscles": "Biceps"},
    {"name": "Inverted Row", "equipment": "bodyweight / bar", "category": "Back", "secondary_muscles": "Biceps"},
    {"name": "Deadlift", "equipment": "barbell", "category": "Posterior Chain", "secondary_muscles": "Back, Glutes"},

    # LEGS & GLUTES
    {"name": "Barbell Back Squat", "equipment": "barbell", "category": "Quads", "secondary_muscles": "Glutes, Hamstrings"},
    {"name": "Front Squat", "equipment": "barbell", "category": "Quads", "secondary_muscles": "Core"},
    {"name": "Goblet Squat", "equipment": "dumbbell/kettlebell", "category": "Quads", "secondary_muscles": "Glutes"},
    {"name": "Sumo Squat", "equipment": "barbell", "category": "Glutes", "secondary_muscles": "Inner Thighs"},
    {"name": "Hack Squat Machine", "equipment": "hack squat machine", "category": "Quads", "secondary_muscles": "Glutes"},
    {"name": "Leg Press", "equipment": "leg press machine", "category": "Quads", "secondary_muscles": "Glutes"},
    {"name": "Bulgarian Split Squat", "equipment": "dumbbells", "category": "Quads", "secondary_muscles": "Glutes"},
    {"name": "Lunge (Forward)", "equipment": "bodyweight/dumbbells", "category": "Quads", "secondary_muscles": "Glutes"},
    {"name": "Reverse Lunge", "equipment": "bodyweight/dumbbells", "category": "Glutes", "secondary_muscles": "Quads"},
    {"name": "Walking Lunge", "equipment": "dumbbells", "category": "Glutes", "secondary_muscles": "Quads"},
    {"name": "Romanian Deadlift", "equipment": "barbell", "category": "Hamstrings", "secondary_muscles": "Glutes"},
    {"name": "Stiff-Leg Deadlift", "equipment": "barbell", "category": "Hamstrings", "secondary_muscles": "Lower Back"},
    {"name": "Leg Extension", "equipment": "leg extension machine", "category": "Quads", "secondary_muscles": ""},
    {"name": "Leg Curl (Lying)", "equipment": "leg curl machine", "category": "Hamstrings", "secondary_muscles": ""},
    {"name": "Leg Curl (Seated)", "equipment": "leg curl machine", "category": "Hamstrings", "secondary_muscles": ""},
    {"name": "Calf Raise (Standing)", "equipment": "machine/bodyweight", "category": "Calves", "secondary_muscles": ""},
    {"name": "Calf Raise (Seated)", "equipment": "seated calf machine", "category": "Calves", "secondary_muscles": ""},
    {"name": "Hip Thrust", "equipment": "barbell/bench", "category": "Glutes", "secondary_muscles": "Hamstrings"},
    {"name": "Glute Bridge", "equipment": "bodyweight/barbell", "category": "Glutes", "secondary_muscles": "Hamstrings"},
    {"name": "Cable Pull-Through", "equipment": "cable machine", "category": "Glutes", "secondary_muscles": "Hamstrings"},

    # SHOULDERS
    {"name": "Overhead Barbell Press", "equipment": "barbell", "category": "Shoulders", "secondary_muscles": "Triceps"},
    {"name": "Dumbbell Shoulder Press", "equipment": "dumbbells", "category": "Shoulders", "secondary_muscles": "Triceps"},
    {"name": "Seated Machine Shoulder Press", "equipment": "machine", "category": "Shoulders", "secondary_muscles": "Triceps"},
    {"name": "Arnold Press", "equipment": "dumbbells", "category": "Shoulders", "secondary_muscles": "Upper Chest"},
    {"name": "Lateral Raise", "equipment": "dumbbells", "category": "Medial Delts", "secondary_muscles": ""},
    {"name": "Front Raise", "equipment": "dumbbells", "category": "Anterior Delts", "secondary_muscles": ""},
    {"name": "Reverse Fly", "equipment": "dumbbells/cable", "category": "Posterior Delts", "secondary_muscles": "Upper Back"},
    {"name": "Upright Row", "equipment": "barbell", "category": "Traps/Shoulders", "secondary_muscles": "Biceps"},
    {"name": "Cable Lateral Raise", "equipment": "cable machine", "category": "Medial Delts", "secondary_muscles": ""},

    # BICEPS
    {"name": "Barbell Biceps Curl", "equipment": "barbell/EZ bar", "category": "Biceps", "secondary_muscles": "Forearms"},
    {"name": "Dumbbell Biceps Curl", "equipment": "dumbbells", "category": "Biceps", "secondary_muscles": "Forearms"},
    {"name": "Hammer Curl", "equipment": "dumbbells", "category": "Brachialis", "secondary_muscles": "Forearms"},
    {"name": "Concentration Curl", "equipment": "dumbbell", "category": "Biceps", "secondary_muscles": ""},
    {"name": "Preacher Curl", "equipment": "preacher bench & bar/dumbbells", "category": "Biceps", "secondary_muscles": ""},
    {"name": "Cable Biceps Curl", "equipment": "cable machine", "category": "Biceps", "secondary_muscles": ""},
    {"name": "Incline Dumbbell Curl", "equipment": "incline bench & dumbbells", "category": "Biceps", "secondary_muscles": ""},
    {"name": "Reverse Barbell Curl", "equipment": "barbell", "category": "Forearms", "secondary_muscles": "Biceps"},

    # TRICEPS
    {"name": "Triceps Pushdown", "equipment": "cable machine", "category": "Triceps", "secondary_muscles": ""},
    {"name": "Overhead Dumbbell Triceps Extension", "equipment": "dumbbell", "category": "Triceps", "secondary_muscles": "Shoulders"},
    {"name": "Skull Crushers", "equipment": "EZ bar", "category": "Triceps", "secondary_muscles": "Forearms"},
    {"name": "Close-Grip Bench Press", "equipment": "barbell", "category": "Triceps", "secondary_muscles": "Chest"},
    {"name": "Dips", "equipment": "parallel bars", "category": "Triceps", "secondary_muscles": "Chest"},
    {"name": "Machine Triceps Extension", "equipment": "machine", "category": "Triceps", "secondary_muscles": ""},
    {"name": "Rope Triceps Pushdown", "equipment": "cable machine", "category": "Triceps", "secondary_muscles": ""},

    # CORE
    {"name": "Crunches", "equipment": "bodyweight", "category": "Abs", "secondary_muscles": "Hip Flexors"},
    {"name": "Cable Crunch", "equipment": "cable machine", "category": "Abs", "secondary_muscles": ""},
    {"name": "Hanging Leg Raise", "equipment": "bodyweight", "category": "Abs", "secondary_muscles": "Hip Flexors"},
    {"name": "Decline Sit-Up", "equipment": "decline bench", "category": "Abs", "secondary_muscles": "Hip Flexors"},
    {"name": "Plank", "equipment": "bodyweight", "category": "Core", "secondary_muscles": "Stabilizers"},
    {"name": "Side Plank", "equipment": "bodyweight", "category": "Obliques", "secondary_muscles": "Core"},
    {"name": "Russian Twist", "equipment": "medicine ball", "category": "Obliques", "secondary_muscles": "Abs"},
    {"name": "Ab Wheel Rollout", "equipment": "ab wheel", "category": "Core", "secondary_muscles": "Shoulders"},
    {"name": "Mountain Climbers", "equipment": "bodyweight", "category": "Core", "secondary_muscles": "Cardio"},
    {"name": "Standing Cable Wood Chop", "equipment": "cable machine", "category": "Obliques", "secondary_muscles": "Core"},

    # FUNCTIONAL / FULL BODY
    {"name": "Barbell Deadlift", "equipment": "barbell", "category": "Posterior Chain", "secondary_muscles": "Full Body"},
    {"name": "Sumo Deadlift", "equipment": "barbell", "category": "Glutes", "secondary_muscles": "Quads/Back"},
    {"name": "Power Clean", "equipment": "barbell", "category": "Full Body", "secondary_muscles": "Shoulders/Legs"},
    {"name": "Clean & Jerk", "equipment": "barbell", "category": "Full Body", "secondary_muscles": "Shoulders/Legs"},
    {"name": "Snatch", "equipment": "barbell", "category": "Full Body", "secondary_muscles": "Back/Shoulders"},
    {"name": "Kettlebell Swing", "equipment": "kettlebell", "category": "Posterior Chain", "secondary_muscles": "Core"},
    {"name": "Thruster", "equipment": "barbell/dumbbells", "category": "Legs/Shoulders", "secondary_muscles": "Core"},
    {"name": "Farmer’s Carry", "equipment": "dumbbells/kettlebells", "category": "Full Body", "secondary_muscles": "Grip/Core"},
    {"name": "Battle Ropes", "equipment": "battle ropes", "category": "Full Body", "secondary_muscles": "Arms/Core"},
    {"name": "Box Jump", "equipment": "plyo box", "category": "Legs", "secondary_muscles": "Explosive Power"},
    {"name": "Burpees", "equipment": "bodyweight", "category": "Full Body", "secondary_muscles": "Cardio"},

    # BODYWEIGHT VARIATIONS
    {"name": "Jump Squat", "equipment": "bodyweight", "category": "Legs", "secondary_muscles": "Glutes"},
    {"name": "Pistol Squat", "equipment": "bodyweight", "category": "Quads", "secondary_muscles": "Balance/Core"},
    {"name": "Push-Up Wide", "equipment": "bodyweight", "category": "Chest", "secondary_muscles": "Triceps"},
    {"name": "Push-Up Close", "equipment": "bodyweight", "category": "Triceps", "secondary_muscles": "Chest"},
    {"name": "Lunge Jump", "equipment": "bodyweight", "category": "Legs", "secondary_muscles": "Cardio"},
    {"name": "Step-Ups", "equipment": "bench/bodyweight", "category": "Legs", "secondary_muscles": "Glutes"},
    {"name": "Chin-Up Close Grip", "equipment": "pull-up bar", "category": "Biceps", "secondary_muscles": "Back"},
    {"name": "Chin-Up Wide Grip", "equipment": "pull-up bar", "category": "Lats", "secondary_muscles": "Biceps"},
    {"name": "Inverted Row Feet Elevated", "equipment": "bodyweight", "category": "Back", "secondary_muscles": "Biceps"},
]
for ex in preload_exercises:
    if not session.query(Exercise).filter_by(name=ex["name"]).first():
        session.add(Exercise(**ex))

session.commit()

# ----------------------
# ENSURE WORKOUTS TABLE COLUMNS EXIST
# ----------------------
from sqlalchemy import inspect, text

inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('exercises')]

with engine.begin() as conn:
    if 'equipment' not in columns:
        conn.execute(text("ALTER TABLE exercises ADD COLUMN equipment TEXT DEFAULT ''"))
    if 'secondary_muscles' not in columns:
       conn.execute(text("ALTER TABLE exercises ADD COLUMN secondary_muscles TEXT DEFAULT ''"))

# ----------------------
# STREAMLIT PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Physique Tracker", layout="wide")

# ----------------------
# SESSION STATE INIT
# ----------------------
for key in ["logged_in", "user_id", "user_email", "page"]:
    if key not in st.session_state:
        if key == "page":
            st.session_state[key] = "Home 🏠"
        elif key == "logged_in":
            st.session_state[key] = False
        else:
            st.session_state[key] = None

# ----------------------
# USER AUTH / LOGIN
# ----------------------
def login_user(user):
    st.session_state.logged_in = True
    st.session_state.user_id = user.id
    st.session_state.user_email = user.email
    st.session_state.page = "Home 🏠"

# ----------------------
# SIDEBAR NAVIGATION
# ----------------------
if st.session_state.logged_in:
    st.sidebar.title(f"👋 Hello, {st.session_state.user_email}")
    pages = ["Home 🏠", "Meals 🍽", "Workouts 🏋️‍♂️", "Dosing 💉", "Bloodwork 🩸", "Photos 📸", "Dashboard 📊", "Settings ⚙️", "Logout"]

    # ensure page is valid
    if st.session_state.page not in pages:
        st.session_state.page = "Home 🏠"

    try:
        current_index = pages.index(st.session_state.page)
    except ValueError:
        current_index = 0
        st.session_state.page = pages[0]

    selected_page = st.sidebar.selectbox("Navigation", pages, index=current_index)

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.experimental_rerun()

    # Logout logic
    if st.session_state.page == "Logout":
        for key in ["logged_in", "user_id", "user_email", "page"]:
            st.session_state[key] = None if key != "page" else "Home 🏠"
        st.success("Logged out successfully")
        st.experimental_rerun()

# ----------------------
# PAGE ROUTING
# ----------------------
page = st.session_state.page
user_id = st.session_state.user_id

# ----------------------
# HOME PAGE
# ----------------------
if page == "Home 🏠":
    st.title("🏠 Home Dashboard")

    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🍽 Log Meal"):
        st.session_state.page = "Meals 🍽"
        st.experimental_rerun()
    if col2.button("🏋️‍♂️ Log Workout"):
        st.session_state.page = "Workouts 🏋️‍♂️"
        st.experimental_rerun()
    if col3.button("💉 Log Dose"):
        st.session_state.page = "Dosing 💉"
        st.experimental_rerun()
    if col4.button("📊 View Progress"):
        st.session_state.page = "Dashboard 📊"
        st.experimental_rerun()

# ----------------------
# DOSING PAGE
# ----------------------
elif page == "Dosing 💉":
    st.title("💉 Dosing")
    st.write("Log your doses here")

    # Simple form for logging a dose
    with st.form("dose_form"):
        compound = st.text_input("Compound")
        amount = st.number_input("Amount", min_value=0.0, step=0.1)
        date = st.date_input("Date", datetime.date.today())
        submitted = st.form_submit_button("Log Dose")
        if submitted:
            if compound and amount > 0:
                new_dose = Dose(user_id=user_id, compound=compound, amount=amount, date=date)
                session.add(new_dose)
                session.commit()
                st.success(f"Dose logged: {compound} {amount}")
            else:
                st.error("Enter a valid compound and amount")

    # Show last 5 doses
    st.subheader("Recent Doses")
    recent = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).order_by(Dose.date.desc()).limit(5).statement, engine)
    st.dataframe(recent)

# ----------------------
# MEALS PAGE
# ----------------------
elif page == "Meals 🍽":
    st.title("🍽 Meals")
    st.write("Log your meals")

    with st.form("meal_form"):
        meal_name = st.text_input("Meal Name")
        calories = st.number_input("Calories", min_value=0.0)
        protein = st.number_input("Protein (g)", min_value=0.0)
        carbs = st.number_input("Carbs (g)", min_value=0.0)
        fats = st.number_input("Fats (g)", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())
        submitted = st.form_submit_button("Log Meal")
        if submitted:
            new_meal = MealLog(user_id=user_id, meal=meal_name, calories=calories, protein=protein, carbs=carbs, fats=fats, date=date)
            session.add(new_meal)
            session.commit()
            st.success(f"Meal logged: {meal_name}")

    st.subheader("Recent Meals")
    recent = pd.read_sql(session.query(MealLog).filter_by(user_id=user_id).order_by(MealLog.date.desc()).limit(5).statement, engine)
    st.dataframe(recent)

# ----------------------
# WORKOUTS PAGE
# ----------------------
elif page == "Workouts 🏋️‍♂️":
    st.title("🏋️‍♂️ Workouts")
    st.write("Log your workouts")

    with st.form("workout_form"):
        exercise = st.text_input("Exercise")
        sets = st.number_input("Sets", min_value=1)
        reps = st.number_input("Reps", min_value=1)
        weight = st.number_input("Weight", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())
        submitted = st.form_submit_button("Log Workout")
        if submitted:
            new_w = Workout(user_id=user_id, exercise=exercise, sets=sets, reps=reps, weight=weight, date=date)
            session.add(new_w)
            session.commit()
            st.success(f"Workout logged: {exercise}")

    st.subheader("Recent Workouts")
    recent = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).order_by(Workout.date.desc()).limit(5).statement, engine)
    st.dataframe(recent)

# ----------------------
# BLOODWORK PAGE
# ----------------------
elif page == "Bloodwork 🩸":
    st.title("🩸 Bloodwork")
    st.write("Log your bloodwork")

# ----------------------
# PHOTOS PAGE
# ----------------------
elif page == "Photos 📸":
    st.title("📸 Photos")
    st.write("Upload and view progress photos")

# ----------------------
# DASHBOARD PAGE
# ----------------------
elif page == "Dashboard 📊":
    st.title("📊 Dashboard Overview")
    try:
        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, engine)
        meals = pd.read_sql(session.query(MealLog).filter_by(user_id=user_id).statement, engine)
        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)
    except Exception as e:
        st.error(f"Database read error: {e}")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Doses Logged", len(doses))
    col2.metric("Meals Logged", len(meals))
    col3.metric("Workouts Logged", len(workouts))

# ----------------------
# SETTINGS PAGE
# ----------------------
elif page == "Settings ⚙️":
    st.title("⚙️ Settings")
    st.write("User settings go here.")
        
# ----------------------
# SESSION STATE INIT
# ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "page" not in st.session_state:
    st.session_state.page = "Dosing"

# ----------------------
# AUTH & NAVIGATION
# ----------------------
st.sidebar.title("User Authentication")

# Ensure session state keys exist
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "page" not in st.session_state:
    st.session_state.page = "Dosing"

def login_user(user):
    """Set session state for logged in user."""
    st.session_state.logged_in = True
    st.session_state.user_id = user.id
    st.session_state.user_email = user.email
    st.session_state.page = "Dosing"

# Show login/register options only if NOT logged in
if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Select Action", ["Login", "Register"])
    email_input = st.sidebar.text_input("Email")
    password_input = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button(auth_mode):

        if not email_input.strip() or not password_input.strip():
            st.sidebar.error("Enter email and password")
            st.stop()

        if auth_mode == "Register":
            existing = session.query(User).filter_by(email=email_input).first()
            if existing:
                st.sidebar.error("User already exists")
            else:
                new_user = User(email=email_input)
                new_user.set_password(password_input)
                session.add(new_user)
                session.commit()
                st.sidebar.success("User registered! You can now log in.")

        if auth_mode == "Login":
            user = session.query(User).filter_by(email=email_input).first()
            if user and user.check_password(password_input):
                login_user(user)
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

# Show navigation menu if logged in
else:
    st.sidebar.title("Navigation")
    pages = ["Dosing", "Meals", "Workouts", "Bloodwork", "Photos", "Dashboard", "Logout"]
    st.session_state.page = st.sidebar.selectbox(
    "Select Page",
    pages,
    index=pages.index(st.session_state.page),
    key="nav_select"
)
    st.sidebar.write(f"Logged in as: {st.session_state.user_email}")

    # Logout logic
    if st.session_state.page == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_email = ""
        st.session_state.page = "Dosing"
        st.success("Logged out successfully")
        st.rerun()
# ----------------------
# PAGE LOGIC
# ----------------------
user_id = st.session_state.user_id
page = st.session_state.page


# ----------------------
# DASHBOARD PAGE
# ----------------------
if st.session_state.logged_in and page == "Dashboard":
    st.header("Dashboard Overview")
    try:
        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, engine)
        meals = pd.read_sql(session.query(MealLog).filter_by(user_id=user_id).statement, engine)
        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)
    except Exception as e:
        st.error(f"Database read error: {e}")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Doses Logged", len(doses))
    col2.metric("Meals Logged", len(meals))
    col3.metric("Workouts Logged", len(workouts))

# ----------------------
# 🏋️‍♂️ DOSING PAGE (Polished)
# ----------------------
if st.session_state.get("logged_in") and st.session_state.get("page") == "Dosing":
    st.header("💉 Dosing Tracker")
    import datetime
    import pandas as pd
    import plotly.express as px

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to view this page.")
        st.stop()

    # ----------------------
    # 1️⃣ Preloaded Compounds
    # ----------------------
    preloaded_compounds = {
        # ------------------ PEPTIDES ------------------
        "CJC-1295 (DAC)": {"Category":"Peptide", "Subclass":"GHRH Analog", "Primary Purpose":"Long-acting GH stimulation", "Typical Goal":"Lean bulk / fat loss"},
        "CJC-1295 (no DAC)": {"Category":"Peptide", "Subclass":"GHRH Analog", "Primary Purpose":"Pulsatile GH release", "Typical Goal":"Lean mass"},
        "Sermorelin": {"Category":"Peptide", "Subclass":"GHRH Analog", "Primary Purpose":"Mild GH stimulation", "Typical Goal":"Anti-aging"},
        "Tesamorelin": {"Category":"Peptide", "Subclass":"GHRH Analog", "Primary Purpose":"Visceral fat reduction", "Typical Goal":"Fat loss"},
        "GHRP-6": {"Category":"Peptide", "Subclass":"GH Secretagogue", "Primary Purpose":"GH release, appetite increase", "Typical Goal":"Bulking"},
        "GHRP-2": {"Category":"Peptide", "Subclass":"GH Secretagogue", "Primary Purpose":"Strong GH release", "Typical Goal":"Lean growth"},
        "Ipamorelin": {"Category":"Peptide", "Subclass":"GH Secretagogue", "Primary Purpose":"Selective GH release", "Typical Goal":"Lean bulk"},
        "Hexarelin": {"Category":"Peptide", "Subclass":"GH Secretagogue", "Primary Purpose":"Potent GH release", "Typical Goal":"Muscle gain"},
        "MK-677 (Ibutamoren)": {"Category":"Peptide", "Subclass":"GH Secretagogue", "Primary Purpose":"GH & IGF-1 increase", "Typical Goal":"Lean mass"},
        "IGF-1 LR3": {"Category":"Peptide", "Subclass":"Growth Factor", "Primary Purpose":"Muscle cell proliferation", "Typical Goal":"Hypertrophy"},
        "IGF-1 DES": {"Category":"Peptide", "Subclass":"Growth Factor", "Primary Purpose":"Local muscle growth", "Typical Goal":"Targeted growth"},
        "MGF": {"Category":"Peptide", "Subclass":"Growth Factor", "Primary Purpose":"Muscle repair", "Typical Goal":"Recovery"},
        "PEG-MGF": {"Category":"Peptide", "Subclass":"Growth Factor", "Primary Purpose":"Extended muscle repair", "Typical Goal":"Lean growth"},
        "Follistatin-344": {"Category":"Peptide", "Subclass":"Myostatin Inhibitor", "Primary Purpose":"Blocks muscle growth limiter", "Typical Goal":"Extreme hypertrophy"},
        "ACE-031": {"Category":"Peptide", "Subclass":"Myostatin Inhibitor", "Primary Purpose":"Myostatin pathway blocker", "Typical Goal":"Experimental growth"},
        "BPC-157": {"Category":"Peptide", "Subclass":"Healing", "Primary Purpose":"Tendon & gut repair", "Typical Goal":"Injury recovery"},
        "TB-500": {"Category":"Peptide", "Subclass":"Healing", "Primary Purpose":"Tissue regeneration", "Typical Goal":"Recovery"},
        "GHK-Cu": {"Category":"Peptide", "Subclass":"Regenerative", "Primary Purpose":"Collagen & skin repair", "Typical Goal":"Anti-aging"},
        "Thymosin Alpha-1": {"Category":"Peptide", "Subclass":"Immune", "Primary Purpose":"Immune modulation", "Typical Goal":"Recovery"},
        "LL-37": {"Category":"Peptide", "Subclass":"Immune", "Primary Purpose":"Antimicrobial & healing", "Typical Goal":"Recovery"},
        "AOD-9604": {"Category":"Peptide", "Subclass":"Fat Loss", "Primary Purpose":"Lipolysis", "Typical Goal":"Cutting"},
        "HGH Fragment 176-191": {"Category":"Peptide", "Subclass":"Fat Loss", "Primary Purpose":"Fat metabolism", "Typical Goal":"Cutting"},
        "MOTS-c": {"Category":"Peptide", "Subclass":"Metabolic", "Primary Purpose":"Mitochondrial optimization", "Typical Goal":"Fat loss"},
        "5-Amino-1MQ": {"Category":"Peptide", "Subclass":"Research Peptide", "Primary Purpose":"NNMT inhibition", "Typical Goal":"Fat loss"},
        "Semaglutide": {"Category":"Peptide", "Subclass":"GLP-1 Agonist", "Primary Purpose":"Appetite suppression", "Typical Goal":"Weight loss"},
        "Tirzepatide": {"Category":"Peptide", "Subclass":"GLP-1/GIP Agonist", "Primary Purpose":"Appetite + glucose control", "Typical Goal":"Weight loss"},
        "Retatrutide": {"Category":"Peptide", "Subclass":"GLP-1/GIP/Glucagon Agonist", "Primary Purpose":"Triple agonist; major fat loss", "Typical Goal":"Weight reduction"},
        "Liraglutide": {"Category":"Peptide", "Subclass":"GLP-1 Agonist", "Primary Purpose":"Appetite suppression", "Typical Goal":"Weight loss"},
        "Insulin": {"Category":"Peptide Hormone", "Subclass":"Anabolic Hormone", "Primary Purpose":"Nutrient partitioning", "Typical Goal":"Mass gain"},
        "Pramlintide": {"Category":"Peptide", "Subclass":"Amylin Analog", "Primary Purpose":"Appetite control", "Typical Goal":"Fat loss"},
        "EPO (Erythropoietin)": {"Category":"Peptide Hormone", "Subclass":"Erythropoietic", "Primary Purpose":"RBC production", "Typical Goal":"Endurance"},
        "PT-141 (Bremelanotide)": {"Category":"Peptide", "Subclass":"Melanocortin", "Primary Purpose":"Libido enhancement", "Typical Goal":"Sexual health"},
        "Melanotan I": {"Category":"Peptide", "Subclass":"Melanocortin", "Primary Purpose":"Skin tanning", "Typical Goal":"Cosmetic"},
        "Melanotan II": {"Category":"Peptide", "Subclass":"Melanocortin", "Primary Purpose":"Tanning + libido", "Typical Goal":"Cosmetic"},
        "Selank": {"Category":"Peptide", "Subclass":"Nootropic", "Primary Purpose":"Anxiety reduction", "Typical Goal":"Cognitive"},
        "Semax": {"Category":"Peptide", "Subclass":"Nootropic", "Primary Purpose":"Cognitive enhancement", "Typical Goal":"Focus"},
        "Dihexa": {"Category":"Peptide", "Subclass":"Neurogenic", "Primary Purpose":"Neuroplasticity", "Typical Goal":"Cognitive"},
        "Epitalon": {"Category":"Peptide", "Subclass":"Longevity", "Primary Purpose":"Telomere research", "Typical Goal":"Anti-aging"},
        "SS-31 (Elamipretide)": {"Category":"Peptide", "Subclass":"Mitochondrial", "Primary Purpose":"Cellular energy support", "Typical Goal":"Longevity"},
        "Humanin": {"Category":"Peptide", "Subclass":"Mitochondrial", "Primary Purpose":"Cytoprotective", "Typical Goal":"Anti-aging"},
        # ------------------ STEROIDS ------------------
        "Testosterone Enanthate": {"Category":"AAS","Subclass":"Testosterone","Primary Purpose":"Mass & strength","Typical Goal":"Bulking"},
        "Testosterone Cypionate": {"Category":"AAS","Subclass":"Testosterone","Primary Purpose":"Mass & strength","Typical Goal":"Bulking"},
        "Testosterone Propionate": {"Category":"AAS","Subclass":"Testosterone","Primary Purpose":"Lean mass","Typical Goal":"Cutting"},
        "Sustanon 250": {"Category":"AAS","Subclass":"Testosterone Blend","Primary Purpose":"General anabolic base","Typical Goal":"Any phase"},
        "Dianabol": {"Category":"AAS","Subclass":"Oral Anabolic","Primary Purpose":"Rapid size gain","Typical Goal":"Bulking"},
        "Anadrol": {"Category":"AAS","Subclass":"Oral Anabolic","Primary Purpose":"Extreme mass","Typical Goal":"Bulking"},
        "Deca-Durabolin": {"Category":"AAS","Subclass":"Nandrolone","Primary Purpose":"Size + joint support","Typical Goal":"Bulking"},
        "Trenbolone": {"Category":"AAS","Subclass":"19-nor","Primary Purpose":"Mass + fat loss","Typical Goal":"Recomp"},
        "Superdrol": {"Category":"AAS","Subclass":"Oral Anabolic","Primary Purpose":"Rapid hypertrophy","Typical Goal":"Bulking"},
        "Equipoise": {"Category":"AAS","Subclass":"Boldenone","Primary Purpose":"Lean mass","Typical Goal":"Lean bulk"},
        "Winstrol": {"Category":"AAS","Subclass":"DHT Derivative","Primary Purpose":"Hardening","Typical Goal":"Cutting"},
        "Anavar": {"Category":"AAS","Subclass":"DHT Derivative","Primary Purpose":"Lean retention","Typical Goal":"Cutting"},
        "Primobolan": {"Category":"AAS","Subclass":"DHT Derivative","Primary Purpose":"Lean muscle","Typical Goal":"Cutting"},
        "Masteron": {"Category":"AAS","Subclass":"DHT Derivative","Primary Purpose":"Hardening effect","Typical Goal":"Contest prep"},
        "Turinabol": {"Category":"AAS","Subclass":"Oral Anabolic","Primary Purpose":"Lean strength","Typical Goal":"Recomp"},
        "Halotestin": {"Category":"AAS","Subclass":"Oral Androgen","Primary Purpose":"Strength & aggression","Typical Goal":"Strength peak"},
        "Proviron": {"Category":"AAS","Subclass":"DHT Derivative","Primary Purpose":"SHBG reduction","Typical Goal":"Hardening"},
        "Methyltestosterone": {"Category":"AAS","Subclass":"Oral Testosterone","Primary Purpose":"Androgenic boost","Typical Goal":"Strength"}
    }

    # ----------------------
    # 2️⃣ Session State for Custom Compounds
    # ----------------------
    if "custom_compounds" not in st.session_state:
        st.session_state.custom_compounds = {}

    # ----------------------
    # 3️⃣ Compound Selection
    # ----------------------
    compound_options = list(preloaded_compounds.keys()) + list(st.session_state.custom_compounds.keys()) + ["Custom"]
    compound_choice = st.selectbox("Select Compound", compound_options, key="compound_choice")

    amount = st.number_input("Amount (mg)", min_value=0.0, key="dose_amount")
    dose_date = st.date_input("Date", datetime.date.today(), key="dose_date")
    graph_type = st.selectbox("Graph Type", ["Bar","Line","Area"], key="graph_type")

    # ----------------------
    # 4️⃣ Handle Custom Compound Input
    # ----------------------
    if compound_choice == "Custom":
        compound_name = st.text_input("Enter Custom Compound Name")
        category = st.text_input("Category")
        subclass = st.text_input("Subclass")
        primary_purpose = st.text_input("Primary Purpose")
        typical_goal = st.text_input("Typical Goal")
        compound_info = {
            "Category": category,
            "Subclass": subclass,
            "Primary Purpose": primary_purpose,
            "Typical Goal": typical_goal
        }
    else:
        compound_name = compound_choice
        if compound_choice in preloaded_compounds:
            compound_info = preloaded_compounds[compound_choice]
        else:
            compound_info = st.session_state.custom_compounds[compound_choice]

    # ----------------------
    # 5️⃣ Display Compound Info
    # ----------------------
    st.subheader("Compound Info")
    st.write(f"**Category:** {compound_info['Category']}")
    st.write(f"**Subclass:** {compound_info['Subclass']}")
    st.write(f"**Primary Purpose:** {compound_info['Primary Purpose']}")
    st.write(f"**Typical Goal:** {compound_info['Typical Goal']}")

    # ----------------------
    # 6️⃣ Save Dose
    # ----------------------
    if st.button("Save Dose"):
        if not compound_name or amount <= 0:
            st.error("Please enter a valid compound and amount")
        else:
            # Save custom compound to session state
            if compound_choice == "Custom":
                st.session_state.custom_compounds[compound_name] = compound_info
            # Save dose to DB
            session.add(Dose(user_id=user_id, compound=compound_name, amount=amount, date=dose_date))
            session.commit()
            st.success(f"Dose saved: {compound_name} {amount} mg on {dose_date}")
            st.experimental_rerun()

    # ----------------------
    # 7️⃣ Fetch Doses
    # ----------------------
    doses = pd.read_sql(
        session.query(Dose).filter_by(user_id=user_id).statement,
        engine
    )

    if doses.empty:
        st.info("No doses logged yet.")
    else:
        doses["date"] = pd.to_datetime(doses["date"])
        doses["week"] = doses["date"].dt.isocalendar().week

        # ----------------------
        # Weekly Compound Summary Cards
        # ----------------------
        st.subheader("📅 Weekly Compound Summary")
        weekly_summary = doses.groupby(["week","compound"])["amount"].sum().reset_index()
        for _, row in weekly_summary.iterrows():
            st.metric(label=f"{row['compound']} (Week {row['week']})", value=f"{row['amount']} mg")

        # ----------------------
        # Active Cycle Tracker (last 7 days)
        # ----------------------
        st.subheader("🟢 Active Cycles (Last 7 Days)")
        cutoff = pd.Timestamp(datetime.date.today() - pd.Timedelta(days=7))
        active_compounds = doses[doses["date"] >= cutoff]
        if active_compounds.empty:
            st.info("No active compounds in the past 7 days")
        else:
            for c in active_compounds["compound"].unique():
                st.success(f"{c} active in last 7 days")

        # ----------------------
        # Visual Stack Timeline
        # ----------------------
        st.subheader("📊 Visual Stack Timeline")
        if graph_type == "Bar":
            fig_stack = px.bar(doses.sort_values("date"), x="date", y="amount", color="compound", title="Compound Stack Timeline")
        elif graph_type == "Line":
            fig_stack = px.line(doses.sort_values("date"), x="date", y="amount", color="compound", title="Compound Stack Timeline", markers=True)
        else:
            fig_stack = px.area(doses.sort_values("date"), x="date", y="amount", color="compound", title="Compound Stack Timeline")
        st.plotly_chart(fig_stack, use_container_width=True)
        
# ----------------------
# MEALS & CALORIE TRACKER PAGE
# ----------------------
if st.session_state.get("logged_in") and st.session_state.get("page") == "Meals":
    st.header("🍽 Meals & Calorie Tracker")

    import datetime
    import pandas as pd
    import plotly.express as px

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to view this page.")
        st.stop()

    # ----------------------
    # 1️⃣ Dynamic Daily Targets
    # ----------------------
    if "macro_targets" not in st.session_state:
        st.session_state.macro_targets = {
            "Calories": 2500,
            "Protein": 200,
            "Carbs": 300,
            "Fats": 70
        }

    st.subheader("Daily Macro Targets")
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.macro_targets["Calories"] = col1.number_input("Calories", min_value=0, value=st.session_state.macro_targets["Calories"])
    st.session_state.macro_targets["Protein"] = col2.number_input("Protein (g)", min_value=0, value=st.session_state.macro_targets["Protein"])
    st.session_state.macro_targets["Carbs"] = col3.number_input("Carbs (g)", min_value=0, value=st.session_state.macro_targets["Carbs"])
    st.session_state.macro_targets["Fats"] = col4.number_input("Fats (g)", min_value=0, value=st.session_state.macro_targets["Fats"])

    # ----------------------
    # 2️⃣ Default Foods
    # ----------------------
    default_foods = {
        "Chicken Breast (100g)": {"Calories":165, "Protein":31, "Carbs":0, "Fats":3.6},
        "Egg (1 large)": {"Calories":70, "Protein":6, "Carbs":0.4, "Fats":5},
        "Oatmeal (1 cup)": {"Calories":154, "Protein":6, "Carbs":27, "Fats":3},
        "Almonds (28g)": {"Calories":161, "Protein":6, "Carbs":6, "Fats":14},
        "Brown Rice (1 cup)": {"Calories":216, "Protein":5, "Carbs":45, "Fats":1.8},
        "Broccoli (100g)": {"Calories":55, "Protein":3.7, "Carbs":11, "Fats":0.6},
        "Salmon (100g)": {"Calories":208, "Protein":20, "Carbs":0, "Fats":13},
    }

    # Fetch user foods from DB
    user_foods = pd.read_sql(
        session.query(FoodItem).filter_by(user_id=user_id).statement,
        engine
    )
    user_food_dict = {
        row["name"]: {"Calories": row["calories"], "Protein": row["protein"], "Carbs": row["carbs"], "Fats": row["fats"]}
        for idx,row in user_foods.iterrows()
    }

    all_foods = {**default_foods, **user_food_dict}
    food_options = list(all_foods.keys()) + ["Add Custom Food"]

    # ----------------------
    # 3️⃣ Log Meals
    # ----------------------
    st.subheader("Log a Meal")
    food_choice = st.selectbox("Select Food", food_options)
    quantity = st.number_input("Quantity", min_value=1, value=1)
    date = st.date_input("Date", datetime.date.today())

    # Custom food input
    if food_choice == "Add Custom Food":
        food_name = st.text_input("Food Name")
        calories = st.number_input("Calories", min_value=0)
        protein = st.number_input("Protein (g)", min_value=0)
        carbs = st.number_input("Carbs (g)", min_value=0)
        fats = st.number_input("Fats (g)", min_value=0)
    else:
        food_name = food_choice
        calories = all_foods[food_choice]["Calories"]
        protein = all_foods[food_choice]["Protein"]
        carbs = all_foods[food_choice]["Carbs"]
        fats = all_foods[food_choice]["Fats"]

    if st.button("Log Meal"):
        if not food_name or calories <= 0:
            st.error("Enter a valid food and calories")
        else:
            # Save custom food if new
            if food_choice == "Add Custom Food":
                exists = session.query(FoodItem).filter_by(name=food_name, user_id=user_id).first()
                if not exists:
                    session.add(FoodItem(
                        user_id=user_id,
                        name=food_name,
                        calories=calories,
                        protein=protein,
                        carbs=carbs,
                        fats=fats
                    ))
                    session.commit()
                    st.success(f"Custom food '{food_name}' saved!")

            # Log meal
            session.add(MealLog(
                user_id=user_id,
                meal=food_name,
                calories=calories*quantity,
                protein=protein*quantity,
                carbs=carbs*quantity,
                fats=fats*quantity,
                date=date
            ))
            session.commit()
            st.success(f"{food_name} logged!")

# ----------------------
# 4️⃣ Fetch Logged Meals
# ----------------------
meals = pd.read_sql(
    session.query(MealLog).filter_by(user_id=user_id).statement,
    engine
)

if meals.empty:
    st.info("No meals logged yet.")
else:
    # Convert date column to datetime
    meals["date"] = pd.to_datetime(meals["date"])
    meals["week"] = meals["date"].dt.isocalendar().week

    # ----------------------
    # Get today's meals
    # ----------------------
    today = pd.Timestamp(datetime.date.today())
    today_meals = meals[meals["date"] == today]

    # ----------------------
    # 5️⃣ Graph Type Selection
    # ----------------------
    graph_type = st.selectbox("Select Graph Type", ["Bar", "Line", "Area"])

    # ----------------------
    # 6️⃣ Today's Macro Progress Bars with Indicators
    # ----------------------
    st.subheader("🍽 Today's Macro Progress")
    if not today_meals.empty:
        daily_totals = today_meals[["calories","protein","carbs","fats"]].sum()

        macro_order = ["Calories", "Protein", "Carbs", "Fats"]
        colors = {"Calories":"#FFA15A","Protein":"#EF553B","Carbs":"#636EFA","Fats":"#00CC96"}

        for macro in macro_order:
            macro_lower = macro.lower()
            target = st.session_state.macro_targets.get(macro, 0)
            actual = daily_totals.get(macro_lower, 0)
            pct = min(actual / target, 1.0)  # cap at 100% for progress bar

            st.markdown(f"**{macro}: {actual:.0f} / {target} ({pct*100:.0f}%)**")
            st.progress(pct)

            # Surplus / Deficit indicator
            if actual < target:
                st.warning(f"{macro} is under target by {target - actual:.0f} g")
            elif actual > target:
                st.success(f"{macro} is over target by {actual - target:.0f} g")
            else:
                st.info(f"{macro} meets the target exactly")

# ----------------------
# 7️⃣ Elite Weekly Nutrition System
# ----------------------
st.subheader("📊 Elite Weekly Nutrition Dashboard")

# Ensure datetime
meals["date"] = pd.to_datetime(meals["date"], errors="coerce")

today = pd.Timestamp.today().normalize()
seven_days_ago = today - pd.Timedelta(days=7)

weekly_meals = meals[meals["date"] >= seven_days_ago]

# Safe macro targets
macro_targets = st.session_state.get("macro_targets", {
    "Calories": 2500,
    "Protein": 180,
    "Carbs": 300,
    "Fats": 70
})

# ----------------------
# STOP if no meals
# ----------------------
if weekly_meals.empty:
    st.info("No meals logged in last 7 days.")
    st.stop()

# ----------------------
# Totals & Averages
# ----------------------
weekly_totals = weekly_meals[["calories","protein","carbs","fats"]].sum()
weekly_avg = weekly_meals[["calories","protein","carbs","fats"]].mean()

# ----------------------
# Compliance Score
# ----------------------
scores = []
for macro in ["Calories","Protein","Carbs","Fats"]:
    target = macro_targets[macro]
    avg_val = weekly_avg[macro.lower()]
    score = max(0, 100 - abs((avg_val - target) / target * 100))
    scores.append(score)

overall_score = sum(scores) / len(scores)
st.metric("🏆 Weekly Nutrition Compliance Score", f"{overall_score:.0f}/100")

# ----------------------
# Bodyweight & Protein Auto Adjust
# ----------------------
bodyweight = st.number_input("Bodyweight (lbs)", min_value=100, max_value=400, value=200)

recommended_protein = bodyweight * 1.0  # 1g per lb baseline
st.write(f"Recommended Protein (1g/lb): {recommended_protein:.0f}g")

# ----------------------
# Phase Mode
# ----------------------
phase = st.radio("Phase Mode", ["Cut", "Maintenance", "Bulk"], horizontal=True)

if phase == "Cut":
    calorie_adjustment = -300
elif phase == "Bulk":
    calorie_adjustment = 300
else:
    calorie_adjustment = 0

adjusted_calories = macro_targets["Calories"] + calorie_adjustment
st.write(f"Adjusted Calorie Target for {phase}: {adjusted_calories}")

# ----------------------
# Daily Aggregation
# ----------------------
daily_grouped = (
    weekly_meals
    .groupby(weekly_meals["date"].dt.date)
    [["calories","protein","carbs","fats"]]
    .sum()
    .reset_index()
)

# ----------------------
# Graph Type Selector
# ----------------------
graph_type = st.selectbox("Graph Type", ["Line", "Bar"])

if graph_type == "Line":
    fig = px.line(
        daily_grouped,
        x="date",
        y=["calories","protein","carbs","fats"],
        markers=True,
        title="7-Day Macro Trend"
    )
else:
    fig = px.bar(
        daily_grouped,
        x="date",
        y=["calories","protein","carbs","fats"],
        barmode="group",
        title="7-Day Macro Trend"
    )

st.plotly_chart(fig, use_container_width=True)

# ----------------------
# Weight Overlay (Optional)
# ----------------------
if "weight" in meals.columns:
    weight_data = weekly_meals.groupby(weekly_meals["date"].dt.date)["weight"].mean().reset_index()
    if not weight_data.empty:
        fig_weight = px.line(
            weight_data,
            x="date",
            y="weight",
            markers=True,
            title="Weight Trend (7 Days)"
        )
        st.plotly_chart(fig_weight, use_container_width=True)

# ----------------------
# Average vs Target Chart
# ----------------------
avg_df = pd.DataFrame({
    "Macro": ["Calories","Protein","Carbs","Fats"],
    "Average": [
        weekly_avg["calories"],
        weekly_avg["protein"],
        weekly_avg["carbs"],
        weekly_avg["fats"]
    ],
    "Target": [
        adjusted_calories,
        macro_targets["Protein"],
        macro_targets["Carbs"],
        macro_targets["Fats"]
    ]
})

fig_avg = px.bar(
    avg_df.melt(id_vars="Macro"),
    x="Macro",
    y="value",
    color="variable",
    barmode="group",
    title="Average Intake vs Target"
)

st.plotly_chart(fig_avg, use_container_width=True)

# ----------------------
# Coach Insight
# ----------------------
if weekly_avg["protein"] < recommended_protein:
    coach_msg = "Increase protein intake to match bodyweight recommendation."
elif weekly_avg["calories"] > adjusted_calories:
    coach_msg = "Calorie intake trending high for selected phase."
else:
    coach_msg = "Nutrition trending well for current phase."

st.info(f"🧠 Coach Insight: {coach_msg}")

# ----------------------
# 8️⃣ Weekly Macro Trends
# ----------------------
st.subheader("Weekly Macro Trends")

meals["week"] = meals["date"].dt.isocalendar().week

weekly_summary = (
    meals
    .groupby("week")[["protein","carbs","fats","calories"]]
    .sum()
    .reset_index()
)

if not weekly_summary.empty:

    if graph_type == "Bar":
        fig_weekly = px.bar(
            weekly_summary,
            x="week",
            y=["protein","carbs","fats"],
            title="Weekly Macros"
        )
    else:
        fig_weekly = px.line(
            weekly_summary,
            x="week",
            y=["protein","carbs","fats"],
            title="Weekly Macros"
        )

    st.plotly_chart(fig_weekly, use_container_width=True)

# ----------------------
# 9️⃣ Rolling 7-Day Averages
# ----------------------
st.subheader("7-Day Rolling Average")

meals_sorted = meals.sort_values("date")

rolling = (
    meals_sorted
    .set_index("date")[["protein","carbs","fats"]]
    .rolling("7D")
    .mean()
    .reset_index()
)

if not rolling.empty:
    fig_rolling = px.line(
        rolling,
        x="date",
        y=["protein","carbs","fats"],
        title="7-Day Rolling Average Macros"
    )

    st.plotly_chart(fig_rolling, use_container_width=True)
        
# ----------------------
# WORKOUT PAGE
# ----------------------
if st.session_state.get("logged_in") and st.session_state.get("page") == "Workouts":
    
    st.set_page_config(layout="wide")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to view this page.")
        st.stop()

    st.header("💪 Log Workout")

    # ----------------------
    # Load Exercises safely
    # ----------------------
    try:
        all_exercises = session.query(Exercise).all()
    except Exception as e:
        st.error(f"Error loading exercises: {e}")
        st.stop()

    if not all_exercises:
        st.warning("No exercises available.")
        st.stop()

    # ----------------------
    # Muscle Filter & Exercise Selection
    # ----------------------
    col1, col2 = st.columns(2)
    with col1:
        muscle_groups = sorted(list(set(ex.category for ex in all_exercises if ex.category)))
        selected_muscles = st.multiselect("Filter by Muscle Group", muscle_groups)
    with col2:
        filtered_exercises = [ex for ex in all_exercises if ex.category in selected_muscles] if selected_muscles else all_exercises
        exercise_options = [f"{ex.name} ({ex.category})" for ex in filtered_exercises]
        
        # Prefill from routine if available
        prefill = st.session_state.get("prefill_workout")
        if prefill:
            default_ex = prefill.get("exercise_name")
            default_idx = next((i for i, ex in enumerate(exercise_options) if ex.startswith(default_ex)), 0)
        else:
            default_idx = 0

        selected_exercise_display = st.selectbox("Exercise", exercise_options, index=default_idx)
        exercise = selected_exercise_display.split(" (")[0]

    # Clear prefill
    if prefill:
        st.session_state.pop("prefill_workout")

    # ----------------------
    # Workout Inputs
    # ----------------------
    col3, col4, col5 = st.columns(3)
    with col3:
        sets = st.number_input("Sets", min_value=1, value=prefill.get("sets") if prefill else 3, step=1)
        reps = st.number_input("Reps", min_value=1, value=prefill.get("reps") if prefill else 10, step=1)
    with col4:
        weight = st.number_input("Weight", min_value=0.0, value=0.0, step=0.5)
        rest_time = st.number_input("Rest (seconds)", min_value=0, value=prefill.get("rest_time") if prefill else 60, step=5)
    with col5:
        goal = st.selectbox(
            "Goal",
            ["Hypertrophy", "Strength", "Fat Loss", "Endurance"],
            index=["Hypertrophy","Strength","Fat Loss","Endurance"].index(prefill.get("goal")) if prefill else 0
        )
        date = st.date_input("Date", datetime.date.today())

    # ----------------------
    # Volume & 1RM
    # ----------------------
    volume = sets * reps * weight
    one_rm = weight * (1 + reps / 30)
    st.markdown(f"**Session Volume:** {volume:.1f} | **Estimated 1RM:** {one_rm:.1f} lbs")

    # ----------------------
    # Save Workout
    # ----------------------
    if st.button("Save Workout"):
        session.add(Workout(
            user_id=user_id,
            exercise=exercise,
            sets=int(sets),
            reps=int(reps),
            weight=float(weight),
            rest_time=int(rest_time),
            goal=goal,
            date=date
        ))
        session.commit()
        st.success("Workout saved!")
        st.experimental_rerun()

    st.markdown("---")

    # ----------------------
    # Load User Workouts
    # ----------------------
    workouts_df = pd.read_sql(
        session.query(Workout).filter_by(user_id=user_id).statement,
        engine
    )

    if workouts_df.empty:
        st.info("No workouts logged yet.")
        st.stop()

    workouts_df["date"] = pd.to_datetime(workouts_df["date"])
    workouts_df["volume"] = workouts_df["sets"] * workouts_df["reps"] * workouts_df["weight"]
    workouts_df["week"] = workouts_df["date"].dt.isocalendar().week
    workouts_df["1RM"] = workouts_df["weight"] * (1 + workouts_df["reps"] / 30)

    # ----------------------
    # 1️⃣ Volume & 1RM PR Tracker
    # ----------------------
    st.subheader("🏆 Volume & 1RM Personal Records")
    pr_df = workouts_df.groupby("exercise").agg({"volume":"max","1RM":"max"}).reset_index().sort_values("volume",ascending=False)
    st.dataframe(pr_df,use_container_width=True)

    # ----------------------
    # 2️⃣ Strength Progression Chart
    # ----------------------
    st.subheader("📈 Strength Progression")
    exercise_list = workouts_df["exercise"].unique()
    selected_ex = st.selectbox("Select Exercise to Track", exercise_list, key="progress_exercise")
    filtered = workouts_df[workouts_df["exercise"] == selected_ex]
    fig_progress = px.line(filtered.sort_values("date"), x="date", y="weight", markers=True, title=f"{selected_ex} Weight Progression")
    st.plotly_chart(fig_progress, use_container_width=True)

    # ----------------------
    # 3️⃣ Weekly Volume Summary
    # ----------------------
    st.subheader("📊 Weekly Volume")
    weekly_summary = workouts_df.groupby(["week","exercise"])["volume"].sum().reset_index()
    fig_weekly = px.bar(weekly_summary, x="week", y="volume", color="exercise", title="Weekly Workout Volume")
    st.plotly_chart(fig_weekly, use_container_width=True)

    st.markdown("---")

    # ----------------------
    # 4️⃣ Edit/Delete Workouts
    # ----------------------
    st.subheader("✏️ Edit / Delete Workouts")
    for idx,row in workouts_df.sort_values("date",ascending=False).iterrows():
        with st.expander(f"{row['date'].date()} - {row['exercise']} ({row['sets']}x{row['reps']} @ {row['weight']} lbs)"):
            new_sets = st.number_input(f"Sets ({row['exercise']})", min_value=1, value=int(row['sets']), key=f"sets_{idx}")
            new_reps = st.number_input(f"Reps ({row['exercise']})", min_value=1, value=int(row['reps']), key=f"reps_{idx}")
            new_weight = st.number_input(f"Weight ({row['exercise']})", min_value=0.0, value=float(row['weight']), step=0.5, key=f"weight_{idx}")
            new_rest = st.number_input(f"Rest ({row['exercise']})", min_value=0, value=int(row['rest_time']), key=f"rest_{idx}")
            new_date = st.date_input(f"Date ({row['exercise']})", value=row['date'].date(), key=f"date_{idx}")
            
            col_edit,col_delete = st.columns([1,1])
            with col_edit:
                if st.button("Update",key=f"update_{idx}"):
                    workout = session.query(Workout).get(row["id"])
                    workout.sets = int(new_sets)
                    workout.reps = int(new_reps)
                    workout.weight = float(new_weight)
                    workout.rest_time = int(new_rest)
                    workout.date = new_date
                    session.commit()
                    st.success("Workout updated!")
                    st.experimental_rerun()
            with col_delete:
                if st.button("Delete",key=f"delete_{idx}"):
                    workout = session.query(Workout).get(row["id"])
                    session.delete(workout)
                    session.commit()
                    st.success("Workout deleted!")
                    st.experimental_rerun()

# ----------------------
# ROUTINE BUILDER
# ----------------------
if st.session_state.get("logged_in") and st.session_state.get("page") == "Workouts":
    st.markdown("---")
    st.subheader("📝 Routine Builder")

    # Load routines
    routines = session.query(Routine).all()
    routine_names = [r.name for r in routines] if routines else []

    selected_routine_name = st.selectbox(
        "Select Routine",
        ["Custom"] + routine_names,
        key="routine_select"
    )

    # Initialize session state for custom routine
    if "custom_routine" not in st.session_state:
        st.session_state.custom_routine = []

    # Load selected routine exercises
    if selected_routine_name != "Custom" and routine_names:
        routine = session.query(Routine).filter_by(name=selected_routine_name).first()
        routine_exercises = session.query(RoutineExercise).filter_by(routine_id=routine.id).all()

        # Convert to editable list in session state
        st.session_state.custom_routine = [
            {
                "exercise_id": re.exercise_id,
                "exercise_name": session.query(Exercise).get(re.exercise_id).name,
                "sets": re.sets,
                "reps": re.reps,
                "rest_time": re.rest_time
            } for re in routine_exercises
        ]

    # Display current routine
    st.markdown("**Current Routine**")
    for idx, ex in enumerate(st.session_state.custom_routine):
        st.markdown(f"**{ex['exercise_name']}** - {ex['sets']}x{ex['reps']}, Rest {ex['rest_time']}s")
        cols = st.columns([1,1,1,1])
        with cols[0]:
            ex["sets"] = st.number_input(f"Sets {idx}", min_value=1, value=ex["sets"], key=f"sets_r_{idx}")
        with cols[1]:
            ex["reps"] = st.number_input(f"Reps {idx}", min_value=1, value=ex["reps"], key=f"reps_r_{idx}")
        with cols[2]:
            ex["rest_time"] = st.number_input(f"Rest {idx}", min_value=0, value=ex["rest_time"], key=f"rest_r_{idx}")
        with cols[3]:
            up_col, down_col, del_col = st.columns([1,1,1])
            if up_col.button("⬆️", key=f"up_{idx}") and idx > 0:
                st.session_state.custom_routine[idx], st.session_state.custom_routine[idx-1] = \
                    st.session_state.custom_routine[idx-1], st.session_state.custom_routine[idx]
                st.experimental_rerun()
            if down_col.button("⬇️", key=f"down_{idx}") and idx < len(st.session_state.custom_routine)-1:
                st.session_state.custom_routine[idx], st.session_state.custom_routine[idx+1] = \
                    st.session_state.custom_routine[idx+1], st.session_state.custom_routine[idx]
                st.experimental_rerun()
            if del_col.button("🗑️", key=f"del_{idx}"):
                st.session_state.custom_routine.pop(idx)
                st.experimental_rerun()

    # Add new exercise
    st.markdown("**Add Exercise to Routine**")
    exercise_options = [ex.name for ex in session.query(Exercise).all()]
    new_ex_name = st.selectbox("Exercise", exercise_options, key="new_routine_exercise")
    new_sets = st.number_input("Sets", min_value=1, value=3, step=1, key="new_routine_sets")
    new_reps = st.number_input("Reps", min_value=1, value=10, step=1, key="new_routine_reps")
    new_rest = st.number_input("Rest Time (s)", min_value=0, value=60, step=5, key="new_routine_rest")

    if st.button("➕ Add Exercise to Routine"):
        new_ex_id = session.query(Exercise).filter_by(name=new_ex_name).first().id
        st.session_state.custom_routine.append({
            "exercise_id": new_ex_id,
            "exercise_name": new_ex_name,
            "sets": new_sets,
            "reps": new_reps,
            "rest_time": new_rest
        })
        st.success(f"{new_ex_name} added!")
        st.experimental_rerun()

    # Save routine to DB
    if selected_routine_name != "Custom" and st.button("💾 Save Routine Changes"):
        # Delete old exercises
        session.query(RoutineExercise).filter_by(routine_id=routine.id).delete()
        session.commit()
        # Add new exercises
        for ex in st.session_state.custom_routine:
            session.add(RoutineExercise(
                routine_id=routine.id,
                exercise_id=ex["exercise_id"],
                sets=ex["sets"],
                reps=ex["reps"],
                rest_time=ex["rest_time"]
            ))
        session.commit()
        st.success(f"Routine '{routine.name}' updated!")
# ----------------------
# BLOODWORK PAGE
# ----------------------
if st.session_state.logged_in and page == "Bloodwork":
    st.header("Log Bloodwork")
    test = st.text_input("Test Name")
    value = st.number_input("Value", min_value=0.0, value=0.0)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Save Bloodwork"):
        session.add(Bloodwork(user_id=user_id, test=test, value=value, date=date))
        session.commit()
        st.success("Bloodwork saved!")

    blood = pd.read_sql(session.query(Bloodwork).filter_by(user_id=user_id).statement, engine)
    if not blood.empty:
        fig = px.line(blood, x="date", y="value", color="test", title="Bloodwork Trends")
        st.plotly_chart(fig)

# ----------------------
# PHOTOS PAGE
# ----------------------
if st.session_state.logged_in and page == "Photos":
    st.header("Progress Photos")
    if not os.path.exists("photos"):
        os.makedirs("photos")

    uploaded = st.file_uploader("Upload Photo", type=["jpg","png"])
    date = st.date_input("Date", datetime.date.today())

    if uploaded and st.button("Save Photo"):
        path = f"photos/{user_id}_{date}_{uploaded.name}"
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
        session.add(Photo(user_id=user_id, path=path, date=date))
        session.commit()
        st.success("Photo saved!")

    photos = session.query(Photo).filter_by(user_id=user_id).all()
    for p in photos:
        st.image(p.path, caption=str(p.date))
