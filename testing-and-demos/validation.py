from pydantic import BaseModel, ValidationError
from typing import List

class OptionModel(BaseModel):
    option_text: str    
    is_correct: bool

class QuestionModel(BaseModel):
    question_id: int
    question: str
    options: List[OptionModel]

class QuizModel(BaseModel):
    quiz_id: int
    title: str
    desc: str
    src_doc: str
    questions: List[QuestionModel]

def validate_quiz_response(response: dict) -> int:
    try:
        quiz = QuizModel(**response)
        print("Validation successful!")
        return 0
    except ValidationError as e:
        print("Validation error:", e.json())
        return 1


sample_response = {
    "quiz_id": 101,
    "title": "Machine Learning and NLP Quiz",
    "desc": "This quiz will test your understanding of various machine learning techniques, NLP tasks, and data preprocessing.",
    "src_doc": "Uploaded Document",
    "questions": [
        {
            "question_id": 1,
            "question": "What does a Bag of Words model do?",
            "options": [
                {"option_text": "Represents text as a set of words, ignoring grammar and word order", "is_correct": True},
                {"option_text": "Translates text from one language to another", "is_correct": False},
                {"option_text": "Summarizes a long text into a few sentences", "is_correct": False},
                {"option_text": "Analyzes sentiment of a text", "is_correct": False}
            ]
        },
        {
            "question_id": 2,
            "question": "Which NLP task involves categorizing a movie review as positive or negative?",
            "options": [
                {"option_text": "Text Classification", "is_correct": True},
                {"option_text": "Machine Translation", "is_correct": False},
                {"option_text": "Text Summarization", "is_correct": False},
                {"option_text": "Sentiment Analysis", "is_correct": False}
            ]
        },
        {
            "question_id": 3,
            "question": "What is Deep Learning?",
            "options": [
                {"option_text": "A subset of machine learning that uses neural networks to model complex patterns", "is_correct": True},
                {"option_text": "A method of text representation", "is_correct": False},
                {"option_text": "A type of NLP task", "is_correct": False},
                {"option_text": "A data preprocessing technique", "is_correct": False}
            ]
        },
        {
            "question_id": 4,
            "question": "What is the importance of Data Preprocessing?",
            "options": [
                {"option_text": "To clean the data because real-world data is often incomplete, noisy, or inconsistent", "is_correct": True},
                {"option_text": "To translate the data from one language to another", "is_correct": False},
                {"option_text": "To classify the data into different categories", "is_correct": False},
                {"option_text": "To create a bag of words model", "is_correct": False}
            ]
        },
        {
            "question_id": 5,
            "question": "What is TF-IDF?",
            "options": [
                {"option_text": "An improvement on the Bag of Words model that weighs words by their importance", "is_correct": True},
                {"option_text": "A type of neural network used in deep learning", "is_correct": False},
                {"option_text": "A data preprocessing technique", "is_correct": False},
                {"option_text": "A task in NLP that involves translating text", "is_correct": False}
            ]
        }
    ]
}




sample_response_3 = {
    "quiz_id": 1,
    "title": "Machine Learning and NLP",
    "description": "A quiz based on the uploaded document.",
    "source_document": "Uploaded Document",
    "questions": [
        {
            "question_id": 1,
            "question_text": "What does Bag of Words method represent text as?",
            "options": [
                {"option_text": "A set of words, ignoring grammar and word order", "is_correct": True},
                {"option_text": "A set of words, considering grammar and word order", "is_correct": False},
                {"option_text": "A set of sentences, ignoring word order", "is_correct": False},
                {"option_text": "A set of sentences, considering word order", "is_correct": False}
            ]
        },
        {
            "question_id": 2,
            "question_text": "What is TF-IDF an improvement of?",
            "options": [
                {"option_text": "Bag of Words model", "is_correct": True},
                {"option_text": "Machine Learning model", "is_correct": False},
                {"option_text": "Text Classification model", "is_correct": False},
                {"option_text": "Sentiment Analysis model", "is_correct": False}
            ]
        },
        {
            "question_id": 3,
            "question_text": "What is an example of a Text Classification NLP task?",
            "options": [
                {"option_text": "Categorizing a movie review as positive or negative", "is_correct": True},
                {"option_text": "Translating an English sentence to French", "is_correct": False},
                {"option_text": "Summarizing a long news article into a few sentences", "is_correct": False},
                {"option_text": "Deciding whether to play outside based on weather conditions", "is_correct": False}
            ]
        },
        {
            "question_id": 4,
            "question_text": "What is the purpose of data transformation in machine learning?",
            "options": [
                {"option_text": "To ensure that data is in a suitable format for machine learning algorithms", "is_correct": True},
                {"option_text": "To identify outliers in the data", "is_correct": False},
                {"option_text": "To replace missing values in the data", "is_correct": False},
                {"option_text": "To increase the size of the data", "is_correct": False}
            ]
        },
        {
            "question_id": 5,
            "question_text": "What is a common method for treating outliers in data?",
            "options": [
                {"option_text": "Transforming the data (e.g., using logarithmic transformations)", "is_correct": True},
                {"option_text": "Increasing the size of the data", "is_correct": False},
                {"option_text": "Using the Bag of Words model", "is_correct": False},
                {"option_text": "Applying Deep Learning techniques", "is_correct": False}
            ]
        }
    ]
}

sample_response_2 = {

    
    "quiz_id": "ML_NLP_Quiz_001",
    "title": "Machine Learning & NLP Quiz",
    "description": "A quiz based on the concepts of Machine Learning, Natural Language Processing and advanced ML techniques.",
    "source_document": "Uploaded Document",
    "questions": [
        {
            "question_id": 1,
            "question_text": "What does Bag of Words method ignore in a text?",
            "options": [
                {"option_text": "Frequency of each word", "is_correct": False},
                {"option_text": "Grammar and word order", "is_correct": True},
                {"option_text": "Unique words", "is_correct": False},
                {"option_text": "Common words", "is_correct": False}
            ]
        },
        {
            "question_id": 2,
            "question_text": "Which of the following is NOT an example of NLP task?",
            "options": [
                {"option_text": "Text Classification", "is_correct": False},
                {"option_text": "Sentiment Analysis", "is_correct": False},
                {"option_text": "Outlier Detection", "is_correct": True},
                {"option_text": "Machine Translation", "is_correct": False}
            ]
        },
        {
            "question_id": 3,
            "question_text": "What is Deep Learning a subset of?",
            "options": [
                {"option_text": "NLP", "is_correct": False},
                {"option_text": "Machine Learning", "is_correct": True},
                {"option_text": "Data Transformation", "is_correct": False},
                {"option_text": "TF-IDF", "is_correct": False}
            ]
        },
        {
            "question_id": 4,
            "question_text": "What is a common technique for Handling Missing Data?",
            "options": [
                {"option_text": "Imputation", "is_correct": True},
                {"option_text": "Outlier Detection", "is_correct": False},
                {"option_text": "Data Transformation", "is_correct": False},
                {"option_text": "Deep Learning", "is_correct": False}
            ]
        },
        {
            "question_id": 5,
            "question_text": "How can outliers in the data be treated?",
            "options": [
                {"option_text": "By increasing their value", "is_correct": False},
                {"option_text": "By reducing their value", "is_correct": False},
                {"option_text": "By removing them or transforming the data", "is_correct": True},
                {"option_text": "By replacing them with mean value", "is_correct": False}
            ]
        }
    ]

}
# sample response of LLM 
sample_response_1 = {
    "quiz_id": 1,
    "title": "Introduction to Machine Learning",
    "desc": "A quiz to test your knowledge on the basics of Machine Learning.",
    "src_doc": "Machine_Learning_Basics.pdf",
    "questions": [
        {
            "question_id": 1,
            "question": "What is Machine Learning?",
            "options": [
                {"option_text": "A subset of artificial intelligence", "is_correct": True},
                {"option_text": "A type of programming language", "is_correct": False},
                {"option_text": "A form of data storage", "is_correct": False},
                {"option_text": "None of the above", "is_correct": False}
            ]
        },
        {
            "question_id": 2,
            "question": "Which of the following is a type of supervised learning?",
            "options": [
                {"option_text": "Regression", "is_correct": True},
                {"option_text": "Clustering", "is_correct": False},
                {"option_text": "Association", "is_correct": False},
                {"option_text": "Anomaly detection", "is_correct": False}
            ]
        }
    ]
}

# Test the validation function
validate_quiz_response(sample_response)