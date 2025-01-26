import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

# MongoDB connection
def connect_to_mongo(uri, db_name, collection_name):
    try:
        client = MongoClient(uri)
        db = client[db_name]
        return db[collection_name]
    except Exception as e:
        st.error("Error connecting to the database.")
        return None

# Fetch a quiz by quiz ID
def fetch_quiz(collection, quiz_id):
    try:
        return collection.find_one({"quiz_id": quiz_id})
    except Exception as e:
        st.error("Error fetching the quiz.")
        return None

# Save scores to MongoDB
def save_score(collection, student_id, quiz_id, score, total_questions, responses):
    try:
        response_records = [
            {
                "question_id": question_id,
                "selected_option": response["selected_option"],
                "is_correct": response["is_correct"]
            }
            for question_id, response in responses.items()
        ]
        record = {
            "student_id": student_id,
            "quiz_id": quiz_id,
            "score": score,
            "total_questions": total_questions,
            "responses": response_records
        }
        collection.insert_one(record)
        return True
    except Exception as e:
        st.error("Error saving your score.")
        return False

def main():
    st.title("Smart Classroom Quiz")
    st.subheader("Test your knowledge and track your progress!")

    # MongoDB connection details (retrieved from secrets)
    mongo_uri = st.secrets["MONGO_URI"]
    db_name = st.secrets["DB_NAME"]
    quiz_collection_name = st.secrets["QUIZ_COLLECTION"]
    score_collection_name = st.secrets["SCORE_COLLECTION"]

    quiz_collection = connect_to_mongo(mongo_uri, db_name, quiz_collection_name)
    score_collection = connect_to_mongo(mongo_uri, db_name, score_collection_name)

    if quiz_collection is None or score_collection is None:
        return

    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    student_id = st.text_input("Enter your Student ID", placeholder="E.g., student_001")
    quiz_id = st.text_input("Enter the Quiz Code", placeholder="E.g., quiz_001")

    if st.button("Start Quiz"):
        if not student_id or not quiz_id:
            st.error("Please enter both your Student ID and Quiz Code.")
            return

        quiz = fetch_quiz(quiz_collection, quiz_id)
        if not quiz:
            st.error("Quiz not found. Please check the Quiz Code.")
            return

        st.session_state.quiz = quiz
        st.session_state.responses = {question['question_id']: {"selected_option": None, "is_correct": None}
                                      for question in quiz['questions']}
        st.session_state.submitted = False

    if st.session_state.quiz:
        quiz = st.session_state.quiz
        st.header(f"Quiz: {quiz['title']}")
        st.write(quiz['description'])

        with st.form(key='quiz_form'):
            for question in quiz['questions']:
                question_id = question['question_id']
                options = question['options']

                st.radio(
                    f"{question['question_text']}",
                    [opt['option_text'] for opt in options],
                    key=f"q{question_id}"
                )

            submit_quiz = st.form_submit_button("Submit Quiz")

        if submit_quiz and not st.session_state.submitted:
            for question in quiz['questions']:
                question_id = question['question_id']
                selected_option = st.session_state.get(f"q{question_id}")
                if selected_option:
                    correct_option = next(opt for opt in question['options'] if opt['is_correct'])
                    is_correct = selected_option == correct_option['option_text']
                    st.session_state.responses[question_id] = {
                        "selected_option": selected_option,
                        "is_correct": is_correct
                    }

            score = sum(1 for response in st.session_state.responses.values() if response['is_correct'])
            total_questions = len(st.session_state.responses)

            if save_score(score_collection, student_id, quiz_id, score, total_questions, st.session_state.responses):
                st.success(f"Quiz submitted! Your score: {score}/{total_questions}.")
            else:
                st.error("Failed to save your score.")

            st.session_state.submitted = True

            st.markdown("### Your Answers")
            for question in quiz['questions']:
                response = st.session_state.responses.get(question['question_id'])
                if response:
                    st.markdown(f"{question['question_text']}")
                    st.write(f"Your answer: {response['selected_option']}")
                    if response['is_correct']:
                        st.success("Correct!")
                    else:
                        st.error(f"Wrong! Correct answer: {next(opt['option_text'] for opt in question['options'] if opt['is_correct'])}")

if __name__ == "__main__":
    main()