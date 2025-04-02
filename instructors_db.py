# instructors_db.py
import psycopg2
import psycopg2.extras
from psycopg2 import sql
import bcrypt
import streamlit as st  # Only needed if you prefer st.cache_resource or st.secrets usage
import os
from dotenv import load_dotenv

load_dotenv()

# DB_URL = os.environ.get("DB_URL")
DB_URL= st.secrets["DB_URL"]
if not DB_URL:
    raise ValueError("DB_URL is not set in .env")

def get_connection():
    """Create and return a new database connection."""
    return psycopg2.connect(DB_URL)

############################################
# CREATE TABLES
############################################
def create_instructors_table():
    """Create the instructors table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS instructors (
            instructor_id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
            -- You can remove the old column if it exists
            -- programs TEXT
        );
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

def create_programs_table():
    """Create the programs table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS programs (
            program_id SERIAL PRIMARY KEY,
            program_name TEXT NOT NULL UNIQUE
        );
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

def create_instructor_programs_table():
    """Create the pivot table (instructor_programs) if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS instructor_programs (
            instructor_id INT NOT NULL,
            program_id INT NOT NULL,
            PRIMARY KEY (instructor_id, program_id),
            FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id),
            FOREIGN KEY (program_id) REFERENCES programs(program_id)
        );
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

############################################
# HELPER: CREATE ALL TABLES
############################################
def initialize_tables():
    """Call this once at startup to ensure all tables exist."""
    create_instructors_table()
    create_programs_table()
    create_instructor_programs_table()

############################################
# INSTRUCTOR ACCOUNT FUNCTIONS
############################################
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def add_instructor(username: str, password: str, role: str) -> bool:
    """Insert a new instructor row into the instructors table."""
    conn = get_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    try:
        cursor.execute(
            """
            INSERT INTO instructors (username, password_hash, role)
            VALUES (%s, %s, %s);
            """,
            (username, pw_hash, role)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        print("Error adding instructor:", e)
        return False
    finally:
        cursor.close()
        conn.close()

def update_instructor_email(instructor_id: int, email: str) -> bool:
    """
    Update an instructor's email address.
    Returns True if successful, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            ALTER TABLE instructors 
            ADD COLUMN IF NOT EXISTS email TEXT;
            """
        )
        conn.commit()
        
        cursor.execute(
            """
            UPDATE instructors
            SET email = %s
            WHERE instructor_id = %s
            """,
            (email, instructor_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating instructor email: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_instructor_email(instructor_id: int) -> str:
    """
    Retrieve an instructor's email address.
    Returns the email string or empty string if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # First ensure the column exists
        cursor.execute(
            """
            ALTER TABLE instructors 
            ADD COLUMN IF NOT EXISTS email TEXT;
            """
        )
        conn.commit()
        
        cursor.execute(
            """
            SELECT email 
            FROM instructors
            WHERE instructor_id = %s
            """,
            (instructor_id,)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] else ""
    except Exception as e:
        print(f"Error getting instructor email: {e}")
        return ""
    finally:
        cursor.close()
        conn.close()

from mailersend import emails

def notify_instructor_program_assignment(instructor_id: int, program_id: int, is_new_assignment=True):
    """
    Send an email notification to an instructor when they're assigned to a program.
    
    Args:
        instructor_id: The ID of the instructor being assigned
        program_id: The ID of the program they're assigned to
        is_new_assignment: True if this is a new assignment, False if removed
    """
    # 1. Get instructor email
    instructor_email = get_instructor_email(instructor_id)
    if not instructor_email:
        print(f"No email found for instructor ID {instructor_id}. Notification not sent.")
        return False
    
    # 2. Get instructor name
    all_instructors = list_instructors()
    instructor_name = "Instructor"
    for instr in all_instructors:
        if instr["instructor_id"] == instructor_id:
            instructor_name = instr["username"]
            break
    
    # 3. Get program name
    all_programs = list_programs()
    program_name = f"Program ID: {program_id}"
    for prog in all_programs:
        if prog["program_id"] == program_id:
            program_name = prog["program_name"]
            break
    
    # 4. Compose email
    action = "assigned to" if is_new_assignment else "removed from"
    subject_line = f"Club Stride: You have been {action} {program_name}"
    
    if is_new_assignment:
        body_text = f"""
Hello {instructor_name},

You have been assigned to the following program in the Club Stride Attendance System:

Program: {program_name}

You can now access student records, take attendance, and generate reports for this program.
Please log in to the system to view your updated assignments.

Thank you,
Club Stride Administration
        """
    else:
        body_text = f"""
Hello {instructor_name},

You have been removed from the following program in the Club Stride Attendance System:

Program: {program_name}

You will no longer have access to student records for this program.
If you believe this is an error, please contact the administrator.

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
        print(f"MailerSend instructor notification response: {response}")
        return True
    except Exception as e:
        print(f"Error sending instructor notification: {e}")
        return False
    
def list_instructors():
    """Return all instructors (excluding password hash)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT instructor_id, username, role FROM instructors"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "instructor_id": r[0],
            "username": r[1],
            "role": r[2]
        })
    return results

# instructors_db.py

def authenticate_instructor(username: str, password: str):
    """
    Check if the given username/password match a row in instructors.
    If valid, return { 'instructor_id': ..., 'role': ... } 
    Otherwise return None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT instructor_id, password_hash, role
        FROM instructors
        WHERE username = %s
        """,
        (username,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    instructor_id, stored_hash, role = row
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return {
            "instructor_id": instructor_id,
            "role": role
        }
    else:
        return None

def update_instructor_role(instructor_id: int, new_role: str):
    """Update an instructor's role by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE instructors
        SET role = %s
        WHERE instructor_id = %s
        """,
        (new_role, instructor_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_instructor_password(instructor_id: int, new_password: str):
    """
    Update the password_hash for a given instructor_id.
    """
    new_hash = hash_password(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE instructors
        SET password_hash = %s
        WHERE instructor_id = %s
        """,
        (new_hash, instructor_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def delete_instructor(instructor_id: int) -> bool:
    """
    Delete an instructor row by instructor_id.
    Returns True if a row was actually deleted, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Also remove from pivot table
    cursor.execute(
        "DELETE FROM instructor_programs WHERE instructor_id = %s",
        (instructor_id,)
    )
    cursor.execute(
        "DELETE FROM instructors WHERE instructor_id = %s",
        (instructor_id,)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    cursor.close()
    conn.close()

    return rows_affected > 0


def add_program(program_name: str) -> int:
    """
    Insert a new program into the programs table, ensuring program_name is unique.
    Returns the newly created program_id, or -1 if there's a duplicate or error.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO programs (program_name)
            VALUES (%s)
            RETURNING program_id
            """,
            (program_name,)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return new_id
    except psycopg2.errors.UniqueViolation:
        # This occurs when program_name is already in use
        conn.rollback()  # Roll back the transaction so we can continue
        return -1
    except psycopg2.Error as e:
        # Catch other database errors if needed
        conn.rollback()
        print("Error adding program:", e)
        return -1
    finally:
        cursor.close()
        conn.close()

def list_programs() -> list:
    """
    Returns a list of all programs: [{program_id, program_name}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT program_id, program_name FROM programs")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "program_id": r[0],
            "program_name": r[1]
        })
    return results

def assign_instructor_to_program(instructor_id: int, program_id: int) -> bool:
    """
    Insert a row into instructor_programs and notify the instructor.
    Returns True if inserted, False if already existing or error.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO instructor_programs (instructor_id, program_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (instructor_id, program_id)
        )
        
        # Check if a row was actually inserted (not a duplicate)
        if cursor.rowcount > 0:
            conn.commit()
            # Send notification email
            notify_instructor_program_assignment(instructor_id, program_id, is_new_assignment=True)
            return True
        else:
            # No rows affected (likely a duplicate)
            conn.commit()
            return False
    except Exception as e:
        print(f"Error assigning instructor to program: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

# Also modify the remove_instructor_from_program function
def remove_instructor_from_program(instructor_id: int, program_id: int) -> bool:
    """
    Remove the row from instructor_programs and notify the instructor.
    Returns True if a row was deleted, else False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM instructor_programs
            WHERE instructor_id = %s AND program_id = %s
            """,
            (instructor_id, program_id)
        )
        
        deleted = (cursor.rowcount > 0)
        conn.commit()
        
        if deleted:
            # Send notification email
            notify_instructor_program_assignment(instructor_id, program_id, is_new_assignment=False)
        
        return deleted
    except Exception as e:
        print(f"Error removing instructor from program: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
        
############################################
# INSTRUCTOR ↔ PROGRAMS RELATION
############################################
# def assign_instructor_to_program(instructor_id: int, program_id: int) -> bool:
#     """
#     Insert a row into instructor_programs.
#     Returns True if inserted, False if already existing or error.
#     """
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute(
#             """
#             INSERT INTO instructor_programs (instructor_id, program_id)
#             VALUES (%s, %s)
#             ON CONFLICT DO NOTHING
#             """,
#             (instructor_id, program_id)
#         )
#         conn.commit()
#         # rowcount won't work for ON CONFLICT DO NOTHING to detect duplicates
#         return True
#     except psycopg2.Error as e:
#         print("Error assigning instructor to program:", e)
#         return False
#     finally:
#         cursor.close()
#         conn.close()

# def remove_instructor_from_program(instructor_id: int, program_id: int) -> bool:
#     """
#     Remove the row from instructor_programs.
#     Returns True if a row was deleted, False otherwise.
#     """
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         """
#         DELETE FROM instructor_programs
#         WHERE instructor_id = %s AND program_id = %s
#         """,
#         (instructor_id, program_id)
#     )
#     conn.commit()
#     deleted = (cursor.rowcount > 0)
#     cursor.close()
#     conn.close()
#     return deleted


def list_instructor_programs(instructor_id: int) -> list:
    """
    Return all program_ids (and names) linked to this instructor
    via the instructor_programs pivot.
    Example return: [
      {"program_id": 101, "program_name": "Youth Leadership"},
      {"program_id": 202, "program_name": "STEM Robotics"}
    ]
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.program_id, p.program_name
        FROM instructor_programs ip
        JOIN programs p ON ip.program_id = p.program_id
        WHERE ip.instructor_id = %s
        """,
        (instructor_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "program_id": r[0],
            "program_name": r[1]
        })
    return results


def delete_program(program_id: int) -> bool:
    """
    Delete a program by program_id.
    Also remove any references in instructor_programs pivot.
    Returns True if the program was deleted, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1) Remove references in the pivot
        cursor.execute("DELETE FROM instructor_programs WHERE program_id = %s", (program_id,))
        
        # 2) Delete the program itself
        cursor.execute("DELETE FROM programs WHERE program_id = %s", (program_id,))
        
        conn.commit()
        rows_affected = cursor.rowcount
        return rows_affected > 0
    except psycopg2.Error as e:
        print("Error deleting program:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_program(program_id: int, new_program_name: str) -> bool:
    """
    Update the name of a program, given its program_id.
    Returns True if the program was updated, or False if the program_id does not exist
    or if there's a database error.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE programs
            SET program_name = %s
            WHERE program_id = %s
            """,
            (new_program_name, program_id)
        )
        if cursor.rowcount == 0:
            # rowcount == 0 means no rows were updated (invalid program_id)
            conn.rollback()
            return False

        conn.commit()
        return True
    except psycopg2.Error as e:
        print("Error updating program:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
