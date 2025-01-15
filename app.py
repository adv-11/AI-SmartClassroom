import streamlit as st
import pymongo
import pandas as pd

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://gayatrikurulkar:gaya031202@quiz-cluster.rde4k.mongodb.net/?retryWrites=true&w=majority&appName=quiz-cluster")  # Update if using a different connection string
db = client["quiz-db"]  # Replace with your actual database name

# Fetch data from the 'score' collection
score_collection = db["scores"]
scores_data = list(score_collection.find())

# Convert data to DataFrame for easier manipulation
df = pd.DataFrame(scores_data)

# Show the data in Streamlit
#st.write(df)

import matplotlib.pyplot as plt

# Plot bar chart of scores per student
fig, ax = plt.subplots()
ax.bar(df["student_id"], df["score"])
ax.set_xlabel('Student ID')
ax.set_ylabel('Score')
st.pyplot(fig)

# Show average score
average_score = df["score"].mean()
st.write(f"Average Score: {average_score}")

# Print column names to debug
print("Column Names in DataFrame:", df.columns)
