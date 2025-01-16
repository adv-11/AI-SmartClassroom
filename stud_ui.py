import streamlit as st
from pymongo import MongoClient

# MongoDB connection
def connect_to_mongo(uri, db_name, collection_name):
    """Connect to a MongoDB collection."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        return db[collection_name]
    except Exception as e:
        st.error("⚠️ Error connecting to the database. Please check your credentials.")
        return None

# Fetch a quiz by quiz ID
def fetch_quiz(collection, quiz_id):
    """Fetch a quiz from the database using its ID."""
    try:
        return collection.find_one({"quiz_id": quiz_id})
    except Exception as e:
        st.error("⚠️ Error fetching the quiz. Please try again.")
        return None

# Save scores to MongoDB
def save_score(collection, student_id, quiz_id, score, total_questions, responses):
    """Save quiz results to the database."""
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
        st.error("⚠️ Error saving your score. Please try again.")
        return False

def main():
    # Page configuration
    st.set_page_config(page_title="Smart Classroom Quiz", page_icon="🎓", layout="wide")
    
    # Header section with background color
    st.markdown(
        """
        <style>
            .main-title {
                font-size: 45px;
                font-weight: bold;
                color: #2b6777;
                text-align: center;
                margin-bottom: 10px;
            }
            .sub-title {
                font-size: 20px;
                color: #52ab98;
                text-align: center;
                margin-bottom: 30px;
            }
            .stButton>button {
                background-color: #2b6777 !important;
                color: white !important;
                font-size: 16px;
                border-radius: 5px;
                height: 40px;
                width: 120px;
                margin: 0 auto;
            }
            .quiz-section {
                background-color: #f2f2f2;
                padding: 20px;
                border-radius: 10px;
            }
            .question-text {
                font-size: 18px;
                color: #2b6777;
                font-weight: bold;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<h1 class="main-title">Smart Classroom Quiz</h1>', unsafe_allow_html=True)
    st.markdown('<h3 class="sub-title">Test your knowledge and track your progress!</h3>', unsafe_allow_html=True)

    # MongoDB connection details
    mongo_uri = st.secrets["MONGO_URI"]
    db_name = st.secrets["DB_NAME"]
    quiz_collection_name = st.secrets["QUIZ_COLLECTION"]
    score_collection_name = st.secrets["SCORE_COLLECTION"]

    # Connect to MongoDB
    quiz_collection = connect_to_mongo(mongo_uri, db_name, quiz_collection_name)
    score_collection = connect_to_mongo(mongo_uri, db_name, score_collection_name)
    if quiz_collection is None or score_collection is None:
        return

    # Initialize session state variables
    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    # Collect Student ID and Quiz Code
    with st.container():
        st.text_input("🔑 Enter your Student ID", placeholder="E.g., student_001", key="student_id")
        st.text_input("📘 Enter the Quiz Code", placeholder="E.g., quiz_001", key="quiz_id")

    if st.button("🚀 Start Quiz"):
        if not st.session_state.student_id or not st.session_state.quiz_id:
            st.error("⚠️ Please enter both your Student ID and Quiz Code.")
            return

        # Fetch quiz details
        quiz = fetch_quiz(quiz_collection, st.session_state.quiz_id)
        if not quiz:
            st.error("⚠️ Quiz not found. Please check the Quiz Code.")
            return

        st.session_state.quiz = quiz
        st.session_state.responses = {question['question_id']: {"selected_option": None, "is_correct": None}
                                      for question in quiz['questions']}
        st.session_state.submitted = False

    # Display quiz questions
    if st.session_state.quiz:
        quiz = st.session_state.quiz
        st.markdown(f"## **📝 Quiz: {quiz['title']}**")
        st.write(f"**📄 Description:** {quiz['description']}")

        # Quiz Form
        with st.form(key='quiz_form', clear_on_submit=True):
            st.markdown('<div class="quiz-section">', unsafe_allow_html=True)
            for question in quiz['questions']:
                question_id = question['question_id']
                options = question['options']

                st.markdown(f'<p class="question-text">{question["question_text"]}</p>', unsafe_allow_html=True)
                st.radio(
                    "",
                    [opt['option_text'] for opt in options],
                    key=f"q{question_id}"
                )
            st.markdown('</div>', unsafe_allow_html=True)

            submit_quiz = st.form_submit_button("✅ Submit Quiz")

        # Process and grade quiz submission
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

            # Calculate score
            score = sum(1 for response in st.session_state.responses.values() if response['is_correct'])
            total_questions = len(st.session_state.responses)

            # Save results to database
            if save_score(score_collection, st.session_state.student_id, st.session_state.quiz_id, score, total_questions, st.session_state.responses):
                st.success(f"🎉 Quiz submitted! Your score: **{score}/{total_questions}**.")
            else:
                st.error("⚠️ Failed to save your score.")

            st.session_state.submitted = True

            # Display detailed results
            st.markdown("### 📊 Your Answers")
            for question in quiz['questions']:
                response = st.session_state.responses.get(question['question_id'])
                if response:
                    st.markdown(f"**{question['question_text']}**")
                    st.write(f"📝 Your answer: `{response['selected_option']}`")
                    if response['is_correct']:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Wrong! Correct answer: `{next(opt['option_text'] for opt in question['options'] if opt['is_correct'])}`")

if __name__ == "__main__":
    main()
