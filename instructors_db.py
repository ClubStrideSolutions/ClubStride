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

############################################
# INSTRUCTOR ↔ PROGRAMS RELATION
############################################
def assign_instructor_to_program(instructor_id: int, program_id: int) -> bool:
    """
    Insert a row into instructor_programs.
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
        conn.commit()
        # rowcount won't work for ON CONFLICT DO NOTHING to detect duplicates
        return True
    except psycopg2.Error as e:
        print("Error assigning instructor to program:", e)
        return False
    finally:
        cursor.close()
        conn.close()

def remove_instructor_from_program(instructor_id: int, program_id: int) -> bool:
    """
    Remove the row from instructor_programs.
    Returns True if a row was deleted, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM instructor_programs
        WHERE instructor_id = %s AND program_id = %s
        """,
        (instructor_id, program_id)
    )
    conn.commit()
    deleted = (cursor.rowcount > 0)
    cursor.close()
    conn.close()
    return deleted


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
