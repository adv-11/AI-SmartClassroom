import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB connection
CONNECTION_STRING = os.getenv("MONGO_DB_URI")
if not CONNECTION_STRING:
    st.error("MongoDB connection string not found. Please set it in the .env file.")
    st.stop()

client = MongoClient(CONNECTION_STRING)

# Databases and collections
master_db = client["master_db"]
students_collection = master_db["students"]
quiz_db = client["quiz-db"]
courses_collection = quiz_db["courses"]

# Get student_id from session state
student_id = st.session_state.get("student_id")

if not student_id:
    st.error("You must be logged in to view this page.")
    st.stop()

# Custom CSS for positioning the Quiz button
st.markdown(
    """
    <style>
        .quiz-button {
            position: absolute;
            top: 10px;
            right: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Quiz Button (Redirect to student_quiz.py)
if st.button("Quiz", key="quiz_button"):
    st.switch_page("pages/student_quiz.py")

def get_enrolled_courses(student_id):
    """Fetch enrolled courses based on course IDs."""
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
    """Enroll a student in a course using course_id and push to subj DB."""
    course = courses_collection.find_one({"course_id": course_id})
    if not course:
        return None  # Invalid course ID

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

    # Push student_id to subj.<enroll_stud> collection
    subj_db = client[course_name.lower()]  # lowercase to match db naming style
    enroll_stud_collection = subj_db["enroll_stud"]
    
    # Avoid duplicate entries
    if not enroll_stud_collection.find_one({"student_id": student_id}):
        enroll_stud_collection.insert_one({"student_id": student_id})

    return course_name

# Sidebar: Display enrolled courses
st.sidebar.title("📚 Enrolled Courses")

enrolled_courses = get_enrolled_courses(student_id)

if enrolled_courses:
    for course_id, course_name in enrolled_courses:
        if st.sidebar.button(course_name, key=course_id):
            st.session_state["active_course"] = course_name  # Store active course
            st.rerun()  # Refresh to show welcome message
else:
    st.sidebar.write("You are not enrolled in any courses.")

# Display welcome message if a course is selected
if "active_course" in st.session_state:
    st.title(f"Hello, welcome to '{st.session_state['active_course']}' course! 🎓")
else:
    st.title("🎓 Student Dashboard")
    st.write("Select a course from the sidebar to get started.")

# Input field to join new courses
st.subheader("Join a New Course")
course_id = st.text_input("Enter the course ID to join a new course")

if st.button("Join Course"):
    if course_id:
        result = enroll_in_course(student_id, course_id)
        if result is None:
            st.error("Invalid Course ID. Please try again.")
        elif result == "already_enrolled":
            st.warning("You are already enrolled in this course.")
        else:
            st.success(f"Successfully enrolled in {result}!")
            st.session_state["active_course"] = result  # Auto-select the new course
            st.rerun()  # Refresh page to update sidebar & welcome message
    else:
        st.error("Please enter a valid course ID.")

st.write("---")
st.write("Thank you for using the student portal!")