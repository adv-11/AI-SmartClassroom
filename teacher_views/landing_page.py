import streamlit as st
from teacher_views.db import get_teacher_classes, create_classroom
from teacher_views.home import home_page




def landing_page():
    st.title("Teacher's Dashboard")

    teacher_id = st.text_input("Enter Teacher ID", "teacher_1")
    if st.button("Load Classes"):
        classes = get_teacher_classes(teacher_id)
        if not classes:
            st.write("No classes found. Create a new classroom below.")
        else:
            for classroom in classes:
                if st.button(f"Open {classroom['name']}"):
                    st.session_state['selected_class'] = classroom['name']
                    home_page()
                    return

    st.subheader("Create a New Classroom")
    new_class_name = st.text_input("Classroom Name")
    if st.button("Create Classroom"):
        create_classroom(teacher_id, new_class_name)
        st.success(f"Classroom '{new_class_name}' created successfully!")
