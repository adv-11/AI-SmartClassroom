import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection setup
@st.cache_resource
def get_database():
    client = MongoClient("mongodb+srv://gayatrikurulkar:gaya031202@quiz-cluster.rde4k.mongodb.net/?retryWrites=true&w=majority&appName=quiz-cluster")  # Replace with your MongoDB connection string
    return client

def load_quizzes(subject):
    db = get_database()["Machine_Learning"]  # Database name is "Machine_Learning"
    collection = db[subject]  # Replace 'subject' with the desired collection name dynamically
    quizzes = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(quizzes)

def main():
    st.title("Quiz Attempt Page")
    st.subheader("Select a Subject")

    # List of available subjects (collections in the database)
    subjects = ["MLquiz"]  # Update this list based on your MongoDB structure
    selected_subject = st.selectbox("Choose a subject to view quizzes:", subjects)

    if selected_subject:
        quizzes = load_quizzes(selected_subject)

        if not quizzes.empty:
            st.subheader(f"Available Quizzes in {selected_subject}")

            for _, quiz in quizzes.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {quiz['title']}")
                    st.write(quiz['description'])
                with col2:
                    if quiz['available']:
                        if st.button(f"Start {quiz['title']}", key=f"start_{quiz['id']}"):
                            start_quiz(quiz)
                    else:
                        st.warning("Not Available", icon="⚠️")
                st.divider()
        else:
            st.warning("No quizzes available for this subject.")

def start_quiz(quiz):
    # Initialize session state only if it’s not already initialized
    if "quiz_started" not in st.session_state:
        st.session_state["quiz_started"] = False
        st.session_state["current_quiz"] = quiz
        st.session_state["start_time"] = datetime.now()
        st.session_state["answers"] = {f"q{idx + 1}": None for idx in range(len(quiz['questions']))}
    
    # Set quiz started flag to True
    st.session_state["quiz_started"] = True
    
    # Rerun the app to move to the quiz attempt page
    

def attempt_quiz():
    quiz = st.session_state["current_quiz"]
    st.title(f"Attempt Quiz: {quiz['title']}")
    st.write(quiz['description'])

    for idx, question in enumerate(quiz['questions']):
        st.markdown(f"**Q{idx + 1}: {question['question']}**")
        st.radio(
            label="Select your answer:",
            options=question['options'],
            key=f"q{idx + 1}"
        )

    if st.button("Submit Quiz"):
        score = 0
        total = len(quiz['questions'])

        for idx, question in enumerate(quiz['questions']):
            selected_option = st.session_state[f"q{idx + 1}"]
            correct_option = question['options'][question['correct_option'] - 1]
            if selected_option == correct_option:
                score += 1

        st.success(f"You scored {score}/{total}!")
        # Reset session state after quiz completion
        del st.session_state["current_quiz"]
        del st.session_state["quiz_started"]
        

if __name__ == "__main__":
    # Ensure that the correct state is checked when running the app
    if "quiz_started" in st.session_state and st.session_state["quiz_started"]:
        attempt_quiz()
    else:
        main()
