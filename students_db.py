
# students_db.py
import os
import hashlib
import pymongo
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv
from mailersend import emails
from bson import ObjectId


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


def get_missed_counts_for_all_students():
    db = connect_to_db()
    coll = db["Student_Records"]
    pipeline = [
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


def update_attendance_subdoc(student_id: str, old_date: str, new_status: str, new_comment: str) -> bool:
    """
    Update the attendance subdoc where 'date' == old_date for the given student_id.
    Returns True if a document was updated, False otherwise.
    
    NOTE: If old_date is stored as an ISO string, parse it carefully.
          If your date is a real Mongo Date object, consider storing a subdoc '_id' instead.
    """
    db = connect_to_db()
    coll = db["Student_Records"]

    # Attempt to parse old_date as ISO 8601
    try:
        parsed_date = datetime.fromisoformat(old_date)
    except ValueError:
        # If that fails, fallback to dateutil
        from dateutil import parser
        parsed_date = parser.parse(old_date)

    result = coll.update_one(
        {
            "student_id": student_id,
            "attendance.date": parsed_date
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
                        new_contact_email: str, new_parent_email: str) -> bool:
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
            "parent_email": new_parent_email
        }
    }

    result = coll.update_one({"student_id": student_id}, update_query)
    return result.modified_count > 0


def record_student_attendance_in_array(name, program_id, status, comment=None):
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
                "contact_email": "",
                "parent_email": "",
                "missed_count": 0
            }
        },
        upsert=True
    )

    # 3) Build attendance sub-doc
    attendance_entry = {
        "date": datetime.utcnow(),
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
        {"missed_count": 1, "parent_email": 1, "name": 1}
    )
    new_missed = doc.get("missed_count", 0)
    parent_email = doc.get("parent_email", "")
    student_name = doc.get("name", "")

    # 6) If absent, maybe send email
    if missed_inc == 1 and parent_email:
        google_form_link = "https://docs.google.com/forms/..."
        if new_missed == 1:
            subject = f"1st Absence: {student_name} Missed Today’s Session"
            body = (
                "Hello,\n\n"
                f"We wanted to inform you that your child, {student_name}, missed today's session. "
                "Please ensure they attend next time. If they had a valid excuse, you can submit it here:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        elif new_missed == 2:
            subject = f"2nd Absence: {student_name} Missed Another Session"
            body = (
                "Hello,\n\n"
                f"Your child, {student_name}, has now missed two sessions. If they miss one more, "
                "they may be removed from the program. Please submit an excuse:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        elif new_missed == 3:
            subject = f"3rd Absence: {student_name}"
            body = (
                "Hello,\n\n"
                f"Your child, {student_name}, has missed three sessions. We will contact you. "
                "You can still submit an excuse here:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )
        else:
            subject = f"{student_name} Has Missed {new_missed} Sessions"
            body = (
                "Hello,\n\n"
                f"Your child, {student_name}, has missed multiple sessions. Please contact us or "
                "submit an excuse:\n"
                f"{google_form_link}\n\n"
                "Thank you,\n"
                "Club Stride Team"
            )

        send_missed_alert_email(
            parent_email=parent_email,
            student_name=student_name,
            program_name=program_id,
            subject_line=subject,
            body_text=body
        )

    return f"Updated attendance for student_id={student_id} (status={status})"


def send_missed_alert_email(parent_email: str,
                            student_name: str,
                            program_name: str,
                            subject_line: str,
                            body_text: str):
    """
    Sends an absence alert via MailerSend.
    """
    # MAILERSEND_API_KEY = os.environ.get("MAILERSEND_API_KEY")
    MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]

    mailer = emails.NewEmail(MAILERSEND_API_KEY)
    mail_body = {}

    mail_from = {
        "name": "Club Stride",
        "email": "javier@clubstride.org"
    }

    recipients = [{"name": parent_email.split('@')[0], "email": parent_email}]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject_line, mail_body)
    mailer.set_plaintext_content(body_text, mail_body)

    response = mailer.send(mail_body)
    print("MailerSend response:", response)
