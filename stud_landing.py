import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB connection using .env variable
CONNECTION_STRING = os.getenv("MONGO_URI")
if not CONNECTION_STRING:
    st.error("MongoDB connection string not found. Please set it in the .env file.")
    st.stop()

client = MongoClient(CONNECTION_STRING)

# Centralized collection to track student enrollments
master_db = client["master_db"]
students_collection = master_db["students"]

# Simulate logged-in student (replace with actual login mechanism)
student_id = "student_123"

def get_enrolled_courses(student_id):
    """Fetch the list of courses a student is enrolled in."""
    student = students_collection.find_one({"student_id": student_id})
    return student.get("enrolled_courses", []) if student else []

def enroll_in_course(student_id, course_name):
    """Enroll a student in a course."""
    student = students_collection.find_one({"student_id": student_id})
    if not student:
        # Create a new student record if it doesn't exist
        students_collection.insert_one({
            "student_id": student_id,
            "enrolled_courses": [course_name]
        })
    elif course_name not in student["enrolled_courses"]:
        # Add the course to the student's enrolled courses
        students_collection.update_one(
            {"student_id": student_id},
            {"$push": {"enrolled_courses": course_name}}
        )
    else:
        return False  # Already enrolled
    return True

# Streamlit UI with Flexbox
st.title("🎓 Student Dashboard")
st.write(f"Welcome, **{student_id}**!")

# Fetch enrolled courses
enrolled_courses = get_enrolled_courses(student_id)

# Display enrolled courses with Flexbox
st.subheader("Your Enrolled Courses")
if enrolled_courses:
    # Custom CSS for flexbox
    st.markdown("""
    <style>
        .flex-container {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 16px;
        }
        .flex-item {
            background-color: #D3ECFF;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            flex: 1 1 calc(30% - 16px);
        }
        .flex-item:hover {
            background-color: #B0DFF8;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create flexbox container
    st.markdown('<div class="flex-container">', unsafe_allow_html=True)
    for course in enrolled_courses:
        st.markdown(
            f'<div class="flex-item"><h4>{course}</h4></div>', 
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("You are not enrolled in any courses yet.")

# Input field to join new courses
st.subheader("Join a New Course")
course_code = st.text_input("Enter the course code to join a new course")

if st.button("Join Course"):
    if course_code:
        success = enroll_in_course(student_id, course_code)
        if success:
            st.success(f"Successfully enrolled in {course_code}!")
            st.experimental_rerun()  # Refresh the page to show updated enrollment
        else:
            st.warning(f"You are already enrolled in {course_code}.")
    else:
        st.error("Please enter a valid course code.")

st.write("---")
st.write("Thank you for using the student portal!")
