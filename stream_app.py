import streamlit as st

from pymongo import MongoClient
# Connect to MongoDB
connection_string = "mongodb+srv://gayatrikurulkar:gaya031202@quiz-cluster.rde4k.mongodb.net/"
client = MongoClient(connection_string)
db = client['quiz-db']
collection = db['quizcollect']

# Streamlit app
st.title("Quiz Viewer")
quiz_id = st.text_input("Enter Quiz ID:")

if st.button("Load Quiz"):
    quiz = collection.find_one({"quiz_id": quiz_id})
    if quiz:
        st.subheader(quiz['title'])
        st.write(quiz['description'])
        for question in quiz['questions']:
            st.write(f"Q{question['question_id']}: {question['question_text']}")
            for option in question['options']:
                st.write(f"- {option['option_text']}")
    else:
        st.error("Quiz not found!")

# Retrieve all quizzes
quizzes = collection.find()
for quiz in quizzes:
    print(quiz)