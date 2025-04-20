import streamlit as st

# Page config
st.set_page_config(page_title="QuizGen Platform", layout="wide")

# Title and Description
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #003566;
        }
        .subtitle {
            text-align: center;
            font-size: 22px;
            color: #555;
            margin-bottom: 3rem;
        }
        .role-box {
            border-radius: 15px;
            padding: 30px;
            background-color: #eaf4ff;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            transition: 0.3s ease;
        }
        .role-box:hover {
            background-color: #eaf4ff;
            transform: scale(1.02);
        }
        .btn {
            background-color: #FFFAFA;
            border: none;
            color: black;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background-color: #87CEEB;
        }
    </style>

    <div class="title">Welcome to the AI Smart Classroom</div>
    <div class="subtitle">Select your role to continue</div>
""", unsafe_allow_html=True)

# URLs
teacher_url = "https://ai-smartclassroom-teacher.streamlit.app/"
student_url = "https://ai-smartclassroom-student.streamlit.app/"

# Layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="role-box">
            <img src="https://img.icons8.com/ios-filled/100/teacher.png" width="80"/>
            <h3>👩‍🏫 I'm a Teacher</h3>
            <p>Create and manage quizzes by leveraging the power of GenAI</p>
            <a href='{}' target='_blank' class="btn">Go to Teacher Portal</a>
        </div>
    """.format(teacher_url), unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="role-box">
            <img src="https://img.icons8.com/ios-filled/100/student-center.png" width="80"/>
            <h3>🎓 I'm a Student</h3>
            <p>Attempt quizzes and track your performance in real-time.</p>
            <a href='{}' target='_blank' class="btn">Go to Student Portal</a>
        </div>
    """.format(student_url), unsafe_allow_html=True)
