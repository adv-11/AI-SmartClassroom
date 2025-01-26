import streamlit as st

def home_page():
    if 'selected_class' not in st.session_state:
        st.warning("No class selected. Return to the landing page.")
        return

    class_name = st.session_state['selected_class']
    st.title(f"Welcome to {class_name}")
    st.write("This is the home page.")
