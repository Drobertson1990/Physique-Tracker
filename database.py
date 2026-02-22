from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

engine = create_engine("sqlite:///tracker.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Dose(Base):
    __tablename__ = "doses"
    id = Column(Integer, primary_key=True)
    compound = Column(String)
    amount_mg = Column(Float)
    date = Column(Date, default=datetime.date.today)

class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    meal_name = Column(String)
    calories = Column(Integer)
    protein = Column(Integer)
    carbs = Column(Integer)
    fats = Column(Integer)
    date = Column(Date, default=datetime.date.today)

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    exercise = Column(String)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    date = Column(Date, default=datetime.date.today)

def init_db():
    Base.metadata.create_all(engine)
