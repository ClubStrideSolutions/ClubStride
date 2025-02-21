import pymongo
import hashlib
from datetime import datetime
import streamlit as st  # Only needed for @st.cache_resource or you can remove if you prefer a different caching approach

@st.cache_resource
def connect_to_db():
    CONNECTION_STRING = "mongodb+srv://javbarrios89:mediasense@clustersense.nh1tclt.mongodb.net/"
    client = pymongo.MongoClient(CONNECTION_STRING)
    db = client["Student_Data"]
    return db

def generate_student_id(name: str, program_id: str) -> str:
    composite_str = f"{name.strip().lower()}:{program_id.strip().lower()}"
    full_hash = hashlib.md5(composite_str.encode('utf-8')).hexdigest()
    return full_hash[:8]

def store_student_record(name, phone, contact_email, parent_email, program_id):
    db = connect_to_db()
    coll = db["Student_Records"]
    student_id = generate_student_id(name, program_id)

    existing = coll.find_one({"student_id": student_id})
    if existing:
        coll.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "name": name,
                "phone": phone,
                "contact_email": contact_email,
                "parent_email": parent_email,
                "program_id": program_id
            }}
        )
        return f"Student record updated for {name} (ID={student_id})."
    else:
        doc = {
            "student_id": student_id,
            "name": name,
            "phone": phone,
            "contact_email": contact_email,
            "parent_email": parent_email,
            "program_id": program_id,
            "attendance": [],
            "missed_count": 0
        }
        coll.insert_one(doc)
        return f"New student record added for {name} (ID={student_id})!"

def get_all_students():
    db = connect_to_db()
    coll = db["Student_Records"]
    return list(coll.find())

def record_student_attendance_in_array(name, program_id, status, comment=None):
    db = connect_to_db()
    coll = db["Student_Records"]
    student_id = generate_student_id(name, program_id)
    missed_inc = 1 if status == "Absent" else 0

    coll.update_one(
        {"student_id": student_id},
        {
            "$setOnInsert": {
                "name": name,
                "program_id": program_id,
                "phone": "",
                "contact_email": "",
                "parent_email": "",
                "missed_count": 0
            }
        },
        upsert=True
    )
    attendance_entry = {
        "date": datetime.utcnow(),
        "status": status,
        "comment": comment
    }
    coll.update_one(
        {"student_id": student_id},
        {
            "$push": {"attendance": attendance_entry},
            "$inc": {"missed_count": missed_inc}
        }
    )
    return f"Updated attendance for student_id={student_id} (status={status})"

def get_all_attendance_subdocs():
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
        { "$unwind": "$attendance" },
        {
            "$project": {
                "_id": 0,
                "student_id": 1,
                "name": 1,
                "program_id": 1,
                "phone": 1,
                "attendance.date": 1,
                "attendance.status": 1,
                "attendance.comment": 1
            }
        }
    ]
    return list(coll.aggregate(pipeline))

def get_missed_counts_for_all_students():
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
        { "$unwind": "$attendance" },
        {
            "$group": {
                "_id": {
                    "student_id": "$student_id",
                    "name": "$name",
                    "phone": "$phone",
                    "program_id": "$program_id"
                },
                "sum_missed": {
                    "$sum": {
                        "$cond": [
                            { "$eq": ["$attendance.status", "Absent"] },
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "student_id": "$_id.student_id",
                "name": "$_id.name",
                "phone": "$_id.phone",
                "program_id": "$_id.program_id",
                "sum_missed": 1
            }
        }
    ]
    return list(coll.aggregate(pipeline))

def check_admin(connection_string):
    """
    Checks if we can connect to MongoDB with the given connection string.
    Returns True if successful, False otherwise.
    """
    try:
        client = pymongo.MongoClient(connection_string)
        client.admin.command("ping")
        return True
    except:
        return False

# students_db.py

def delete_student_record(student_id: str) -> bool:
    """
    Delete a student document from 'Student_Records' by student_id.
    Returns True if a doc was actually deleted, False otherwise.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    result = coll.delete_one({"student_id": student_id})
    return result.deleted_count > 0

# students_db.py
def fetch_all_attendance_records():
    """
    Unwind attendance sub-docs into one row per record.
    Returns a list of dicts with {student_id, name, program_id, attendance: {date, status, comment}}
    """
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
        { "$unwind": "$attendance" },
        {
            "$project": {
                "_id": 0,
                "student_id": 1,
                "name": 1,
                "program_id": 1,
                "attendance.date": 1,
                "attendance.status": 1,
                "attendance.comment": 1
            }
        }
    ]
    return list(coll.aggregate(pipeline))
