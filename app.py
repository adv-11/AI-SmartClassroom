import streamlit as st

# List of example classes
classes = [
    {"name": "Mathematics 101", "instructor": "Dr. John Doe"},
    {"name": "Physics Fundamentals", "instructor": "Prof. Jane Smith"},
    {"name": "Introduction to Programming", "instructor": "Mr. Alan Turing"},
    {"name": "Data Structures", "instructor": "Ms. Ada Lovelace"},
    {"name": "Machine Learning", "instructor": "Dr. Andrew Ng"},
]

# Sidebar for class navigation
st.sidebar.title("AI-SmartClassroom")
st.sidebar.subheader("Your Classes")
class_choice = st.sidebar.radio("Select a Class", ["Dashboard"] + [cls["name"] for cls in classes])

# Dashboard Page
if class_choice == "Dashboard":
    st.title("Dashboard")
    st.subheader("Your Classes")

    # Displaying Classes as Cards
    cols = st.columns(3)
    for i, cls in enumerate(classes):
        with cols[i % 3]:  # Arrange cards in 3 columns
            st.markdown(
                f"""
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 10px; text-align: center; background-color: #f9f9f9;">
                    <h3 style="color: black;">{cls["name"]}</h3>
                    <p style="color: black;">Instructor: {cls["instructor"]}</p>
                    <button style="background-color: #4285F4; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">
                        View Class
                    </button>
                </div>
                """,
                unsafe_allow_html=True,
            )

# Class Details Page
else:
    # Find selected class details
    selected_class = next(cls for cls in classes if cls["name"] == class_choice)

    # Class Header
    st.title(f"Class: {selected_class['name']}")
    st.subheader(f"Instructor: {selected_class['instructor']}")

    # Tabs for Class Details and Assignments
    tab = st.radio("Select View", ["Stream", "Classwork", "People"])

    if tab == "Stream":
        st.subheader("Announcements and Updates")
        st.text_area("Post an update...", placeholder="Share something with your class.")
        st.button("Post")
    elif tab == "Classwork":
        st.subheader("Classwork")
        st.markdown(
            """
            - [Assignment 1: Key Concepts](#)
            - [Material: Lecture Notes](#)
            - [Quiz: Midterm Preparation](#)
            """
        )
        st.button("Create New Classwork")
    elif tab == "People":
        st.subheader("Class Members")
        st.markdown(f"**Instructor:** {selected_class['instructor']}")
        st.markdown("**Students:**")
        st.markdown("- Student 1")
        st.markdown("- Student 2")
        st.markdown("- Student 3")
