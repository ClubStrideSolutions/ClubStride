# instructors_db_postgres.py

import psycopg2
import psycopg2.extras
from psycopg2 import sql
import bcrypt

import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL is not set in .env")
    
def get_connection():
    """Create and return a new database connection."""
    print(psycopg2.connect(DB_URL))
    return psycopg2.connect(DB_URL)

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
            role TEXT NOT NULL,
            programs TEXT
        );
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def add_instructor(username: str, password: str, role: str, programs: str = "") -> bool:
    """Insert a new instructor row into the DB."""
    conn = get_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    try:
        cursor.execute(
            """
            INSERT INTO instructors (username, password_hash, role, programs)
            VALUES (%s, %s, %s, %s);
            """,
            (username, pw_hash, role, programs)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        # Catch any Postgres errors (like unique constraint violations).
        print("Error adding instructor:", e)
        return False
    finally:
        cursor.close()
        conn.close()

def list_instructors():
    """Return all instructors (excluding password hash)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT instructor_id, username, role, programs FROM instructors")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "instructor_id": r[0],
            "username": r[1],
            "role": r[2],
            "programs": r[3]
        })
    return results

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

def update_instructor_programs(instructor_id: int, new_programs: str):
    """Update an instructor's programs by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE instructors
        SET programs = %s
        WHERE instructor_id = %s
        """,
        (new_programs, instructor_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def authenticate_instructor(username: str, password: str):
    """
    Check if the given username/password match a row in instructors.
    If valid, return a dict { 'instructor_id': ..., 'role': ..., 'programs': ... }
    Otherwise return None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT instructor_id, password_hash, role, programs
        FROM instructors
        WHERE username = %s
        """,
        (username,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None  # No such user

    instructor_id, stored_hash, role, programs = row
    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return {
            "instructor_id": instructor_id,
            "role": role,
            "programs": programs
        }
    else:
        return None

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
    cursor.execute(
        "DELETE FROM instructors WHERE instructor_id = %s",
        (instructor_id,)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    cursor.close()
    conn.close()

    return rows_affected > 0

# create_instructors_table()