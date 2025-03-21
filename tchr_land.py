import streamlit as st
from pymongo import MongoClient
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
CONNECTION_STRING = os.getenv("MONGO_URI")
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
    created_courses = [
        {"course_name": course["course_name"], "course_id": course["course_id"]}
        for course in courses_collection.find({"creator_name": teacher_name})
    ]

    # Display created courses with buttons
    st.subheader("Your Created Courses")
    for course in created_courses:
        if st.button(course['course_name']):
            st.session_state.selected_course_id = course['course_id']
            st.session_state.selected_course_name = course['course_name']
            st.success(f"Selected course: {course['course_name']}")

    # Input fields to create a new course
    st.subheader("Create a New Course")
    new_course_name = st.text_input("Enter the course name")
    new_course_id = st.text_input("Enter the course ID (unique)")
    creator_name = teacher_name

    if st.button("Create Course"):
        if new_course_name and new_course_id:
            if courses_collection.find_one({"course_id": new_course_id}):
                st.warning(f"A course with ID '{new_course_id}' already exists.")
            else:
                sanitized_db_name = re.sub(r"[^a-zA-Z0-9_]", "_", new_course_name.lower())
                course_data = {
                    "course_id": new_course_id,
                    "course_name": new_course_name,
                    "creator_name": creator_name,
                    "db_name": sanitized_db_name
                }
                courses_collection.insert_one(course_data)

                # Create a new database for the course
                course_db = client[sanitized_db_name]
                course_db.create_collection("quiz")
                course_db.create_collection("test_scores")

                st.success(f"Successfully created the course: {new_course_name}!")
                st.rerun()
        else:
            st.error("Please fill in all the fields to create a new course.")

    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# Handle users who are not logged in and try to access Home
if selected == "🏠 Home" and not st.session_state.logged_in:
    st.warning("Please log in first!")


if selected == "📝 Quiz Generation" and st.session_state.logged_in:
    teacher_name = st.session_state.teacher_name
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
        st.write("Upload a document and generate quizzes based on its content.")

        # User Inputs
        quiz_id = st.text_input("Enter Test ID:")
        subject_name = st.text_input("Enter Subject Name:")
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
        "subject": "{subject_name}",
        
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
                    
                    # Check if the subject name exists as a database
                    if subject_name in client.list_database_names():
                        subject_db = client[subject_name]  # Access subject database
                        subject_db["quiz"].insert_one(result_to_send)  # Store in "quiz" collection
                        st.success(f"Quiz successfully stored in '{subject_name}' database under 'quiz' collection!")
                    else:
                        st.warning("Subject name not found in the database. Quiz not stored.")

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
        "subject": "{subject_name}",
        
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

if selected == "📊 Visualization" and  st.session_state.logged_in:
    st.title("📊 Quiz Performance Visualization")
    
    quiz_id = st.text_input("Enter Quiz ID:")
    subject_name = st.text_input("Enter Subject Name:")
    
    if st.button("Show Visualization"):
        if quiz_id and subject_name:
            # Check if the subject database exists
            if subject_name in client.list_database_names():
                subject_db = client[subject_name]  # Access subject database
                test_scores_collection = subject_db["test_scores"]
                
                # Fetch scores of students who attempted the quiz
                scores_data = list(test_scores_collection.find({"quiz_id": quiz_id}))
                
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
                    ax.set_title(f"Scores for Quiz ID: {quiz_id}")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                    
                    # Show Data Table
                    st.subheader("Raw Scores Data")
                    st.dataframe(df)
                else:
                    st.warning("No data found for the entered Quiz ID.")
            else:
                st.error("Subject name not found in the database.")
        else:
            st.error("Please enter both Quiz ID and Subject Name.")
