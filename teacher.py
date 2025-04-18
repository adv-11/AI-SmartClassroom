import streamlit as st
from dotenv import load_dotenv
import os
import re  # To sanitize database names
from streamlit_option_menu import option_menu
import tempfile
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from pydantic import BaseModel, ValidationError
from typing import List
import json
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt


# Load environment variables
load_dotenv()

# MongoDB connection
CONNECTION_STRING = os.getenv("MONGO_DB_URI")
if not CONNECTION_STRING:
    st.error("MongoDB connection string not found. Please set it in the .env file.")
    st.stop()

client = MongoClient(CONNECTION_STRING)
quiz_db = client["quiz-db"]
teachers_collection = quiz_db["teacher_meta"]
courses_collection = quiz_db["courses"]

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.teacher_name = ""

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Teacher Dashboard",
        options=[ "🔑 Login","🏠 Home", "📝 Quiz Generation", "📊 Visualization"],
        icons=["house", "person", "clipboard-check", "bar-chart"],
        menu_icon="cast",
        default_index=0,
    )

# Login & Signup Page
if selected == "🔑 Login":
    st.title("👩‍🎓 Teacher Login & Signup")
    option = st.radio("Select an option", ("Login", "Sign Up"))

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            teacher = teachers_collection.find_one({"username": username, "password": password})
            if teacher:
                st.session_state.logged_in = True
                st.session_state.teacher_name = teacher["full_name"]
                st.success("Login successful! Redirecting to Home...")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    elif option == "Sign Up":
        full_name = st.text_input("Full Name")
        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")

        if st.button("Sign Up"):
            if teachers_collection.find_one({"username": username}):
                st.warning("Username already exists! Choose a different one.")
            else:
                teachers_collection.insert_one({"username": username, "password": password, "full_name": full_name})
                st.success("Sign-up successful! Please log in.")

# Home Page - Teacher Dashboard
if selected == "🏠 Home" and st.session_state.logged_in:
    teacher_name = st.session_state.teacher_name
    st.title("👩‍🎓 Teacher Dashboard")
    st.write(f"Welcome, {teacher_name}!")

    # Fetch courses created by the logged-in teacher
    created_courses = list(courses_collection.find({"creator_name": teacher_name}))

    # Display created courses with selection buttons
    st.subheader("📚 Your Created Courses")
    if created_courses:
        for i, course in enumerate(created_courses):  # Unique keys for buttons
            if st.button(course['course_name'], key=f"course_{i}"):
                st.session_state.selected_course_id = course['course_id']
                st.session_state.selected_course_name = course['course_name']
                st.success(f"Selected course: {course['course_name']}")

    else:
        st.info("You haven't created any courses yet.")

    # Section: Create a New Course
    st.subheader("➕ Create a New Course")
    new_course_name = st.text_input("Enter Course Name")
    new_course_id = st.text_input("Enter Unique Course ID")

    if st.button("Create Course", key="create_course_button"):
        if new_course_name and new_course_id:
            if courses_collection.find_one({"course_id": new_course_id}):
                st.warning(f"A course with ID '{new_course_id}' already exists. Please choose another ID.")
            else:
                # Sanitize database name (replace special characters with underscores)
                sanitized_db_name = re.sub(r"[^a-zA-Z0-9_]", "_", new_course_name.lower())

                # Insert course details into MongoDB
                course_data = {
                    "course_id": new_course_id,
                    "course_name": new_course_name,
                    "creator_name": teacher_name,
                    "db_name": sanitized_db_name
                }
                courses_collection.insert_one(course_data)

                # Create a separate database for this course
                course_db = client[sanitized_db_name]
                course_db.create_collection("quiz")
                course_db.create_collection("test_scores")
                course_db.create_collection("enroll_stud")

                st.success(f"🎉 Course '{new_course_name}' created successfully!")
                st.rerun()
        else:
            st.error("⚠️ Please enter both the Course Name and Unique Course ID.")

    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# Handle users who are not logged in and try to access Home
if selected == "🏠 Home" and not st.session_state.logged_in:
    st.warning("Please log in first!")


if selected == "📝 Quiz Generation" and st.session_state.logged_in:
    teacher_name = st.session_state.teacher_name
    
    # Fetch courses created by the logged-in teacher
    created_courses = list(courses_collection.find({"creator_name": teacher_name}))
    
    # Create a dropdown to select course
    if created_courses:
        course_options = {course['course_name']: course for course in created_courses}
        selected_course_name = st.selectbox("Select Course", list(course_options.keys()))
        selected_course = course_options[selected_course_name]
        db_name = selected_course['db_name']  # Get the sanitized DB name
        course_id = selected_course['course_id']  # Get the course ID
    else:
        st.warning("You don't have any courses. Please create a course first.")
        st.stop()
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))

    # Embeddings    
    from langchain.embeddings.openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings()

    # Initialize retriever in session state if not already present
    if 'retriever' not in st.session_state:
        st.session_state['retriever'] = None

    def generate_quiz(prompt, retriever):
        if retriever is None:
            st.error("Retriever is not initialized. Please upload a document and generate a quiz first.")
            return None
        
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
        )
        return rag_chain.invoke(prompt)

    def generate_quiz_page():
        st.title("Generate Quiz")
        st.write(f"Creating quiz for course: {selected_course_name}")

        # User Inputs
        quiz_id = st.text_input("Enter Test ID:")
        num_questions = st.slider("Number of Questions", min_value=1, max_value=10, value=5)
        test_description = st.text_area("Describe the test:", "Enter a short description of the test.")
        difficulty = st.slider("Difficulty Level", min_value=1, max_value=3, value=2)
        quiz_file = st.file_uploader("Upload a document (PDF only):", type=["pdf"])

        if st.button("Generate Quiz"):
            if quiz_file:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(quiz_file.read())
                    temp_file_path = temp_file.name

                try:
                    # Load and split the document
                    loader = PyPDFLoader(temp_file_path)
                    docs = loader.load()

                    if not docs:
                        st.error("Failed to extract content from the uploaded document. Please try another file.")
                        return

                    # Chunking 
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    splits = text_splitter.split_documents(docs)

                    # Vector Store - FAISS
                    vector_store = FAISS.from_documents(splits, embeddings)
                    st.session_state['retriever'] = vector_store.as_retriever()

                    # Prompt
                    prompt = f"""
    You are a teacher and need to generate a quiz for your class based on the provided document.

    The quiz should contain {num_questions} questions.

    Each question should have 4 options, out of which only one is correct.

    Format the output as a JSON object with the following structure:

    {{
        "quiz_id": "{quiz_id}",
        "title": "",
        "desc": "{test_description}",
        "subject": "{selected_course_name}",
        "course_id": "{course_id}",
        
        "questions": [
            {{
                "question_id": 1,
                "question": "",
                "options": [
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}}
                ]
            }},
            ...
        ]
    }}

    Ensure the questions are relevant to the content of the uploaded document.
                    """

                    st.info("Generating quiz, please wait...")
                    result = generate_quiz(prompt, st.session_state['retriever'])
                    if result:
                        st.success("Quiz generated successfully!")
                        result_to_send = json.loads(result['result'].strip())
                        st.session_state['generated_quiz'] = result_to_send

                        # Display quiz preview
                        st.subheader("📜 Quiz Preview")
                        st.json(result_to_send)
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.error("Please upload a document before generating a quiz.")

        # If a quiz is generated, show Post and Discard buttons
        if 'generated_quiz' in st.session_state:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Post Quiz"):
                    result_to_send = st.session_state['generated_quiz']
                    
                    # Use the db_name from the selected course
                    subject_db = client[db_name]  # Access subject database using correct db name
                    subject_db["quiz"].insert_one(result_to_send)  # Store in "quiz" collection
                    st.success(f"Quiz successfully stored in '{selected_course_name}' course!")

                    # Clear session state after posting
                    del st.session_state['generated_quiz']

            with col2:
                if st.button("❌ Discard Quiz"):
                    st.session_state['discarded_quiz'] = st.session_state.pop('generated_quiz')
                    st.warning("Quiz discarded! Provide feedback for improvement.")

        if 'discarded_quiz' in st.session_state:
            st.subheader("💡 Provide Feedback for Quiz Improvement")
            feedback = st.text_area("Enter your feedback on how to improve the quiz:")
            if st.button("🔄 Regenerate Quiz"):
                new_prompt = f''' The previous quiz was discarded due to some reasons. Here is the feedback provided by the teacher : {feedback}. Improve the quiz accordingly. 

                Keep the response JSON format the same.

                Number of questions: {num_questions}
                
    {{
        "quiz_id": "{quiz_id}",
        "title": "",
        "desc": "{test_description}",
        "subject": "{selected_course_name}",
        "course_id": "{course_id}",
        
        "questions": [
            {{
                "question_id": 1,
                "question": "",
                "options": [
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}},
                    {{"option_text": "", "is_correct": false or true}}
                ]
            }},
            ...
        ]
    }}
                '''
                st.info("Regenerating quiz, please wait...")
                new_result = generate_quiz(new_prompt, st.session_state['retriever'])
                if new_result:
                    # st.write(new_result) uncomment and check JSON if validation Error!
                    result_to_send = json.loads(new_result['result'].strip())
                    st.session_state['generated_quiz'] = result_to_send
                    del st.session_state['discarded_quiz']
                    st.success("Quiz regenerated successfully!")
                    st.subheader("📜 New Quiz Preview")
                    st.json(st.session_state['generated_quiz'])

    generate_quiz_page()

if selected == "📊 Visualization" and st.session_state.logged_in:
    st.title("📊 Quiz Performance Visualization")
    
    teacher_name = st.session_state.teacher_name
    
    # Fetch courses created by the logged-in teacher
    created_courses = list(courses_collection.find({"creator_name": teacher_name}))
    
    # Create a dropdown to select course
    if created_courses:
        course_options = {course['course_name']: course for course in created_courses}
        selected_course_name = st.selectbox("Select Course", list(course_options.keys()))
        selected_course = course_options[selected_course_name]
        db_name = selected_course['db_name']  # Get the sanitized DB name
        
        # Connect to the selected course database
        course_db = client[db_name]
        
        # Get all quizzes for this course
        quizzes = list(course_db["quiz"].find({}, {"quiz_id": 1, "title": 1}))
        
        if quizzes:
            quiz_options = {quiz.get('title', quiz['quiz_id']): quiz['quiz_id'] for quiz in quizzes}
            selected_quiz_title = st.selectbox("Select Quiz", list(quiz_options.keys()))
            selected_quiz_id = quiz_options[selected_quiz_title]
            
            if st.button("Show Visualization"):
                # Fetch scores of students who attempted the quiz
                test_scores_collection = course_db["test_scores"]
                scores_data = list(test_scores_collection.find({"quiz_id": selected_quiz_id}))
                
                if scores_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(scores_data)
                    df = df[["student_id", "score"]]  # Select only relevant columns
                    
                    # Visualization - Bar Chart
                    st.subheader("Test Scores Visualization")
                    fig, ax = plt.subplots()
                    ax.bar(df["student_id"], df["score"], color='skyblue')
                    ax.set_xlabel("Students")
                    ax.set_ylabel("Scores")
                    ax.set_title(f"Scores for Quiz: {selected_quiz_title}")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                    
                    # Show Data Table
                    st.subheader("Raw Scores Data")
                    st.dataframe(df)
                else:
                    st.warning("No scores data found for the selected quiz.")
        else:
            st.warning("No quizzes found for this course.")
    else:
        st.warning("You don't have any courses. Please create a course first.")