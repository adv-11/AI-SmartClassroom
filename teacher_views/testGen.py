import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from typing import List
import json
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))

# Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# Utility to format document content
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Streamlit App
def generate_quiz_page():
    st.title("Generate Quiz")
    st.write("Upload a document and generate quizzes based on its content.")

    # User Inputs
    num_questions = st.slider("Number of Questions", min_value=1, max_value=10, value=5)
    test_description = st.text_area("Describe the test:", "Enter a short description of the test.")
    difficulty = st.slider("Difficulty Level", min_value=1, max_value=3, value=2)
    quiz_file = st.file_uploader("Upload a document (PDF only):", type=["pdf"])

    if st.button("Generate Quiz"):
        st.write("Quiz generation started")
        if quiz_file:
            st.write("File uploaded successfully")
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(quiz_file.read())
                temp_file_path = temp_file.name

            try:
                # Load and split the document
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()
                st.write(f"Loaded {len(docs)} document(s)")

                if not docs:
                    st.error("Failed to extract content from the uploaded document. Please try another file.")
                    return

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)
                st.write(f"Split document into {len(splits)} chunks")

                # Vector Store
                vector_store = FAISS.from_documents(splits, embeddings)
                retriever = vector_store.as_retriever()
                st.write("Vector store created")

                prompt = f"""
You are a teacher and need to generate a quiz for your class based on the provided document.

The quiz should contain {num_questions} questions.

Each question should have 4 options, out of which only one is correct.

Format the output as a valid JSON object. Do not include explanations or additional text.

{{
    "quiz_id": 1,
    "title": "Generated Quiz",
    "desc": "{test_description}",
    "src_doc": "Uploaded Document",
    "questions": [
        {{
            "question_id": 1,
            "question": "",
            "options": [
                {{"option_text": "", "is_correct": true}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}}
            ]
        }}
    ]
}}
                """
                st.write("Prompt prepared")

                # Ensure prompt is a string before invoking
                if not isinstance(prompt, str):
                    st.write("Warning: Prompt is not a string, converting to string...")
                    prompt = str(prompt)
                st.write(f"Type of prompt before invoke: {type(prompt)}")
                st.write(f"Prompt content: {prompt}")

                # Retrieval-based QA
                rag_chain = llm | retriever
                st.write("RAG chain created")

                teacher_quiz_config = f"Number of questions: {num_questions}, Test Description: {test_description}, Difficulty Level: {difficulty}"
                st.write("Config: ", teacher_quiz_config)

                st.info("Generating quiz, please wait...")
                result = rag_chain.invoke(prompt)
                st.write("Raw result from LLM:", result)

                print(f"Type of result: {type(result)}")
                print(f"Value of result: {result}")

                if isinstance(result, dict):
                    result = json.dumps(result)
                    st.write("Converted result to JSON string")
                
                if result:
                    try:
                        quiz_json = json.loads(result)
                        st.write("Quiz generated successfully!")
                        st.json(quiz_json)
                    except json.JSONDecodeError as e:
                        st.error(f"Failed to parse JSON: {str(e)}")
                        st.write(f"Raw response from LLM: {result}")
                else:
                    st.error("Failed to generate quiz. LLM returned an empty response.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write(f"Exception details: {e}")

        else:
            st.error("Please upload a document before generating a quiz.")

generate_quiz_page()
