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
# Ensure rest_time column exists in Workouts table
# ----------------------
with engine.connect() as conn:
    try:
        # Attempt to add 'rest_time' column, default 60 seconds
        conn.execute(text('ALTER TABLE workouts ADD COLUMN rest_time INTEGER DEFAULT 60'))
        conn.commit()
    except Exception:
        # If the column already exists, ignore the error
        pass

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
Base.metadata.create_all(engine)
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
        conn.execute(text("ALTER TABLE exercises ADD COLUMN equipment STRING DEFAULT ''"))
    if 'secondary_muscles' not in columns:
        conn.execute(text("ALTER TABLE exercises ADD COLUMN secondary_muscles STRING DEFAULT ''"))
        
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
    email_input = st.sidebar.text_input("Email", key="email_input")
    password_input = st.sidebar.text_input("Password", type="password", key="password_input")
    st.sidebar.button("Login", key="login_btn")
    st.sidebar.button("Register", key="register_btn")

    if auth_mode == "Register" and st.sidebar.button("Register"):
        if email_input.strip() and password_input.strip():
            existing = session.query(User).filter_by(email=email_input).first()
            if existing:
                st.sidebar.error("User already exists")
            else:
                new_user = User(email=email_input)
                new_user.set_password(password_input)
                session.add(new_user)
                session.commit()
                st.sidebar.success("User registered! You can now log in.")
        else:
            st.sidebar.error("Enter email and password")

    if auth_mode == "Login" and st.sidebar.button("Login"):
        user = session.query(User).filter_by(email=email_input).first()
        if user and user.check_password(password_input):
            login_user(user)
            st.experimental_rerun()  # Safe rerun AFTER session state updates
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
        st.experimental_rerun()
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
    # DOSING PAGE
    # ----------------------
if st.session_state.logged_in and page == "Dosing":
    st.header("Dosing Tracker Page")
    st.info("Add your dosing logic here")

    # ----------------------
    # Prepopulated compounds with detailed info
    # ----------------------
    compounds = {
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
       
    # Add Custom option
    compound_options = list(compounds.keys()) + ["Custom"]
    compound_choice = st.selectbox("Select Compound", compound_options, key="compound_choice")
    amount = st.number_input("Amount (mg)", min_value=0.0, key="dose_amount")
    date = st.date_input("Date", datetime.date.today(), key="dose_date")
    st.button("Save Dose", key="save_dose_btn")
    graph_type = st.selectbox("Graph Type", ["Bar","Line","Area"], key="graph_type")

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
        compound_info = compounds[compound_choice]

    # Display info
    st.subheader("Compound Info")
    st.write(f"**Category:** {compound_info['Category']}")
    st.write(f"**Subclass:** {compound_info['Subclass']}")
    st.write(f"**Primary Purpose:** {compound_info['Primary Purpose']}")
    st.write(f"**Typical Goal:** {compound_info['Typical Goal']}")

    # Dose input
    amount = st.number_input("Amount (mg)", min_value=0.0)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Save Dose"):
        if compound_name.strip() == "" or amount <= 0:
            st.error("Please enter a valid compound and amount")
        else:
            session.add(Dose(user_id=user_id, compound=compound_name, amount=amount, date=date))
            session.commit()
            st.success("Dose saved!")

    # ----------------------
    # Graph Style Selector
    # ----------------------
    graph_type = st.selectbox("Graph Type", ["Bar","Line","Area"])

    # Fetch doses
    doses = pd.read_sql(
        session.query(Dose).filter_by(user_id=user_id).statement,
        engine
    )

    if doses.empty:
        st.info("No doses logged yet.")
    else:
        if "amount" in doses.columns and "compound" in doses.columns and "date" in doses.columns:
            doses["week"] = pd.to_datetime(doses["date"]).dt.isocalendar().week
            summary = doses.groupby(["week","compound"])["amount"].sum().reset_index()
            if graph_type == "Bar":
                fig = px.bar(summary, x="week", y="amount", color="compound", title="Weekly Dose Totals")
            elif graph_type == "Line":
                fig = px.line(summary, x="week", y="amount", color="compound", title="Weekly Dose Totals")
            else:
                fig = px.area(summary, x="week", y="amount", color="compound", title="Weekly Dose Totals")
            st.plotly_chart(fig)
        else:
            st.error("Dose table missing expected columns.")
# ----------------------
# MEALS & CALORIE TRACKER PAGE
# ----------------------
if st.session_state.logged_in and page == "Meals":
    st.header("Meals & Calorie Tracker")
    st.info("Add your meals logic here")
    
    # Default foods
    default_foods = {
        "Chicken Breast (100g)": {"Calories":165, "Protein":31, "Carbs":0, "Fats":3.6},
        "Egg (1 large)": {"Calories":70, "Protein":6, "Carbs":0.4, "Fats":5},
        "Oatmeal (1 cup)": {"Calories":154, "Protein":6, "Carbs":27, "Fats":3},
        "Almonds (28g)": {"Calories":161, "Protein":6, "Carbs":6, "Fats":14},
        "Brown Rice (1 cup)": {"Calories":216, "Protein":5, "Carbs":45, "Fats":1.8},
        "Broccoli (100g)": {"Calories":55, "Protein":3.7, "Carbs":11, "Fats":0.6},
        "Salmon (100g)": {"Calories":208, "Protein":20, "Carbs":0, "Fats":13},
    }

    # Fetch user foods
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

    food_choice = st.selectbox("Select Food", food_options, key="food_choice")
    food_name = st.text_input("Food Name", key="custom_food_name")
    calories = st.number_input("Calories", min_value=0, key="food_calories")
    protein = st.number_input("Protein (g)", min_value=0, key="food_protein")
    carbs = st.number_input("Carbs (g)", min_value=0, key="food_carbs")
    fats = st.number_input("Fats (g)", min_value=0, key="food_fats")
    quantity = st.number_input("Quantity", min_value=1, value=1, key="food_quantity")
    date = st.date_input("Date", datetime.date.today(), key="meal_date")
    st.button("Log Meal", key="log_meal_btn")

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

    quantity = st.number_input("Quantity", min_value=1, value=1)
    date = st.date_input("Date", datetime.date.today())

    if st.button("Log Meal"):
        if food_name.strip() == "" or calories <= 0:
            st.error("Enter a valid food and calories")
        else:
            # Save custom food if not default
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

            # Log the meal
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

    # -----------------------
    # FETCH LOGGED MEALS
    # -----------------------
    meals = pd.read_sql(
        session.query(MealLog).filter_by(user_id=user_id).statement,
        engine
    )

    if meals.empty:
        st.info("No meals logged yet.")
    else:
        meals["week"] = pd.to_datetime(meals["date"]).dt.isocalendar().week

        # Daily Pie Chart
        st.subheader("Today's Macro Breakdown")
        today = datetime.date.today()
        today_meals = meals[meals["date"] == pd.to_datetime(today)]
        if not today_meals.empty:
            daily_totals = today_meals[["protein","carbs","fats"]].sum()
            fig_pie = px.pie(
                values=daily_totals.values,
                names=daily_totals.index,
                title=f"Macros for {today}"
            )
            st.plotly_chart(fig_pie)

        # Daily stacked macro chart
        st.subheader("Daily Macros Over Time")
        daily_summary = meals.groupby("date")[["protein","carbs","fats"]].sum().reset_index()
        fig_daily = px.bar(
            daily_summary,
            x="date",
            y=["protein","carbs","fats"],
            title="Daily Macros",
            labels={"value":"Grams", "date":"Date"},
            color_discrete_map={"protein":"#EF553B","carbs":"#636EFA","fats":"#00CC96"}
        )
        st.plotly_chart(fig_daily)

        # Weekly stacked macro chart
        st.subheader("Weekly Macros")
        weekly_summary = meals.groupby("week")[["protein","carbs","fats"]].sum().reset_index()
        fig_weekly = px.bar(
            weekly_summary,
            x="week",
            y=["protein","carbs","fats"],
            title="Weekly Macros",
            labels={"value":"Grams", "week":"Week"},
            color_discrete_map={"protein":"#EF553B","carbs":"#636EFA","fats":"#00CC96"}
        )
        st.plotly_chart(fig_weekly)
        
# ----------------------
# WORKOUT PAGE
# ----------------------
if st.session_state.get("logged_in") and st.session_state.get("page") == "Workouts":

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to view this page.")
        st.stop()

    st.header("Log Workout")

   # ----------------------
# Exercise selection with Muscle Filter
# ----------------------

    all_exercises = session.query(Exercise).all()

if not all_exercises:
    st.warning("No exercises available. Please add exercises first.")
    st.stop()

    # Get unique muscle groups
    muscle_groups = sorted(list(set([ex.muscle_group for ex in all_exercises if ex.muscle_group])))

    selected_muscle = st.selectbox(
    "Filter by Muscle Group",
    ["All"] + muscle_groups,
    key="muscle_filter"
)

    # Apply filter
if selected_muscle == "All":
    filtered_exercises = all_exercises
else:
    filtered_exercises = [
        ex for ex in all_exercises if ex.muscle_group == selected_muscle
    ]

    exercise_library = [ex.name for ex in filtered_exercises]

if not exercise_library:
    st.warning("No exercises found for this muscle group.")
    st.stop()

    exercise = st.selectbox(
    "Exercise",
    exercise_library,
    key="workout_exercise"
)
    # ----------------------
    # Workout inputs
    # ----------------------
    sets = st.number_input("Sets", min_value=1, value=1, step=1)
    reps = st.number_input("Reps", min_value=1, value=1, step=1)
    weight = st.number_input("Weight", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    rest_time = st.number_input("Rest (seconds)", min_value=0, value=60, step=5)
    goal = st.selectbox("Goal", ["Hypertrophy", "Strength", "Fat Loss", "Endurance"])
    date = st.date_input("Date", datetime.date.today())

    # ----------------------
    # Save workout
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

    # ----------------------
    # Display workout summary
    # ----------------------
    try:
        workouts_df = pd.read_sql(
            session.query(Workout).filter_by(user_id=user_id).statement,
            engine
        )
    except Exception:
        st.error("Unable to load workouts. Check database setup.")
        st.stop()

    if not workouts_df.empty:
        workouts_df["volume"] = workouts_df["sets"] * workouts_df["reps"] * workouts_df["weight"]
        workouts_df["week"] = pd.to_datetime(workouts_df["date"]).dt.isocalendar().week

        weekly_summary = workouts_df.groupby(["week","exercise"])["volume"].sum().reset_index()
        fig = px.bar(
            weekly_summary,
            x="week",
            y="volume",
            color="exercise",
            title="Weekly Workout Volume"
        )
        st.plotly_chart(fig)
    else:
        st.info("No workouts logged yet.")

    # ----------------------
    # Routine selection
    # ----------------------
    routines = session.query(Routine).all()
    routine_names = [r.name for r in routines] if routines else []
    selected_routine_name = st.selectbox(
    "Select Routine",
    ["Custom"] + routine_names,
    key="workout_routine_select"
)

    if selected_routine_name != "Custom" and routine_names:
        routine = session.query(Routine).filter_by(name=selected_routine_name).first()
        routine_exercises = session.query(RoutineExercise).filter_by(routine_id=routine.id).all()
        st.subheader(f"Routine: {routine.name} ({routine.goal})")

        for re in routine_exercises:
            ex = session.query(Exercise).get(re.exercise_id)
            st.write(f"**{ex.name}** - {re.sets}x{re.reps}, Rest {re.rest_time}s")
  
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
