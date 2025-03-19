from students_db import connect_to_db

def remove_program_id_6():
    db = connect_to_db()
    coll = db["Student_Records"]
    result = coll.delete_many({"program_id": 6})
    print(f"Deleted {result.deleted_count} documents with program_id=6.")

if __name__ == "__main__":
    remove_program_id_6()
