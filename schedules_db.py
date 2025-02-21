import pymongo
from datetime import datetime
from typing import List, Optional

# If you already have a connect_to_db() from your existing code:
from students_db import connect_to_db

# def create_schedule(instructor_id: str, program_id: str, title: str, start_dt: datetime,
#                     end_dt: datetime, recurrence: str = "None",
#                     days_of_week: Optional[List[str]] = None,
#                     notes: str = "") -> str:
#     """
#     Insert a new schedule document in 'Schedules' collection.
#     Returns the inserted _id as a string.
#     """
#     db = connect_to_db()
#     coll = db["Schedules"]

#     doc = {
#         "instructor_id": instructor_id,
#         "program_id": program_id,
#         "title": title,
#         "recurrence": recurrence,
#         "days_of_week": days_of_week or [],
#         "start_datetime": start_dt,
#         "end_datetime": end_dt,
#         "notes": notes
#     }

#     result = coll.insert_one(doc)
#     return str(result.inserted_id)

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

    from bson import ObjectId
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

    from bson import ObjectId
    result = coll.delete_one({"_id": ObjectId(schedule_id)})
    return result.deleted_count > 0
