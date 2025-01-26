from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client["google_classroom"]

def get_teacher_classes(teacher_id):
    db = get_db()
    return list(db.classes.find({"owner": teacher_id}))

def create_classroom(teacher_id, class_name):
    db = get_db()
    db.classes.insert_one({"name": class_name, "owner": teacher_id, "students": [], "content": {}})
