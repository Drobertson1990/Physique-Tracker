import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.express as px

# ----------------------
# DATABASE SETUP
# ----------------------

engine = create_engine("sqlite:///tracker.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# ----------------------
# MODELS
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

class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    calories = Column(Integer)
    protein = Column(Integer)
    carbs = Column(Integer)
    fats = Column(Integer)
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
# APP START
# ----------------------

st.set_page_config(layout="wide")
st.title("💪 Physique Tracker")

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------
# SIDEBAR AND LOGIN / REGISTER
# ----------------------
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar
if st.session_state.user:
    # Show navigation sidebar
    page = st.sidebar.radio("Navigation", ["Dashboard","Dosing","Meals","Workouts","Bloodwork","Photos","Logout"])
else:
    # Show login/register sidebar
    choice = st.sidebar.radio("Account", ["Login", "Register"])
    page = None

# LOGIN / REGISTER HANDLING
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
    # LOGOUT
    if page == "Logout":
        st.session_state.user = None
        st.success("Logged out")
    # ---------------- Dashboard ----------------
    if page == "Dashboard":
        st.header("Overview")

        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, engine)
        meals = pd.read_sql(session.query(Meal).filter_by(user_id=user_id).statement, engine)
        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)

        col1,col2,col3 = st.columns(3)
        col1.metric("Doses", len(doses))
        col2.metric("Meals", len(meals))
        col3.metric("Workouts", len(workouts))

    # ---------------- Dosing ----------------
    if page == "Dosing":
        st.header("Log Dose")

        compounds = ["BPC-157","TB-500","CJC-1295","Ipamorelin",
                     "Testosterone","Nandrolone","Oxandrolone","Custom"]

        compound = st.selectbox("Compound", compounds)

        if compound == "Custom":
            compound = st.text_input("Enter Custom Compound")

        amount = st.number_input("Amount (mg)", min_value=0.0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Dose"):
            session.add(Dose(user_id=user_id, compound=compound, amount=amount, date=date))
            session.commit()
            st.success("Saved")

        doses = pd.read_sql(session.query(Dose).filter_by(user_id=user_id).statement, engine)
        if not doses.empty:
            doses["week"] = pd.to_datetime(doses["date"]).dt.isocalendar().week
            summary = doses.groupby(["week","compound"])["amount"].sum().reset_index()
            fig = px.bar(summary, x="week", y="amount", color="compound", title="Weekly Totals")
            st.plotly_chart(fig)

    # ---------------- Meals ----------------
    if page == "Meals":
        st.header("Log Meal")

        name = st.text_input("Meal Name")
        calories = st.number_input("Calories",0)
        protein = st.number_input("Protein",0)
        carbs = st.number_input("Carbs",0)
        fats = st.number_input("Fats",0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Meal"):
            session.add(Meal(user_id=user_id,name=name,calories=calories,
                             protein=protein,carbs=carbs,fats=fats,date=date))
            session.commit()
            st.success("Saved")

        meals = pd.read_sql(session.query(Meal).filter_by(user_id=user_id).statement, engine)
        if not meals.empty:
            meals["week"] = pd.to_datetime(meals["date"]).dt.isocalendar().week
            summary = meals.groupby("week")[["calories","protein","carbs","fats"]].sum().reset_index()
            fig = px.line(summary, x="week", y=["calories","protein","carbs","fats"])
            st.plotly_chart(fig)

    # ---------------- Workouts ----------------
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
            st.success("Saved")

        workouts = pd.read_sql(session.query(Workout).filter_by(user_id=user_id).statement, engine)
        if not workouts.empty:
            workouts["volume"] = workouts["sets"]*workouts["reps"]*workouts["weight"]
            workouts["week"] = pd.to_datetime(workouts["date"]).dt.isocalendar().week
            summary = workouts.groupby(["week","exercise"])["volume"].sum().reset_index()
            fig = px.bar(summary, x="week", y="volume", color="exercise")
            st.plotly_chart(fig)

    # ---------------- Bloodwork ----------------
    if page == "Bloodwork":
        st.header("Bloodwork")

        test = st.text_input("Test Name")
        value = st.number_input("Value",0.0)
        date = st.date_input("Date", datetime.date.today())

        if st.button("Save Bloodwork"):
            session.add(Bloodwork(user_id=user_id,test=test,value=value,date=date))
            session.commit()
            st.success("Saved")

        blood = pd.read_sql(session.query(Bloodwork).filter_by(user_id=user_id).statement, engine)
        if not blood.empty:
            fig = px.line(blood, x="date", y="value", color="test")
            st.plotly_chart(fig)

    # ---------------- Photos ----------------
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
            st.success("Saved")

        photos = session.query(Photo).filter_by(user_id=user_id).all()
        for p in photos:
            st.image(p.path, caption=str(p.date))
