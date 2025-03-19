# schedules_db.py
import pymongo
from datetime import datetime
from typing import List, Optional

# If you already have a connect_to_db() from your existing code:
from students_db import connect_to_db, list_programs
import streamlit as st
from bson import ObjectId

from dotenv import load_dotenv

from mailersend import emails  # so we can query the "Student_Records" collection
import os
load_dotenv()

def notify_schedule_change(program_id: int, schedule_doc: dict, event_type="created"):
    """
    Sends an email notification to all students in the given program_id
    about a newly created or updated schedule.

    :param program_id: numeric program_id from the schedule
    :param schedule_doc: the entire schedule document (title, recurrence, etc.)
    :param event_type: "created" or "updated" for the email subject/body
    """

    db = connect_to_db()
    coll = db["Student_Records"]
    # 1) Fetch all students in the given program
    students_in_program = coll.find({"program_id": program_id})

    recipients = []
    for student in students_in_program:
        email = student.get("contact_email")
        if email:
            recipients.append({
                "name": student.get("name", "Student"),
                "email": email
            })

    if not recipients:
        print(f"No student emails found for program_id={program_id}. No email sent.")
        return

     # --- 2) Lookup the program name from Postgres
    all_progs = list_programs()  # e.g. [{program_id: 101, program_name: 'STEM'}, ...]
    prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
    program_name = prog_map.get(program_id, f"Program ID={program_id}")

    # 3) Compose subject/body
    schedule_title = schedule_doc.get("title", "Untitled Class")
    recurrence = schedule_doc.get("recurrence", "None")
    msg_type = "New" if event_type == "created" else "Updated"

    subject_line = f"{msg_type} Class Schedule: {schedule_title}"
    body_text = (
        f"Hello,\n\n"
        f"We have {msg_type} a class schedule for your program: {program_name}.\n"
        f"Title: {schedule_title}\n"
        f"Recurrence: {recurrence}\n\n"
        "Best regards,\n"
        "Club Stride Team"
    )


    # 4) Send the email via MailerSend
    # MAILERSEND_API_KEY = os.environ.get("MAILERSEND_API_KEY")
    MAILERSEND_API_KEY= st.secrets["MAILERSEND_API_KEY"]

    mailer = emails.NewEmail(MAILERSEND_API_KEY)
    mail_body = {}

    mail_from = {
        "name": "Club Stride",
        "email": "javier@clubstride.org"
    }

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject_line, mail_body)
    mailer.set_plaintext_content(body_text, mail_body)

    response = mailer.send(mail_body)
    print("MailerSend schedule notification response:", response)


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

def list_schedules_by_program(program_ids: List[int]) -> List[dict]:
    db = connect_to_db()
    coll = db["Schedules"]

    # If the user has multiple programs, we want any schedule doc with program_id in that list
    query = {
        "program_id": {"$in": program_ids}
    }
    return list(coll.find(query))

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


