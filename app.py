import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.express as px

# ----------------------
# DATABASE SETUP
# ----------------------
DB_PATH = "tracker.db"
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

class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String, unique=True)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)

class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    meal = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    date = Column(Date)

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    exercise = Column(String)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
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

Base.metadata.create_all(engine)

# ----------------------
# SESSION STATE INITIALIZATION
# ----------------------
# THIS MUST COME BEFORE ANY 'st.session_state.user' OR 'logged_in' ACCESS
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None
# ----------------------
# SIDEBAR NAVIGATION
# ----------------------
if st.session_state.user:
    page = st.sidebar.radio("Navigation", ["Dashboard","Dosing","Meals","Workouts","Bloodwork","Photos","Logout"])
else:
    choice = st.sidebar.radio("Account", ["Login", "Register"])
    page = None

# ----------------------
# LOGIN / REGISTER / LOGOUT
# ----------------------
if st.session_state.user is None:

    if choice == "Register":
        st.subheader("Create Account")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            if session.query(User).filter_by(email=email).first():
                st.error("Email already exists")
            else:
                user = User(email=email)
                user.set_password(password)
                session.add(user)
                session.commit()
                st.success("Account created! Please log in.")

    if choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = session.query(User).filter_by(email=email).first()
            if user and user.check_password(password):
                st.session_state.user = user.id
                st.success("Logged in successfully!")
            else:
                st.error("Invalid login credentials")

else:
    # Define user_id after login
    user_id = st.session_state.user

    if page == "Logout":
        st.session_state.user = None
        st.success("Logged out")

    # ----------------------
    # DASHBOARD
    # ----------------------
    if page == "Dashboard":
        st.header("Overview")
        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, engine)
        meals = pd.read_sql(session.query(Meal).filter_by(user_id=user_id).statement, engine)
        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)

        col1,col2,col3 = st.columns(3)
        col1.metric("Doses Logged", len(doses))
        col2.metric("Meals Logged", len(meals))
        col3.metric("Workouts Logged", len(workouts))

    # ----------------------
    # DOSING PAGE
    # ----------------------
if page == "Dosing":
    st.header("Log Dose")

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
    compound_choice = st.selectbox("Select Compound", compound_options)

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
    # MEALS PAGE
    # ----------------------
if page == "Meals":
    st.header("Meal & Calorie Tracking")

    # -----------------------
    # Prepopulated meals
    # -----------------------
    default_meals = {
        "Chicken Breast (100g)": {"Calories":165, "Protein":31, "Carbs":0, "Fats":3.6},
        "Egg (1 large)": {"Calories":70, "Protein":6, "Carbs":0.4, "Fats":5},
        "Oatmeal (1 cup)": {"Calories":154, "Protein":6, "Carbs":27, "Fats":3},
        "Almonds (28g)": {"Calories":161, "Protein":6, "Carbs":6, "Fats":14},
        "Brown Rice (1 cup)": {"Calories":216, "Protein":5, "Carbs":45, "Fats":1.8},
        "Broccoli (100g)": {"Calories":55, "Protein":3.7, "Carbs":11, "Fats":0.6},
        "Salmon (100g)": {"Calories":208, "Protein":20, "Carbs":0, "Fats":13},
    }

    # Fetch user-defined foods from DB
    user_foods = pd.read_sql(session.query(FoodItem).filter_by(user_id=user_id).statement, engine)
    user_food_dict = {row["name"]: {"Calories": row["calories"], "Protein": row["protein"], "Carbs": row["carbs"], "Fats": row["fats"]} for idx,row in user_foods.iterrows()}

    all_foods = {**default_meals, **user_food_dict}
    food_options = list(all_foods.keys()) + ["Add Custom Food"]
    food_choice = st.selectbox("Select Food", food_options)

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
                    session.add(FoodItem(user_id=user_id, name=food_name, calories=calories, protein=protein, carbs=carbs, fats=fats))
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
    # Fetch meal logs
    # -----------------------
    meals = pd.read_sql(session.query(MealLog).filter_by(user_id=user_id).statement, engine)
    if meals.empty:
        st.info("No meals logged yet.")
    else:
        meals["week"] = pd.to_datetime(meals["date"]).dt.isocalendar().week

        # Daily summary
        daily_summary = meals.groupby("date")[["calories","protein","carbs","fats"]].sum().reset_index()
        st.subheader("Daily Nutrition")
        st.line_chart(daily_summary.set_index("date"))

        # Weekly summary
        weekly_summary = meals.groupby("week")[["calories","protein","carbs","fats"]].sum().reset_index()
        st.subheader("Weekly Nutrition")
        st.bar_chart(weekly_summary.set_index("week"))

    # ----------------------
    # WORKOUTS PAGE
    # ----------------------
    if page == "Workouts":
        st.header("Log Workout")
        exercise = st.text_input("Exercise")
        sets = st.number_input("Sets",1)
        reps = st.number_input("Reps",1)
        weight = st.number_input("Weight",0.0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Workout"):
            session.add(Workout(user_id=user_id,exercise=exercise,
                                sets=sets,reps=reps,weight=weight,date=date))
            session.commit()
            st.success("Workout saved!")

        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)
        if not workouts.empty:
            workouts["volume"] = workouts["sets"]*workouts["reps"]*workouts["weight"]
            workouts["week"] = pd.to_datetime(workouts["date"]).dt.isocalendar().week
            summary = workouts.groupby(["week","exercise"])["volume"].sum().reset_index()
            fig = px.bar(summary, x="week", y="volume", color="exercise", title="Weekly Workout Volume")
            st.plotly_chart(fig)

    # ----------------------
    # BLOODWORK PAGE
    # ----------------------
    if page == "Bloodwork":
        st.header("Log Bloodwork")
        test = st.text_input("Test Name")
        value = st.number_input("Value",0.0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Bloodwork"):
            session.add(Bloodwork(user_id=user_id,test=test,value=value,date=date))
            session.commit()
            st.success("Bloodwork saved!")

        blood = pd.read_sql(session.query(Bloodwork).filter_by(user_id=user_id).statement, engine)
        if not blood.empty:
            fig = px.line(blood, x="date", y="value", color="test", title="Bloodwork Trends")
            st.plotly_chart(fig)

    # ----------------------
    # PHOTOS PAGE
    # ----------------------
    if page == "Photos":
        st.header("Progress Photos")
        if not os.path.exists("photos"):
            os.makedirs("photos")

        uploaded = st.file_uploader("Upload Photo", type=["jpg","png"])
        date = st.date_input("Date", datetime.date.today())

        if uploaded and st.button("Save Photo"):
            path = f"photos/{user_id}_{date}_{uploaded.name}"
            with open(path,"wb") as f:
                f.write(uploaded.getbuffer())
            session.add(Photo(user_id=user_id,path=path,date=date))
            session.commit()
            st.success("Photo saved!")

        photos = session.query(Photo).filter_by(user_id=user_id).all()
        for p in photos:
            st.image(p.path, caption=str(p.date))
