import streamlit as st
from pymongo import MongoClient

# MongoDB connection
def connect_to_mongo(uri, db_name, collection_name):
    try:
        st.write(f"Connecting to MongoDB at {uri}, database: {db_name}, collection: {collection_name}")
        client = MongoClient(uri)
        db = client[db_name]
        st.write("Connection successful")
        return db[collection_name]
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None

# Fetch a quiz by quiz ID
def fetch_quiz(collection, quiz_id):
    try:
        st.write(f"Fetching quiz with ID: {quiz_id}")
        quiz = collection.find_one({"quiz_id": quiz_id})
        if quiz:
            st.write("Quiz fetched successfully.")
        else:
            st.error("Quiz not found.")
        return quiz
    except Exception as e:
        st.error(f"Error fetching quiz: {e}")
        return None

# Save scores to MongoDB
def save_score(collection, student_id, quiz_id, score, total_questions, responses):
    try:
        st.write(f"Saving score for student: {student_id}, quiz: {quiz_id}")
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

        st.write(f"Record to be inserted: {record}")
        collection.insert_one(record)
        st.write("Score saved successfully")
        return True
    except Exception as e:
        st.error(f"Error saving score: {e}")
        return False

def main():
    # App title and introduction
    st.title("Smart Classroom Quiz")
    st.subheader("Test your knowledge and track your progress!")

    # MongoDB connection details
    mongo_uri = st.secrets["MONGO_URI"]
    db_name = "quiz-db"
    quiz_collection_name = "quizcollect"
    score_collection_name = "scores"

    # Connect to MongoDB collections
    quiz_collection = connect_to_mongo(mongo_uri, db_name, quiz_collection_name)
    score_collection = connect_to_mongo(mongo_uri, db_name, score_collection_name)

    if quiz_collection is None or score_collection is None:
        st.error("Database connection failed. Please check your configuration.")
        return

    # Initialize session state variables
    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    # Student details
    student_id = st.text_input("Enter your Student ID", placeholder="E.g., student_001")
    quiz_id = st.text_input("Enter the Quiz Code", placeholder="E.g., quiz_001")

    if st.button("Start Quiz"):
        st.write("Start Quiz button clicked")
        if not student_id or not quiz_id:
            st.error("Please enter both your Student ID and Quiz Code to begin.")
            return

        # Fetch and store quiz in session state
        quiz = fetch_quiz(quiz_collection, quiz_id)
        if not quiz:
            st.error("Quiz not found. Please check the Quiz Code and try again.")
            return

        st.session_state.quiz = quiz
        st.session_state.responses = {question['question_id']: {"selected_option": None, "is_correct": None}
                                      for question in quiz['questions']}
        st.session_state.submitted = False

    # If a quiz is loaded in session state, display it
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

        # Handle quiz submission
        if submit_quiz and not st.session_state.submitted:
            st.write("Submit Quiz button clicked")
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

            # Save to MongoDB
            if save_score(score_collection, student_id, quiz_id, score, total_questions, st.session_state.responses):
                st.success(f"Your quiz has been submitted! You scored {score}/{total_questions}.")
            else:
                st.error("Failed to save your score. Please try again.")

            st.session_state.submitted = True

            # Display result breakdown
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
