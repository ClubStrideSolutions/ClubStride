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


def notify_instructor_schedule_change(instructor_id: int, schedule_doc: dict, event_type="created"):
    """
    Sends an email notification to the instructor about a schedule change.
    
    Args:
        instructor_id: The instructor's ID
        schedule_doc: The schedule document with details
        event_type: "created", "updated", or "deleted"
    """
    from instructors_db import get_instructor_email, list_instructors
    
    # 1. Get instructor email
    instructor_email = get_instructor_email(instructor_id)
    if not instructor_email:
        print(f"No email found for instructor ID {instructor_id}. Schedule notification not sent.")
        return False
    
    # 2. Get instructor name
    all_instructors = list_instructors()
    instructor_name = "Instructor"
    for instr in all_instructors:
        if instr["instructor_id"] == instructor_id:
            instructor_name = instr["username"]
            break
    
    # 3. Get program details
    program_id = schedule_doc.get("program_id")
    all_programs = list_programs()
    program_name = f"Program ID: {program_id}"
    for prog in all_programs:
        if prog["program_id"] == program_id:
            program_name = prog["program_name"]
            break
    
    # 4. Compose email based on event type
    title = schedule_doc.get("title", "Untitled Class")
    recurrence = schedule_doc.get("recurrence", "None").replace("None", "One-Time")
    
    if event_type == "created":
        action = "New class schedule created"
    elif event_type == "updated":
        action = "Class schedule updated"
    else:
        action = "Class schedule deleted"
    
    subject_line = f"Club Stride: {action} - {title}"
    
    # Format time details based on recurrence type
    time_details = ""
    if recurrence == "One-Time":
        start_dt = schedule_doc.get("start_datetime")
        end_dt = schedule_doc.get("end_datetime")
        location = schedule_doc.get("location", "Not specified")
        
        if start_dt and end_dt:
            if isinstance(start_dt, str):
                from dateutil import parser
                start_dt = parser.parse(start_dt)
                end_dt = parser.parse(end_dt)
            
            date_str = start_dt.strftime("%A, %B %d, %Y")
            start_time = start_dt.strftime("%I:%M %p")
            end_time = end_dt.strftime("%I:%M %p")
            
            time_details = f"""
Date: {date_str}
Time: {start_time} to {end_time}
Location: {location}
"""
    elif recurrence == "Weekly":
        days_times = schedule_doc.get("days_times", [])
        if days_times:
            time_details = "Weekly Schedule:\n"
            for day_info in days_times:
                day = day_info.get("day", "")
                start = day_info.get("start_time", "")
                end = day_info.get("end_time", "")
                loc = day_info.get("location", "Not specified")
                
                time_details += f"- {day}: {start} to {end}, Location: {loc}\n"
    
    notes = schedule_doc.get("notes", "")
    notes_section = f"\nAdditional Notes:\n{notes}" if notes else ""
    
    body_text = f"""
Hello {instructor_name},

A class schedule has been {event_type} for you in the Club Stride Attendance System.

Class: {title}
Program: {program_name}
Type: {recurrence}
{time_details}{notes_section}

Please log in to the Club Stride Attendance System to view the complete details.

Thank you,
Club Stride Administration
"""
    
    # 5. Send email via MailerSend
    try:
        MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]
        
        mailer = emails.NewEmail(MAILERSEND_API_KEY)
        mail_body = {}
        
        mail_from = {
            "name": "Club Stride Administration",
            "email": "javier@clubstride.org"
        }
        
        recipients = [{
            "name": instructor_name,
            "email": instructor_email
        }]
        
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject(subject_line, mail_body)
        mailer.set_plaintext_content(body_text, mail_body)
        
        response = mailer.send(mail_body)
        print(f"MailerSend instructor schedule notification response: {response}")
        return True
    except Exception as e:
        print(f"Error sending instructor schedule notification: {e}")
        return False

# Modify the create_schedule function to notify the instructor
def create_schedule(schedule_doc) -> str:
    db = connect_to_db()
    coll = db["Schedules"]
    result = coll.insert_one(schedule_doc)
    
    # Notify the instructor if an instructor_id is present
    instructor_id = schedule_doc.get("instructor_id")
    if instructor_id:
        notify_instructor_schedule_change(instructor_id, schedule_doc, event_type="created")
    
    return str(result.inserted_id)

# Modify the update_schedule function to notify the instructor
def update_schedule(schedule_id: str, updates: dict) -> bool:
    """
    Update the schedule with the given _id using the keys in `updates`.
    Return True if a document was modified, else False.
    """
    db = connect_to_db()
    coll = db["Schedules"]
    
    # First get the original document to extract instructor_id
    original_doc = coll.find_one({"_id": ObjectId(schedule_id)})
    
    result = coll.update_one(
        {"_id": ObjectId(schedule_id)},
        {"$set": updates}
    )
    
    if result.modified_count > 0 and original_doc:
        # Get the updated document
        updated_doc = coll.find_one({"_id": ObjectId(schedule_id)})
        
        # Check if there's an instructor_id
        instructor_id = original_doc.get("instructor_id")
        if instructor_id:
            # Merge original and updates to get complete document
            merged_doc = {**original_doc, **updates}
            # Convert ObjectId to string for JSON serialization
            merged_doc["_id"] = str(merged_doc["_id"])
            
            notify_instructor_schedule_change(instructor_id, merged_doc, event_type="updated")
    
    return result.modified_count > 0

# Modify the delete_schedule function to notify the instructor
def delete_schedule(schedule_id: str) -> bool:
    """
    Delete a schedule document by _id.
    Returns True if a doc was deleted, else False.
    """
    db = connect_to_db()
    coll = db["Schedules"]
    
    # First get the document to extract instructor_id
    schedule_doc = coll.find_one({"_id": ObjectId(schedule_id)})
    
    result = coll.delete_one({"_id": ObjectId(schedule_id)})
    
    if result.deleted_count > 0 and schedule_doc:
        # Check if there's an instructor_id
        instructor_id = schedule_doc.get("instructor_id")
        if instructor_id:
            # Convert ObjectId to string for JSON serialization
            schedule_doc["_id"] = str(schedule_doc["_id"])
            
            notify_instructor_schedule_change(instructor_id, schedule_doc, event_type="deleted")
    
    return result.deleted_count > 0


# schedules_db.py
# def create_schedule(schedule_doc) -> str:
#     db = connect_to_db()
#     coll = db["Schedules"]
#     result = coll.insert_one(schedule_doc)
#     return str(result.inserted_id)

# def update_schedule(schedule_id: str, updates: dict) -> bool:
#     """
#     Update the schedule with the given _id using the keys in `updates`.
#     Return True if a document was modified, else False.
#     """
#     db = connect_to_db()
#     coll = db["Schedules"]

#     result = coll.update_one(
#         {"_id": ObjectId(schedule_id)},
#         {"$set": updates}
#     )
#     return result.modified_count > 0

# def delete_schedule(schedule_id: str) -> bool:
#     """
#     Delete a schedule document by _id.
#     Returns True if a doc was deleted, else False.
#     """
#     db = connect_to_db()
#     coll = db["Schedules"]

#     result = coll.delete_one({"_id": ObjectId(schedule_id)})
#     return result.deleted_count > 0
