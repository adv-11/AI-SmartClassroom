import streamlit as st
import pymongo
import pandas as pd
import matplotlib.pyplot as plt

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://gayatrikurulkar:gaya031202@quiz-cluster.rde4k.mongodb.net/?retryWrites=true&w=majority&appName=quiz-cluster")
db = client["quiz-db"]
collection = db["scores"]

# Fetch data from MongoDB
data = list(collection.find())
df = pd.DataFrame(data)

# Ensure '_id' is not part of the analysis
df = df.drop(columns=["_id"], errors="ignore")

# Allow student selection
st.title("Student Progress Dashboard")
student_ids = df["student_id"].unique()
selected_student = st.selectbox("Select a Student ID", student_ids)

# Filter data for the selected student
student_data = df[df["student_id"] == selected_student]

# Ensure quizzes are sorted in chronological order
student_data = student_data.sort_values(by=["quiz_id"])

# Check if the student has multiple quiz attempts
if len(student_data) < 2:
    st.warning("This student has not attempted multiple quizzes.")
else:
    # Create a line chart for progress
    fig, ax = plt.subplots()
    ax.plot(student_data["quiz_id"], student_data["score"], marker="o", label="Score")
    ax.set_title(f"Progress for Student {selected_student}")
    ax.set_xlabel("Quiz ID")
    ax.set_ylabel("Score")
    ax.grid(True)
    ax.legend()

    # Display the line chart
    st.pyplot(fig)

# Optional: Display raw data
st.write("Raw Data for Selected Student")
st.write(student_data)
