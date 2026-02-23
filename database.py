import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash

engine = create_engine("sqlite:///tracker.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)

# --------------------
# USERS
# --------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)

    doses = relationship("Dose", back_populates="user")
    meals = relationship("Meal", back_populates="user")
    workouts = relationship("Workout", back_populates="user")
    bloodwork = relationship("Bloodwork", back_populates="user")
    cycles = relationship("Cycle", back_populates="user")
    photos = relationship("Photo", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --------------------
# DOSES
# --------------------
class Dose(Base):
    __tablename__ = "doses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    compound = Column(String)
    amount_mg = Column(Float)
    date = Column(Date, default=datetime.date.today)
    user = relationship("User", back_populates="doses")

# --------------------
# CYCLE PLANNER
# --------------------
class Cycle(Base):
    __tablename__ = "cycles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    compound = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    weekly_dose = Column(Float)
    user = relationship("User", back_populates="cycles")

# --------------------
# MEALS
# --------------------
class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meal_name = Column(String)
    calories = Column(Integer)
    protein = Column(Integer)
    carbs = Column(Integer)
    fats = Column(Integer)
    date = Column(Date, default=datetime.date.today)
    user = relationship("User", back_populates="meals")

# --------------------
# WORKOUTS
# --------------------
class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise = Column(String)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    date = Column(Date, default=datetime.date.today)
    user = relationship("User", back_populates="workouts")

# --------------------
# BLOODWORK
# --------------------
class Bloodwork(Base):
    __tablename__ = "bloodwork"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_name = Column(String)
    value = Column(Float)
    date = Column(Date, default=datetime.date.today)
    user = relationship("User", back_populates="bloodwork")

# --------------------
# PROGRESS PHOTOS
# --------------------
class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String)
    date = Column(Date, default=datetime.date.today)
    user = relationship("User", back_populates="photos")

def init_db():
    Base.metadata.create_all(engine)
