import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from pydantic import BaseModel, ValidationError, Field
from typing import List
import json
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))


# Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# Validation Models
class OptionModel(BaseModel):
    option_text: str = Field(description="Option text")
    is_correct: bool = Field(description="Correct option flag")   

class QuestionModel(BaseModel):
    question_id: int = Field(description="Unique ID for the question")
    question_text: str  = Field(description="Question text")
    options: List[OptionModel] = Field(description="List of options")

class QuizModel(BaseModel):
    quiz_id: int = Field(description="Unique ID for the quiz")
    title: str = Field(description="Title of the quiz")
    description: str = Field(description="Description of the quiz")
    source_document: str = Field(description="Source document for the quiz")
    questions: List[QuestionModel]  = Field(description="List of questions")


parser = PydanticOutputParser(pydantic_object=QuizModel)

def validate_quiz_response(response: dict) -> int:
    try:
        quiz = QuizModel(**response)
        print("Validation successful!")
        return 0
    except ValidationError as e:
        print("Validation error:", e.json())
        return 1

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
        if quiz_file:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(quiz_file.read())
                temp_file_path = temp_file.name

            try:
                # Load and split the document
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()

                if not docs:
                    st.error("Failed to extract content from the uploaded document. Please try another file.")
                    return

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)

                # Vector Store
                vector_store = FAISS.from_documents(splits, embeddings)
                retriever = vector_store.as_retriever()

                parser = PydanticOutputParser(pydantic_object=QuizModel)
                prompt = PromptTemplate(
                    template="You are a teacher and need to generate a quiz for your class based on the provided document. Generate 5 questions. Format Instructions:\n{format_instructions}\n",

                    partial_variables={"format_instructions": parser.get_format_instructions()},
                    )



                # Prompt
#                 prompt = f"""
# You are a teacher and need to generate a quiz for your class based on the provided document.

# The quiz should contain {num_questions} questions.

# Each question should have 4 options, out of which only one is correct.

# Format the output as a JSON object with the following structure:

# {{
#     "quiz_id": ,
#     "title": "",
#     "desc": "{test_description}",
#     "src_doc": "Uploaded Document",
#     "questions": [
#         {{
#             "question_id": 1,
#             "question": "",
#             "options": [
#                 {{"option_text": "", "is_correct": True}},
#                 {{"option_text": "", "is_correct": False}},
#                 {{"option_text": "", "is_correct": False}},
#                 {{"option_text": "", "is_correct": False}}
#             ]
#         }},
#         ...
#     ]
# }}



#Ensure the questions are relevant to the content of the uploaded document.
                # """

                # Retrieval-based QA
                rag_chain = prompt | llm | retriever | parser
                

                # rag_chain = llm | prompt | retriever

                teacher_quiz_config = f"Number of questions: {num_questions}, Test Description: {test_description}, Difficulty Level: {difficulty}"



                st.info("Generating quiz, please wait...")
                result = rag_chain.invoke({"query": ''})  

                if result:
                    
                    st.write("Quiz generated successfully!")
                    st.write(result)
                    # Validate Response
                    if validate_quiz_response(result['result']):

                        st.error("Validation failed. Check the quiz structure.")
                else:
                    st.error("Failed to generate quiz. LLM returned an empty response.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

        else:
            st.error("Please upload a document before generating a quiz.")

generate_quiz_page()
