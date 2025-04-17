import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import bcrypt
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection Details
MONGO_URI = os.getenv("MONGO_DB_URI")
DB_NAME = "quiz-db"
STUDENT_COLLECTION = "student_meta"
TEACHER_COLLECTION = "teacher_meta"

# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
student_collection = db[STUDENT_COLLECTION]
teacher_collection = db[TEACHER_COLLECTION]
master_db = client["master_db"]
students_collection = master_db["students"]
courses_collection = db["courses"]

# ✅ Utility Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(stored_hash, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)

def register_student(username, password):
    if student_collection.find_one({"username": username}):
        st.error("🚨 Username already exists. Try a different one.")
        return
    hashed_pw = hash_password(password)
    student_collection.insert_one({"username": username, "password": hashed_pw})
    st.success("✅ Account created successfully! Please login.")

def get_user(username):
    return student_collection.find_one({"username": username})

def get_enrolled_courses(student_id):
    student = students_collection.find_one({"student_id": student_id})
    if not student:
        return []
    course_ids = student.get("enrolled_courses", [])
    courses = []
    for course_id in course_ids:
        course = courses_collection.find_one({"course_id": course_id})
        if course:
            courses.append((course_id, course["course_name"]))
    return courses

def enroll_in_course(student_id, course_id):
    course = courses_collection.find_one({"course_id": course_id})
    if not course:
        return None
    course_name = course["course_name"]
    student = students_collection.find_one({"student_id": student_id})
    if not student:
        students_collection.insert_one({
            "student_id": student_id,
            "enrolled_courses": [course_id]
        })
    elif course_id not in student["enrolled_courses"]:
        students_collection.update_one(
            {"student_id": student_id},
            {"$push": {"enrolled_courses": course_id}}
        )
    else:
        return "already_enrolled"
    return course_name

def get_quiz_subjects():
    database_names = client.list_database_names()
    quiz_subjects = []
    for db_name in database_names:
        if db_name not in ['admin', 'local', 'config']:
            db_temp = client[db_name]
            if "quiz" in db_temp.list_collection_names():
                quiz_subjects.append(db_name)
    return quiz_subjects

def load_quizzes(subject):
    db_temp = client[subject]
    collection = db_temp["quiz"]
    quizzes = list(collection.find({}, {"_id": 0, "quiz_id": 1, "title": 1, "desc": 1, "questions": 1}))
    return pd.DataFrame(quizzes) if quizzes else pd.DataFrame()

# ✅ Set page config
st.set_page_config(page_title="🎓 Student Dashboard", layout="wide")

# ✅ Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="📺 Student Dashboard",
        options=["🔐 Login", "🏠 Home", "📝 Quizzes", "📊 Visualization"],
        icons=["key", "house", "clipboard-check", "bar-chart"],
        menu_icon="cast",
        default_index=1,
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "black", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "5px"},
            "nav-link-selected": {"background-color": "#ff4b4b", "color": "white"},
        }
    )

# ✅ Session State Init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student_id = ""
    st.session_state.active_course = ""

# ✅ Main Navigation Logic
if selected == "🔐 Login":
    st.title("🔐 Login / Sign Up")
    if not st.session_state.logged_in:
        option = st.radio("Choose an option:", ["Login", "Sign Up"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if option == "Login":
            if st.button("Login"):
                user = get_user(username)
                if user and check_password(user["password"], password):
                    st.success(f"🎉 Welcome, {username}!")
                    st.session_state.logged_in = True
                    st.session_state.student_id = username
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials.")
        elif option == "Sign Up":
            if st.button("Create Account"):
                register_student(username, password)
    else:
        st.success(f"🎓 You are already logged in as {st.session_state.student_id}")

elif selected == "🏠 Home":
    st.title("🏠 Welcome to the Student Dashboard")
    if st.session_state.logged_in:
        st.subheader(f"👋 Hello, {st.session_state.student_id}")
        enrolled_courses = get_enrolled_courses(st.session_state.student_id)
        st.markdown("### 📚 Your Courses")
        if enrolled_courses:
            for cid, cname in enrolled_courses:
                st.write(f"- **{cname}** (`{cid}`)")
        else:
            st.warning("You are not enrolled in any courses yet.")

        st.markdown("### ✍️ Enroll in New Course")
        course_id = st.text_input("Enter Course ID to Enroll")
        if st.button("Enroll"):
            result = enroll_in_course(st.session_state.student_id, course_id)
            if result == "already_enrolled":
                st.info("✅ Already enrolled in this course.")
            elif result is None:
                st.error("🚫 Invalid Course ID.")
            else:
                st.success(f"🎉 Successfully enrolled in **{result}**")
                st.rerun()
    else:
        st.warning("🔐 Please login first.")

elif selected == "📝 Quizzes":
    st.title("📝 Available Quizzes")
    if st.session_state.logged_in:
        subjects = get_quiz_subjects()
        if subjects:
            selected_subject = st.selectbox("Choose a subject:", subjects)
            quizzes = load_quizzes(selected_subject)
            if not quizzes.empty:
                for _, quiz in quizzes.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {quiz['title']}")
                        st.write(quiz.get("desc", "No description available"))
                    with col2:
                        st.button(f"Start {quiz['title']}", key=f"start_{quiz['quiz_id']}")
                    st.divider()
            else:
                st.info("No quizzes available.")
        else:
            st.warning("No subjects with quizzes found.")
    else:
        st.warning("🔐 Please login to access quizzes.")

elif selected == "📊 Visualization":
    st.title("📊 Performance Visualization")
    if st.session_state.logged_in:
        st.info("📈 Performance data coming soon!")
    else:
        st.warning("🔐 Please login to view performance data.")
