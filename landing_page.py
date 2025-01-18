import streamlit as st
from streamlit.components.v1 import iframe
import requests

def main():
    # Sidebar - Navigation
    st.sidebar.title("Teacher Dashboard")

    # Class Selection in Sidebar
    st.sidebar.write("### Select a Class")
    class_list = ["Machine Learning", "Natural Language Processing", "Deep Learning"]  # Example classes
    selected_class = st.sidebar.selectbox("Classes", class_list)

    if selected_class:
        classes_page(selected_class)

# Function for the Classes Page
def classes_page(selected_class):
    st.title(f"{selected_class} - Class Management")

    # Add Announcement Section
    st.write("### Add an Announcement")
    announcement = st.text_area("Enter your announcement:")
    if st.button("Post Announcement"):
        st.success("Announcement posted successfully!")

    # Upload Documents Section

    # Quiz Generator Section
    st.write("### Quiz Generator")
    num_questions = st.slider("Number of Questions", min_value=5, max_value=50, value=10)
    test_description = st.text_area("Describe the test:", "Enter a short description of the test.")
    difficulty = st.slider("Difficulty Level", min_value=1, max_value=10, value=5)

    st.write("### Uploaded Document for Quiz")
    quiz_file = st.file_uploader("Upload a document (ppt/pdf/doc):", type=["ppt", "pdf", "doc"])
    if st.button("Generate Quiz"):
        if quiz_file:
            st.info("Sending document to LLM for quiz generation...")
            # Mock API Request to LLM for generating quiz (replace with actual API call)
            response = requests.post("https://example-llm-api.com/generate_quiz", data={
                "file": quiz_file.name,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "description": test_description
            })
            if response.status_code == 200:
                st.success("Quiz generated successfully!")
            else:
                st.error("Failed to generate quiz. Please try again.")
        else:
            st.error("Please upload a file before generating a quiz.")

if __name__ == "__main__":
    main()
