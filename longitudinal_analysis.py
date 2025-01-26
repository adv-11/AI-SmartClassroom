import streamlit as st
import pymongo
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from pymongo import MongoClient
import os
from dotenv import load_env

# MongoDB Connection
client = MongoClient(os.environ.get('MONGO_DB_URI'))
db = client["quiz-db"]
collection = db["scores"]

# Fetch Data from MongoDB
data = list(collection.find())
df = pd.json_normalize(data)

# Dashboard Configuration
st.set_page_config(page_title="Student Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("🎓 Student Performance Dashboard")

# Sidebar Navigation
st.sidebar.title("Student Navigation")
student_ids = df["student_id"].unique()
selected_student = st.sidebar.selectbox("Select a Student ID:", student_ids)

# Filter Data for Selected Student
student_data = df[df["student_id"] == selected_student]

if student_data.empty:
    st.warning(f"No data available for Student ID {selected_student}.")
else:
    # Student Info and Key Metrics
    st.header(f"Student Overview: ID {selected_student}")
    total_quizzes = student_data["quiz_id"].nunique()
    avg_score = student_data["score"].mean()
    max_score = student_data["score"].max()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Quizzes Taken", total_quizzes)
    col2.metric("Average Score", f"{avg_score:.2f}")
    col3.metric("Highest Score", max_score)

    st.markdown("---")

    # Quiz-wise Performance Bar Chart
    st.subheader("Bar Chart: Performance by Quiz")
    quiz_scores = student_data[["quiz_id", "score"]]
    bar_chart = px.bar(
        quiz_scores,
        x="quiz_id",
        y="score",
        title="Performance in Each Quiz",
        labels={"quiz_id": "Quiz ID", "score": "Score"},
        color="score",
        color_continuous_scale=["#add8e6", "#4682b4"],  # Gradient from light blue to steel blue
    )
    bar_chart.update_layout(
        paper_bgcolor="white", 
        plot_bgcolor="white",
        coloraxis_colorbar=dict(title="Score", tickvals=list(range(0, 11))),
    )
    st.plotly_chart(bar_chart, use_container_width=True)

    st.markdown("---")

    # Line Chart: Score Progression
    st.subheader("Line Chart: Score Progression")
    score_progression = student_data.sort_values("quiz_id")
    line_chart = px.line(
        score_progression,
        x="quiz_id",
        y="score",
        title="Score Progression Over Time",
        markers=True,
        labels={"quiz_id": "Quiz ID", "score": "Score"},
    )
    line_chart.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black")
    )
    st.plotly_chart(line_chart, use_container_width=True)

    st.markdown("---")

    # Detailed Table of Responses
    st.subheader("Detailed Responses")
    if "responses" in df.columns:
        responses = pd.json_normalize(data, "responses", ["student_id", "quiz_id"])
        student_responses = responses[responses["student_id"] == selected_student]

        if not student_responses.empty:
            st.write("Responses for Each Question:")
            st.dataframe(student_responses[["quiz_id", "question_id", "selected_option", "is_correct"]])
        else:
            st.warning("No detailed responses available for this student.")

    # Footer
    st.markdown("Built with ❤️ using Streamlit")
#st.cloumns
#pygo