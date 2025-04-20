import streamlit as st
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ✅ Load environment variables
load_dotenv()

# ✅ MongoDB Connection Details
MONGO_URI = os.getenv("MONGO_DB_URI")
DB_NAME = "quiz-db"
STUDENT_COLLECTION = "student_meta"

# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
student_collection = db[STUDENT_COLLECTION]

# ✅ Function to Fetch Student Data
def get_student(username):
    return student_collection.find_one({"username": username})

# ✅ Function to Hash Password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# ✅ Function to Verify Password
def check_password(stored_hash, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)

# ✅ Function to Register a New Student
def register_student(username, password):
    if student_collection.find_one({"username": username}):
        st.error("🚨 Username already exists. Try a different one.")
        return
    hashed_pw = hash_password(password)
    student_collection.insert_one({"username": username, "password": hashed_pw})
    st.success("✅ Account created successfully! Please login.")

# ✅ Streamlit Student Login/Signup Interface
st.title("🎓 Student Portal")

option = st.radio("Select an option", ["Login", "Sign Up"])
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if option == "Login":
    if st.button("Login"):
        if username and password:
            user = get_student(username)
            if user:
                if check_password(user["password"], password):
                    st.success(f"🎉 Welcome Student {username}!")
                    st.session_state.student_id = username
                else:
                    st.error("❌ Invalid password.")
            else:
                st.error("❌ Student not found.")
        else:
            st.warning("⚠️ Please enter your username and password.")

elif option == "Sign Up":
    if st.button("Create Account"):
        if username and password:
            register_student(username, password)
        else:
            st.warning("⚠️ Please enter both username and password to sign up.")