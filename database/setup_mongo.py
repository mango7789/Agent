import os, sys, json
from pathlib import Path
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from src.utils import get_curr_str_time

TEMPLATE_DIR = Path("./template")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def create_indexes():
    """Create indexes on collections for resume_id, job_id, and task_id"""
    db = client["CV_RESUME"]

    # Create index for resume
    resume_collections = db["resume"]
    resume_collections.create_index([("resume_id", 1)], unique=True)

    # Create index for task
    task_collections = db["task"]
    task_collections.create_index([("task_id", 1)], unique=True)

    # Create index for score
    score_collections = db["score"]
    score_collections.create_index([("job_id", 1)])
    score_collections.create_index([("resume_id", 1)])

    # Create index for chat
    chat_collections = db["chat"]
    chat_collections.create_index([("resume_id", 1)])


if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["CV_RESUME"]

    # Clear existing collections
    db.drop_collection("resume")
    db.drop_collection("job")
    db.drop_collection("task")
    db.drop_collection("score")
    db.drop_collection("chat")

    # Load template jsons
    with open(TEMPLATE_DIR / "resume.json", encoding="utf-8") as f:
        resume = json.load(f)

    with open(TEMPLATE_DIR / "job.json", encoding="utf-8") as f:
        job = json.load(f)

    with open(TEMPLATE_DIR / "task.json", encoding="utf-8") as f:
        task = json.load(f)

    with open(TEMPLATE_DIR / "score.json", encoding="utf-8") as f:
        score = json.load(f)

    with open(TEMPLATE_DIR / "chat.json", encoding="utf-8") as f:
        chat = json.load(f)

    # Insert template data into MongoDB
    resume_collections = db["resume"]
    resume["created_at"] = get_curr_str_time()
    resume_inserted = resume_collections.insert_one(resume)

    job_collections = db["job"]
    job["created_at"] = get_curr_str_time()
    job_inserted = job_collections.insert_one(job)
    job_id = job_inserted.inserted_id

    task_collections = db["task"]
    task["created_at"] = get_curr_str_time()
    task_inserted = task_collections.insert_one(task)
    task_id = task_inserted.inserted_id

    score_collections = db["score"]
    score["job_id"] = ObjectId(job_id)
    score["updated_at"] = get_curr_str_time()
    score_inserted = score_collections.insert_one(score)

    chat_collections = db["chat"]
    chat["created_at"] = get_curr_str_time()
    chat_collections.insert_one(chat)

    # Create indexes after data insertion
    create_indexes()
