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

# Database and collections
quiz_db = client["quiz-db"]
teachers_collection = quiz_db["teacher-meta"]
courses_collection = quiz_db["courses"]

# Hardcoded welcome message
teacher_name = "John Doe"  # Replace with the teacher's name later

# Streamlit UI
st.title("👩‍🏫 Teacher Dashboard")
st.write(f"Welcome, *{teacher_name}*!")  # Hardcoded welcome message

# Fetch courses created by the teacher from courses collection
created_courses = [
    {
        "course_name": course["course_name"]
    }
    for course in courses_collection.find({"creator_name": teacher_name})
]

# Display courses created by the teacher
st.subheader("Your Created Courses")
if created_courses:
    # Flexbox CSS with spacing and wrapping
    st.markdown("""
    <style>
        .flex-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px; /* Space between boxes */
            justify-content: center;
            margin-top: 16px;
        }
        .flex-item {
            background-color: #FFE4E4;
            padding: 20px;
            margin: 10px; /* Extra margin for better separation */
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            flex: 1 1 calc(30% - 40px); /* Adjust width to fit three boxes per row */
            
        }
        .flex-item:hover {
            background-color: #FFCCCC;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    # Render courses using flexbox
    st.markdown('<div class="flex-container">', unsafe_allow_html=True)
    for course in created_courses:
        st.markdown(
            f'<div class="flex-item"><h4>{course["course_name"]}</h4></div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("You have not created any courses yet.")

# Input fields to create a new course
st.subheader("Create a New Course")
new_course_name = st.text_input("Enter the course name")
new_course_id = st.text_input("Enter the course ID (unique)")
creator_name = st.text_input("Enter your name (creator's name)", value=teacher_name)

if st.button("Create Course"):
    if new_course_name and new_course_id and creator_name:
        # Check if the course ID already exists
        if courses_collection.find_one({"course_id": new_course_id}):
            st.warning(f"A course with ID '{new_course_id}' already exists.")
        else:
            # Add course metadata to the courses collection
            course_data = {
                "course_id": new_course_id,
                "course_name": new_course_name,
                "creator_name": creator_name
            }
            courses_collection.insert_one(course_data)

            st.success(f"Successfully created the course: {new_course_name}!")
            st.experimental_rerun()  # Refresh to show the new course
    else:
        st.error("Please fill in all the fields to create a new course.")

st.write("---")
st.write("Thank you for using the Teacher Portal!")