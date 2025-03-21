import streamlit as st
import openai
import os
from dotenv import load_dotenv

load_dotenv()

from PyPDF2 import PdfReader
import docx
import pandas as pd
import random
import time
import json

# Set page config
st.set_page_config(page_title="FlashQuiz Generator", page_icon="📚", layout="wide")

# App title and description
st.title("📚 FlashQuiz Generator")
st.subheader("Upload a document and generate flashcards and quizzes to test your knowledge")

# Style
st.markdown("""
<style>
.flashcard {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.question {
    background-color: #e6f3ff;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.score-card {
    background-color: #f0fff0;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Function to extract text from different document types
def extract_text(uploaded_file):
    text = ""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'txt':
        text = uploaded_file.getvalue().decode('utf-8')
    
    elif file_extension == 'pdf':
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    
    elif file_extension in ['docx', 'doc']:
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    
    else:
        st.error(f"Unsupported file format: {file_extension}")
        return None
    
    return text

# Function to generate flashcards and quizzes
def generate_flashcards_and_quizzes(text, num_cards=5):
    # Initialize OpenAI API
    client = openai.OpenAI(api_key=st.session_state.openai_api_key)
    
    # Create a prompt for GPT-4o Mini
    prompt = f"""
    Based on the following document, create {num_cards} flashcards paired with questions.
    
    For each flashcard:
    1. Extract an important concept or information as "note"
    2. Create a corresponding question that tests understanding
    3. Provide the correct answer
    4. Include 3 incorrect answer options
    
    Format your response as JSON with the following structure:
    {{
        "flashcards": [
            {{
                "note": "Brief explanation of a key concept",
                "question": "Question about this concept",
                "correct_answer": "The correct answer",
                "incorrect_answers": ["Wrong option 1", "Wrong option 2", "Wrong option 3"]
            }},
            ... more flashcards ...
        ]
    }}
    
    Document text:
    {text[:15000]}  # Limiting to 15000 chars to avoid token limits
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o Mini
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        
        # Parse JSON response and ensure it has the expected structure
        try:
            parsed_json = json.loads(result)
            
            # Ensure we have the flashcards key
            if "flashcards" not in parsed_json:
                raise ValueError("Response does not contain 'flashcards' key")
            
            # Process each flashcard to ensure it has the required fields
            processed_flashcards = []
            for card in parsed_json["flashcards"]:
                # Check for different possible field names for the note/concept
                note_content = card.get("note", card.get("concept", "No concept provided"))
                
                processed_card = {
                    "note": note_content,
                    "question": card.get("question", "No question provided"),
                    "correct_answer": card.get("correct_answer", "No answer provided"),
                    "incorrect_answers": card.get("incorrect_answers", ["Option A", "Option B", "Option C"])
                }
                processed_flashcards.append(processed_card)
            
            return processed_flashcards
            
        except json.JSONDecodeError:
            st.error("Failed to parse JSON response from the API")
            st.code(result)  # Display the raw response for debugging
            return None
            
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        return None

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False
if 'current_selection' not in st.session_state:
    st.session_state.current_selection = ""
if 'answered' not in st.session_state:
    st.session_state.answered = False

# Function to move to the next step
def next_step():
    st.session_state.current_step += 1
    st.session_state.current_selection = ""
    st.session_state.answered = False

# Function to handle answer selection
def handle_answer_selection(answer):
    st.session_state.current_selection = answer

# Function to submit answer
def submit_answer(idx, selected_answer, correct_answer, question, note):
    st.session_state.total_questions += 1
    is_correct = selected_answer == correct_answer
    
    if is_correct:
        st.session_state.score += 1
    
    # Store user's answer and correctness
    st.session_state.user_answers.append({
        "question": question,
        "user_answer": selected_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "note": note
    })
    
    st.session_state.answered = True

# API key input
# api_key = st.text_input("Enter your OpenAI API Key:", type="password", 
#                        help="Your API key is required to use GPT-4o Mini.")

api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    st.session_state.openai_api_key = api_key

# File uploader
uploaded_file = st.file_uploader("Upload a document (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])

# Number of flashcards selector
num_cards = st.slider("Number of flashcards to generate", min_value=3, max_value=20, value=5)

# Process button
if uploaded_file and st.session_state.openai_api_key and st.button("Generate FlashQuiz"):
    with st.spinner("Processing document and generating flashcards..."):
        # Extract text from document
        document_text = extract_text(uploaded_file)
        
        if document_text:
            # Generate flashcards and quizzes
            flashcards_data = generate_flashcards_and_quizzes(document_text, num_cards)
            
            if flashcards_data is not None:
                st.session_state.flashcards = flashcards_data
                st.session_state.current_step = 0
                st.session_state.score = 0
                st.session_state.total_questions = 0
                st.session_state.user_answers = []
                st.session_state.current_selection = ""
                st.session_state.answered = False
                st.session_state.file_processed = True
                st.success("FlashQuiz generated! Click 'Start Quiz' to begin.")

# Start quiz button
if st.session_state.file_processed and st.session_state.current_step == 0:
    if st.button("Start Quiz"):
        next_step()
        st.rerun()

# Display flashcards and questions
if st.session_state.flashcards and st.session_state.current_step > 0:
    # Get current flashcard index
    idx = (st.session_state.current_step - 1) // 2
    
    # Check if we're still within the flashcards range
    if idx < len(st.session_state.flashcards):
        current_card = st.session_state.flashcards[idx]
        
        # Even steps show flashcard
        if st.session_state.current_step % 2 == 1:
            st.markdown(f"""
            <div class='flashcard'>
                <h3>Flashcard {idx + 1}/{len(st.session_state.flashcards)}</h3>
                <p>{current_card['note']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Next", key="next_flashcard"):
                next_step()
                st.rerun()
        
        # Odd steps show question
        else:
            st.markdown(f"""
            <div class='question'>
                <h3>Question {idx + 1}/{len(st.session_state.flashcards)}</h3>
                <p>{current_card['question']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a list of all answers and shuffle them
            # Make sure to only shuffle once, not on every rerun
            question_key = f"q_{idx}"
            answer_key = f"a_{idx}"
            
            if answer_key not in st.session_state:
                all_answers = [current_card['correct_answer']] + current_card['incorrect_answers']
                random.shuffle(all_answers)
                st.session_state[answer_key] = all_answers
            
            # Get answers from session state
            all_answers = st.session_state[answer_key]
            
            # Create radio buttons for answer options with a unique key
            selected_answer = st.radio(
                "Select your answer:", 
                all_answers, 
                key=question_key,
                index=all_answers.index(st.session_state.current_selection) if st.session_state.current_selection in all_answers else 0,
                on_change=handle_answer_selection, 
                args=(st.session_state.get(question_key),)
            )
            
            # Store the selection in session state immediately
            st.session_state.current_selection = selected_answer
            
            # Show appropriate buttons based on whether the question has been answered
            if not st.session_state.answered:
                if st.button("Submit Answer", key=f"submit_{idx}"):
                    submit_answer(
                        idx, 
                        selected_answer, 
                        current_card['correct_answer'], 
                        current_card['question'], 
                        current_card['note']
                    )
                    st.rerun()
            else:
                # Show result after answering
                if selected_answer == current_card['correct_answer']:
                    st.success("Correct! 👍")
                else:
                    st.error(f"Incorrect. The correct answer is: {current_card['correct_answer']}")
                
                # Continue button to next flashcard
                if st.button("Continue to Next Flashcard", key=f"continue_{idx}"):
                    next_step()
                    st.rerun()
    
    # End of quiz - show results
    else:
        score_percentage = int((st.session_state.score / st.session_state.total_questions) * 100) if st.session_state.total_questions > 0 else 0
        
        st.markdown(f"""
        <div class='score-card'>
            <h2>Quiz Completed!</h2>
            <h3>Your Score: {st.session_state.score}/{st.session_state.total_questions} ({score_percentage}%)</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate areas for improvement
        if st.session_state.user_answers:
            incorrect_answers = [ans for ans in st.session_state.user_answers if not ans['is_correct']]
            
            if incorrect_answers:
                st.subheader("Areas for Improvement:")
                for i, ans in enumerate(incorrect_answers):
                    with st.expander(f"Topic {i+1}: {ans['question']}"):
                        st.markdown(f"**Concept:** {ans['note']}")
                        st.markdown(f"**Your answer:** {ans['user_answer']}")
                        st.markdown(f"**Correct answer:** {ans['correct_answer']}")
            else:
                st.success("Excellent! You answered all questions correctly.")
        
        # Option to restart
        if st.button("Start Over"):
            # Reset all quiz-related state
            st.session_state.current_step = 0
            st.session_state.file_processed = False
            st.session_state.answered = False
            st.session_state.score = 0
            st.session_state.total_questions = 0
            st.session_state.user_answers = []
            
            # Clear answer-related session state
            keys_to_remove = []
            for key in st.session_state:
                if key.startswith('q_') or key.startswith('a_'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del st.session_state[key]
                
            st.rerun()

# Display errors in a special debug section if in development
if st.session_state.get('debug_info'):
    with st.expander("Debug Information"):
        st.write(st.session_state.debug_info)

# Instructions and help
with st.expander("How to use FlashQuiz Generator"):
    st.markdown("""
    1. Log in to the platform.
    2. Upload a document (PDF, DOCX, or TXT)
    3. Select the number of flashcards you want to generate
    4. Click 'Generate FlashQuiz'
    5. Start the quiz and go through each flashcard and question
    6. See your score and areas for improvement at the end
    """)

# Footer
st.markdown("---")
st.markdown("FlashQuiz Generator v1.0 | Powered by GPT-4o Mini")