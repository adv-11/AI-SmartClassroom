import streamlit as st

def analytics_page():
    if 'selected_class' not in st.session_state:
        st.warning("No class selected. Return to the landing page.")
        return

    class_name = st.session_state['selected_class']
    st.title(f"Analytics for {class_name}")
    st.write("Here, you'll see analytics related to the class.")
