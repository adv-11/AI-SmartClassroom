import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import uuid  # For generating unique course IDs

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

# Simulated logged-in teacher (replace with your login mechanism)
teacher_id = "teacher_001"  # Replace with dynamic teacher login
teacher_data = teachers_collection.find_one({"teacher_id": teacher_id})

if not teacher_data:
    st.error("Teacher not found. Please check your login credentials.")
    st.stop()

teacher_name = teacher_data.get("name", "Unknown Teacher")
created_courses = teacher_data.get("created_courses", [])

# Streamlit UI for Teacher Dashboard
st.title("👩‍🏫 Teacher Dashboard")
st.write(f"Welcome, **{teacher_name}**!")

# Display courses created by the teacher
st.subheader("Your Created Courses")
if created_courses:
    # Flexbox CSS for course display
    st.markdown("""
    <style>
        .flex-container {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 16px;
        }
        .flex-item {
            background-color: #FFD4D4;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            flex: 1 1 calc(30% - 16px);
        }
        .flex-item:hover {
            background-color: #FFB3B3;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    # Render courses in a flexbox
    st.markdown('<div class="flex-container">', unsafe_allow_html=True)
    for course in created_courses:
        course_page_url = f"/course_page?course_id={course}"  # Adjust URL for navigation
        st.markdown(
            f'<div class="flex-item"><a href="{course_page_url}" target="_self" style="text-decoration:none; color:inherit;"><h4>{course}</h4></a></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("You have not created any courses yet.")

# Input field to create a new course
st.subheader("Create a New Course")
new_course_name = st.text_input("Enter the name of the new course")

if st.button("Create Course"):
    if new_course_name:
        if new_course_name not in created_courses:
            # Generate unique course ID
            course_id = str(uuid.uuid4())

            # Add course to the teacher's document in teacher-meta collection
            teachers_collection.update_one(
                {"teacher_id": teacher_id},
                {"$push": {"created_courses": new_course_name}}
            )

            # Add course metadata to the courses collection
            course_data = {
                "course_id": course_id,
                "course_name": new_course_name,
                "creator_name": teacher_name,
                "creator_id": teacher_id
            }
            courses_collection.insert_one(course_data)

            st.success(f"Successfully created the course: {new_course_name}!")
              # Refresh to show the new course
        else:
            st.warning(f"The course '{new_course_name}' already exists.")
    else:
        st.error("Please enter a valid course name.")

st.write("---")
st.write("Thank you for using the Teacher Portal!")
