
# students_db.py
import os
import hashlib
import pymongo
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv
from mailersend import emails
from bson import ObjectId

from instructors_db import list_programs

load_dotenv()

@st.cache_resource
def connect_to_db():
    # CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
    CONNECTION_STRING = st.secrets["CONNECTION_STRING"]

    client = pymongo.MongoClient(CONNECTION_STRING)
    db = client["Student_Data"]
    return db


def generate_student_id(name: str, program_id: str) -> str:
    composite_str = f"{name.strip().lower()}:{str(program_id).lower()}"
    full_hash = hashlib.md5(composite_str.encode('utf-8')).hexdigest()
    return full_hash[:8]


def get_attendance_subdocs_in_range(start_date, end_date):
    """
    Returns all unwound attendance sub-docs from Student_Records
    where attendance.date is between start_date and end_date (inclusive).
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    pipeline = [
        {"$unwind": "$attendance"},
        {
            "$match": {
                "attendance.date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
        },
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


def get_attendance_subdocs_last_week():
    """
    Convenience function returning attendance sub-docs for the last 7 days.
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    return get_attendance_subdocs_in_range(seven_days_ago, now)


def get_student_count_as_of_last_week():
    """
    Returns how many Student_Records existed as of ~7 days ago,
    by comparing _id timestamps (embedded in ObjectId).
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    last_week_oid = ObjectId.from_datetime(seven_days_ago)

    count = coll.count_documents({"_id": {"$lt": last_week_oid}})
    return count


def store_student_record(name, phone, contact_email, program_id, grade="", school=""): #parent_email
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
                # "parent_email": parent_email,
                "program_id": program_id,
                "grade": grade,
                "school": school
            }}
        )
        return f"Student record updated for {name} (ID={student_id})."
    else:
        doc = {
            "student_id": student_id,
            "name": name,
            "phone": phone,
            "contact_email": contact_email,
            # "parent_email": parent_email,
            "program_id": program_id,
            "attendance": [],
            "missed_count": 0,
            "grade": grade,
            "school": school
        }
        coll.insert_one(doc)
        return f"New student record added for {name} (ID={student_id})!"


# def get_all_students():
#     db = connect_to_db()
#     coll = db["Student_Records"]
#     return list(coll.find())
def get_all_students(program_ids=None):
    """
    Returns a list of student records.
    If 'program_ids' is provided (list of numeric IDs),
    only returns those records where 'program_id' is in that list.
    """
    db = connect_to_db()
    coll = db["Student_Records"]
    
    if program_ids:
        query = {"program_id": {"$in": program_ids}}
    else:
        query = {}
    
    return list(coll.find(query))


def get_all_attendance_subdocs():
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
        {"$unwind": "$attendance"},
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


def get_missed_counts_for_all_students(program_ids=None):
    """
    Returns a list of {student_id, name, phone, program_id, sum_missed}
    Optionally filters by a list of program_ids if provided.
    """
    db = connect_to_db()
    coll = db["Student_Records"]
    
    pipeline = []
    
    # Only match certain program IDs if given (i.e., instructor scenario)
    if program_ids:
        pipeline.append({"$match": {"program_id": {"$in": program_ids}}})
    
    pipeline += [
        {"$unwind": "$attendance"},
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
                            {"$eq": ["$attendance.status", "Absent"]},
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


def delete_student_record(student_id: str) -> bool:
    """
    Delete a student document from 'Student_Records' by student_id.
    Returns True if a doc was actually deleted, False otherwise.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    result = coll.delete_one({"student_id": student_id})
    return result.deleted_count > 0


def fetch_all_attendance_records():
    """
    Unwind attendance sub-docs into one row per record.
    Returns a list of dicts with:
      {
        student_id, name, program_id,
        attendance: { date, status, comment }
      }
    """
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
        {"$unwind": "$attendance"},
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

from datetime import timedelta

def update_attendance_subdoc(student_id: str, old_date, new_status: str, new_comment: str) -> bool:
    
    db = connect_to_db()
    coll = db["Student_Records"]

    # Check and ensure old_date is datetime
    if isinstance(old_date, str):
        from dateutil import parser
        parsed_date = parser.parse(old_date)
    elif isinstance(old_date, datetime):
        parsed_date = old_date
    else:
        raise ValueError("old_date must be a datetime object or an ISO-formatted string")

    date_upper_bound = parsed_date + timedelta(milliseconds=1)

    result = coll.update_one(
        {
            "student_id": student_id,
            "attendance.date": {
                "$gte": parsed_date,
                "$lt": parsed_date + timedelta(milliseconds=1)
            }
        },
        {
            "$set": {
                "attendance.$.status": new_status,
                "attendance.$.comment": new_comment
            }
        }
    )
    return result.modified_count > 0

def update_student_info(student_id: str, new_name: str, new_phone: str,
                        new_contact_email: str, new_grade: str, new_school: str) -> bool:
    # new_parent_email: str
    """
    Update fields of an existing student document by student_id.
    Returns True if an update occurred, False otherwise.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    update_query = {
        "$set": {
            "name": new_name,
            "phone": new_phone,
            "contact_email": new_contact_email,
            # "parent_email": new_parent_email,
            "grade": new_grade,
            "school": new_school
        }
    }

    result = coll.update_one({"student_id": student_id}, update_query)
    return result.modified_count > 0


def record_student_attendance_in_array(name, program_id, status, comment=None, attendance_date=None):
    db = connect_to_db()
    coll = db["Student_Records"]
    student_id = generate_student_id(name, program_id)

    # 1) If "Absent," increment missed_count by 1
    missed_inc = 1 if status == "Absent" else 0

    # 2) Upsert in case doc doesn't exist
    coll.update_one(
        {"student_id": student_id},
        {
            "$setOnInsert": {
                "name": name,
                "program_id": program_id,
                "phone": "",
                "contact_email": "",  # Student's email
                # "parent_email": "",   # (unused now, but left for reference)
                "missed_count": 0,
                "grade": "",        # Optionally you can default them too
                "school": ""
            }
        },
        upsert=True
    )
    
    if attendance_date is None:
        attendance_date = datetime.utcnow()
    # 3) Build attendance sub-doc
    attendance_entry = {
        "date": attendance_date,
        "status": status,
        "comment": comment
    }

    # 4) Push + inc missed_count if absent
    coll.update_one(
        {"student_id": student_id},
        {
            "$push": {"attendance": attendance_entry},
            "$inc": {"missed_count": missed_inc}
        }
    )

    # 5) Retrieve updated doc, possibly send email
    doc = coll.find_one(
        {"student_id": student_id},
        # Now fetch contact_email, not parent_email
        {"missed_count": 1, "contact_email": 1, "name": 1}
    )
    new_missed = doc.get("missed_count", 0)
    student_email = doc.get("contact_email", "")
    student_name = doc.get("name", "")

    # 6) If absent, maybe send email to the student
    
    if missed_inc == 1 and student_email:
        program_list = list_programs()
        prog_map = {p["program_id"]: p["program_name"] for p in program_list}
        program_name = prog_map.get(program_id, f"Program ID={program_id}")
        absent_date_str = attendance_date.strftime("%B %d, %Y")  
        google_form_link = "https://docs.google.com/forms/d/e/1FAIpQLSdeM6AUXXcCK3mNWaCQFrnoc-fmjFC615sh4cMGJ04iLGua1g/viewform?usp=dialog"  # Update your form link

        # Customize the subject/body text as you see fit
        if new_missed == 1:
            subject = f"[1st Absence] {student_name} missed {program_name} on {absent_date_str}"
            body = (
                f"Hello {student_name},\n\n"
                f"You missed our {program_name} session on {absent_date_str}. "
                "If you had a valid excuse, please submit it here:\n"
                f"\n{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        elif new_missed == 2:
            subject = f"[2nd Absence] {student_name} missed {program_name} again on {absent_date_str}"
            body = (
                f"Hello {student_name},\n\n"
                f"You've now missed two {program_name} sessions. The latest absence was {absent_date_str}..."
                "If you miss one more, you may be removed from the program. Please submit an excuse:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        elif new_missed == 3:
            subject = f"3rd Absence: {student_name}"
            body = (
                f"Hello {student_name},\n\n"
                f"You have missed three {program_name} sessions. The latest absence was {absent_date_str}..."
                "We will contact you directly. "
                "If you had a valid excuse, you can still submit it here:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        else:
            subject = f"{student_name} has missed {new_missed} {program_name} sessions"
            body = (
                f"Hello {student_name},\n\n"
                f"You have missed {new_missed} sessions. Please contact us or "
                f"submit an excuse:\n{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )

        # Now call the email function with the student’s email
        send_missed_alert_email(
            student_email=student_email,
            student_name=student_name,
            program_name=program_id,
            subject_line=subject,
            body_text=body
        )

    return f"Updated attendance for student_id={student_id} (status={status})"


def send_missed_alert_email(student_email: str,
                            student_name: str,
                            program_name: str,
                            subject_line: str,
                            body_text: str):
    """
    Sends an absence alert via MailerSend to the student's email.
    """
    # MAILERSEND_API_KEY = os.environ.get("MAILERSEND_API_KEY")
    MAILERSEND_API_KEY= st.secrets["MAILERSEND_API_KEY"]

    mailer = emails.NewEmail(MAILERSEND_API_KEY)
    mail_body = {}

    mail_from = {
        "name": "Club Stride",
        "email": "javier@clubstride.org"
    }

    # Single recipient is the student
    recipients = [{"name": student_email.split('@')[0], "email": student_email}]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject_line, mail_body)
    mailer.set_plaintext_content(body_text, mail_body)

    response = mailer.send(mail_body)
    print("MailerSend response:", response)

def delete_attendance_subdoc(student_id: str, target_date) -> bool:
    """
    Remove an attendance sub-document that matches a specific date.
    Returns True if a sub-document was actually removed, False otherwise.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    # If target_date is a string, parse to a datetime
    if isinstance(target_date, str):
        from dateutil import parser
        target_date = parser.parse(target_date)
    
    result = coll.update_one(
        {"student_id": student_id},
        {
            # $pull removes array elements that match the query
            "$pull": {
                "attendance": {
                    # We match on exact date/time (to millisecond).
                    # If your stored times can vary by microseconds, consider a range match.
                    "date": { 
                        "$gte": target_date, 
                        "$lt": target_date + timedelta(milliseconds=1)
                    }
                }
            }
        }
    )
    return result.modified_count > 0


def upsert_attendance_subdoc(student_id: str, target_date, new_status: str, new_comment: str = "") -> bool:
    """
    Upsert an attendance record on a specific date for this student_id.
    If the date already exists, we update it. Otherwise, we insert a new sub-doc.
    
    Returns True if a sub-document was created or updated, False if nothing changed.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    # 1) Ensure target_date is a datetime object
    if isinstance(target_date, str):
        from dateutil import parser
        target_date = parser.parse(target_date)

    # 2) Try to update an existing sub-doc
    result = coll.update_one(
        {
            "student_id": student_id,
            "attendance.date": {
                "$gte": target_date,
                "$lt": target_date + timedelta(milliseconds=1)
            }
        },
        {
            "$set": {
                "attendance.$.status": new_status,
                "attendance.$.comment": new_comment
            }
        }
    )

    if result.matched_count > 0:
        # We found and updated an existing sub-document
        return result.modified_count > 0
    else:
        # 3) If no match, we push a new attendance sub-document
        attendance_entry = {
            "date": target_date,
            "status": new_status,
            "comment": new_comment
        }
        result_push = coll.update_one(
            {"student_id": student_id},
            {"$push": {"attendance": attendance_entry}}
        )
        return result_push.modified_count > 0
