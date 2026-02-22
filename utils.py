import pandas as pd
import plotly.express as px
from database import Dose, Meal, Workout, Bloodwork, Session
import datetime

session = Session()

def weekly_dose_chart(user_id):
    doses = pd.read_sql(session.query(Dose).filter(Dose.user_id==user_id).statement, session.bind)
    if doses.empty:
        return None
    doses['week'] = doses['date'].apply(lambda x: x.isocalendar()[1])
    summary = doses.groupby(['week', 'compound'])['amount_mg'].sum().reset_index()
    fig = px.bar(summary, x='week', y='amount_mg', color='compound', barmode='group', title='Weekly Dose Summary')
    return fig

def weekly_meals_chart(user_id):
    meals = pd.read_sql(session.query(Meal).filter(Meal.user_id==user_id).statement, session.bind)
    if meals.empty:
        return None
    meals['week'] = meals['date'].apply(lambda x: x.isocalendar()[1])
    summary = meals.groupby('week')[['calories','protein','carbs','fats']].sum().reset_index()
    fig = px.line(summary, x='week', y=['calories','protein','carbs','fats'], title='Weekly Macros')
    return fig

def weekly_workout_chart(user_id):
    workouts = pd.read_sql(session.query(Workout).filter(Workout.user_id==user_id).statement, session.bind)
    if workouts.empty:
        return None
    workouts['volume'] = workouts['sets']*workouts['reps']*workouts['weight']
    workouts['week'] = workouts['date'].apply(lambda x: x.isocalendar()[1])
    summary = workouts.groupby(['week','exercise'])['volume'].sum().reset_index()
    fig = px.bar(summary, x='week', y='volume', color='exercise', barmode='group', title='Weekly Workout Volume')
    return fig

def bloodwork_chart(user_id):
    blood = pd.read_sql(session.query(Bloodwork).filter(Bloodwork.user_id==user_id).statement, session.bind)
    if blood.empty:
        return None
    fig = px.line(blood, x='date', y='value', color='test_name', markers=True, title='Bloodwork Trends')
    return fig
