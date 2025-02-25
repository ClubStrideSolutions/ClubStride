import pymongo
from datetime import datetime
from typing import List, Optional

# If you already have a connect_to_db() from your existing code:
from students_db import connect_to_db

from bson import ObjectId


# schedules_db.py
def create_schedule(schedule_doc) -> str:
    db = connect_to_db()
    coll = db["Schedules"]
    result = coll.insert_one(schedule_doc)
    return str(result.inserted_id)

def list_schedules(instructor_id: Optional[str] = None) -> List[dict]:
    """
    Retrieve all schedules or filter by instructor_id if provided.
    """
    db = connect_to_db()
    coll = db["Schedules"]

    query = {}
    if instructor_id:
        query["instructor_id"] = instructor_id

    docs = list(coll.find(query))
    # Convert ObjectIds to string if needed
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

def update_schedule(schedule_id: str, updates: dict) -> bool:
    """
    Update the schedule with the given _id using the keys in `updates`.
    Return True if a document was modified, else False.
    """
    db = connect_to_db()
    coll = db["Schedules"]

    result = coll.update_one(
        {"_id": ObjectId(schedule_id)},
        {"$set": updates}
    )
    return result.modified_count > 0

def delete_schedule(schedule_id: str) -> bool:
    """
    Delete a schedule document by _id.
    Returns True if a doc was deleted, else False.
    """
    db = connect_to_db()
    coll = db["Schedules"]

    result = coll.delete_one({"_id": ObjectId(schedule_id)})
    return result.deleted_count > 0


