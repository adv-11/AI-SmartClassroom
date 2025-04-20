import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection from .env
CONNECTION_STRING = os.getenv("MONGO_DB_URI")
if not CONNECTION_STRING:
    st.error("MongoDB connection string not found. Please set it in the .env file.")
    st.stop()

@st.cache_resource
def get_database():
    client = MongoClient(CONNECTION_STRING)
    return client

student_id = st.session_state.get("student_id")

if not student_id:
    st.error("You must be logged in to view this page.")
    st.stop()

def get_quiz_subjects():
    client = get_database()
    database_names = client.list_database_names()
    quiz_subjects = []
    
    for db_name in database_names:
        if db_name not in ['admin', 'local', 'config']:
            db = client[db_name]
            if "quiz" in db.list_collection_names() and "enroll_stud" in db.list_collection_names():
                enrolled = db["enroll_stud"].find_one({"student_id": student_id})
                if enrolled:
                    quiz_subjects.append(db_name)
    return quiz_subjects

def load_quizzes(subject):
    client = get_database()
    db = client[subject]
    quiz_collection = db["quiz"]
    score_collection = db["test_scores"]

    quizzes = list(quiz_collection.find({}, {"_id": 0, "quiz_id": 1, "title": 1, "desc": 1, "questions": 1}))

    for quiz in quizzes:
        quiz_id = quiz["quiz_id"]
        score_doc = score_collection.find_one({"student_id": student_id, "quiz_id": quiz_id})
        quiz["attempted"] = bool(score_doc)
        if score_doc:
            quiz["score"] = score_doc["score"]
            quiz["total"] = score_doc["total"]
    return pd.DataFrame(quizzes) if quizzes else pd.DataFrame()

def main():
    st.title("Quiz Attempt Page")
    st.subheader("Select a Subject")
    
    subjects = get_quiz_subjects()
    
    if subjects:
        selected_subject = st.selectbox("Choose a subject to view quizzes:", subjects)
        
        if selected_subject:
            quizzes = load_quizzes(selected_subject)
            
            if not quizzes.empty:
                st.subheader(f"Available Quizzes in {selected_subject}")
                
                for _, quiz in quizzes.iterrows():
                    quiz_id = quiz.get("quiz_id", f"unknown_{_}")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {quiz['title']}")
                        st.write(quiz.get('desc', 'No description available'))

                        if quiz.get("attempted") and "score" in quiz:
                            st.info(f"📊 You scored **{quiz['score']} / {quiz['total']}**")

                    with col2:
                        if quiz.get("attempted"):
                            st.button("✅ Attempted", key=f"attempted_{quiz_id}", disabled=True)
                        else:
                            if st.button(f"Start {quiz['title']}", key=f"start_{quiz_id}"):
                                start_quiz(quiz, selected_subject)
                    st.divider()
            else:
                st.warning("No quizzes available for this subject.")
    else:
        st.warning("You are not enrolled in any quiz subjects.")

def start_quiz(quiz, subject):
    st.session_state["quiz_started"] = True
    st.session_state["current_quiz"] = quiz
    st.session_state["selected_subject"] = subject
    st.session_state["quiz_id"] = quiz["quiz_id"]
    st.session_state["start_time"] = datetime.now()

    if "answers" not in st.session_state:
        st.session_state["answers"] = {f"q{idx + 1}": None for idx in range(len(quiz['questions']))}
    
    st.rerun()

def attempt_quiz():
    quiz = st.session_state["current_quiz"]
    subject = st.session_state["selected_subject"]
    quiz_id = st.session_state.get("quiz_id")

    st.title(f"Attempt Quiz: {quiz['title']}")
    st.write(quiz['desc'])

    if "answers" not in st.session_state:
        st.session_state["answers"] = {f"q{idx + 1}": None for idx in range(len(quiz['questions']))}
    
    for idx, question in enumerate(quiz['questions']):
        key = f"q{idx + 1}"
        st.markdown(f"**Q{idx + 1}: {question['question']}**")
        
        options = [option["option_text"] for option in question["options"]]
        prev_selection = st.session_state["answers"].get(key, None)
        
        selected_option = st.radio(
            label=f"Select your answer for Q{idx + 1}:",
            options=options,
            key=key,
            index=options.index(prev_selection) if prev_selection in options else 0
        )
        
        st.session_state["answers"][key] = selected_option
    
    if st.button("Submit Quiz"):
        score = 0
        total = len(quiz['questions'])

        for idx, question in enumerate(quiz['questions']):
            key = f"q{idx + 1}"
            selected_option = st.session_state["answers"].get(key, None)

            correct_option = next((opt["option_text"] for opt in question["options"] if opt["is_correct"]), None)

            if selected_option == correct_option:
                score += 1

        st.success(f"🎉 You scored {score}/{total}! 🎯")
        save_test_score(subject, quiz_id, student_id, score, total)

        time.sleep(3)
        st.session_state["quiz_completed"] = True
        st.switch_page("pages/analysis.py")
        reset_session()

def save_test_score(subject, quiz_id, student_id, score, total):
    client = get_database()
    db = client[subject]
    test_scores_collection = db["test_scores"]

    result_data = {
        "student_id": student_id,
        "quiz_id": quiz_id,
        "score": score,
        "total": total,
        "timestamp": datetime.utcnow()
    }

    test_scores_collection.insert_one(result_data)
    st.success("✅ Quiz result has been saved successfully!")

def reset_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if __name__ == "__main__":
    if "quiz_started" in st.session_state and st.session_state["quiz_started"]:
        attempt_quiz()
    else:
        main()