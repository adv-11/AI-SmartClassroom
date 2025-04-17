import streamlit as st
import pymongo
from pymongo import MongoClient
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv
import bcrypt
import fitz  # PyMuPDF
import base64
import re
from dotenv import load_dotenv
from mistralai import Mistral
from mistralai.client import MistralClient
import time
from google.generativeai import GenerativeModel, configure  # Specific functions

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")  # Securely fetch MongoDB URI from .env

# Connect to MongoDB
client = MongoClient(MONGO_URI)


# ---------------- Streamlit UI Configuration ----------------
st.set_page_config(page_title="Teacher Dashboard", page_icon="📚", layout="wide")

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Teacher Dashboard",
        options=["🔑Login/Signup","🏠 Home", "📝 Create New Test", "📊 Evaluate the Test"],
        icons=["house", "file-earmark-plus", "clipboard-check"],
        menu_icon="cast",
        default_index=1,
    )

# -------------------- Home Section --------------------
# -------------------- Home Section --------------------
# -------------------- Home Section --------------------
# -------------------- Home Section --------------------

 
if selected == "🔑Login/Signup":
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["teacher"]  # Database for teachers
        collection = db["teacher_metadata"]  # Collection for storing teacher credentials
        client.admin.command('ping')  # Check connection
        st.success("✅ Connected to MongoDB")
    except Exception as e:
        st.error(f"❌ MongoDB Connection Failed: {e}")
        st.stop()

    # ---- SESSION MANAGEMENT ----
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "teacher_name" not in st.session_state:
        st.session_state["teacher_name"] = ""

    # ---- UI Design ----
    st.title("👩‍🏫 Teacher Login/Signup")
    st.write("Welcome! Please login or sign up below.")

    # ---- Tabs for Login & Signup ----
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Signup"])

    # ---- SIGNUP ----
    with tab2:
        st.subheader("Create a Teacher Account")
        teacher_name = st.text_input("Full Name", key="signup_name")
        teacher_id = st.text_input("Teacher ID", key="signup_id")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Sign Up"):
            if not (teacher_name and teacher_id and password and confirm_password):
                st.error("❌ All fields are required.")
            elif password != confirm_password:
                st.error("❌ Passwords do not match.")
            else:
                # Check if teacher already exists
                existing_teacher = collection.find_one({"teacher_id": teacher_id})
                if existing_teacher:
                    st.error("❌ Teacher ID already exists. Please login.")
                else:
                    # Hash password
                    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    teacher_data = {
                        "teacher_name": teacher_name,
                        "teacher_id": teacher_id,
                        "password": hashed_password
                    }
                    collection.insert_one(teacher_data)
                    st.success("✅ Signup successful! Please login.")

    # ---- LOGIN ----
    with tab1:
        st.subheader("Teacher Login")
        login_id = st.text_input("Teacher ID", key="login_id")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            teacher = collection.find_one({"teacher_id": login_id})
            if teacher and bcrypt.checkpw(login_password.encode(), teacher["password"].encode()):
                st.session_state["authenticated"] = True
                st.session_state["teacher_name"] = teacher["teacher_name"]
                st.success(f"✅ Welcome, {teacher['teacher_name']}! Login successful.")
                st.rerun()
            else:
                st.error("❌ Invalid Teacher ID or Password.")

    # ---- LOGOUT ----
    if st.session_state["authenticated"]:
        st.subheader(f"👋 Welcome, {st.session_state['teacher_name']}!")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.session_state["teacher_name"] = ""
            st.success("✅ Logged out successfully.")
            st.rerun()

elif selected == "🏠 Home":
    st.title("📚 Welcome to the Teacher Dashboard")
    st.write("Manage and evaluate tests efficiently ")

    # Ensure teacher is logged in
    if "teacher_name" not in st.session_state or not st.session_state["teacher_name"]:
        st.error("❌ Please log in to view your tests.")
        st.stop()

    teacher_name = st.session_state["teacher_name"].replace(" ", "_")  # Replace spaces with underscores
    teacher_db = client[teacher_name]  # Use sanitized name for MongoDB database

    quiz_ids = teacher_db.list_collection_names()
    subject_tests = {}  # Dictionary to store tests grouped by subject

    for quiz_id in quiz_ids:
        collection = teacher_db[quiz_id]
        test_data = collection.find_one({}, {"_id": 0})  # Fetch first document (ignore _id)

        if test_data:
            subject = test_data.get("subject")  # Extract subject
            if subject:
                if subject not in subject_tests:
                    subject_tests[subject] = []
                subject_tests[subject].append(quiz_id)  # Store quiz_id (collection name)

    # ---- Updated CSS (Two Columns, Centered Layout) ----
    st.markdown(
        """
        <style>
        .subject-container {
            display: grid;
            grid-template-columns: repeat(2, minmax(250px, 1fr)); /* Two columns */
            gap: 25px;  /* Increased gap between flexboxes */
            justify-content: center;
            max-width: 800px; /* Prevents full-screen width */
            margin: auto;
            margin-top: 20px;
        }
        .subject-card {
            background: #D6EAF8;  /* Light Blue */
            border-radius: 12px;
            padding: 20px;
            box-shadow: 3px 3px 10px rgba(0,0,0,0.1);
            color: #1A5276; /* Dark Blue Text */
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            text-align: center;
            max-width: 350px; /* Prevents oversized cards */
            margin: auto;
        }
        .subject-card:hover {
            transform: scale(1.05);
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
        }
        .subject-title {
            font-size: 20px;
            font-weight: bold;
            text-transform: capitalize;
            margin-bottom: 10px;
        }
        .test-list {
            font-size: 16px;
            list-style-type: none;
            padding: 0;
        }
        .test-list li {
            background: rgba(255, 255, 255, 0.7);
            padding: 8px;
            border-radius: 6px;
            margin: 5px 0;
            transition: background 0.2s ease;
        }
        .test-list li:hover {
            background: rgba(255, 255, 255, 0.9);
            cursor: pointer;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ---- Display Subject-wise Tests ----
    st.markdown('<div class="subject-container">', unsafe_allow_html=True)

    if subject_tests:
        for subject, test_list in subject_tests.items():
            test_list_html = "".join([f'<li>{quiz_id}</li>' for quiz_id in test_list])

            subject_card_html = f"""
            <div class="subject-card">
                <div class="subject-title">{subject}</div>
                <ul class="test-list">{test_list_html}</ul>
            </div>
            """

            st.markdown(subject_card_html, unsafe_allow_html=True)
    else:
        st.info("No tests found. Create a new test in the 'Create New Test' section.")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Create New Test Section --------------------
elif selected == "📝 Create New Test":
    st.title("📝 Create New Test")

    # Ensure teacher is logged in
    if "teacher_name" not in st.session_state or not st.session_state["teacher_name"]:
        st.error("❌ Please log in to create tests.")
        st.stop()

    teacher_name = st.session_state["teacher_name"].replace(" ", "_")  # Replace spaces with underscores
    teacher_db = client[teacher_name]  # Use sanitized name for MongoDB database

 

    with st.form("create_test_form"):
        quiz_id = st.text_input("Test ID (Quiz ID)").strip().replace(" ", "_")
        subject_name = st.text_input("Subject Name")

        questions = []
        keywords = []

        for i in range(1, 7):
            q = st.text_area(f"Question {i}")
            k = st.text_input(f"Keywords for Question {i} (comma-separated)")
            questions.append(q)
            keywords.append(k)

        submit_button = st.form_submit_button("Save Test")

        if submit_button:
            if quiz_id and subject_name and all(questions) and all(keywords):
                collection = teacher_db[quiz_id]  # Create a collection named after the test ID

                # Insert test data
                test_data = {
                    "subject": subject_name,
                    "quiz_id": quiz_id,
                    "questions": [{"question": q, "keywords": k} for q, k in zip(questions, keywords)],
                    "created_by": st.session_state["teacher_name"]  # Store the teacher name
                }

                collection.insert_one(test_data)

                st.success(f"Test '{quiz_id}' created successfully in database '{st.session_state['teacher_name']}'!")
            else:
                st.error("Please fill in all fields.")


# -------------------- Evaluate the Test Section --------------------
elif selected == "📊 Evaluate the Test":
    st.title("📊 Evaluate the Test")
    

    # Ensure teacher is logged in
    if "teacher_name" not in st.session_state or not st.session_state["teacher_name"]:
        st.error("❌ Please log in to view your tests.")
        st.stop()

    # Teacher's database (replace spaces with underscores)
    teacher_name = st.session_state["teacher_name"].replace(" ", "_")
    teacher_db = client[teacher_name]

    # Fetch all test collections
    test_ids = teacher_db.list_collection_names()

    # Initialize Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    configure(api_key=GEMINI_API_KEY)
    gemini_model = GenerativeModel("gemini-1.5-pro")

    # Student scores database
    students_db = client["student"]
    scores_collection = students_db["student_scores"]

    # Function to fetch questions and keywords from MongoDB
    def fetch_questions(test_id):
        try:
            collection = teacher_db[test_id]  # Access the test collection  
            document = collection.find_one({}, {"_id": 0, "questions": 1})  # Fetch first document with questions  
            
            if document and "questions" in document:
                return document["questions"]
            else:
                st.error(f"❌ No questions found for Test ID '{test_id}' in {teacher_db.name}.")
                return []
        
        except Exception as e:
            st.error(f"❌ Error accessing test '{test_id}': {e}")
            return []

    # Convert PDF to base64 images using PyMuPDF
    def pdf_to_base64_pymupdf(pdf_path):
        doc = fitz.open(pdf_path)
        base64_images = []
        for page_num in range(len(doc)):
            pix = doc[page_num].get_pixmap()
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            base64_images.append(img_base64)
        return base64_images

    # Extract text from all images using Gemini API
    def extract_text_from_images(base64_images):
        full_text = ""
        for idx, image in enumerate(base64_images):
            st.write(f"Processing Page {idx+1}...")
            response = gemini_model.generate_content([
                "Extract the handwritten text from the following image:",
                {"mime_type": "image/png", "data": image}
            ])
            extracted_text = response.text if response.text else "Text extraction failed"
            full_text += f"\nPage {idx+1}:\n{extracted_text}\n"
            time.sleep(3)  # Reduce request frequency
        return full_text

    # Group answers based on questions
    def group_answers_by_questions(full_text, questions_data):
        grouped_answers = {}
        for question in questions_data:
            q_num = question.get("question_number", "Unknown")
            q_text = question.get("question", "No question found")
            
            # Search for the question in the extracted text
            pattern = re.escape(q_text[:15])  # Match first few words of question
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                start_idx = match.start()
                grouped_answers[q_num] = full_text[start_idx:]
        
        return grouped_answers

    # Chunked Processing - Evaluate answers in batches
    def evaluate_answers(grouped_answers, questions_data, student_name, prn, test_id):
        results = []
        
        # Create evaluation prompts for each question
        eval_prompts = []
        for question in questions_data:
            q_num = question.get("question_number", "Unknown")
            q_text = question.get("question", "No question found")
            keywords = question.get("expected_keywords", [])
            student_answer = grouped_answers.get(q_num, "No Answer Found")

            eval_prompts.append(
                f"*Question {q_num}:* {q_text}\n"
                f"*Expected Keywords:* {', '.join(keywords)}\n"
                f"*Student Answer:* {student_answer}\n\n"
            )

        # Process in chunks (max 3 questions per batch)
        chunk_size = 3
        for i in range(0, len(eval_prompts), chunk_size):
            eval_prompt = "Evaluate the following student answers and assign a score out of 5. Provide feedback for each.\n\n"
            eval_prompt += "".join(eval_prompts[i:i+chunk_size])
            
            try:
                response = gemini_model.generate_content(eval_prompt)
                evaluations = response.text.split("\n\n")  # Assuming Gemini returns responses separated by newline
                
                # Match evaluations with questions
                for idx, question in enumerate(questions_data[i:i+chunk_size]):
                    q_num = question.get("question_number", "Unknown")
                    evaluation_result = evaluations[idx] if idx < len(evaluations) else "No Evaluation Found"
                    results.append({"question_number": q_num, "evaluation": evaluation_result})
                    st.subheader(f"Evaluation for Question {q_num}:")
                    st.markdown(evaluation_result)

                time.sleep(5)  # Delay between batches
            except Exception as e:
                st.error(f"API Error: {e}")

        # Store results in MongoDB
        scores_collection.insert_one({
            "test_id": test_id,
            "student_name": student_name,
            "prn": prn,
            "results": results
        })
        st.success("Evaluation results saved successfully!")

    # Streamlit UI
    st.title("Handwritten Answer Evaluator")
    st.write("Enter details and upload a handwritten PDF containing answers for evaluation.")

    # Input fields
    test_id = st.text_input("Enter Test ID:")
    student_name = st.text_input("Enter Student Name:")
    prn = st.text_input("Enter PRN Number:")
    uploaded_answers = st.file_uploader("Upload Answer Sheet (PDF)", type=["pdf"])

    if test_id and student_name and prn and uploaded_answers:
        try:
            pdf_path = "uploaded_answers.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_answers.read())
            
            st.write("Fetching test questions and keywords from MongoDB...")
            questions_data = fetch_questions(test_id)

            if not questions_data:
                st.error("No questions found in the database. Please check MongoDB entries.")
            else:
                st.write("Converting PDF to images...")
                base64_images = pdf_to_base64_pymupdf(pdf_path)
                
                st.write("Extracting text from images...")
                full_text = extract_text_from_images(base64_images)
                
                st.write("Grouping answers by questions...")
                grouped_answers = group_answers_by_questions(full_text, questions_data)
                
                st.write("Evaluating answers...")
                evaluate_answers(grouped_answers, questions_data, student_name, prn, test_id)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")