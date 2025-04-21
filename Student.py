import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
import importlib.util

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Student Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

# Import view modules dynamically
def load_view(view_name):
    module_path = f"student_views/{view_name}.py"
    if not os.path.exists(module_path):
        st.error(f"View module {module_path} not found")
        return None
    
    spec = importlib.util.spec_from_file_location(view_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[view_name] = module
    spec.loader.exec_module(module)
    return module

# Navigation function
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# Sidebar navigation after login
def show_navigation():
    st.sidebar.title("🎓 Student Portal")
    st.sidebar.markdown("---")
    
    # Navigation buttons
    if st.sidebar.button("📚 Dashboard"):
        navigate_to("dashboard")
    
    if st.sidebar.button("📝 Quizzes"):
        navigate_to("quiz")
    
    if st.sidebar.button("📊 Performance Analysis"):
        navigate_to("analysis")
    
    if st.sidebar.button("🔍 Flash Cards"):
        navigate_to("flash_card")
    
    if st.sidebar.button("🚪 Logout"):
        # Clear session state and return to login
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.current_page = "login"
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Display enrolled courses (if on dashboard)
    if st.session_state.current_page == "dashboard":
        show_enrolled_courses()

def show_enrolled_courses():
    st.sidebar.title("📚 Enrolled Courses")
    
    student_id = st.session_state.get("student_id")
    if not student_id:
        return
    
    enrolled_courses = get_enrolled_courses(student_id)
    
    if enrolled_courses:
        for course_id, course_name in enrolled_courses:
            if st.sidebar.button(course_name, key=course_id):
                st.session_state["active_course"] = course_name
                st.rerun()
    else:
        st.sidebar.write("You are not enrolled in any courses.")

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

def show_dashboard():
    st.title("🎓 Student Dashboard")
    
    # Check if a course is selected
    if "active_course" in st.session_state:
        st.title(f"Hello, welcome to '{st.session_state['active_course']}' course! 🎓")
    else:
        st.write("Select a course from the sidebar to get started or join a new course below.")
    
    # Input field to join new courses
    st.subheader("Join a New Course")
    course_id = st.text_input("Enter the course ID to join a new course")
    
    student_id = st.session_state.get("student_id")
    
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

# Main content logic based on current page
def main():
    # Load login view for unauthorized users
    if "student_id" not in st.session_state or st.session_state.current_page == "login":
        login_module = load_view("login")
        if login_module:
            # After login.py executes and sets student_id, it will continue to dashboard
            if "student_id" in st.session_state:
                st.session_state.current_page = "dashboard"
                st.rerun()
        return
    
    # Show navigation sidebar for logged-in users
    show_navigation()
    
    # Load appropriate view based on navigation
    if st.session_state.current_page == "dashboard":
        show_dashboard()
    elif st.session_state.current_page == "quiz":
        quiz_module = load_view("quiz")
    elif st.session_state.current_page == "analysis":
        analysis_module = load_view("analysis")
    elif st.session_state.current_page == "flash_card":
        flash_card_module = load_view("flash_card")
    else:
        st.error("Page not found")

if __name__ == "__main__":
    main()