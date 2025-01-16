import streamlit as st
import pymongo
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb+srv://gayatrikurulkar:gaya031202@quiz-cluster.rde4k.mongodb.net/?retryWrites=true&w=majority&appName=quiz-cluster")
db = client["quiz-db"]
collection = db["scores"]

# Fetch Data from MongoDB
data = list(collection.find())
df = pd.json_normalize(data)

# Dashboard
st.set_page_config(page_title="Attractive Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.title("📊 Student Quiz Performance Dashboard")

# Key Metrics
st.subheader("Key Metrics")
total_students = df["student_id"].nunique()
total_quizzes = df["quiz_id"].nunique()
avg_score = df["score"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total Students", total_students)
col2.metric("Total Quizzes", total_quizzes)
col3.metric("Average Score", f"{avg_score:.2f}")

st.markdown("---")


# Sidebar
st.sidebar.title("Navigation")
options = ["Overview", "Detailed Analysis"]
choice = st.sidebar.radio("Select a View:", options)

# Pie Chart: Correct vs Incorrect
st.subheader("Correct vs Incorrect Responses")
if "responses" in df.columns:
    responses = pd.json_normalize(data, "responses", ["student_id", "quiz_id"])
    correct_count = responses["is_correct"].sum()
    incorrect_count = len(responses) - correct_count

    pie_data = pd.DataFrame({
        "Response Type": ["Correct", "Incorrect"],
        "Count": [correct_count, incorrect_count]
    })

    pie_chart = px.pie(pie_data, names="Response Type", values="Count", title="Overall Responses")
    st.plotly_chart(pie_chart, use_container_width=True)

st.markdown("---")

# Line Chart: Distribution of Scores
st.subheader("Line Chart: Distribution of Scores")
if "score" in df.columns:
    score_distribution = df["score"].value_counts().sort_index()

    # Create figure with a smaller size
    fig, ax = plt.subplots(figsize=(6, 3))  # Adjusted figure size to be smaller
    
    # Plot the line chart
    ax.plot(
        score_distribution.index,
        score_distribution.values,
        marker="o",
        color="cyan",
        linewidth=2,
    )

    # Set axis labels and title with black font color
    ax.set_xlabel("Scores", fontsize=10, color="black")
    ax.set_ylabel("Frequency", fontsize=10, color="black")
    ax.set_title("Score Distribution", fontsize=12, color="black")
    
    # Adjust tick parameters for clarity and black font color
    ax.tick_params(axis="x", labelsize=8, rotation=45, colors="black")  # Rotate x-axis labels if needed for clarity
    ax.tick_params(axis="y", labelsize=8, colors="black")

    # Set the background color to white for both the plot and figure
    ax.set_facecolor("white")  # Set the plot area background to white
    fig.patch.set_facecolor("white")  # Set the outer figure background to white

    # Change axis color to black
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.spines['bottom'].set_color('black')

    # Display the plot
    st.pyplot(fig)
else:
    st.write("No scores available.")

st.markdown("---")


# Footer
st.markdown("Built with ❤️ using Streamlit")
