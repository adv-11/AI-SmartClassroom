# streamlit logic will go here
import streamlit as st
from modules.quiz_validation import validate_quiz_response


# # sample response of LLM 
# sample_response = {
#     "quiz_id": 1,
#     "title": "Introduction to Machine Learning",
#     "desc": "A quiz to test your knowledge on the basics of Machine Learning.",
#     "src_doc": "Machine_Learning_Basics.pdf",
#     "questions": [
#         {
#             "question_id": 1,
#             "question": "What is Machine Learning?",
#             "options": [
#                 {"option_text": "A subset of artificial intelligence", "is_correct": True},
#                 {"option_text": "A type of programming language", "is_correct": False},
#                 {"option_text": "A form of data storage", "is_correct": False},
#                 {"option_text": "None of the above", "is_correct": False}
#             ]
#         },
#         {
#             "question_id": 2,
#             "question": "Which of the following is a type of supervised learning?",
#             "options": [
#                 {"option_text": "Regression", "is_correct": True},
#                 {"option_text": "Clustering", "is_correct": False},
#                 {"option_text": "Association", "is_correct": False},
#                 {"option_text": "Anomaly detection", "is_correct": False}
#             ]
#         }
#     ]
# }

# print (validate_quiz_response(sample_response))