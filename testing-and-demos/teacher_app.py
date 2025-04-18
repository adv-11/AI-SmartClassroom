import streamlit as st
from teacher_views.landing_page import landing_page

# Navigation logic
PAGES = {
    "Landing Page": landing_page,
}

# Main app logic
def main():
    st.set_page_config(page_title="Google Classroom", layout="wide")
    selected_page = st.sidebar.selectbox("Navigate", list(PAGES.keys()))
    PAGES[selected_page]()

if __name__ == "__main__":
    main()

    