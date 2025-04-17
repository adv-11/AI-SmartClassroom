import os
import tempfile
import json
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from pydantic import BaseModel, ValidationError
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
embeddings = OpenAIEmbeddings()

# Validation Models
class OptionModel(BaseModel):
    option_text: str
    is_correct: bool

class QuestionModel(BaseModel):
    question_id: int
    question_text: str
    options: List[OptionModel]

class QuizModel(BaseModel):
    quiz_id: int
    title: str
    description: str
    source_document: str
    questions: List[QuestionModel]

def validate_quiz_response(response: dict) -> int:
    try:
        quiz = QuizModel(**response)
        print("Validation successful!")
        return 0
    except ValidationError as e:
        print("Validation error:", e.json())
        return 1

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate_quiz():
    # Inputs
    num_questions = int(input("Enter number of questions (1-10): "))
    test_description = input("Enter a short description of the test: ")
    difficulty = int(input("Enter difficulty level (1-3): "))
    file_path = input("Enter the path to the PDF file: ")

    if not os.path.exists(file_path):
        print("File not found!")
        return
    
    try:
        # Load and split document
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        if not docs:
            print("Failed to extract content from the document.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Vector Store
        vector_store = FAISS.from_documents(splits, embeddings)
        retriever = vector_store.as_retriever()

        parser = PydanticOutputParser(pydantic_object=QuizModel)

        prompt = f"""
You are a teacher and need to generate a quiz for your class based on the provided document.

The quiz should contain {num_questions} questions.

Each question should have 4 options, out of which only one is correct.

Format the output as a JSON object with the following structure:

{{
    "quiz_id": ,
    "title": "",
    "desc": "{test_description}",
    "src_doc": "Uploaded Document",
    "questions": [
        {{
            "question_id": 1,
            "question": "",
            "options": [
                {{"option_text": "", "is_correct": True}},
                {{"option_text": "", "is_correct": False}},
                {{"option_text": "", "is_correct": False}},
                {{"option_text": "", "is_correct": False}}
            ]
        }},
        ...
    ]
}}

Ensure the questions are relevant to the content of the uploaded document.
        """
        
        rag_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

        print("Generating quiz, please wait...")
        result = rag_chain.invoke(prompt)

        if result:
            print("Quiz generated successfully!")
            print(json.dumps(result, indent=4))

            if validate_quiz_response(result.result):
                print("Validation failed. Check the quiz structure.")
        else:
            print("Failed to generate quiz. LLM returned an empty response.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    generate_quiz()
