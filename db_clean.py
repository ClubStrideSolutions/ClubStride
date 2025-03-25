from students_db import connect_to_db

def remove_program_id_6():
    db = connect_to_db()
    coll = db["Student_Records"]
    result = coll.delete_many({"program_id": 6})
    print(f"Deleted {result.deleted_count} documents with program_id=6.")

if __name__ == "__main__":
    remove_program_id_6()

# def page_manage_students():
    
#     if not st.session_state.get("instructor_logged_in", False) and not st.session_state.get("is_admin", False):
#         st.error("You must be logged in.")
#         return
    
#     col_left, col_center, col_right = st.columns([1, 5, 1])

#     with col_center:
#         st.header("Manage Students")

#         is_admin = st.session_state.get("is_admin", False)

#         # =========== NEW: Program Filter for Admin ===========
#         if is_admin:
#             all_programs = list_programs()  # from instructors_db
#             prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#             # Build a list of (program_id, "name") for the selectbox
#             program_choices = [(None, "All Programs")] + [
#                 (p["program_id"], p["program_name"]) for p in all_programs
#             ]
            
#             selected_prog_id = st.selectbox(
#                 "Select Program to View:",
#                 options=[pc[0] for pc in program_choices],
#                 format_func=lambda pid: "All Programs" if pid is None else prog_map[pid]
#             )

#             if selected_prog_id is None:
#                 # Admin sees all students
#                 students = get_all_students()
#             else:
#                 # Admin sees only students in the chosen program
#                 students = get_all_students(program_ids=[selected_prog_id])

#         else:
#             # Instructors see only assigned programs
#             permitted_ids = st.session_state.get("instructor_program_ids", [])
#             if not permitted_ids:
#                 st.warning("You have no assigned programs. Contact an admin for access.")
#                 return
#             students = get_all_students(program_ids=permitted_ids)

#         if not students:
#             st.info("No students in the database (for the selected program).")

#         # ---------------------------
#         # CURRENT STUDENTS
#         # ---------------------------
#         with st.expander("Current Students", expanded=True):
#             for s in students:
#                 student_id = s.get("student_id")
#                 name = s.get("name", "")
#                 phone = s.get("phone", "")
#                 contact_email = s.get("contact_email", "")
#                 prog_id = s.get("program_id", None)  # numeric program ID
#                 grade = s.get("grade", "")
#                 school = s.get("school", "")

#                 st.write(
#                     f"**Name:** {name}, **ID:** {student_id}, **Program ID:** {prog_id}, "
#                     f"**Phone:** {phone}, **Contact:** {contact_email}, "
#                     f"**Grade:** {grade}, **School:** {school}"
#                 )

#                 col_del, col_edit, col_today, col_past = st.columns(4)

#                 with col_del:
#                     if st.button(f"Delete (ID={student_id})", key=f"btn_delete_{student_id}"):
#                         # Instructors must only delete if the student's program_id is in permitted_ids
#                         if not is_admin:
#                             permitted_ids = st.session_state.get("instructor_program_ids", [])
#                             if prog_id not in permitted_ids:
#                                 st.error("You are not permitted to delete students in this program.")
#                                 st.stop()

#                         success = delete_student_record(student_id)
#                         if success:
#                             st.success(f"Deleted student {name} (ID={student_id}).")
#                             st.rerun()
#                         else:
#                             st.error("Delete failed or no such student.")

#                 with col_edit:
#                     # NEW: The Edit button
#                     if st.button(f"Edit (ID={student_id})", key=f"btn_edit_{student_id}"):
#                         # Put this student's info into session state
#                         st.session_state["editing_student"] = s
#                         st.rerun()

#                 with col_today:
#                     # Mark Attendance "today"
#                     if st.button(f"Mark Attendance", key=f"btn_attendance_{student_id}"):
#                         st.session_state["attendance_student"] = s  # store the entire student doc
#                         st.rerun()

#                 with col_past:
#                     # Mark Past Attendance
#                     if st.button(f"Mark Past", key=f"btn_attendance_past_{student_id}"):
#                         st.session_state["attendance_student"] = s
#                         st.session_state["attendance_mode"] = "past"
#                         st.rerun()

#             # ---------------------------
#             # INDIVIDUAL ATTENDANCE
#             # ---------------------------
#             if "attendance_student" in st.session_state:
#                 single_stud = st.session_state["attendance_student"]
#                 mode = st.session_state.get("attendance_mode", "today")

#                 if mode == "today":
#                     st.subheader(f"Mark Attendance (Today) for {single_stud['name']}")
                    
#                     # date_val = st.date_input("Date", value=date.today(), key="single_stud_date")
#                     # time_val = st.time_input("Time", value=time(9, 0), key="single_stud_time")
#                     # combined_dt = datetime.combine(date_val, time_val)
#                     current_dt = datetime.now()

#                     status_opt = ["Present", "Late", "Absent", "Excused"]
#                     chosen_status = st.selectbox("Status", options=status_opt, index=0, key="single_stud_status")
#                     comment_txt = st.text_input("Comment (Optional)", key="single_stud_comment")

#                     if st.button("Submit Attendance"):
#                         try:
#                             msg = record_student_attendance_in_array(
#                                 name=single_stud["name"],
#                                 program_id=single_stud["program_id"],
#                                 status=chosen_status,
#                                 comment=comment_txt,
#                                 attendance_date=current_dt
#                             )
#                             st.success(f"Marked {single_stud['name']} as {chosen_status}. {msg}")
#                         except Exception as e:
#                             st.error(f"Error: {e}")

#                         st.session_state.pop("attendance_student")
#                         st.session_state.pop("attendance_mode", None)
#                         st.rerun()

#                     if st.button("Cancel", key="single_attendance_cancel"):
#                         st.session_state.pop("attendance_student")
#                         st.session_state.pop("attendance_mode", None)
#                         st.info("Individual attendance marking canceled.")
#                         st.rerun()

#                 elif mode == "past":
#                     st.subheader(f"Mark Past Attendance for {single_stud['name']}")

#                     date_val = st.date_input("Session Date", value=date.today(), key="past_single_date")
#                     time_val = st.time_input("Session Time", value=time(9, 0), key="past_single_time")
#                     combined_dt = datetime.combine(date_val, time_val)

#                     status_opt = ["Present", "Late", "Absent", "Excused"]
#                     chosen_status = st.selectbox("Status", options=status_opt, index=0, key="past_single_status")
#                     comment_txt = st.text_input("Comment (Optional)", key="past_single_comment")

#                     if st.button("Submit Past Attendance", key="past_single_submit"):
#                         try:
#                             msg = record_student_attendance_in_array(
#                                 name=single_stud["name"],
#                                 program_id=single_stud["program_id"],
#                                 status=chosen_status,
#                                 comment=comment_txt,
#                                 attendance_date=combined_dt
#                             )
#                             st.success(f"Marked {single_stud['name']} as {chosen_status} on {combined_dt}. {msg}")
#                         except Exception as e:
#                             st.error(f"Error: {e}")

#                         st.session_state.pop("attendance_student")
#                         st.session_state.pop("attendance_mode", None)
#                         st.rerun()

#                     if st.button("Cancel Past", key="past_single_cancel"):
#                         st.session_state.pop("attendance_student")
#                         st.session_state.pop("attendance_mode", None)
#                         st.info("Past attendance marking canceled.")
#                         st.rerun()

#         # ---------------------------
#         # EDIT STUDENT WORKFLOW
#         # ---------------------------
#         if "editing_student" in st.session_state:
#             edited_stud = st.session_state["editing_student"]
#             st.subheader(f"Edit Student: {edited_stud.get('name', '')} (ID={edited_stud.get('student_id', '')})")

#             # Guard against editing a student in a program that the instructor doesn't have
#             if not is_admin:
#                 permitted_ids = st.session_state.get("instructor_program_ids", [])
#                 if edited_stud.get("program_id") not in permitted_ids:
#                     st.error("You do not have permission to edit students in this program.")
#                     if st.button("OK"):
#                         st.session_state.pop("editing_student")
#                         st.rerun()
#                 # else we let them continue

#             with st.form("edit_student_form"):
#                 new_name = st.text_input("Name", value=edited_stud.get("name", ""))
#                 new_phone = st.text_input("Phone", value=edited_stud.get("phone", ""))
#                 new_email = st.text_input("Contact Email", value=edited_stud.get("contact_email", ""))
#                 new_grade = st.text_input("Grade", value=edited_stud.get("grade", ""))
#                 new_school = st.text_input("School", value=edited_stud.get("school", ""))

#                 # If admin, let them pick a new program
#                 if is_admin:
#                     all_programs = list_programs()
#                     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#                     prog_ids = list(prog_map.keys())

#                     # Find current program's index in the list, if present
#                     current_pid = edited_stud.get("program_id")
#                     if current_pid not in prog_ids:
#                         prog_index = 0
#                     else:
#                         prog_index = prog_ids.index(current_pid)

#                     selected_id = st.selectbox(
#                         "Select Program:",
#                         options=prog_ids,
#                         format_func=lambda pid: f"{pid} - {prog_map[pid]}",
#                         index=prog_index
#                     )
#                     new_program_id = selected_id
#                 else:
#                     # If instructor, we show them only their permitted IDs
#                     permitted_ids = st.session_state.get("instructor_program_ids", [])
#                     current_pid = edited_stud.get("program_id")
#                     if current_pid not in permitted_ids and permitted_ids:
#                         # default to the first permitted if there's a mismatch
#                         current_pid = permitted_ids[0]
#                     new_program_id = st.selectbox(
#                         "Select Program ID:",
#                         options=permitted_ids,
#                         index=permitted_ids.index(current_pid) if current_pid in permitted_ids else 0
#                     )

#                 submitted = st.form_submit_button("Save Changes")
#                 if submitted:
#                     try:
#                         # You must implement this update function in your DB code
#                         msg = update_student_info(
#                             student_id=edited_stud["student_id"],
#                             name=new_name,
#                             phone=new_phone,
#                             contact_email=new_email,
#                             program_id=new_program_id,
#                             grade=new_grade,
#                             school=new_school
#                         )
#                         st.success(f"{msg}")
#                         st.session_state.pop("editing_student")
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"Error updating student: {e}")

#             if st.button("Cancel Edit"):
#                 st.session_state.pop("editing_student")
#                 st.rerun()

#         # ---------------------------
#         # ADD OR UPDATE STUDENTS (NEW)
#         # ---------------------------
#         with st.expander("Add or Update Students", expanded=True):
#             action = st.radio(
#                 "Choose method:",
#                 ["Single Student Entry", "Bulk CSV Upload"],
#                 horizontal=True
#             )

#             # SINGLE STUDENT ENTRY
#             if action == "Single Student Entry":
#                 with st.form("student_form"):
#                     name_val = st.text_input("Name *", "")
#                     phone_val = st.text_input("Phone", "")
#                     contact_val = st.text_input("Contact Email", "")
#                     grade_val = st.text_input("Grade", "")
#                     school_val  = st.text_input("School", "")

#                     if is_admin:
#                         all_programs = list_programs()
#                         if not all_programs:
#                             st.warning("No programs found in Postgres.")
#                             st.stop()

#                         prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#                         selected_id = st.selectbox(
#                             "Select Program:",
#                             options=prog_map.keys(),
#                             format_func=lambda pid: f"{pid} - {prog_map[pid]}"
#                         )
#                         prog_val = selected_id

#                     else:
#                         permitted_ids = st.session_state.get("instructor_program_ids", [])
#                         if not permitted_ids:
#                             st.warning("No assigned programs available.")
#                             prog_val = None
#                         else:
#                             prog_val = st.selectbox(
#                                 "Select Program ID:",
#                                 options=permitted_ids,
#                                 format_func=lambda pid: f"Program ID: {pid}"
#                             )

#                     submitted = st.form_submit_button("Save Student Info")
#                     if submitted:
#                         if not name_val.strip():
#                             st.error("Name is required.")
#                         elif prog_val is None:
#                             st.error("No valid program selected.")
#                         else:
#                             result = store_student_record(
#                                 name_val, phone_val, contact_val, prog_val,
#                                 grade=grade_val, school=school_val
#                             )
#                             st.success(result)
#                             st.rerun()

#             # BULK CSV UPLOAD
#             else:
#                 if is_admin:
#                     all_programs = list_programs()
#                     if not all_programs:
#                         st.warning("No programs found in Postgres.")
#                         st.stop()

#                     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=prog_map.keys(),
#                         format_func=lambda pid: f"{pid} - {prog_map[pid]}"
#                     )
#                 else:
#                     permitted_ids = st.session_state.get("instructor_program_ids", [])
#                     if not permitted_ids:
#                         st.warning("No assigned programs available.")
#                         st.stop()
#                     selected_prog_id = st.selectbox(
#                         "Select Program ID for CSV Rows:",
#                         options=permitted_ids,
#                         format_func=lambda pid: f"Program ID: {pid}"
#                     )

#                 uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])
#                 if uploaded_file:
#                     df = pd.read_csv(uploaded_file)
#                     st.write("Preview of data:", df.head())

#                     required_cols = {
#                         "First Name", "Last Name", "Number", "Email", "Grade", "School"
#                     }
#                     if not required_cols.issubset(df.columns):
#                         st.error(f"CSV must have columns: {required_cols}")
#                     else:
#                         if st.button("Process CSV"):
#                             successes = 0
#                             failures = 0
#                             for idx, row in df.iterrows():
#                                 first_name = str(row["First Name"]).strip()
#                                 last_name = str(row["Last Name"]).strip()
#                                 name_val = f"{first_name} {last_name}".strip()

#                                 phone_val = row["Number"]
#                                 contact_val = row["Email"]
#                                 grade_val = row["Grade"]
#                                 school_val = row["School"]

#                                 if not is_admin:
#                                     permitted_ids = st.session_state.get("instructor_program_ids", [])
#                                     if selected_prog_id not in permitted_ids:
#                                         st.warning(f"Row {idx}: Program ID '{selected_prog_id}' is not in your assigned list.")
#                                         failures += 1
#                                         continue

#                                 result_msg = store_student_record(
#                                     name_val, phone_val, contact_val,
#                                     selected_prog_id, grade_val, school_val
#                                 )
#                                 if "New student record" in result_msg or "updated" in result_msg:
#                                     successes += 1
#                                 else:
#                                     failures += 1

#                             st.success(f"Bulk upload complete. Successes: {successes}, Failures: {failures}")
#                             st.rerun()

# def page_take_attendance():
#     st.subheader("Take Attendance")
#     attendance_mode = st.radio(
#         "Choose attendance mode:",
#         ["Take Attendance (Today)", "Record Past Session"], horizontal=True
#     )
#     is_admin = st.session_state.get("is_admin", False)
    
#     all_programs = list_programs()
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#      # =========== NEW: Admin Program Filter ===========
#     if is_admin:

#         program_choices = [(None, "All Programs")] + [(p["program_id"], p["program_name"]) for p in all_programs]
#         selected_prog_id = st.selectbox(
#             "Select Program:",
#             options=[pc[0] for pc in program_choices],
#             format_func=lambda pid: "All Programs" if pid is None else prog_map[pid]
#         )

#         if selected_prog_id is None:
#             # Admin sees *all* students
#             students = get_all_students()
#         else:
#             # Admin sees only students in one chosen program
#             students = get_all_students(program_ids=[selected_prog_id])
#     else:
#         permitted_ids = st.session_state.get("instructor_program_ids", [])
#         if not permitted_ids:
#             st.info("No assigned programs found. Contact an admin for access.")
#             return
#         students = get_all_students(program_ids=permitted_ids)
#     if not students:
#         st.info("No students found. (Check whether you have assigned programs or student data.)")
#         return

#     if attendance_mode == "Take Attendance (Today)":
#         st.subheader("Today’s Attendance")
#         # 4) Build an attendance form
#         with st.form("attendance_form"):
#             attendance_dict = {}
#             for s in students:
#                 sid = s.get("student_id")
#                 name = s.get("name", "")
#                 pid = s.get("program_id", 0)   # numeric program_id from Mongo

#                 # Look up program name from our dictionary (fallback if not found)
#                 prog_name = prog_map.get(pid, f"Program ID={pid}")

#                 st.subheader(f"{name} – Program: {prog_name}")
#                 status = st.selectbox(
#                     "Status",
#                     options=["Present", "Late", "Absent"],
#                     key=f"{sid}_status"
#                 )
#                 comment = st.text_input("Comment (Optional)", key=f"{sid}_comment")

#                 attendance_dict[sid] = {
#                     "name": name,
#                     "program_id": pid,   # store numeric ID so we can record attendance
#                     "status": status,
#                     "comment": comment
#                 }

#             submitted = st.form_submit_button("Submit Attendance")

#         # 5) Process form submissions
#         if submitted:
#             for sid, data in attendance_dict.items():
#                 name = data["name"]
#                 prog_id = data["program_id"]
#                 status = data["status"]
#                 comment = data["comment"]

#                 try:
#                     # record_student_attendance_in_array expects (name, program_id, status, comment)
#                     result_msg = record_student_attendance_in_array(name, prog_id, status, comment)
#                     st.write(f"{name} – Marked {status}: {result_msg}")
#                 except Exception as e:
#                     st.error(f"Error for {name}: {e}")

#             st.success("All attendance data submitted!")

#     else:
#         st.subheader("Record Past Session")
#         # 2) Let the user pick the date/time of this past session
#         session_date = st.date_input("Session Date", value=date(2025, 1, 7))
#         session_time = st.time_input("Session Start Time", value=time(9, 0))
#         session_time_past = _format_time_12h(session_time)
#         st.write(f"**Date/Time**: {session_date} → {session_time_past}")

#         # Combine them into a single datetime
#         chosen_datetime = datetime.combine(session_date, session_time)

#         # 3) (Optional) "Mark All Present" button for the PAST session
#         if "past_defaults" not in st.session_state:
#             st.session_state["past_defaults"] = {}

#         if st.button("Mark All Present for Past Session"):
#             for s in students:
#                 sid = s.get("student_id")
#                 st.session_state["past_defaults"][sid] = "Present"
#             st.rerun()

#         # 4) Build the manual form for final attendance
#         with st.form("past_attendance_form"):
#             past_attendance = {}
#             for s in students:
#                 sid = s.get("student_id")
#                 student_name = s.get("name", "")
#                 prog_id = s.get("program_id", 0)
#                 program_name = prog_map.get(prog_id, f"ProgID={prog_id}")

#                 # Default to “Present” if Mark All Present was pressed
#                 default_status = st.session_state["past_defaults"].get(sid, "Absent")

#                 st.write(f"**{student_name}** (Program: {program_name})")
#                 status_choice = st.selectbox(
#                     "Status",
#                     ["Present", "Late", "Absent", "Excused"],
#                     index=["Present", "Late", "Absent", "Excused"].index(default_status),
#                     key=f"past_status_{sid}"
#                 )
#                 comment_val = st.text_input("Comment (Optional)", key=f"past_comment_{sid}")

#                 past_attendance[sid] = {
#                     "name": student_name,
#                     "program_id": prog_id,
#                     "status": status_choice,
#                     "comment": comment_val
#                 }

#             # 5) Submit button
#             submitted = st.form_submit_button("Submit Past Attendance")
        
#         # 6) Process submissions
#         if submitted:
#             for sid, data in past_attendance.items():
#                 record_student_attendance_in_array(
#                     name=data["name"],
#                     program_id=data["program_id"],
#                     status=data["status"],
#                     comment=data["comment"],
#                     attendance_date=chosen_datetime  # <— THIS is key
#                 )
#             st.success(f"Past attendance recorded for session on {chosen_datetime}!")
#             # Clear any defaults
#             st.session_state["past_defaults"] = {}


# def show_attendance_logs():
#     # 1) If not cached, fetch raw attendance docs from Mongo.
#     # if st.session_state["attendance_records"] is None:
#     if "attendance_records" not in st.session_state or st.session_state["attendance_records"] is None:
#         try:
#             # Each record looks like:
#             # {"student_id":..., "name":..., "program_id":..., "attendance":{ "date":..., "status":..., "comment":... }}
#             records = get_all_attendance_subdocs()
#             st.session_state["attendance_records"] = records


#         except Exception as e:
#             st.error(f"Error: {e}")
#             st.session_state["attendance_records"] = []
#             return
        
#     logs = st.session_state["attendance_records"]
#     if not logs:
#         st.info("No attendance records found.")
#         return
#             # is_admin = st.session_state.get("is_admin", False)
#             # if is_admin:
#                 # 1) Build a dropdown to select program or "All"
#     all_programs = list_programs()  # from instructors_db
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#     is_admin = st.session_state.get("is_admin", False)
#     if is_admin:
#         # Option structure: [(None, "All Programs"), (101, "STEM"), ...]
#         program_choices = [(None, "All Programs")] + [
#             (p["program_id"], p["program_name"]) for p in all_programs
#         ]

#         selected_prog_id = st.selectbox(
#             "Filter Attendance by Program",
#             options=[pc[0] for pc in program_choices],  # just the IDs (None or int)
#             format_func=lambda pid: "All Programs" if pid is None else prog_map[pid],
#             key="daily_logs_program_select"
#         )

#         if selected_prog_id is not None:
#             logs = [r for r in logs if (r["program_id"] == selected_prog_id or selected_prog_id is None)]

#             # If user chooses a specific program, filter records
#             # records = [r for r in records if r.get("program_id") == selected_prog_id]

#     else:
#                 # 2) Instructor filtering by assigned program(s)
#         permitted_ids = st.session_state.get("instructor_program_ids", [])
#         logs = [r for r in logs if r.get("program_id") in permitted_ids]

#     for r in logs:
#         pid = r.get("program_id", 0)
#         r["program_name"] = prog_map.get(pid, f"Program ID={pid}")

#       # 5) Next filter by Name
#     if logs:
#         # Gather unique names from the filtered logs
#         all_names = sorted({doc.get("name", "Unknown") for doc in logs})
#         name_choice = st.selectbox(
#             label="Filter by Student Name",
#             options=["All Students"] + all_names,
#             key="daily_logs_name_select"
#         )

#         if name_choice != "All Students":
#             logs = [doc for doc in logs if doc.get("name") == name_choice]
#     else:
#         st.info("No attendance records after program filtering.")
#         return

#     if not logs:
#         st.info("No attendance records found.")
#         return

#     global_idx = 0

#     for doc in logs:
#         att = doc.get("attendance", {})
#         date_val = att.get("date", "")
#         status_val = att.get("status", "")
#         comment_val = att.get("comment", "")
#         s_name = doc.get("name", "")
#         p_name = doc.get("program_name", "?")
#         student_id = doc.get("student_id", "?")

#         st.markdown(
#             f"**Name:** {s_name} | **Program:** {p_name} | **Date:** {date_val} "
#             f"| **Status:** {status_val} | **Comment:** {comment_val}"
#         )

#         colB, colC = st.columns([1, 1])

#         # DELETE button
#         with colB:
#             if st.button(f"Delete (Row {global_idx})", key=f"delete_{global_idx}"):
#                 deleted = delete_attendance_subdoc(student_id, date_val)
#                 if deleted:
#                     st.success("Attendance record deleted.")
#                     st.session_state["attendance_records"] = None
#                 else:
#                     st.warning("No matching record found.")
#                 st.rerun()

#         # UPSERT button
#         with colC:
#             if st.button(f"Upsert (Row {global_idx})", key=f"upsert_{global_idx}"):
#                 # We store old info in case we want to adjust date or fields
#                 st.session_state["upsert_data"] = {
#                     "student_id": student_id,
#                     "student_name": s_name,  # Let's store the name
#                     "old_date": date_val,
#                     "old_status": status_val,
#                     "old_comment": comment_val
#                 }
#                 st.rerun()

#         st.write("---")
#         global_idx += 1  # increment so each record has a unique key

#     # 4) If user clicked "Upsert", show the minimal upsert form
#     if "upsert_data" in st.session_state:
#         record = st.session_state["upsert_data"]
#         st.subheader("Upsert Attendance Record (Create or Update)")

#         default_dt = record["old_date"]
#         if isinstance(default_dt, str):
#             default_dt = parser.parse(default_dt)

#         with st.form("upsert_form"):
#             st.write(f"**Student Name**: {record['student_name']}")
#             st.write(f"**Student ID**: {record['student_id']}")
#             st.write(f"**Existing Date**: {record['old_date']}")

#             # Let user pick a new or same date/time
#             new_date = st.date_input("Date", value=default_dt.date())
#             new_time = st.time_input("Time", value=default_dt.time() if default_dt.time() else time(9, 0))
#             combined_dt = datetime.combine(new_date, new_time)

#             status_options = ["Present", "Late", "Absent", "Excused"]
#             old_status = record["old_status"]
#             try:
#                 status_index = status_options.index(old_status)
#             except ValueError:
#                 status_index = 0

#             final_status = st.selectbox("Status", status_options, index=status_index)
#             final_comment = st.text_input("Comment", value=record["old_comment"])

#             submitted_upsert = st.form_submit_button("Upsert Attendance")
#             if submitted_upsert:
#                 success = upsert_attendance_subdoc(
#                     student_id=record["student_id"],
#                     target_date=combined_dt,
#                     new_status=final_status,
#                     new_comment=final_comment
#                 )
#                 if success:
#                     st.success(f"Attendance upserted (Date={combined_dt}).")
#                     # If date changed, optionally delete old record
#                     if combined_dt != parser.parse(str(record["old_date"])):
#                         delete_attendance_subdoc(record["student_id"], record["old_date"])
#                     st.session_state["attendance_records"] = None
#                 else:
#                     st.warning("No changes made or upsert failed.")

#                 st.session_state.pop("upsert_data")
#                 st.rerun()

#         if st.button("Cancel Upsert"):
#             st.session_state.pop("upsert_data")
#             st.info("Upsert cancelled.")
#             st.rerun()


# def show_attendance_logs():
#     # ---------------------------------------------------------
#     # 1) Load attendance records from session cache or DB
#     # ---------------------------------------------------------
#     if "attendance_records" not in st.session_state or st.session_state["attendance_records"] is None:
#         try:
#             # Each record is like:
#             # {"student_id":..., "name":..., "program_id":..., 
#             #  "attendance":{"date":..., "status":..., "comment":...}}
#             records = get_all_attendance_subdocs()
#             st.session_state["attendance_records"] = records
#         except Exception as e:
#             st.error(f"Error fetching attendance logs: {e}")
#             st.session_state["attendance_records"] = []
#             return

#     logs = st.session_state["attendance_records"]
#     if not logs:
#         st.info("No attendance records found.")
#         return

#     # ---------------------------------------------------------
#     # 2) Admin or Instructor program filtering
#     # ---------------------------------------------------------
#     all_programs = list_programs()  # from instructors_db
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#     is_admin = st.session_state.get("is_admin", False)

#     if is_admin:
#         # Admin sees a program filter
#         program_choices = [(None, "All Programs")] + [
#             (p["program_id"], p["program_name"]) for p in all_programs
#         ]
#         selected_prog_id = st.selectbox(
#             "Filter by Program (Admin)",
#             options=[pc[0] for pc in program_choices],
#             format_func=lambda pid: "All Programs" if pid is None else prog_map[pid],
#         )
#         if selected_prog_id is not None:
#             logs = [
#                 r for r in logs
#                 if (r["program_id"] == selected_prog_id or selected_prog_id is None)
#             ]
#     else:
#         # Instructor sees only assigned programs
#         permitted_ids = st.session_state.get("instructor_program_ids", [])
#         logs = [r for r in logs if r.get("program_id") in permitted_ids]

#     if not logs:
#         st.info("No attendance records after program filtering.")
#         return

#     # ---------------------------------------------------------
#     # 3) Filter by Student Name
#     # ---------------------------------------------------------
#     all_names = sorted({doc.get("name", "Unknown") for doc in logs})
#     name_choice = st.selectbox(
#         "Filter by Student Name",
#         options=["All Students"] + all_names
#     )
#     if name_choice != "All Students":
#         logs = [doc for doc in logs if doc.get("name") == name_choice]

#     if not logs:
#         st.info("No attendance records found for that filter.")
#         return

#     # ---------------------------------------------------------
#     # 4) Display each record in an expander with color-coded/emoji status
#     # ---------------------------------------------------------
#     # We'll map "Present" -> "✅ Present", "Late" -> "🕑 Late", etc.
#     emoji_map = {
#         "Present": "✅ Present",
#         "Late": "🕑 Late",
#         "Absent": "🚫 Absent",
#         "Excused": "🤝 Excused"
#     }

#     for idx, doc in enumerate(logs):
#         att = doc.get("attendance", {})
#         date_val = att.get("date", "")
#         status_val = att.get("status", "")
#         comment_val = att.get("comment", "")
#         s_name = doc.get("name", "")
#         p_id = doc.get("program_id", 0)
#         student_id = doc.get("student_id", "?")

#         program_name = prog_map.get(p_id, f"Program ID={p_id}")
#         # Convert status to emoji label if recognized
#         display_status = emoji_map.get(status_val, status_val)

#         # Build a short label for the expander
#         expander_label = f"{s_name} | {program_name} | {date_val} | {display_status}"

#         with st.expander(expander_label, expanded=False):
#             st.write(f"**Student ID:** {student_id}")
#             st.write(f"**Date:** {date_val}")
#             st.write(f"**Status:** {display_status}")
#             if comment_val:
#                 st.write(f"**Comment:** {comment_val}")

#             # ~~~ Buttons for Delete / Edit (Upsert) ~~~
#             colDel, colEdit = st.columns([1, 1])

#             with colDel:
#                 if st.button("Delete", key=f"delete_btn_{idx}"):
#                     # Attempt to delete the record
#                     deleted = delete_attendance_subdoc(student_id, date_val)
#                     if deleted:
#                         st.success("Attendance record deleted.")
#                         # Force re-fetch logs next time
#                         st.session_state["attendance_records"] = None
#                     else:
#                         st.warning("No matching record found.")
#                     st.rerun()

#             with colEdit:
#                 if st.button("Edit", key=f"edit_btn_{idx}"):
#                     # We'll store old info in session so we can upsert in place
#                     st.session_state["upsert_data"] = {
#                         "student_id": student_id,
#                         "student_name": s_name,
#                         "old_date": date_val,
#                         "old_status": status_val,
#                         "old_comment": comment_val
#                     }
#                     record = st.session_state["upsert_data"]
#                     st.subheader("Edit / Upsert Attendance Record")

#                     default_dt = record["old_date"]
#                     if isinstance(default_dt, str):
#                         default_dt = parser.parse(default_dt)

#                     with st.form("upsert_form"):
#                         st.write(f"**Student Name**: {record['student_name']}")
#                         st.write(f"**Student ID**: {record['student_id']}")
#                         st.write(f"**Original Date**: {record['old_date']}")

#                         new_date = st.date_input("New Date", value=default_dt.date())
#                         new_time = st.time_input("New Time", value=default_dt.time() or time(9,0))
#                         combined_dt = datetime.combine(new_date, new_time)

#                         status_opts = ["Present", "Late", "Absent", "Excused"]
#                         try:
#                             default_idx = status_opts.index(record["old_status"])
#                         except ValueError:
#                             default_idx = 0

#                         new_status = st.selectbox("Status", status_opts, index=default_idx)
#                         new_comment = st.text_input("Comment", value=record["old_comment"])

#                         upsert_submitted = st.form_submit_button("Save Changes")
#                         if upsert_submitted:
#                             success = upsert_attendance_subdoc(
#                                 student_id=record["student_id"],
#                                 target_date=combined_dt,
#                                 new_status=new_status,
#                                 new_comment=new_comment
#                             )
#                             if success:
#                                 st.success(f"Attendance upserted (Date={combined_dt}).")
#                                 # If the date changed, optionally remove the old record
#                                 if combined_dt != parser.parse(str(record["old_date"])):
#                                     delete_attendance_subdoc(record["student_id"], record["old_date"])
#                                 # Force re-fetch logs next time
#                                 st.session_state["attendance_records"] = None
#                             else:
#                                 st.warning("No changes made or upsert failed.")

#                             # Clear upsert state
#                             st.session_state.pop("upsert_data")
#                             st.rerun()

#                     if st.button("Cancel Edit"):
#                         st.session_state.pop("upsert_data")
#                         st.info("Edit canceled.")
#                         st.rerun()
#                     # st.rerun()

 # ---------------------------------------------------------
    # 5) If user clicked "Edit," show the minimal upsert form
    # ---------------------------------------------------------
    # if "upsert_data" in st.session_state:
        # record = st.session_state["upsert_data"]
        # st.subheader("Edit / Upsert Attendance Record")

        # default_dt = record["old_date"]
        # if isinstance(default_dt, str):
        #     default_dt = parser.parse(default_dt)

        # with st.form("upsert_form"):
        #     st.write(f"**Student Name**: {record['student_name']}")
        #     st.write(f"**Student ID**: {record['student_id']}")
        #     st.write(f"**Original Date**: {record['old_date']}")

        #     new_date = st.date_input("New Date", value=default_dt.date())
        #     new_time = st.time_input("New Time", value=default_dt.time() or time(9,0))
        #     combined_dt = datetime.combine(new_date, new_time)

        #     status_opts = ["Present", "Late", "Absent", "Excused"]
        #     try:
        #         default_idx = status_opts.index(record["old_status"])
        #     except ValueError:
        #         default_idx = 0

        #     new_status = st.selectbox("Status", status_opts, index=default_idx)
        #     new_comment = st.text_input("Comment", value=record["old_comment"])

        #     upsert_submitted = st.form_submit_button("Save Changes")
        #     if upsert_submitted:
        #         success = upsert_attendance_subdoc(
        #             student_id=record["student_id"],
        #             target_date=combined_dt,
        #             new_status=new_status,
        #             new_comment=new_comment
        #         )
        #         if success:
        #             st.success(f"Attendance upserted (Date={combined_dt}).")
        #             # If the date changed, optionally remove the old record
        #             if combined_dt != parser.parse(str(record["old_date"])):
        #                 delete_attendance_subdoc(record["student_id"], record["old_date"])
        #             # Force re-fetch logs next time
        #             st.session_state["attendance_records"] = None
        #         else:
        #             st.warning("No changes made or upsert failed.")

        #         # Clear upsert state
        #         st.session_state.pop("upsert_data")
        #         st.rerun()

        # if st.button("Cancel Edit"):
        #     st.session_state.pop("upsert_data")
        #     st.info("Edit canceled.")
        #     st.rerun()

# def page_review_attendance():
#     st.header("Review Attendance Logs")

#     ############################################
#     # A) Show st.metric for "This Week" vs. "Last Week"
#     ############################################
#     now = datetime.utcnow()
#     seven_days_ago = now - timedelta(days=7)
#     fourteen_days_ago = now - timedelta(days=14)

#     # 1) "This Week" = last 7 days
#     subdocs_this_week = get_attendance_subdocs_in_range(seven_days_ago, now)
#     total_this_week = len(subdocs_this_week)

#     # 2) "Last Week" = from 14 days ago until 7 days ago
#     subdocs_last_week = get_attendance_subdocs_in_range(fourteen_days_ago, seven_days_ago)
#     total_last_week = len(subdocs_last_week)

#     attendance_delta = total_this_week - total_last_week

#     # --- Only fetch students in permitted programs (if instructor) ---
#     is_admin = st.session_state.get("is_admin", False)
#     if is_admin:
#         all_students = get_all_students()  # returns ALL students
#     else:
#         # gather instructor_program_ids from session
#         program_ids = st.session_state.get("instructor_program_ids", [])
#         # fetch only those students in the instructor’s assigned programs
#         all_students = get_all_students(program_ids=program_ids)

#     # all_students = get_all_students()
#     total_students = len(all_students)

#     # Use our new function to get last week's count from ObjectId logic
#     last_week_count = get_student_count_as_of_last_week()

#     # Calculate the difference
#     student_delta = total_students - last_week_count


#     col1, col2, col3= st.columns(3)
#     with col1:
#         st.metric(
#             label="Attendance This Week",
#             value=total_this_week,
#             delta=f"{attendance_delta} compared to previous week"
#         )

#     # Add a second metric if you want, e.g. "Absent This Week" vs. "Absent Last Week"
#     # We'll count how many in subdocs_this_week have status == "Absent"
#     absent_this_week = sum(1 for r in subdocs_this_week if r["attendance"]["status"] == "Absent")
#     absent_last_week = sum(1 for r in subdocs_last_week if r["attendance"]["status"] == "Absent")
#     delta_absent = absent_this_week - absent_last_week
#     with col2:
#         st.metric(
#             label="Absences This Week",
#             value=absent_this_week,
#             delta=f"{delta_absent} from last week"
#         )

#     with col3:
#         st.metric(
#             label="Total Students",
#             value=total_students,
#             delta=f"{student_delta} from last week"
#         )


#     st.write("---")  # visual separator

#     ############################################
#     # B) Original Buttons: Load All, Missed, etc.
#     ############################################
#     if "review_mode" not in st.session_state:
#         st.session_state["review_mode"] = "none"

#     # Prepare containers for logs & missed counts if not present
#     if "attendance_records" not in st.session_state:
#         st.session_state["attendance_records"] = None
#     if "missed_counts" not in st.session_state:
#         st.session_state["missed_counts"] = None

#     # Show two or three buttons
#     colA, colB = st.columns(2)
#     if colA.button("Load All Attendance"):
#         st.session_state["review_mode"] = "attendance"
#         st.session_state["attendance_records"] = None
#         st.session_state["missed_counts"] = None
#     if colB.button("Load Missed Counts"):
#         st.session_state["review_mode"] = "missed"
#         st.session_state["attendance_records"] = None
#         st.session_state["missed_counts"] = None

#     # Display whichever mode is selected
#     if st.session_state["review_mode"] == "attendance":
#         show_attendance_logs()  # your existing function
#     elif st.session_state["review_mode"] == "missed":
#         show_missed_counts()    # your existing function
#     else:
#         st.info("Choose an option to display data.")
        

# def page_manage_schedules():
#     """
#     Page for an instructor (or admin) to create, view, edit, and delete schedules.
#     Now includes logic so that instructors can only edit/delete schedules
#     they themselves created, unless they are admins.
#     """

#     # 1) Check login
#     instructor_id = st.session_state.get("instructor_id", None)
#     is_admin = st.session_state.get("is_admin", False)
#     if not instructor_id and not is_admin:
#         st.error("You must be logged in as an instructor or admin to manage schedules.")
#         return

#     # 2) Build a program map from Postgres
#     all_programs = list_programs()
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#     # 3) Determine which program IDs this user can manage
#     if is_admin:
#         # Admin sees schedules for all existing programs
#         program_id_options = list(prog_map.keys())
#     else:
#         program_id_options = st.session_state.get("instructor_program_ids", [])
#         if not program_id_options:
#             st.warning("You have no assigned programs. Contact an admin for access.")
#             return

#     st.header("Manage Class Schedules")

#     # ------------------------------------------------------------------------------
#     # A) Create a New Schedule
#     # ------------------------------------------------------------------------------
#     with st.expander("Create a New Schedule", expanded=True):
#         # Ensure we can pick a program to attach this schedule to
#         if program_id_options:
#             selected_prog_id = st.selectbox(
#                 "Select Program",
#                 options=program_id_options,
#                 format_func=lambda pid: prog_map.get(pid, f"Unknown (ID={pid})"),
#                 key="select_program_for_new_schedule"
#             )
#         else:
#             st.warning("No assigned programs available.")
#             return

#         # Basic schedule fields
#         title = st.text_input("Class Title", "", key="new_schedule_title")
#         notes = st.text_area("Additional Notes/Description", key="new_schedule_notes")

#         recurrence = st.selectbox(
#             "Recurrence",
#             ["None", "Weekly", "Monthly"],
#             help="Choose 'None' for a one-time class, or 'Weekly/Monthly' for recurring classes.",
#             key="new_schedule_recurrence"
#         )

#         location = ""
#         days_times = []
#         start_dt = None
#         end_dt = None

#         # ------------------------------------------------------------------------
#         # If "None": single date/time. Else: multiple days in a repeating pattern
#         # ------------------------------------------------------------------------
#         if recurrence == "None":
#             chosen_date = st.date_input("Class Date", value=date.today(), key="new_schedule_date")

#             col_start, col_end = st.columns(2)
#             with col_start:
#                 start_t = st.time_input("Start Time", value=time(9, 0), key="new_schedule_start_time")
#                 st.write(f"Selected Start: **{start_t.strftime('%I:%M %p')}**")

#             with col_end:
#                 end_t = st.time_input("End Time", value=time(10, 0), key="new_schedule_end_time")
#                 st.write(f"Ends at: **{end_t.strftime('%I:%M %p').lstrip('0')}**")

#             location = st.text_input("Location (Zoom or Physical Room)", key="new_schedule_location")

#         else:
#             # Weekly or Monthly
#             st.write("Select multiple days, each with its own time and location.")
#             selected_days = st.multiselect(
#                 "Days of Week",
#                 ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
#                 key="new_schedule_selected_days"
#             )
#             for d in selected_days:
#                 st.write(f"**Times/Location for {d}**")
#                 col1, col2 = st.columns(2)

#                 start_for_day = col1.time_input(
#                     f"{d} Start",
#                     value=time(9, 0),
#                     key=f"{d}_start_time"
#                 )
#                 col1.write(f"Starts at: **{start_for_day.strftime('%I:%M %p').lstrip('0')}**")

#                 end_for_day = col2.time_input(
#                     f"{d} End",
#                     value=time(10, 0),
#                     key=f"{d}_end_time"
#                 )
#                 col2.write(f"Ends at: **{end_for_day.strftime('%I:%M %p').lstrip('0')}**")

#                 loc_for_day = st.text_input(
#                     f"{d}_loc",
#                     "",
#                     key=f"{d}_loc"
#                 )

#                 days_times.append({
#                     "day": d,
#                     "start_time": str(start_for_day),
#                     "end_time": str(end_for_day),
#                     "location": loc_for_day
#                 })

#         # ------------------------------------------------------------------------
#         # "Create Schedule" button
#         # ------------------------------------------------------------------------
#         if st.button("Create Schedule", key="btn_create_schedule"):
#             if recurrence == "None":
#                 start_dt = datetime.combine(chosen_date, start_t)
#                 end_dt = datetime.combine(chosen_date, end_t)
#                 doc = {
#                     "instructor_id": instructor_id,
#                     "program_id": selected_prog_id,
#                     "title": title,
#                     "recurrence": "None",
#                     "notes": notes,
#                     "start_datetime": start_dt,
#                     "end_datetime": end_dt,
#                     "days_times": [],
#                     "location": location,
#                     "created_by_username": st.session_state.get("instructor_username", "Admin"),
#                     "created_at": datetime.utcnow()
#                 }
#             else:
#                 doc = {
#                     "instructor_id": instructor_id,
#                     "program_id": selected_prog_id,
#                     "title": title,
#                     "recurrence": recurrence,
#                     "notes": notes,
#                     "days_times": days_times,
#                     "start_datetime": None,
#                     "end_datetime": None,
#                     "created_by_username": st.session_state.get("instructor_username", "Admin"),
#                     "created_at": datetime.utcnow()
#                 }

#             new_id = create_schedule(doc)
#             st.success(f"Created schedule with ID: {new_id}")

#             # Optionally send email notifications
#             notify_schedule_change(selected_prog_id, doc, event_type="created")
#             st.rerun()

#     # ------------------------------------------------------------------------------
#     # B) Show Existing Schedules
#     # ------------------------------------------------------------------------------
#     st.subheader("Existing Schedules")

#     # Instead of filtering by instructor_id, we retrieve schedules by the user’s permitted programs
#     schedules_for_programs = list_schedules_by_program(program_id_options)
#     # If you also want admin to see everything, note that admin’s program_id_options = all

#     if not schedules_for_programs:
#         st.info("No schedules found for your assigned programs.")
#         return

#     # Render each schedule
#     for sch in schedules_for_programs:
#         sid = sch["_id"]
#         pid = sch.get("program_id", None)
#         prog_name = prog_map.get(pid, f"Unknown (ID={pid})")

#         st.write("---")
#         st.write(f"**Title**: {sch.get('title', '')} | **Program**: {prog_name}")
#         st.write(f"**Recurrence**: {sch.get('recurrence', 'None')}")
#         st.write(f"**Notes**: {sch.get('notes', '')}")

#         created_by = sch.get("created_by_username", "N/A")
#         created_at = sch.get("created_at", "N/A")
#         updated_by = sch.get("updated_by_username", "N/A")
#         updated_at = sch.get("updated_at", "N/A")

#         st.write(f"**Created by**: {created_by} at {created_at}")
#         st.write(f"**Last Updated by**: {updated_by} at {updated_at}")

#         # If "None" = single session
#         if sch.get("recurrence") == "None":
#             start_text = _format_time_12h(sch.get("start_datetime"))
#             end_text = _format_time_12h(sch.get("end_datetime"))
#             st.write(f"**Date/Time**: {start_text} → {end_text}")
#             if sch.get("location"):
#                 st.write(f"**Location**: {sch['location']}")

#         else:
#             # Weekly or Monthly sessions
#             dt_list = sch.get("days_times", [])
#             if dt_list:
#                 st.write("**Days/Times**:")
#                 for d_obj in dt_list:
#                     day = d_obj["day"]
#                     s_24 = d_obj["start_time"]
#                     e_24 = d_obj["end_time"]
#                     s_12 = _format_time_12h(s_24)
#                     e_12 = _format_time_12h(e_24)
#                     loc = d_obj.get("location", "")
#                     st.write(f"- {day}: {s_12} → {e_12}, Loc: {loc}")

#         # ------------------------------------------------------------------
#         # Only show EDIT/DELETE if is_admin or schedule’s instructor = current user
#         # ------------------------------------------------------------------
#         schedule_creator = sch.get("instructor_id")
#         user_can_edit = is_admin or (schedule_creator == instructor_id)

#         if user_can_edit:
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button(f"Edit {sid}", key=f"edit_btn_{sid}"):
#                     st.session_state["editing_schedule"] = sid
#                     st.rerun()
#             with col2:
#                 if st.button(f"Delete {sid}", key=f"delete_btn_{sid}"):
#                     if delete_schedule(sid):
#                         st.success("Schedule deleted.")
#                         st.rerun()
#                     else:
#                         st.error("Delete failed or no such schedule.")
#         else:
#             st.info("You can view this schedule but cannot edit or delete it.")
        
#         # ------------------------------------------------------------------------------
#         # C) Edit Form (only if user_can_edit)
#         # ------------------------------------------------------------------------------
#         editing_id = st.session_state.get("editing_schedule")
#         if user_can_edit and editing_id == sid:
#             st.subheader(f"Editing Schedule: {editing_id}")
#             schedule_doc = next((x for x in schedules_for_programs if x["_id"] == editing_id), None)
#             if not schedule_doc:
#                 st.error("Schedule not found or not authorized.")
#                 return

#             old_title = schedule_doc.get("title", "")
#             old_notes = schedule_doc.get("notes", "")
#             old_recurrence = schedule_doc.get("recurrence", "None")
#             old_location = schedule_doc.get("location", "")
#             old_days_times = schedule_doc.get("days_times", [])
#             old_program_id = schedule_doc.get("program_id", None)

#             st.write("**Program**:", prog_map.get(old_program_id, f"Unknown (ID={old_program_id})"))

#             new_title = st.text_input(
#                 "Edit Title",
#                 value=old_title,
#                 key=f"edit_title_{sid}"
#             )
#             new_recurrence = st.selectbox(
#                 "Recurrence",
#                 ["None", "Weekly", "Monthly"],
#                 index=["None", "Weekly", "Monthly"].index(old_recurrence),
#                 key=f"edit_recurrence_{sid}"
#             )
#             new_notes = st.text_area(
#                 "Edit Notes",
#                 value=old_notes,
#                 key=f"edit_notes_{sid}"
#             )

#             from dateutil import parser
#             if new_recurrence == "None":
#                 existing_start = schedule_doc.get("start_datetime")
#                 existing_end = schedule_doc.get("end_datetime")

#                 if isinstance(existing_start, str):
#                     existing_start = parser.parse(existing_start)
#                 if isinstance(existing_end, str):
#                     existing_end = parser.parse(existing_end)

#                 start_date_val = existing_start.date() if existing_start else date.today()
#                 start_time_val = existing_start.time() if existing_start else time(9, 0)
#                 end_date_val = existing_end.date() if existing_end else date.today()
#                 end_time_val = existing_end.time() if existing_end else time(10, 0)

#                 edited_start_date = st.date_input(
#                     "Start Date",
#                     value=start_date_val,
#                     key=f"edit_start_date_{sid}"
#                 )
#                 edited_start_time = st.time_input(
#                     "Start Time",
#                     value=start_time_val,
#                     key=f"edit_start_time_{sid}"
#                 )

#                 edited_end_date = st.date_input(
#                     "End Date",
#                     value=end_date_val,
#                     key=f"edit_end_date_{sid}"
#                 )
#                 edited_end_time = st.time_input(
#                     "End Time",
#                     value=end_time_val,
#                     key=f"edit_end_time_{sid}"
#                 )
#                 edited_location = st.text_input(
#                     "Location",
#                     value=old_location,
#                     key=f"edit_location_{sid}"
#                 )
#                 new_days_times = []
#             else:
#                 old_selected_days = [d["day"] for d in old_days_times]
#                 selected_days = st.multiselect(
#                     "Days of Week",
#                     ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
#                     default=old_selected_days,
#                     key=f"edit_selected_days_{sid}"
#                 )

#                 new_days_times = []
#                 for d in selected_days:
#                     existing = next((x for x in old_days_times if x["day"] == d), None)
#                     default_start = time(9, 0)
#                     default_end = time(10, 0)
#                     default_loc = ""

#                     if existing:
#                         if "start_time" in existing:
#                             try:
#                                 hh, mm, ss = existing["start_time"].split(":")
#                                 default_start = time(int(hh), int(mm))
#                             except:
#                                 pass
#                         if "end_time" in existing:
#                             try:
#                                 hh, mm, ss = existing["end_time"].split(":")
#                                 default_end = time(int(hh), int(mm))
#                             except:
#                                 pass
#                         default_loc = existing.get("location", "")

#                     st.write(f"**Times/Location for {d}**")
#                     col_a, col_b = st.columns(2)

#                     new_start = col_a.time_input(
#                         f"{editing_id}_{d}_start",
#                         value=default_start,
#                         key=f"{editing_id}_{d}_start_key"
#                     )
#                     col_a.write(f"Starts at: **{new_start.strftime('%I:%M %p').lstrip('0')}**")

#                     new_end = col_a.time_input(
#                         f"{editing_id}_{d}_end",
#                         value=default_end,
#                         key=f"{editing_id}_{d}_end_key"
#                     )
#                     col_a.write(f"Ends at: **{new_end.strftime('%I:%M %p').lstrip('0')}**")

#                     new_loc = col_b.text_input(
#                         f"{editing_id}_{d}_loc",
#                         value=default_loc,
#                         key=f"{editing_id}_{d}_loc_key"
#                     )

#                     new_days_times.append({
#                         "day": d,
#                         "start_time": str(new_start),
#                         "end_time": str(new_end),
#                         "location": new_loc
#                     })

#                 edited_location = None

#             # Save Changes button
#             if st.button("Save Changes", key=f"save_changes_btn_{sid}"):
#                 updates = {
#                     "title": new_title,
#                     "recurrence": new_recurrence,
#                     "notes": new_notes,
#                     "updated_by_username": st.session_state.get("username", "Unknown"),
#                     "updated_at": datetime.utcnow()
#                 }

#                 if new_recurrence == "None":
#                     updates["days_times"] = []
#                     s_dt = datetime.combine(edited_start_date, edited_start_time)
#                     e_dt = datetime.combine(edited_end_date, edited_end_time)
#                     updates["start_datetime"] = s_dt
#                     updates["end_datetime"] = e_dt
#                     updates["location"] = edited_location
#                 else:
#                     updates["days_times"] = new_days_times
#                     updates["start_datetime"] = None
#                     updates["end_datetime"] = None
#                     updates.pop("location", None)

#                 success = update_schedule(editing_id, updates)
#                 if success:
#                     st.success("Schedule updated.")

#                     # Build a doc for the notification email
#                     updated_doc = {
#                         "program_id": old_program_id,
#                         "title": new_title,
#                         "recurrence": new_recurrence,
#                         "notes": new_notes,
#                         "days_times": new_days_times if new_recurrence != "None" else [],
#                         "location": edited_location if new_recurrence == "None" else None,
#                     }
#                     notify_schedule_change(
#                         program_id=old_program_id,
#                         schedule_doc=updated_doc,
#                         event_type="updated"
#                     )
#                 else:
#                     st.error("No changes made, or update failed.")

#                 st.session_state.pop("editing_schedule", None)
#                 st.rerun()
# def page_manage_students():
#     # 1) Must be logged in (admin or instructor)
#     if not st.session_state.get("instructor_logged_in", False) and not st.session_state.get("is_admin", False):
#         st.error("You must be logged in.")
#         return

#     # We’ll keep your center column layout if you prefer
#     col_left, col_center, col_right = st.columns([1, 5, 1])
#     with col_center:
#         st.header("Manage Students")

#         is_admin = st.session_state.get("is_admin", False)

#         # ----------------------------------------------------------
#         # A) Program Filter for Admin
#         # ----------------------------------------------------------
#         if is_admin:
#             all_programs = list_programs()  # from instructors_db
#             prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#             # Build a list of (program_id, "program_name") pairs
#             program_choices = [(None, "All Programs")] + [
#                 (p["program_id"], p["program_name"]) for p in all_programs
#             ]
#             selected_prog_id = st.selectbox(
#                 "Select Program to View:",
#                 options=[pc[0] for pc in program_choices],
#                 format_func=lambda pid: "All Programs" if pid is None else prog_map[pid]
#             )

#             if selected_prog_id is None:
#                 # Admin sees all students
#                 students = get_all_students()
#             else:
#                 # Admin sees only students in the chosen program
#                 students = get_all_students(program_ids=[selected_prog_id])

#         else:
#             # Instructors see only their assigned programs
#             permitted_ids = st.session_state.get("instructor_program_ids", [])
#             if not permitted_ids:
#                 st.warning("You have no assigned programs. Contact an admin for access.")
#                 return
#             students = get_all_students(program_ids=permitted_ids)

#         if not students:
#             st.info("No students in the database (for the selected program).")

#         # ----------------------------------------------------------
#         # B) Create Tabs: [ “View & Manage” | “Add / Update” ]
#         # ----------------------------------------------------------
#         tab_labels = ["View & Manage", "Add or Update"]
#         tabs = st.tabs(tab_labels)

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 1: VIEW & MANAGE CURRENT STUDENTS
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[0]:
#             st.subheader("Current Students")

#             if students:
#                 for s in students:
#                     student_id = s.get("student_id")
#                     name = s.get("name", "")
#                     phone = s.get("phone", "")
#                     contact_email = s.get("contact_email", "")
#                     prog_id = s.get("program_id", None)
#                     grade = s.get("grade", "")
#                     school = s.get("school", "")

#                     st.write(
#                         f"**Name:** {name}, **ID:** {student_id}, **Program ID:** {prog_id}, "
#                         f"**Phone:** {phone}, **Contact:** {contact_email}, "
#                         f"**Grade:** {grade}, **School:** {school}"
#                     )

#                     col_del, col_edit, col_today, col_past = st.columns(4)

#                     # ------------ Delete Button ------------
#                     with col_del:
#                         if st.button(f"Delete (ID={student_id})", key=f"btn_delete_{student_id}"):
#                             # Instructors must only delete if the student's program_id is in permitted_ids
#                             if not is_admin:
#                                 perm_ids = st.session_state.get("instructor_program_ids", [])
#                                 if prog_id not in perm_ids:
#                                     st.error("You are not permitted to delete students in this program.")
#                                     st.stop()

#                             success = delete_student_record(student_id)
#                             if success:
#                                 st.success(f"Deleted student {name} (ID={student_id}).")
#                                 st.rerun()
#                             else:
#                                 st.error("Delete failed or no such student.")

#                     # ------------ Edit Button ------------
#                     with col_edit:
#                         if st.button(f"Edit (ID={student_id})", key=f"btn_edit_{student_id}"):
#                             st.session_state["editing_student"] = s
#                             st.rerun()

#                     # ------------ Mark Attendance Today ------------
#                     with col_today:
#                         if st.button(f"Mark Attendance", key=f"btn_attendance_{student_id}"):
#                             st.session_state["attendance_student"] = s
#                             st.rerun()

#                     # ------------ Mark Past Attendance ------------
#                     with col_past:
#                         if st.button(f"Mark Past", key=f"btn_attendance_past_{student_id}"):
#                             st.session_state["attendance_student"] = s
#                             st.session_state["attendance_mode"] = "past"
#                             st.rerun()

#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 # INDIVIDUAL ATTENDANCE LOGIC
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 if "attendance_student" in st.session_state:
#                     single_stud = st.session_state["attendance_student"]
#                     mode = st.session_state.get("attendance_mode", "today")

#                     if mode == "today":
#                         st.subheader(f"Mark Attendance (Today) for {single_stud['name']}")
#                         current_dt = datetime.now()
#                         status_opt = ["Present", "Late", "Absent", "Excused"]
#                         chosen_status = st.selectbox("Status", status_opt, index=0)
#                         comment_txt = st.text_input("Comment (Optional)")

#                         if st.button("Submit Attendance"):
#                             try:
#                                 msg = record_student_attendance_in_array(
#                                     name=single_stud["name"],
#                                     program_id=single_stud["program_id"],
#                                     status=chosen_status,
#                                     comment=comment_txt,
#                                     attendance_date=current_dt
#                                 )
#                                 st.success(f"Marked {single_stud['name']} as {chosen_status}. {msg}")
#                             except Exception as e:
#                                 st.error(f"Error: {e}")

#                             st.session_state.pop("attendance_student")
#                             st.session_state.pop("attendance_mode", None)
#                             st.rerun()

#                         if st.button("Cancel"):
#                             st.session_state.pop("attendance_student")
#                             st.session_state.pop("attendance_mode", None)
#                             st.info("Individual attendance marking canceled.")
#                             st.rerun()

#                     elif mode == "past":
#                         st.subheader(f"Mark Past Attendance for {single_stud['name']}")
#                         date_val = st.date_input("Session Date", value=date.today())
#                         time_val = st.time_input("Session Time", value=time(9, 0))
#                         combined_dt = datetime.combine(date_val, time_val)

#                         status_opt = ["Present", "Late", "Absent", "Excused"]
#                         chosen_status = st.selectbox("Status", status_opt, index=0)
#                         comment_txt = st.text_input("Comment (Optional)")

#                         if st.button("Submit Past Attendance"):
#                             try:
#                                 msg = record_student_attendance_in_array(
#                                     name=single_stud["name"],
#                                     program_id=single_stud["program_id"],
#                                     status=chosen_status,
#                                     comment=comment_txt,
#                                     attendance_date=combined_dt
#                                 )
#                                 st.success(f"Marked {single_stud['name']} as {chosen_status} on {combined_dt}. {msg}")
#                             except Exception as e:
#                                 st.error(f"Error: {e}")

#                             st.session_state.pop("attendance_student")
#                             st.session_state.pop("attendance_mode", None)
#                             st.rerun()

#                         if st.button("Cancel Past"):
#                             st.session_state.pop("attendance_student")
#                             st.session_state.pop("attendance_mode", None)
#                             st.info("Past attendance marking canceled.")
#                             st.rerun()
#             # End if students

#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#             # EDIT STUDENT WORKFLOW
#             # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#             if "editing_student" in st.session_state:
#                 edited_stud = st.session_state["editing_student"]
#                 st.subheader(f"Edit Student: {edited_stud.get('name', '')} (ID={edited_stud.get('student_id', '')})")

#                 # Guard against editing a student in a program the instructor doesn't have
#                 if not is_admin:
#                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                     if edited_stud.get("program_id") not in perm_ids:
#                         st.error("You do not have permission to edit students in this program.")
#                         if st.button("OK"):
#                             st.session_state.pop("editing_student")
#                             st.rerun()

#                 with st.form("edit_student_form"):
#                     new_name = st.text_input("Name", value=edited_stud.get("name", ""))
#                     new_phone = st.text_input("Phone", value=edited_stud.get("phone", ""))
#                     new_email = st.text_input("Contact Email", value=edited_stud.get("contact_email", ""))
#                     new_grade = st.text_input("Grade", value=edited_stud.get("grade", ""))
#                     new_school = st.text_input("School", value=edited_stud.get("school", ""))

#                     # If admin, let them pick a new program
#                     if is_admin:
#                         all_progs = list_programs()
#                         prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                         prog_ids = list(prog_map.keys())

#                         current_pid = edited_stud.get("program_id")
#                         if current_pid not in prog_ids:
#                             prog_index = 0
#                         else:
#                             prog_index = prog_ids.index(current_pid)

#                         selected_id = st.selectbox(
#                             "Select Program:",
#                             options=prog_ids,
#                             format_func=lambda pid: f"{pid} - {prog_map[pid]}",
#                             index=prog_index
#                         )
#                         new_program_id = selected_id
#                     else:
#                         perm_ids = st.session_state.get("instructor_program_ids", [])
#                         current_pid = edited_stud.get("program_id")
#                         if current_pid not in perm_ids and perm_ids:
#                             current_pid = perm_ids[0]
#                         new_program_id = st.selectbox(
#                             "Select Program ID:",
#                             options=perm_ids,
#                             index=perm_ids.index(current_pid) if current_pid in perm_ids else 0
#                         )

#                     submitted = st.form_submit_button("Save Changes")
#                     if submitted:
#                         try:
#                             msg = update_student_info(
#                                 student_id=edited_stud["student_id"],
#                                 name=new_name,
#                                 phone=new_phone,
#                                 contact_email=new_email,
#                                 program_id=new_program_id,
#                                 grade=new_grade,
#                                 school=new_school
#                             )
#                             st.success(f"{msg}")
#                             st.session_state.pop("editing_student")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"Error updating student: {e}")

#                 if st.button("Cancel Edit"):
#                     st.session_state.pop("editing_student")
#                     st.rerun()

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 2: ADD OR UPDATE STUDENTS (Single or Bulk)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[1]:
#             st.subheader("Add or Update Students")

#             # We keep your radio approach to switch Single / Bulk
#             action = st.radio(
#                 "Choose method:",
#                 ["Single Student Entry", "Bulk CSV Upload"],
#                 horizontal=True
#             )

#             if action == "Single Student Entry":
#                 with st.form("student_form"):
#                     name_val = st.text_input("Name *", "")
#                     phone_val = st.text_input("Phone", "")
#                     contact_val = st.text_input("Contact Email", "")
#                     grade_val = st.text_input("Grade", "")
#                     school_val = st.text_input("School", "")

#                     if is_admin:
#                         all_progs = list_programs()
#                         if not all_progs:
#                             st.warning("No programs found in Postgres.")
#                             st.stop()

#                         prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                         selected_id = st.selectbox(
#                             "Select Program:",
#                             options=prog_map.keys(),
#                             format_func=lambda pid: f"{pid} - {prog_map[pid]}"
#                         )
#                         prog_val = selected_id
#                     else:
#                         perm_ids = st.session_state.get("instructor_program_ids", [])
#                         if not perm_ids:
#                             st.warning("No assigned programs available.")
#                             prog_val = None
#                         else:
#                             prog_val = st.selectbox(
#                                 "Select Program ID:",
#                                 options=perm_ids,
#                                 format_func=lambda pid: f"Program ID: {pid}"
#                             )

#                     submitted = st.form_submit_button("Save Student Info")
#                     if submitted:
#                         if not name_val.strip():
#                             st.error("Name is required.")
#                         elif prog_val is None:
#                             st.error("No valid program selected.")
#                         else:
#                             result = store_student_record(
#                                 name_val, phone_val, contact_val, prog_val,
#                                 grade=grade_val, school=school_val
#                             )
#                             st.success(result)
#                             st.rerun()

#             else:
#                 # Bulk CSV Upload
#                 if is_admin:
#                     all_progs = list_programs()
#                     if not all_progs:
#                         st.warning("No programs found in Postgres.")
#                         st.stop()

#                     prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=prog_map.keys(),
#                         format_func=lambda pid: f"{pid} - {prog_map[pid]}"
#                     )
#                 else:
#                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                     if not perm_ids:
#                         st.warning("No assigned programs available.")
#                         st.stop()
#                     selected_prog_id = st.selectbox(
#                         "Select Program ID for CSV Rows:",
#                         options=perm_ids,
#                         format_func=lambda pid: f"Program ID: {pid}"
#                     )

#                 uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])
#                 if uploaded_file:
#                     df = pd.read_csv(uploaded_file)
#                     st.write("Preview of data:", df.head())

#                     required_cols = {"First Name", "Last Name", "Number", "Email", "Grade", "School"}
#                     if not required_cols.issubset(df.columns):
#                         st.error(f"CSV must have columns: {required_cols}")
#                     else:
#                         if st.button("Process CSV"):
#                             successes = 0
#                             failures = 0
#                             for idx, row in df.iterrows():
#                                 first_name = str(row["First Name"]).strip()
#                                 last_name = str(row["Last Name"]).strip()
#                                 name_val = f"{first_name} {last_name}".strip()

#                                 phone_val = row["Number"]
#                                 contact_val = row["Email"]
#                                 grade_val = row["Grade"]
#                                 school_val = row["School"]

#                                 # Instructors can only upload if the CSV's program_id is in their assigned list
#                                 if not is_admin:
#                                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                                     if selected_prog_id not in perm_ids:
#                                         st.warning(f"Row {idx}: Program ID '{selected_prog_id}' is not in your assigned list.")
#                                         failures += 1
#                                         continue

#                                 result_msg = store_student_record(
#                                     name_val, phone_val, contact_val,
#                                     selected_prog_id, grade_val, school_val
#                                 )
#                                 if ("New student record" in result_msg) or ("updated" in result_msg):
#                                     successes += 1
#                                 else:
#                                     failures += 1

#                             st.success(f"Bulk upload complete. Successes: {successes}, Failures: {failures}")
#                             st.rerun()

# def page_generate_reports():
#     st.header("Generate Reports")

#     # 1) Admin or Instructor?
#     is_admin = st.session_state.get("is_admin", False)

#     # 2) Build program map from Postgres
#     all_programs = list_programs()  # e.g. [{"program_id":1,"program_name":"STEM"}, ...]
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#     # 3) Determine permitted program IDs
#     if is_admin:
#         program_id_options = [p["program_id"] for p in all_programs]  # admin sees all
#     else:
#         program_id_options = st.session_state.get("instructor_program_ids", [])
#         if not program_id_options:
#             st.warning("You have no assigned programs. Contact an admin for access.")
#             return

#     # 4) Fetch attendance records from Mongo
#     records = fetch_all_attendance_records()
#     if not records:
#         st.info("No attendance data found.")
#         return

#     # 5) Filter by permitted program IDs
#     filtered_records = [r for r in records if r.get("program_id") in program_id_options]
#     if not filtered_records:
#         st.info("No attendance data found for your assigned programs.")
#         return

#     # 6) Flatten records
#     flattened = []
#     for r in filtered_records:
#         att = r["attendance"]
#         pid = r.get("program_id", 0)
#         flattened.append({
#             "student_id": r.get("student_id"),
#             "name": r.get("name"),
#             "program_id": pid,
#             "program_name": prog_map.get(pid, f"Program ID={pid}"),
#             "date": att.get("date"),
#             "status": att.get("status"),
#             "comment": att.get("comment", "")
#         })

#     if not flattened:
#         st.info("No valid attendance data to display.")
#         return

#     df = pd.DataFrame(flattened)
#     if df.empty:
#         st.info("No valid attendance data to display.")
#         return

#     # -------------------------------------------------------------------------
#     # A) Admin-Only Visualizations (Overview)
#     # -------------------------------------------------------------------------
#     if is_admin:
#         with st.expander("Admin Visualizations of Full Attendance Data", expanded=False):
#             def status_to_numeric(s):
#                 if s == "Present":
#                     return 1
#                 elif s == "Late":
#                     return 0.5
#                 else:
#                     return 0

#             df["attendance_value"] = df["status"].apply(status_to_numeric)

#             # Ranking by average attendance
#             ranking_df = df.groupby("program_name", as_index=False)["attendance_value"].mean()
#             ranking_df.rename(columns={"attendance_value": "avg_attendance_score"}, inplace=True)
#             ranking_df.sort_values("avg_attendance_score", ascending=False, inplace=True)

#             st.subheader("Program Ranking by Average Attendance")
#             st.table(ranking_df)

#             # Bar chart: average attendance score
#             fig_bar = px.bar(
#                 ranking_df,
#                 x="program_name",
#                 y="avg_attendance_score",
#                 title="Average Attendance Score by Program"
#             )

#             # Pie chart: overall status distribution
#             status_counts = df["status"].value_counts().reset_index()
#             status_counts.columns = ["status", "count"]
#             fig_pie = px.pie(
#                 status_counts,
#                 values="count",
#                 names="status",
#                 title="Distribution of Attendance Statuses",
#                 hole=0.4
#             )

#             # Time-series
#             df["date"] = pd.to_datetime(df["date"], errors="coerce")
#             daily_df = df.groupby("date", as_index=False)["attendance_value"].mean()
#             fig_line = px.line(
#                 daily_df,
#                 x="date",
#                 y="attendance_value",
#                 title="Average Attendance Over Time (All Programs)"
#             )

#             # Multi-line by program
#             multi_df = df.groupby(["date", "program_name"], as_index=False)["attendance_value"].mean()
#             fig_multi = px.line(
#                 multi_df,
#                 x="date",
#                 y="attendance_value",
#                 color="program_name",
#                 title="Attendance Over Time by Program"
#             )

#             colA, colB = st.columns(2)
#             with colA:
#                 st.subheader("Average Attendance Score by Program")
#                 st.plotly_chart(fig_bar, use_container_width=True)

#             with colB:
#                 st.subheader("Proportion of Attendance Statuses")
#                 st.plotly_chart(fig_pie, use_container_width=True)

#             st.write("---")
#             st.subheader("Average Attendance Over Time (All Programs)")
#             st.plotly_chart(fig_line, use_container_width=True)

#             st.subheader("Attendance Over Time by Program")
#             st.plotly_chart(fig_multi, use_container_width=True)

#     # -------------------------------------------------------------------------
#     # B) Data Explorer + Chart Building from Filtered Data
#     # -------------------------------------------------------------------------
#     with st.expander("Data Explorer"):
#         explorer_output = dataframe_explorer(df, case=False)
#         explorer_df = pd.DataFrame(explorer_output)

#         if explorer_df.empty:
#             st.info("No data selected in the explorer.")
#         else:
#             st.dataframe(explorer_df, use_container_width=True)
#             st.markdown("### Build a Plotly Chart from the Filtered Data")
#             chart_type = st.selectbox(
#                 "Select Chart Type",
#                 [
#                     "Bar - Status Counts",
#                     "Line - Attendance Over Time",
#                     "Bar - Student Attendance",
#                     "Pie - Status Distribution",
#                     # "Scatter - Attendance vs. Date (Line)"  # example line scatter
#                 ]
#             )

#             # Convert 'date' to datetime if needed
#             explorer_df["date"] = pd.to_datetime(explorer_df["date"], errors="coerce")

#             if chart_type == "Bar - Status Counts":
#                 status_counts = explorer_df["status"].value_counts().reset_index()
#                 status_counts.columns = ["status", "count"]
#                 fig_bar_filter = px.bar(
#                     status_counts,
#                     x="status",
#                     y="count",
#                     title="Status Counts in Filtered Data"
#                 )
#                 st.plotly_chart(fig_bar_filter, use_container_width=True)

#             elif chart_type == "Line - Attendance Over Time":
#                 def status_to_numeric(s):
#                     if s == "Present":
#                         return 1
#                     elif s == "Late":
#                         return 0.5
#                     else:
#                         return 0
#                 explorer_df["attendance_value"] = explorer_df["status"].apply(status_to_numeric)
#                 daily_mean = explorer_df.groupby("date", as_index=False)["attendance_value"].mean().sort_values("date")
#                 fig_line_filter = px.line(
#                     daily_mean,
#                     x="date",
#                     y="attendance_value",
#                     title="Average Attendance Over Time (Filtered Data)"
#                 )
#                 st.plotly_chart(fig_line_filter, use_container_width=True)

#             elif chart_type == "Bar - Student Attendance":
#                 group_data = explorer_df.groupby(["name", "status"]).size().reset_index(name="count")
#                 fig_bar_student = px.bar(
#                     group_data,
#                     x="name",
#                     y="count",
#                     color="status",
#                     barmode="group",
#                     title="Attendance by Student (Filtered Data)"
#                 )
#                 st.plotly_chart(fig_bar_student, use_container_width=True)

#             elif chart_type == "Pie - Status Distribution":
#                 status_counts = explorer_df["status"].value_counts().reset_index()
#                 status_counts.columns = ["status", "count"]
#                 fig_pie_filter = px.pie(
#                     status_counts,
#                     values="count",
#                     names="status",
#                     title="Status Distribution (Filtered Data)",
#                     hole=0.4
#                 )
#                 st.plotly_chart(fig_pie_filter, use_container_width=True)

#             elif chart_type == "Scatter - Attendance vs. Date (Line)":
#                 # line scatter approach
#                 def status_to_numeric(s):
#                     if s == "Present":
#                         return 1
#                     elif s == "Late":
#                         return 0.5
#                     else:
#                         return 0
#                 explorer_df["attendance_value"] = explorer_df["status"].apply(status_to_numeric)

#                 fig_scatter_line = px.line(
#                     explorer_df,
#                     x="date",
#                     y="attendance_value",
#                     color="name",
#                     markers=True,  # so we see scatter points on the line
#                     title="Line Scatter: Attendance by Date (Filtered Data)"
#                 )
#                 st.plotly_chart(fig_scatter_line, use_container_width=True)

#     # -------------------------------------------------------------------------
#     # C) Program-Specific XLSX (with advanced insights)
#     # -------------------------------------------------------------------------
#     st.write("---")
#     st.subheader("Generate Program-Specific XLSX (with Total Absences + Advanced Insights)")

#     # Let user pick a program from df
#     selectable_pids = sorted(df["program_id"].unique())
#     selected_pid = st.selectbox(
#         "Select a Program to Export/Analyze",
#         options=selectable_pids,
#         format_func=lambda pid: prog_map.get(pid, f"Program ID={pid}")
#     )

#     if "pivot_df" not in st.session_state:
#         st.session_state["pivot_df"] = None

#     if st.button("Create Pivot + Insights"):
#         # Filter DF to chosen program
#         sub_df = df[df["program_id"] == selected_pid].copy()
#         if sub_df.empty:
#             st.warning("No attendance data for that program!")
#             return

#         sub_df["date"] = pd.to_datetime(sub_df["date"], errors="coerce").dt.date
#         pivot_df = sub_df.pivot(index="name", columns="date", values="status").fillna("Missed")

#         # Count absences
#         def count_absences(row):
#             return sum(x in ["Absent", "Missed"] for x in row)
#         pivot_df["Total Absences"] = pivot_df.apply(count_absences, axis=1)

#         st.session_state["pivot_df"] = pivot_df

#         # ---- Additional Summaries/Insights ----
#         total_students = len(pivot_df.index)
#         average_absences = pivot_df["Total Absences"].mean()
#         max_absences = pivot_df["Total Absences"].max()

#         st.write(f"**Total Students:** {total_students}")
#         st.write(f"**Average Absences:** {average_absences:.2f}")
#         st.write(f"**Maximum Absences by Any Student:** {max_absences}")

#         # "High-risk" threshold
#         absence_threshold = 3
#         high_risk_students = pivot_df[pivot_df["Total Absences"] > absence_threshold].index.tolist()
#         if high_risk_students:
#             st.warning(f"**Alert**: The following students exceeded {absence_threshold} absences:")
#             for s in high_risk_students:
#                 st.write(f"- {s} (Total Absences = {pivot_df.loc[s, 'Total Absences']})")
#         else:
#             st.success(f"No students have more than {absence_threshold} absences. Great job!")

#         # Quick bar chart
#         # abs_data = pivot_df["Total Absences"].reset_index()
#         # abs_data.columns = ["name", "total_absences"]
#         # fig_bar_absences = px.bar(
#         #     abs_data,
#         #     x="name",
#         #     y="total_absences",
#         #     title="Total Absences by Student"
#         # )
#         # st.plotly_chart(fig_bar_absences, use_container_width=True)

#     if st.session_state["pivot_df"] is not None:
#         st.write("### Pivot Preview (Enhanced)")
#         # highlight rows above threshold
#         pivot_styled = st.session_state["pivot_df"].style.apply(
#             highlight_high_absences, axis=1
#         )
#         st.dataframe(pivot_styled, use_container_width=True)

#         if st.button("Create Downloadable XLSX"):
#             output = io.BytesIO()
#             with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
#                 st.session_state["pivot_df"].to_excel(writer, sheet_name="Attendance Pivot")

#                 workbook = writer.book
#                 worksheet = writer.sheets["Attendance Pivot"]
#                 red_format = workbook.add_format({"font_color": "red"})
#                 row_count, col_count = st.session_state["pivot_df"].shape
#                 worksheet.conditional_format(
#                     1, 1, row_count, col_count,
#                     {
#                         "type": "text",
#                         "criteria": "containing",
#                         "value": "Missed",
#                         "format": red_format
#                     }
#                 )

#             excel_data = output.getvalue()
#             st.download_button(
#                 label="Download Program XLSX",
#                 data=excel_data,
#                 file_name="program_attendance.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )

    def page_review_attendance():
    st.header("Review Attendance Logs")

    # -------------------------------------------------------------
    # A) Show summary metrics: This Week vs. Last Week
    # -------------------------------------------------------------
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # 1) "This Week" subdocs
    subdocs_this_week = get_attendance_subdocs_in_range(seven_days_ago, now)
    total_this_week = len(subdocs_this_week)

    # 2) "Last Week" subdocs
    subdocs_last_week = get_attendance_subdocs_in_range(fourteen_days_ago, seven_days_ago)
    total_last_week = len(subdocs_last_week)
    attendance_delta = total_this_week - total_last_week

    # Admin vs. Instructor logic
    is_admin = st.session_state.get("is_admin", False)
    if is_admin:
        all_students = get_all_students()  # Admin sees all
    else:
        # Instructors see only assigned programs
        program_ids = st.session_state.get("instructor_program_ids", [])
        all_students = get_all_students(program_ids=program_ids)

    total_students = len(all_students)

    # Get last week's student count from ObjectId logic
    last_week_count = get_student_count_as_of_last_week()
    student_delta = total_students - last_week_count

    # Absent comparison
    absent_this_week = sum(1 for r in subdocs_this_week if r["attendance"]["status"] == "Absent")
    absent_last_week = sum(1 for r in subdocs_last_week if r["attendance"]["status"] == "Absent")
    delta_absent = absent_this_week - absent_last_week

    # -------------------------------------------------------------
    # B) Display the top-level metrics
    # -------------------------------------------------------------
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     st.metric(
    #         label="Attendance This Week",
    #         value=total_this_week,
    #         delta=f"{attendance_delta} vs. last week"
    #     )
    # with col2:
    #     st.metric(
    #         label="Absences This Week",
    #         value=absent_this_week,
    #         delta=f"{delta_absent} vs. last week"
    #     )
    # with col3:
    #     st.metric(
    #         label="Total Students",
    #         value=total_students,
    #         delta=f"{student_delta} vs. last week"
    #     )

    # st.write("---")

    # -------------------------------------------------------------
    # C) Tabs for “All Attendance” vs. “Missed Counts”
    # -------------------------------------------------------------
    # tab_labels = ["All Attendance", "Missed Counts"]
    # tabs = st.tabs(tab_labels)

    # with tabs[0]:
    with st.expander("Show Missed Counts"):
            show_missed_counts()

    st.subheader("All Attendance Records")
    show_attendance_logs()

    # This calls your existing function to display logs
    # e.g. show_attendance_logs() 
    # (You might consider adding color-coded or emoji-coded statuses in that function.)
   

    # with tabs[1]:
    #     st.subheader("Missed Counts Overview")
    #     # This calls your existing function for missed data
    #     # e.g. show_missed_counts()
    #     show_missed_counts()

    # def page_manage_schedules():
#     """
#     Page for an instructor (or admin) to create, view, edit, and delete schedules,
#     with a streamlined recurrence pattern selection for "One-Time" or "Weekly."
#     (Monthly is commented out below.)
#     """

#     # 1) Check login
#     instructor_id = st.session_state.get("instructor_id", None)
#     is_admin = st.session_state.get("is_admin", False)
#     if not instructor_id and not is_admin:
#         st.error("You must be logged in as an instructor or admin to manage schedules.")
#         return

#     # 2) Build a program map from Postgres
#     all_programs = list_programs()
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#     # 3) Determine which program IDs this user can manage
#     if is_admin:
#         program_id_options = list(prog_map.keys())
#     else:
#         program_id_options = st.session_state.get("instructor_program_ids", [])
#         if not program_id_options:
#             st.warning("You have no assigned programs. Contact an admin for access.")
#             return

#     st.header("Manage Class Schedules")

#     # --------------------------------------------------------------------------
#     # A) Create a New Schedule
#     # --------------------------------------------------------------------------
#     with st.expander("Create a New Schedule", expanded=True):
#         if program_id_options:
#             selected_prog_id = st.selectbox(
#                 "Select Program",
#                 options=program_id_options,
#                 format_func=lambda pid: prog_map.get(pid, f"Unknown (ID={pid})"),
#                 key="select_program_for_new_schedule"
#             )
#         else:
#             st.warning("No assigned programs available.")
#             return

#         # Basic fields
#         title = st.text_input("Class Title", "", key="new_schedule_title")
#         notes = st.text_area("Additional Notes/Description", key="new_schedule_notes")

#         # ***** Recurrence radio: Only "One-Time" or "Weekly" *****
#         # To re-enable monthly, add it back into the list
#         recurrence_choice = st.radio(
#             "Recurrence Pattern",
#             ["One-Time", "Weekly"],  # <-- "Monthly" removed from here
#             horizontal=True,
#             help="Pick how often this session recurs."
#         )

#         # We'll store location/time/days in these variables
#         location = ""
#         days_times = []
#         start_dt = None
#         end_dt = None

#         # --------- One-Time vs Weekly (Monthly lines are commented out) ---------
#         if recurrence_choice == "One-Time":
#             chosen_date = st.date_input("Class Date", value=date.today())
#             col_start, col_end = st.columns(2)
#             with col_start:
#                 start_t = st.time_input("Start Time", value=time(9, 0))
#             with col_end:
#                 end_t = st.time_input("End Time", value=time(10, 0))
#             location = st.text_input("Location (Zoom or Physical Room)")

#         elif recurrence_choice == "Weekly":
#             st.write("Select multiple days, each with its own time and location.")
#             selected_days = st.multiselect(
#                 "Days of Week",
#                 ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
#             )
#             for d in selected_days:
#                 st.write(f"**Times/Location for {d}**")
#                 col1, col2 = st.columns(2)

#                 start_for_day = col1.time_input(
#                     f"{d} Start",
#                     value=time(9, 0),
#                     key=f"{d}_start_time"
#                 )
#                 end_for_day = col2.time_input(
#                     f"{d} End",
#                     value=time(10, 0),
#                     key=f"{d}_end_time"
#                 )
#                 loc_for_day = st.text_input(
#                     f"{d}_loc",
#                     "",
#                     key=f"{d}_loc"
#                 )
#                 days_times.append({
#                     "day": d,
#                     "start_time": str(start_for_day),
#                     "end_time": str(end_for_day),
#                     "location": loc_for_day
#                 })

#         # COMMENT OUT THIS ENTIRE SECTION IF YOU DON'T WANT "MONTHLY"
#         # else:  # <-- COMMENT OUT
#         #     # "Monthly" logic here
#         #     st.write("Monthly (commented out)")  # <-- COMMENT OUT
#         #     # ...
#         #     # days_times logic for monthly
#         #     # day_of_month input
#         #     # ...
#         # END COMMENT OUT

#         # -------------- "Create Schedule" button --------------
#         if st.button("Create Schedule"):
#             if recurrence_choice == "One-Time":
#                 start_dt = datetime.combine(chosen_date, start_t)
#                 end_dt = datetime.combine(chosen_date, end_t)
#                 doc = {
#                     "instructor_id": instructor_id,
#                     "program_id": selected_prog_id,
#                     "title": title,
#                     "recurrence": "None",  # internally store as "None"
#                     "notes": notes,
#                     "start_datetime": start_dt,
#                     "end_datetime": end_dt,
#                     "days_times": [],
#                     "location": location,
#                     "created_by_username": st.session_state.get("instructor_username", "Admin"),
#                     "created_at": datetime.utcnow()
#                 }
#             else:  # "Weekly" only
#                 doc = {
#                     "instructor_id": instructor_id,
#                     "program_id": selected_prog_id,
#                     "title": title,
#                     "recurrence": "Weekly",
#                     "notes": notes,
#                     "days_times": days_times,
#                     "start_datetime": None,
#                     "end_datetime": None,
#                     "created_by_username": st.session_state.get("instructor_username", "Admin"),
#                     "created_at": datetime.utcnow()
#                 }

#             new_id = create_schedule(doc)
#             st.success(f"Created schedule with ID: {new_id}")
#             notify_schedule_change(selected_prog_id, doc, event_type="created")
#             st.rerun()

#     # --------------------------------------------------------------------------
#     # B) Show Existing Schedules
#     # --------------------------------------------------------------------------
#     st.subheader("Existing Schedules")
#     schedules_for_programs = list_schedules_by_program(program_id_options)

#     if not schedules_for_programs:
#         st.info("No schedules found for your assigned programs.")
#         return

#     for sch in schedules_for_programs:
#         sid = sch["_id"]
#         pid = sch.get("program_id", None)
#         prog_name = prog_map.get(pid, f"Unknown (ID={pid})")

#         st.write("---")
#         st.write(f"**Title**: {sch.get('title', '')} | **Program**: {prog_name}")
#         st.write(f"**Recurrence**: {sch.get('recurrence', 'None')}")
#         st.write(f"**Notes**: {sch.get('notes', '')}")

#         created_by = sch.get("created_by_username", "N/A")
#         created_at = sch.get("created_at", "N/A")
#         updated_by = sch.get("updated_by_username", "N/A")
#         updated_at = sch.get("updated_at", "N/A")

#         st.write(f"**Created by**: {created_by} at {created_at}")
#         st.write(f"**Last Updated by**: {updated_by} at {updated_at}")

#         # If "None" => One-Time
#         if sch.get("recurrence") == "None":
#             start_text = _format_time_12h(sch.get("start_datetime"))
#             end_text = _format_time_12h(sch.get("end_datetime"))
#             st.write(f"**Date/Time**: {start_text} → {end_text}")
#             if sch.get("location"):
#                 st.write(f"**Location**: {sch['location']}")
#         elif sch.get("recurrence") == "Weekly":
#             dt_list = sch.get("days_times", [])
#             if dt_list:
#                 st.write("**Days/Times**:")
#                 for d_obj in dt_list:
#                     day = d_obj["day"]
#                     s_24 = d_obj["start_time"]
#                     e_24 = d_obj["end_time"]
#                     s_12 = _format_time_12h(s_24)
#                     e_12 = _format_time_12h(e_24)
#                     loc = d_obj.get("location", "")
#                     st.write(f"- {day}: {s_12} → {e_12}, Loc: {loc}")

#         # COMMENT OUT or skip "Monthly" display
#         # elif sch.get("recurrence") == "Monthly":  # <-- COMMENT OUT
#         #     # Display monthly details
#         #     st.write("Monthly schedule...")  # <-- COMMENT OUT
#         #     # etc. for dt_list or day_of_month
#         # END COMMENT OUT

#         # Edit/ Delete logic
#         schedule_creator = sch.get("instructor_id")
#         user_can_edit = is_admin or (schedule_creator == instructor_id)

#         if user_can_edit:
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button(f"Edit {sid}", key=f"edit_btn_{sid}"):
#                     st.session_state["editing_schedule"] = sid
#                     st.rerun()
#             with col2:
#                 if st.button(f"Delete {sid}", key=f"delete_btn_{sid}"):
#                     if delete_schedule(sid):
#                         st.success("Schedule deleted.")
#                         st.rerun()
#                     else:
#                         st.error("Delete failed or no such schedule.")
#         else:
#             st.info("You can view this schedule but cannot edit or delete it.")

#         # If editing:
#         editing_id = st.session_state.get("editing_schedule")
#         if user_can_edit and editing_id == sid:
#             # st.subheader(f"Editing Schedule: {editing_id}")
#             # ... same logic as before ...
#             # st.subheader(f"Editing Schedule: {editing_id}")
#             schedule_doc = next((x for x in schedules_for_programs if x["_id"] == editing_id), None)
#             if not schedule_doc:
#                 st.error("Schedule not found or not authorized.")
#                 return

#             old_title = schedule_doc.get("title", "")
#             old_notes = schedule_doc.get("notes", "")
#             old_recurrence = schedule_doc.get("recurrence", "None")
#             old_location = schedule_doc.get("location", "")
#             old_days_times = schedule_doc.get("days_times", [])
#             old_program_id = schedule_doc.get("program_id", None)
#             # st.subheader(f"Editing Schedule: {prog_map.get(old_program_id, f"Unknown (ID={old_program_id}")}")
#             st.subheader(f"Editing Schedule: {prog_map.get(old_program_id, f'Unknown (ID={old_program_id})')}")

#             st.write("**Program**:", prog_map.get(old_program_id, f"Unknown (ID={old_program_id})"))

#             new_title = st.text_input(
#                 "Edit Title",
#                 value=old_title,
#                 key=f"edit_title_{sid}"
#             )
#             new_recurrence = st.selectbox(
#                 "Recurrence",
#                 ["None", "Weekly", "Monthly"],
#                 index=["None", "Weekly", "Monthly"].index(old_recurrence),
#                 key=f"edit_recurrence_{sid}"
#             )
#             new_notes = st.text_area(
#                 "Edit Notes",
#                 value=old_notes,
#                 key=f"edit_notes_{sid}"
#             )

#             from dateutil import parser
#             if new_recurrence == "None":
#                 existing_start = schedule_doc.get("start_datetime")
#                 existing_end = schedule_doc.get("end_datetime")

#                 if isinstance(existing_start, str):
#                     existing_start = parser.parse(existing_start)
#                 if isinstance(existing_end, str):
#                     existing_end = parser.parse(existing_end)

#                 start_date_val = existing_start.date() if existing_start else date.today()
#                 start_time_val = existing_start.time() if existing_start else time(9, 0)
#                 end_date_val = existing_end.date() if existing_end else date.today()
#                 end_time_val = existing_end.time() if existing_end else time(10, 0)

#                 edited_start_date = st.date_input(
#                     "Start Date",
#                     value=start_date_val,
#                     key=f"edit_start_date_{sid}"
#                 )
#                 edited_start_time = st.time_input(
#                     "Start Time",
#                     value=start_time_val,
#                     key=f"edit_start_time_{sid}"
#                 )

#                 edited_end_date = st.date_input(
#                     "End Date",
#                     value=end_date_val,
#                     key=f"edit_end_date_{sid}"
#                 )
#                 edited_end_time = st.time_input(
#                     "End Time",
#                     value=end_time_val,
#                     key=f"edit_end_time_{sid}"
#                 )
#                 edited_location = st.text_input(
#                     "Location",
#                     value=old_location,
#                     key=f"edit_location_{sid}"
#                 )
#                 new_days_times = []
#             else:
#                 old_selected_days = [d["day"] for d in old_days_times]
#                 selected_days = st.multiselect(
#                     "Days of Week",
#                     ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
#                     default=old_selected_days,
#                     key=f"edit_selected_days_{sid}"
#                 )

#                 new_days_times = []
#                 for d in selected_days:
#                     existing = next((x for x in old_days_times if x["day"] == d), None)
#                     default_start = time(9, 0)
#                     default_end = time(10, 0)
#                     default_loc = ""

#                     if existing:
#                         if "start_time" in existing:
#                             try:
#                                 hh, mm, ss = existing["start_time"].split(":")
#                                 default_start = time(int(hh), int(mm))
#                             except:
#                                 pass
#                         if "end_time" in existing:
#                             try:
#                                 hh, mm, ss = existing["end_time"].split(":")
#                                 default_end = time(int(hh), int(mm))
#                             except:
#                                 pass
#                         default_loc = existing.get("location", "")

#                     st.write(f"**Times/Location for {d}**")
#                     col_a, col_b = st.columns(2)

#                     new_start = col_a.time_input(
#                         f"{editing_id}_{d}_start",
#                         value=default_start,
#                         key=f"{editing_id}_{d}_start_key"
#                     )
#                     col_a.write(f"Starts at: **{new_start.strftime('%I:%M %p').lstrip('0')}**")

#                     new_end = col_a.time_input(
#                         f"{editing_id}_{d}_end",
#                         value=default_end,
#                         key=f"{editing_id}_{d}_end_key"
#                     )
#                     col_a.write(f"Ends at: **{new_end.strftime('%I:%M %p').lstrip('0')}**")

#                     new_loc = col_b.text_input(
#                         f"{editing_id}_{d}_loc",
#                         value=default_loc,
#                         key=f"{editing_id}_{d}_loc_key"
#                     )

#                     new_days_times.append({
#                         "day": d,
#                         "start_time": str(new_start),
#                         "end_time": str(new_end),
#                         "location": new_loc
#                     })

#                 edited_location = None
#             save_col, cancel_col = st.columns(2)

#             # Save Changes button
#             with save_col:
#                 if st.button("Save Changes", key=f"save_changes_btn_{sid}"):
#                     updates = {
#                         "title": new_title,
#                         "recurrence": new_recurrence,
#                         "notes": new_notes,
#                         "updated_by_username": st.session_state.get("username", "Unknown"),
#                         "updated_at": datetime.utcnow()
#                     }

#                     if new_recurrence == "None":
#                         updates["days_times"] = []
#                         s_dt = datetime.combine(edited_start_date, edited_start_time)
#                         e_dt = datetime.combine(edited_end_date, edited_end_time)
#                         updates["start_datetime"] = s_dt
#                         updates["end_datetime"] = e_dt
#                         updates["location"] = edited_location
#                     else:
#                         updates["days_times"] = new_days_times
#                         updates["start_datetime"] = None
#                         updates["end_datetime"] = None
#                         updates.pop("location", None)

#                     success = update_schedule(editing_id, updates)
#                     if success:
#                         st.success("Schedule updated.")

#                         # Build a doc for the notification email
#                         updated_doc = {
#                             "program_id": old_program_id,
#                             "title": new_title,
#                             "recurrence": new_recurrence,
#                             "notes": new_notes,
#                             "days_times": new_days_times if new_recurrence != "None" else [],
#                             "location": edited_location if new_recurrence == "None" else None,
#                         }
#                         notify_schedule_change(
#                             program_id=old_program_id,
#                             schedule_doc=updated_doc,
#                             event_type="updated"
#                         )
#                     else:
#                         st.error("No changes made, or update failed.")

#                     st.session_state.pop("editing_schedule", None)
#                     st.rerun()
#             with cancel_col:
#                 if st.button("Cancel Edit", key=f"cancel_edit_btn_{sid}"):
#                     # Remove the editing_schedule from session state
#                     st.session_state.pop("editing_schedule", None)
#                     st.success("Edit canceled")
#                     st.rerun()

# def page_take_attendance():
#     st.header("Take Attendance")

#     # -----------------------------------------------------------------
#     # 1) Determine if user is admin or instructor; filter programs
#     # -----------------------------------------------------------------
#     is_admin = st.session_state.get("is_admin", False)
#     all_programs = list_programs()  # e.g. from instructors_db
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#     if is_admin:
#         # Admin can pick any program or "All"
#         program_choices = [(None, "All Programs")] + [(p["program_id"], p["program_name"]) for p in all_programs]
#         selected_prog_id = st.selectbox(
#             "Select Program:",
#             options=[pc[0] for pc in program_choices],
#             format_func=lambda pid: "All Programs" if pid is None else prog_map[pid]
#         )

#         if selected_prog_id is None:
#             # Admin sees all students
#             students = get_all_students()
#         else:
#             # Admin sees only students in the chosen program
#             students = get_all_students(program_ids=[selected_prog_id])

#     else:
#         # Instructor sees only their assigned programs
#         permitted_ids = st.session_state.get("instructor_program_ids", [])
#         if not permitted_ids:
#             st.info("No assigned programs found. Contact an admin for access.")
#             return
#         students = get_all_students(program_ids=permitted_ids)

#     if not students:
#         st.info("No students found. (Check whether you have assigned programs or student data.)")
#         return

#     # -----------------------------------------------------------------
#     # 2) Create Tabs: [ "Attendance (Today)" | "Record Past Session" ]
#     # -----------------------------------------------------------------
#     tab_labels = ["Attendance (Today)", "Record Past Session"]
#     tabs = st.tabs(tab_labels)

#     # --------------- TAB 1: Attendance (Today) ---------------
#     with tabs[0]:
#         st.subheader("Today’s Attendance")

#         # We'll use a color-coded or emoji-labeled radio for statuses:
#         # "✅ Present", "🕑 Late", "🚫 Absent"
#         status_options_today = ["✅ Present", "🕑 Late", "🚫 Absent"]
#         status_map_today = {
#             "✅ Present": "Present",
#             "🕑 Late": "Late",
#             "🚫 Absent": "Absent"
#         }

#         # Build a form to handle all students at once
#         with st.form("attendance_today_form"):
#             attendance_dict = {}

#             for s in students:
#                 sid = s.get("student_id")
#                 name = s.get("name", "")
#                 pid = s.get("program_id", 0)

#                 prog_name = prog_map.get(pid, f"Program ID={pid}")

#                 st.subheader(f"{name} — {prog_name}")

#                 chosen_emoji_label = st.radio(
#                     "Status:",
#                     options=status_options_today,
#                     index=0,
#                     key=f"{sid}_radio_today"
#                 )
#                 comment = st.text_input("Comment (Optional)", key=f"{sid}_comment_today")

#                 # Convert from emoji-labeled to DB status
#                 final_status = status_map_today[chosen_emoji_label]

#                 attendance_dict[sid] = {
#                     "name": name,
#                     "program_id": pid,
#                     "status": final_status,
#                     "comment": comment
#                 }

#             submitted_today = st.form_submit_button("Submit Attendance")

#         if submitted_today:
#             # Process each student's chosen status
#             for sid, data in attendance_dict.items():
#                 name = data["name"]
#                 prog_id = data["program_id"]
#                 status = data["status"]
#                 comment = data["comment"]

#                 try:
#                     result_msg = record_student_attendance_in_array(name, prog_id, status, comment)
#                     st.write(f"{name} – Marked {status}: {result_msg}")
#                 except Exception as e:
#                     st.error(f"Error for {name}: {e}")

#             st.success("All attendance data submitted for today!")

#     # --------------- TAB 2: Record Past Session ---------------
#     with tabs[1]:
#         st.subheader("Record Past Session")

#         # Let user pick date/time
#         session_date = st.date_input("Session Date", value=date.today())
#         session_time = st.time_input("Session Start Time", value=time(9, 0))
#         chosen_datetime = datetime.combine(session_date, session_time)

#         st.write(f"**Selected Date/Time**: {session_date} at {session_time.strftime('%I:%M %p')}")

#         # Past statuses can include "Excused" as well
#         status_options_past = ["✅ Present", "🕑 Late", "🚫 Absent", "🤝 Excused"]
#         status_map_past = {
#             "✅ Present": "Present",
#             "🕑 Late": "Late",
#             "🚫 Absent": "Absent",
#             "🤝 Excused": "Excused"
#         }

#         # Optional "Mark All Present"
#         if "past_defaults" not in st.session_state:
#             st.session_state["past_defaults"] = {}

#         if st.button("Mark All Present for Past Session"):
#             for s in students:
#                 sid = s["student_id"]
#                 # We'll store "✅ Present" so the radio default matches it
#                 st.session_state["past_defaults"][sid] = "✅ Present"
#             st.rerun()

#         # Build a form to finalize each student's status
#         with st.form("past_attendance_form"):
#             past_data = {}

#             for s in students:
#                 sid = s.get("student_id")
#                 name = s.get("name", "")
#                 pid = s.get("program_id", 0)
#                 prog_name = prog_map.get(pid, f"ProgID={pid}")

#                 default_emoji = st.session_state["past_defaults"].get(sid, "🚫 Absent")

#                 st.write(f"**{name}** — {prog_name}")
#                 chosen_emoji_label = st.radio(
#                     "Status",
#                     options=status_options_past,
#                     index=status_options_past.index(default_emoji),
#                     key=f"past_{sid}_radio"
#                 )

#                 comment_val = st.text_input("Comment (Optional)", key=f"past_comment_{sid}")

#                 final_status = status_map_past[chosen_emoji_label]
#                 past_data[sid] = {
#                     "name": name,
#                     "program_id": pid,
#                     "status": final_status,
#                     "comment": comment_val
#                 }

#             submitted_past = st.form_submit_button("Submit Past Attendance")

#         if submitted_past:
#             # Process each student's chosen status for the selected datetime
#             for sid, data in past_data.items():
#                 record_student_attendance_in_array(
#                     name=data["name"],
#                     program_id=data["program_id"],
#                     status=data["status"],
#                     comment=data["comment"],
#                     attendance_date=chosen_datetime
#                 )
#             st.success(f"Past attendance recorded for {chosen_datetime}!")
#             # Clear any defaults
#             st.session_state["past_defaults"] = {}

# #####################
# # PAGE: Review Attendance
# #####################

# def page_review_attendance():
#     st.header("Review Attendance Logs")

#     # -------------------------------------------------------------
#     # A) Show summary metrics: This Week vs. Last Week
#     # -------------------------------------------------------------
#     now = datetime.utcnow()
#     seven_days_ago = now - timedelta(days=7)
#     fourteen_days_ago = now - timedelta(days=14)

#     # 1) "This Week" subdocs
#     subdocs_this_week = get_attendance_subdocs_in_range(seven_days_ago, now)
#     total_this_week = len(subdocs_this_week)

#     # 2) "Last Week" subdocs
#     subdocs_last_week = get_attendance_subdocs_in_range(fourteen_days_ago, seven_days_ago)
#     total_last_week = len(subdocs_last_week)
#     attendance_delta = total_this_week - total_last_week

#     # Admin vs. Instructor logic
#     is_admin = st.session_state.get("is_admin", False)
#     if is_admin:
#         all_students = get_all_students()  # Admin sees all
#     else:
#         # Instructors see only assigned programs
#         program_ids = st.session_state.get("instructor_program_ids", [])
#         all_students = get_all_students(program_ids=program_ids)

#     total_students = len(all_students)

#     # Get last week's student count from ObjectId logic
#     last_week_count = get_student_count_as_of_last_week()
#     student_delta = total_students - last_week_count

#     # Absent comparison
#     absent_this_week = sum(1 for r in subdocs_this_week if r["attendance"]["status"] == "Absent")
#     absent_last_week = sum(1 for r in subdocs_last_week if r["attendance"]["status"] == "Absent")
#     delta_absent = absent_this_week - absent_last_week

#     # -------------------------------------------------------------
#     # B) Display the top-level metrics
#     # -------------------------------------------------------------
#     # col1, col2, col3 = st.columns(3)
#     # with col1:
#     #     st.metric(
#     #         label="Attendance This Week",
#     #         value=total_this_week,
#     #         delta=f"{attendance_delta} vs. last week"
#     #     )
#     # with col2:
#     #     st.metric(
#     #         label="Absences This Week",
#     #         value=absent_this_week,
#     #         delta=f"{delta_absent} vs. last week"
#     #     )
#     # with col3:
#     #     st.metric(
#     #         label="Total Students",
#     #         value=total_students,
#     #         delta=f"{student_delta} vs. last week"
#     #     )

#     # st.write("---")

#     # -------------------------------------------------------------
#     # C) Tabs for “All Attendance” vs. “Missed Counts”
#     # -------------------------------------------------------------
#     # tab_labels = ["All Attendance", "Missed Counts"]
#     # tabs = st.tabs(tab_labels)

#     # with tabs[0]:
#     with st.expander("Show Missed Counts"):
#             show_missed_counts()

#     st.subheader("All Attendance Records")
#     show_attendance_logs()

#     # This calls your existing function to display logs
#     # e.g. show_attendance_logs() 
#     # (You might consider adding color-coded or emoji-coded statuses in that function.)
   

#     # with tabs[1]:
#     #     st.subheader("Missed Counts Overview")
#     #     # This calls your existing function for missed data
#     #     # e.g. show_missed_counts()
#     #     show_missed_counts()

# def show_attendance_logs():
#     # Initialize the edit state if not already done
#     if "edit_record_key" not in st.session_state:
#         st.session_state["edit_record_key"] = None
    
#     # ---------------------------------------------------------
#     # 1) Load attendance records from session cache or DB
#     # ---------------------------------------------------------
#     if "attendance_records" not in st.session_state or st.session_state["attendance_records"] is None:
#         try:
#             # Each record is like:
#             # {"student_id":..., "name":..., "program_id":..., 
#             #  "attendance":{"date":..., "status":..., "comment":...}}
#             records = get_all_attendance_subdocs()
#             st.session_state["attendance_records"] = records
#         except Exception as e:
#             st.error(f"Error fetching attendance logs: {e}")
#             st.session_state["attendance_records"] = []
#             return

#     logs = st.session_state["attendance_records"]
#     if not logs:
#         st.info("No attendance records found.")
#         return

#     # ---------------------------------------------------------
#     # 2) Admin or Instructor program filtering
#     # ---------------------------------------------------------
#     all_programs = list_programs()  # from instructors_db
#     prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
#     is_admin = st.session_state.get("is_admin", False)

#     if is_admin:
#         # Admin sees a program filter
#         program_choices = [(None, "All Programs")] + [
#             (p["program_id"], p["program_name"]) for p in all_programs
#         ]
#         selected_prog_id = st.selectbox(
#             "Filter by Program (Admin)",
#             options=[pc[0] for pc in program_choices],
#             format_func=lambda pid: "All Programs" if pid is None else prog_map[pid],
#         )
#         if selected_prog_id is not None:
#             logs = [
#                 r for r in logs
#                 if (r["program_id"] == selected_prog_id or selected_prog_id is None)
#             ]
#     else:
#         # Instructor sees only assigned programs
#         permitted_ids = st.session_state.get("instructor_program_ids", [])
#         logs = [r for r in logs if r.get("program_id") in permitted_ids]

#     if not logs:
#         st.info("No attendance records after program filtering.")
#         return

#     # ---------------------------------------------------------
#     # 3) Filter by Student Name
#     # ---------------------------------------------------------
#     all_names = sorted({doc.get("name", "Unknown") for doc in logs})
#     name_choice = st.selectbox(
#         "Filter by Student Name",
#         options=["All Students"] + all_names
#     )
#     if name_choice != "All Students":
#         logs = [doc for doc in logs if doc.get("name") == name_choice]

#     if not logs:
#         st.info("No attendance records found for that filter.")
#         return

#     # ---------------------------------------------------------
#     # 4) Display each record in an expander with color-coded/emoji status
#     # ---------------------------------------------------------
#     # We'll map "Present" -> "✅ Present", "Late" -> "🕑 Late", etc.
#     emoji_map = {
#         "Present": "✅ Present",
#         "Late": "🕑 Late",
#         "Absent": "🚫 Absent",
#         "Excused": "🤝 Excused"
#     }

#     for idx, doc in enumerate(logs):
#         att = doc.get("attendance", {})
#         date_val = att.get("date", "")
#         status_val = att.get("status", "")
#         comment_val = att.get("comment", "")
#         s_name = doc.get("name", "")
#         p_id = doc.get("program_id", 0)
#         student_id = doc.get("student_id", "?")

#         program_name = prog_map.get(p_id, f"Program ID={p_id}")
#         # Convert status to emoji label if recognized
#         display_status = emoji_map.get(status_val, status_val)

#         # Build a unique record key for tracking edit state
#         record_key = f"{student_id}_{date_val}"
        
#         # Check if this record is being edited
#         is_editing = st.session_state["edit_record_key"] == record_key
        
#         # Build a short label for the expander
#         expander_label = f"{s_name} | {program_name} | {date_val} | {display_status}"
        
#         # Determine if expander should be expanded (if editing)
#         with st.expander(expander_label, expanded=is_editing):
#             if not is_editing:
#                 # Normal view mode
#                 st.write(f"**Student ID:** {student_id}")
#                 st.write(f"**Date:** {date_val}")
#                 st.write(f"**Status:** {display_status}")
#                 if comment_val:
#                     st.write(f"**Comment:** {comment_val}")

#                 # Buttons for Delete / Edit
#                 colDel, colEdit = st.columns([1, 1])
                
#                 with colDel:
#                     if st.button("Delete", key=f"delete_btn_{idx}"):
#                         deleted = delete_attendance_subdoc(student_id, date_val)
#                         if deleted:
#                             st.success("Attendance record deleted.")
#                             st.session_state["attendance_records"] = None
#                         else:
#                             st.warning("No matching record found.")
#                         st.rerun()
                
#                 with colEdit:
#                     if st.button("Edit", key=f"edit_btn_{idx}"):
#                         # Set this record as the one being edited
#                         st.session_state["edit_record_key"] = record_key
#                         # Store the current values for the form
#                         st.session_state["edit_student_id"] = student_id
#                         st.session_state["edit_student_name"] = s_name
#                         st.session_state["edit_date"] = date_val
#                         st.session_state["edit_status"] = status_val
#                         st.session_state["edit_comment"] = comment_val
#                         st.rerun()
#             else:
#                 # Edit mode - show the form in the expander
#                 st.subheader("Edit Attendance Record")
                
#                 default_dt = st.session_state["edit_date"]
#                 if isinstance(default_dt, str):
#                     try:
#                         default_dt = parser.parse(default_dt)
#                     except:
#                         default_dt = datetime.now()
                
#                 with st.form("edit_form"):
#                     st.write(f"**Student Name**: {st.session_state['edit_student_name']}")
#                     st.write(f"**Student ID**: {st.session_state['edit_student_id']}")
#                     st.write(f"**Original Date**: {st.session_state['edit_date']}")
                    
#                     new_date = st.date_input("New Date", value=default_dt.date())
#                     new_time = st.time_input("New Time", value=default_dt.time())
#                     combined_dt = datetime.combine(new_date, new_time)
                    
#                     status_opts = ["Present", "Late", "Absent", "Excused"]
#                     try:
#                         default_idx = status_opts.index(st.session_state["edit_status"])
#                     except ValueError:
#                         default_idx = 0
                    
#                     new_status = st.selectbox("Status", status_opts, index=default_idx)
#                     new_comment = st.text_input("Comment", value=st.session_state["edit_comment"])
                    
#                     col1, col2 = st.columns([1, 1])
                    
#                     with col1:
#                         if st.form_submit_button("Save Changes"):
#                             success = upsert_attendance_subdoc(
#                                 student_id=st.session_state["edit_student_id"],
#                                 target_date=combined_dt, 
#                                 new_status=new_status,
#                                 new_comment=new_comment
#                             )
                            
#                             if success:
#                                 st.success(f"Attendance updated successfully.")
#                                 # If date changed, remove old record
#                                 old_date = st.session_state["edit_date"]
#                                 if isinstance(old_date, str):
#                                     old_date = parser.parse(old_date)
#                                 if combined_dt != old_date:
#                                     delete_attendance_subdoc(
#                                         st.session_state["edit_student_id"], 
#                                         st.session_state["edit_date"]
#                                     )
#                                 # Reset edit state and refresh records
#                                 st.session_state["edit_record_key"] = None
#                                 st.session_state["attendance_records"] = None
#                                 st.rerun()
#                             else:
#                                 st.error("Failed to update attendance record.")
                    
#                     with col2:
#                         if st.form_submit_button("Cancel"):
#                             # Reset edit state
#                             st.session_state["edit_record_key"] = None
#                             st.rerun()


####################
# PAGE: Instructor Login
####################
# def page_instructor_login():
#     col_left, col_center, col_right = st.columns([1, 5, 1])

#     with col_center:
#         st.header("Instructor Login")

#         if st.session_state.get("is_admin", False):
#             st.error("An admin is currently logged in. Please log out as admin first.")
#             return
#         if st.session_state.get("instructor_logged_in"):
#             st.info("You are already logged in as an instructor.")
#             return

#         username = st.text_input("Username (Instructor)")
#         password = st.text_input("Password", type="password")

#         if st.button("Login"):
#             result = authenticate_instructor(username, password)
#             if result:
#                 st.session_state.instructor_logged_in = True
#                 st.session_state.instructor_id = result["instructor_id"]
#                 st.session_state.instructor_username = username  # <-- Add this
#                 st.session_state.instructor_role = result["role"]

#                 # GET assigned programs from pivot
#                 assigned_progs = list_instructor_programs(result["instructor_id"])
#                 # Instead of storing the whole dict, store just the names:
#                 # permitted_names = [p["program_name"] for p in assigned_progs]  # <-- CHANGED
#                 # st.session_state.instructor_programs = permitted_names         # <-- CHANGED
#                 st.session_state.instructor_program_ids = [p["program_id"] for p in assigned_progs]


#                 st.success(f"Welcome, {username}! Role = {result['role']}")
#                 st.session_state.menu_choice = "Student Management Suite"

#                 st.rerun() 
#             else:
#                 st.error("Invalid username or password.")


# def page_manage_students():
#     # Initialize edit state if not already done
#     if "editing_student_id" not in st.session_state:
#         st.session_state["editing_student_id"] = None

#     # 1) Must be logged in (admin or instructor)
#     if not st.session_state.get("instructor_logged_in", False) and not st.session_state.get("is_admin", False):
#         st.error("🔒 You must be logged in to access this page.")
#         return

#     # We'll keep your center column layout if you prefer
#     col_left, col_center, col_right = st.columns([1, 5, 1])
#     with col_center:
#         st.header("👨‍🎓 Manage Students")

#         is_admin = st.session_state.get("is_admin", False)
#         user_role = "Administrator" if is_admin else "Instructor"
#         st.write(f"*Logged in as: {user_role}*")

#         # ----------------------------------------------------------
#         # A) Program Filter for Admin with improved UI
#         # ----------------------------------------------------------
#         st.markdown("### 🔍 Filter Students")

#         # Get all programs for reference
#         all_programs = list_programs()  # from instructors_db
#         prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

#         if is_admin:
#             # Build a list of (program_id, "program_name") pairs
#             program_choices = [(None, "All Programs")] + [
#                 (p["program_id"], p["program_name"]) for p in all_programs
#             ]

#             with st.container():
#                 selected_prog_id = st.selectbox(
#                     "Select Program to View:",
#                     options=[pc[0] for pc in program_choices],
#                     format_func=lambda pid: "All Programs" if pid is None else f"{prog_map[pid]} (ID: {pid})",
#                     help="As an admin, you can view students from all programs or filter by a specific program"
#                 )

#             if selected_prog_id is None:
#                 # Admin sees all students
#                 students = get_all_students()
#                 st.success(f"Showing all students from all programs")
#             else:
#                 # Admin sees only students in the chosen program
#                 students = get_all_students(program_ids=[selected_prog_id])
#                 st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")

#         else:
#             # Instructors see only their assigned programs
#             permitted_ids = st.session_state.get("instructor_program_ids", [])
#             if not permitted_ids:
#                 st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
#                 return

#             # Show a filter for instructors with multiple programs
#             if len(permitted_ids) > 1:
#                 program_choices = [(None, "All My Programs")] + [
#                     (pid, prog_map.get(pid, f"Program ID: {pid}")) for pid in permitted_ids
#                 ]

#                 selected_prog_id = st.selectbox(
#                     "Filter by Program:",
#                     options=[pc[0] for pc in program_choices],
#                     format_func=lambda pid: "All My Programs" if pid is None else f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                     help="Select a specific program or view all your assigned programs"
#                 )

#                 if selected_prog_id is None:
#                     # Instructor sees all their permitted programs
#                     students = get_all_students(program_ids=permitted_ids)
#                     program_names = [prog_map.get(pid, f"Program {pid}") for pid in permitted_ids]
#                     st.success(f"Showing students from all your assigned programs: {', '.join(program_names)}")
#                 else:
#                     # Instructor sees only the selected program
#                     students = get_all_students(program_ids=[selected_prog_id])
#                     st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")
#             else:
#                 # Instructor has only one program, so show all students from that program
#                 students = get_all_students(program_ids=permitted_ids)
#                 program_name = prog_map.get(permitted_ids[0], f"Program {permitted_ids[0]}")
#                 st.success(f"Showing students from your assigned program: {program_name}")

#         st.write("---")

#         if not students:
#             st.info("📌 No students found matching your criteria.")

#         # ----------------------------------------------------------
#         # B) Create Tabs: [ "View & Manage" | "Add / Update" ]
#         # ----------------------------------------------------------
#         tab_labels = ["👀 View & Manage", "➕ Add or Update"]
#         tabs = st.tabs(tab_labels)

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 1: VIEW & MANAGE CURRENT STUDENTS
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[0]:
#             st.subheader("Current Students")

#             # Help expander
#             with st.expander("ℹ️ How to manage students", expanded=False):
#                 st.markdown("""
#                 ### Managing Students:
#                 - **View:** Each student is displayed with their basic information
#                 - **Delete:** Remove a student from the database (requires confirmation)
#                 - **Edit:** Update a student's information directly within the student card
#                 - **Mark Attendance:** Record attendance for today
#                 - **Mark Past Attendance:** Record attendance for a previous date

#                 All changes are saved immediately to the database.
#                 """)

#             if students:
#                 st.write(f"Total students: {len(students)}")

#                 # Add a search box for filtering students by name
#                 search_term = st.text_input(
#                     "🔍 Search students by name:",
#                     help="Type a name to filter the list of students"
#                 )

#                 # Filter students by search term if provided
#                 if search_term:
#                     filtered_students = [s for s in students if search_term.lower() in s.get("name", "").lower()]
#                     if not filtered_students:
#                         st.info(f"No students found matching '{search_term}'")
#                     students_to_display = filtered_students
#                 else:
#                     students_to_display = students

#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 # INDIVIDUAL ATTENDANCE LOGIC - Outside the student loop
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 attendance_placeholder = st.empty()

#                 for i, s in enumerate(students_to_display):
#                     student_id = s.get("student_id")
#                     name = s.get("name", "")
#                     phone = s.get("phone", "")
#                     contact_email = s.get("contact_email", "")
#                     prog_id = s.get("program_id", None)
#                     grade = s.get("grade", "")
#                     school = s.get("school", "")

#                     # Get program name for display
#                     program_name = prog_map.get(prog_id, f"Program ID: {prog_id}")

#                     # Check if this student is currently being edited
#                     is_editing = st.session_state["editing_student_id"] == student_id

#                     # Create a card-like container for each student
#                     with st.container():
#                         # Use an expander for each student to save space
#                         # Automatically expand if this student is being edited
#                         with st.expander(f"**{name}** - {program_name}", expanded=is_editing):
#                             if not is_editing:
#                                 # Normal view mode
#                                 # Create two columns - one for info, one for actions
#                                 col_info, col_actions = st.columns([3, 1])

#                                 with col_info:
#                                     st.markdown(f"**Student ID:** {student_id}")
#                                     st.markdown(f"**Program:** {program_name}")
#                                     st.markdown(f"**Grade:** {grade}")
#                                     st.markdown(f"**School:** {school}")
#                                     st.markdown(f"**Contact:** {contact_email}")
#                                     st.markdown(f"**Phone:** {phone}")

#                                 with col_actions:
#                                     # Group the buttons into a more organized layout
#                                     st.write("**Actions:**")

#                                     # Edit Button
#                                     if st.button("✏️ Edit", key=f"btn_edit_{student_id}",
#                                                  help=f"Edit information for {name}"):
#                                         st.session_state["editing_student_id"] = student_id
#                                         st.session_state["edit_data"] = s
#                                         st.rerun()

#                                     # Attendance Buttons
#                                     if st.button("✅ Mark Today", key=f"btn_attendance_{student_id}",
#                                                  help=f"Record today's attendance for {name}"):
#                                         st.session_state["attendance_student"] = s
#                                         st.rerun()

#                                     if st.button("📆 Mark Past", key=f"btn_attendance_past_{student_id}",
#                                                  help=f"Record past attendance for {name}"):
#                                         st.session_state["attendance_student"] = s
#                                         st.session_state["attendance_mode"] = "past"
#                                         st.rerun()

#                                     # Delete Button
#                                     if st.button("🗑️ Delete", key=f"btn_delete_{student_id}",
#                                                  help=f"Permanently delete {name} from the database"):
#                                         # Add a confirmation step to prevent accidental deletions
#                                         st.warning(f"Are you sure you want to delete {name}?")

#                                         # ------------- FIX: No nested st.columns -------------
#                                         # Instead of columns, use two separate buttons:
#                                         cancel_btn = st.button("Cancel", key=f"cancel_delete_{student_id}")
#                                         confirm_btn = st.button("Confirm Delete", key=f"confirm_delete_{student_id}")

#                                         if cancel_btn:
#                                             st.rerun()

#                                         if confirm_btn:
#                                             # Instructors must only delete if the student's program_id is in permitted_ids
#                                             if not is_admin:
#                                                 perm_ids = st.session_state.get("instructor_program_ids", [])
#                                                 if prog_id not in perm_ids:
#                                                     st.error("⛔ You are not permitted to delete students in this program.")
#                                                     st.stop()

#                                             with st.spinner(f"Deleting {name}..."):
#                                                 success = delete_student_record(student_id)
#                                                 if success:
#                                                     # st.session_state["students_list"] = None

#                                                     st.success(f"✅ Deleted student {name} (ID={student_id}).")
#                                                     st.rerun()
                                                    
#                                                 else:
#                                                     st.error("❌ Delete failed or no such student.")

#                             else:
#                                 # Edit mode within the expander
#                                 st.subheader(f"✏️ Edit Student Information")

#                                 # Get the student data from session state
#                                 edited_stud = st.session_state["edit_data"]

#                                 # Guard against editing a student in a program the instructor doesn't have
#                                 if not is_admin:
#                                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                                     if edited_stud.get("program_id") not in perm_ids:
#                                         st.error("⛔ You do not have permission to edit students in this program.")
#                                         if st.button("OK"):
#                                             st.session_state["editing_student_id"] = None
#                                             st.rerun()

#                                 with st.form(f"edit_student_form_{student_id}"):
#                                     col1, col2 = st.columns(2)

#                                     with col1:
#                                         new_name = st.text_input("Name *", value=edited_stud.get("name", ""))
#                                         new_phone = st.text_input("Phone", value=edited_stud.get("phone", ""))
#                                         new_email = st.text_input("Contact Email", value=edited_stud.get("contact_email", ""))

#                                     with col2:
#                                         new_grade = st.text_input("Grade", value=edited_stud.get("grade", ""))
#                                         new_school = st.text_input("School", value=edited_stud.get("school", ""))

#                                         # If admin, let them pick a new program
#                                         if is_admin:
#                                             all_progs = list_programs()
#                                             prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                                             prog_ids = list(prog_map.keys())

#                                             current_pid = edited_stud.get("program_id")
#                                             if current_pid not in prog_ids:
#                                                 prog_index = 0
#                                             else:
#                                                 prog_index = prog_ids.index(current_pid)

#                                             selected_id = st.selectbox(
#                                                 "Select Program:",
#                                                 options=prog_ids,
#                                                 format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
#                                                 index=prog_index
#                                             )
#                                             new_program_id = selected_id
#                                         else:
#                                             perm_ids = st.session_state.get("instructor_program_ids", [])
#                                             current_pid = edited_stud.get("program_id")
#                                             if current_pid not in perm_ids and perm_ids:
#                                                 current_pid = perm_ids[0]
#                                             new_program_id = st.selectbox(
#                                                 "Select Program:",
#                                                 options=perm_ids,
#                                                 format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                                                 index=perm_ids.index(current_pid) if current_pid in perm_ids else 0
#                                             )

#                                     st.markdown("**Required fields are marked with * **")

#                                     col_cancel, col_save = st.columns(2)

#                                     with col_cancel:
#                                         cancel_btn = st.form_submit_button("Cancel")

#                                     with col_save:
#                                         submit_btn = st.form_submit_button("Save Changes")

#                                     if submit_btn:
#                                         if not new_name.strip():
#                                             st.error("❌ Name is required.")
#                                         else:
#                                             with st.spinner("Updating student information..."):
#                                                 try:
#                                                     msg = update_student_info(
#                                                         student_id=edited_stud["student_id"],
#                                                         new_name=new_name,
#                                                         new_phone=new_phone,
#                                                         new_contact_email=new_email,
#                                                         # program_id=new_program_id,
#                                                         new_grade=new_grade,
#                                                         new_school=new_school
#                                                     )
#                                                     st.success(f"✅ {msg}")
#                                                     st.session_state["editing_student_id"] = None
#                                                     st.rerun()
#                                                 except Exception as e:
#                                                     st.error(f"❌ Error updating student: {e}")

#                                     if cancel_btn:
#                                         st.session_state["editing_student_id"] = None
#                                         st.rerun()

#                         # Add a visual separator between students
#                         if i < len(students_to_display) - 1:
#                             st.write("---")

#                 # Handle attendance forms - placed outside the student loop to avoid UI conflicts
#                 if "attendance_student" in st.session_state:
#                     with attendance_placeholder.container():
#                         st.write("---")
#                         st.subheader("📝 Attendance Recording")

#                         single_stud = st.session_state["attendance_student"]
#                         mode = st.session_state.get("attendance_mode", "today")

#                         if mode == "today":
#                             with st.form("today_attendance_form"):
#                                 st.write(f"**Recording attendance for: {single_stud['name']}**")
#                                 current_dt = datetime.now()
#                                 st.write(f"Date: {current_dt.strftime('%Y-%m-%d')}")
#                                 st.write(f"Time: {current_dt.strftime('%H:%M')}")

#                                 status_opt = ["Present", "Late", "Absent", "Excused"]
#                                 status_icons = ["✅", "🕒", "❌", "🔖"]
#                                 status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]

#                                 selected_status_idx = st.selectbox(
#                                     "Status:",
#                                     options=range(len(status_opt)),
#                                     format_func=lambda i: status_options_with_icons[i],
#                                     index=0
#                                 )
#                                 chosen_status = status_opt[selected_status_idx]

#                                 comment_txt = st.text_area("Comment (Optional)", height=100)

#                                 col1, col2 = st.columns(2)
#                                 with col1:
#                                     cancel_btn = st.form_submit_button("Cancel")

#                                 with col2:
#                                     submit_btn = st.form_submit_button("Submit Attendance")

#                                 if submit_btn:
#                                     with st.spinner("Recording attendance..."):
#                                         try:
#                                             msg = record_student_attendance_in_array(
#                                                 name=single_stud["name"],
#                                                 program_id=single_stud["program_id"],
#                                                 status=chosen_status,
#                                                 comment=comment_txt,
#                                                 attendance_date=current_dt
#                                             )
#                                             st.success(f"✅ Marked {single_stud['name']} as {chosen_status}. {msg}")
#                                         except Exception as e:
#                                             st.error(f"❌ Error: {e}")

#                                         st.session_state.pop("attendance_student")
#                                         st.session_state.pop("attendance_mode", None)
#                                         st.rerun()

#                                 if cancel_btn:
#                                     st.session_state.pop("attendance_student")
#                                     st.session_state.pop("attendance_mode", None)
#                                     st.info("ℹ️ Individual attendance marking canceled.")
#                                     st.rerun()

#                         elif mode == "past":
#                             with st.form("past_attendance_form_students"):
#                                 st.write(f"**Recording past attendance for: {single_stud['name']}**")

#                                 date_val = st.date_input("Session Date", value=date.today())
#                                 time_val = st.time_input("Session Time", value=time(9, 0))
#                                 combined_dt = datetime.combine(date_val, time_val)

#                                 status_opt = ["Present", "Late", "Absent", "Excused"]
#                                 status_icons = ["✅", "🕒", "❌", "🔖"]
#                                 status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]

#                                 selected_status_idx = st.selectbox(
#                                     "Status:",
#                                     options=range(len(status_opt)),
#                                     format_func=lambda i: status_options_with_icons[i],
#                                     index=0
#                                 )
#                                 chosen_status = status_opt[selected_status_idx]

#                                 comment_txt = st.text_area("Comment (Optional)", height=100)

#                                 col1, col2 = st.columns(2)
#                                 with col1:
#                                     cancel_btn = st.form_submit_button("Cancel")

#                                 with col2:
#                                     submit_btn = st.form_submit_button("Submit Past Attendance")

#                                 if submit_btn:
#                                     with st.spinner("Recording past attendance..."):
#                                         try:
#                                             msg = record_student_attendance_in_array(
#                                                 name=single_stud["name"],
#                                                 program_id=single_stud["program_id"],
#                                                 status=chosen_status,
#                                                 comment=comment_txt,
#                                                 attendance_date=combined_dt
#                                             )
#                                             st.success(
#                                                 f"✅ Marked {single_stud['name']} as {chosen_status} on "
#                                                 f"{combined_dt.strftime('%Y-%m-%d %H:%M')}. {msg}"
#                                             )
#                                         except Exception as e:
#                                             st.error(f"❌ Error: {e}")

#                                         st.session_state.pop("attendance_student")
#                                         st.session_state.pop("attendance_mode", None)
#                                         st.rerun()

#                                 if cancel_btn:
#                                     st.session_state.pop("attendance_student")
#                                     st.session_state.pop("attendance_mode", None)
#                                     st.info("ℹ️ Past attendance marking canceled.")
#                                     st.rerun()
#             # End if students

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 2: ADD OR UPDATE STUDENTS (Single or Bulk)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[1]:
#             st.subheader("Add or Update Students")

#             # Help expander
#             with st.expander("ℹ️ How to add students", expanded=False):
#                 st.markdown("""
#                 ### Adding Students:
#                 - **Single Student Entry:** Add one student at a time with complete details
#                 - **Bulk CSV Upload:** Upload multiple students at once using a CSV file

#                 #### CSV Format Requirements:
#                 Your CSV file should include these columns:
#                 - First Name
#                 - Last Name
#                 - Number (phone)
#                 - Email
#                 - Grade
#                 - School

#                 The program ID will be applied to all students in the CSV.
#                 """)

#             # We keep your radio approach to switch Single / Bulk
#             action = st.radio(
#                 "Choose method:",
#                 ["Single Student Entry", "Bulk CSV Upload"],
#                 horizontal=True,
#                 help="Choose how you want to add students to the system"
#             )

#             if action == "Single Student Entry":
#                 st.write("### Add a New Student")

#                 with st.form("student_form"):
#                     col1, col2 = st.columns(2)

#                     with col1:
#                         name_val = st.text_input("Name *", "", help="Student's full name")
#                         phone_val = st.text_input("Phone", "", help="Contact phone number")
#                         contact_val = st.text_input("Contact Email", "", help="Email address for the student or parent")

#                     with col2:
#                         grade_val = st.text_input("Grade", "", help="Student's current grade level")
#                         school_val = st.text_input("School", "", help="Student's school name")

#                         # Program selection based on user role
#                         if is_admin:
#                             all_progs = list_programs()
#                             if not all_progs:
#                                 st.warning("⚠️ No programs found in database.")
#                                 st.stop()

#                             prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                             selected_id = st.selectbox(
#                                 "Select Program *:",
#                                 options=prog_map.keys(),
#                                 format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})"
#                             )
#                             prog_val = selected_id
#                         else:
#                             perm_ids = st.session_state.get("instructor_program_ids", [])
#                             if not perm_ids:
#                                 st.warning("⚠️ No assigned programs available.")
#                                 prog_val = None
#                             else:
#                                 prog_val = st.selectbox(
#                                     "Select Program *:",
#                                     options=perm_ids,
#                                     format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}"
#                                 )

#                     st.markdown("**Required fields are marked with * **")

#                     submitted = st.form_submit_button("Save Student")
#                     if submitted:
#                         if not name_val.strip():
#                             st.error("❌ Name is required.")
#                         elif prog_val is None:
#                             st.error("❌ No valid program selected.")
#                         else:
#                             with st.spinner("Saving student information..."):
#                                 result = store_student_record(
#                                     name_val, phone_val, contact_val, prog_val,
#                                     grade=grade_val, school=school_val
#                                 )
#                                 st.success(f"✅ {result}")
#                                 if result != '':
#                                     st.rerun()

#             else:
#                 # Bulk CSV Upload
#                 st.write("### Bulk Upload Students")

#                 # Step 1: Select Program
#                 st.markdown("#### 1️⃣ Select Program")
#                 st.write("All students in the CSV will be assigned to this program:")

#                 if is_admin:
#                     all_progs = list_programs()
#                     if not all_progs:
#                         st.warning("⚠️ No programs found in database.")
#                         st.stop()

#                     prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=prog_map.keys(),
#                         format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
#                         key="csv_upload_program_selector_admin"
#                     )
#                 else:
#                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                     if not perm_ids:
#                         st.warning("⚠️ No assigned programs available.")
#                         st.stop()
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=perm_ids,
#                         format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                         key="csv_upload_program_selector"
#                     )

#                 # Step 2: Upload File
#                 st.markdown("#### 2️⃣ Upload CSV File")
#                 st.write("Upload a CSV file with student information:")

#                 # Sample template
#                 st.markdown("""
#                 Need a template? Here's a sample CSV format:
#                 ```
#                 First Name,Last Name,Number,Email,Grade,School
#                 John,Doe,555-123-4567,john.doe@email.com,10,Lincoln High
#                 Jane,Smith,555-987-6543,jane.smith@email.com,11,Washington High
#                 ```
#                 """)

#                 uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])

#                 if uploaded_file:
#                     # Step 3: Preview and Process
#                     st.markdown("#### 3️⃣ Preview and Process")

#                     with st.spinner("Reading CSV data..."):
#                         df = pd.read_csv(uploaded_file)

#                     # Preview in a clean format
#                     st.write("Preview of first 5 rows:")
#                     st.dataframe(df.head(), use_container_width=True)

#                     # Check for required columns
#                     required_cols = {"First Name", "Last Name", "Number", "Email", "Grade", "School"}
#                     missing_cols = required_cols - set(df.columns)

#                     if missing_cols:
#                         st.error(f"❌ CSV is missing required columns: {', '.join(missing_cols)}")
#                         st.info(f"Required columns are: {', '.join(required_cols)}")
#                     else:
#                         total_rows = len(df)
#                         st.write(f"Total records to process: {total_rows}")

#                         # Process button with progress indication
#                         if st.button("🔄 Process CSV Data"):
#                             # Progress bar
#                             progress_bar = st.progress(0)
#                             status_text = st.empty()

#                             successes = 0
#                             failures = 0
#                             messages = []

#                             for idx, row in df.iterrows():
#                                 # Update progress
#                                 progress = int((idx + 1) / total_rows * 100)
#                                 progress_bar.progress(progress)
#                                 status_text.text(f"Processing row {idx+1} of {total_rows}...")

#                                 try:
#                                     first_name = str(row["First Name"]).strip()
#                                     last_name = str(row["Last Name"]).strip()
#                                     name_val = f"{first_name} {last_name}".strip()

#                                     phone_val = row["Number"]
#                                     contact_val = row["Email"]
#                                     grade_val = row["Grade"]
#                                     school_val = row["School"]

#                                     # Instructors can only upload if the CSV's program_id is in their assigned list
#                                     if not is_admin:
#                                         perm_ids = st.session_state.get("instructor_program_ids", [])
#                                         if selected_prog_id not in perm_ids:
#                                             message = f"Row {idx+1}: Program ID '{selected_prog_id}' is not in your assigned list."
#                                             messages.append(message)
#                                             failures += 1
#                                             continue

#                                     result_msg = store_student_record(
#                                         name_val, phone_val, contact_val,
#                                         selected_prog_id, grade_val, school_val
#                                     )

#                                     if ("New student record" in result_msg) or ("updated" in result_msg):
#                                         successes += 1
#                                         messages.append(f"Row {idx+1}: {result_msg}")
#                                     else:
#                                         failures += 1
#                                         messages.append(f"Row {idx+1}: Failed - {result_msg}")

#                                 except Exception as e:
#                                     failures += 1
#                                     messages.append(f"Row {idx+1}: Error - {str(e)}")

#                             # Final update
#                             progress_bar.progress(100)
#                             status_text.text("Processing complete!")

#                             # Summary
#                             st.success(f"✅ Bulk upload complete. Successes: {successes}, Failures: {failures}")

#                             # Show detailed messages in an expander
#                             if messages:
#                                 with st.expander("View Processing Details", expanded=(failures > 0)):
#                                     for msg in messages:
#                                         if "Failed" in msg or "Error" in msg:
#                                             st.error(msg)
#                                         else:
#                                             st.success(msg)

#                             # Offer to refresh the page
#                             if st.button("View Updated Student List"):
#                                 st.rerun()

# def page_manage_students():
#     # Initialize edit state if not already done
#     if "editing_student_id" not in st.session_state:
#         st.session_state["editing_student_id"] = None
    
#     # 1) Must be logged in (admin or instructor)
#     if not st.session_state.get("instructor_logged_in", False) and not st.session_state.get("is_admin", False):
#         st.error("🔒 You must be logged in to access this page.")
#         return

#     # We'll keep your center column layout if you prefer
#     col_left, col_center, col_right = st.columns([1, 5, 1])
#     with col_center:
#         st.header("👨‍🎓 Manage Students")
        
#         is_admin = st.session_state.get("is_admin", False)
#         user_role = "Administrator" if is_admin else "Instructor"
#         st.write(f"*Logged in as: {user_role}*")

#         # ----------------------------------------------------------
#         # A) Program Filter for Admin with improved UI
#         # ----------------------------------------------------------
#         st.markdown("### 🔍 Filter Students")
        
#         # Get all programs for reference
#         all_programs = list_programs()  # from instructors_db
#         prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
        
#         if is_admin:
#             # Build a list of (program_id, "program_name") pairs
#             program_choices = [(None, "All Programs")] + [
#                 (p["program_id"], p["program_name"]) for p in all_programs
#             ]
            
#             with st.container():
#                 selected_prog_id = st.selectbox(
#                     "Select Program to View:",
#                     options=[pc[0] for pc in program_choices],
#                     format_func=lambda pid: "All Programs" if pid is None else f"{prog_map[pid]} (ID: {pid})",
#                     help="As an admin, you can view students from all programs or filter by a specific program"
#                 )

#             if selected_prog_id is None:
#                 # Admin sees all students
#                 students = get_all_students()
#                 st.success(f"Showing all students from all programs")
#             else:
#                 # Admin sees only students in the chosen program
#                 students = get_all_students(program_ids=[selected_prog_id])
#                 st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")

#         else:
#             # Instructors see only their assigned programs
#             permitted_ids = st.session_state.get("instructor_program_ids", [])
#             if not permitted_ids:
#                 st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
#                 return
                
#             # Show a filter for instructors with multiple programs
#             if len(permitted_ids) > 1:
#                 program_choices = [(None, "All My Programs")] + [
#                     (pid, prog_map.get(pid, f"Program ID: {pid}")) for pid in permitted_ids
#                 ]
                
#                 selected_prog_id = st.selectbox(
#                     "Filter by Program:",
#                     options=[pc[0] for pc in program_choices],
#                     format_func=lambda pid: "All My Programs" if pid is None else f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                     help="Select a specific program or view all your assigned programs"
#                 )
                
#                 if selected_prog_id is None:
#                     # Instructor sees all their permitted programs
#                     students = get_all_students(program_ids=permitted_ids)
#                     program_names = [prog_map.get(pid, f"Program {pid}") for pid in permitted_ids]
#                     st.success(f"Showing students from all your assigned programs: {', '.join(program_names)}")
#                 else:
#                     # Instructor sees only the selected program
#                     students = get_all_students(program_ids=[selected_prog_id])
#                     st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")
#             else:
#                 # Instructor has only one program, so show all students from that program
#                 students = get_all_students(program_ids=permitted_ids)
#                 program_name = prog_map.get(permitted_ids[0], f"Program {permitted_ids[0]}")
#                 st.success(f"Showing students from your assigned program: {program_name}")

#         st.write("---")

#         if not students:
#             st.info("📌 No students found matching your criteria.")

#         # ----------------------------------------------------------
#         # B) Create Tabs: [ "View & Manage" | "Add / Update" ]
#         # ----------------------------------------------------------
#         tab_labels = ["👀 View & Manage", "➕ Add or Update"]
#         tabs = st.tabs(tab_labels)

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 1: VIEW & MANAGE CURRENT STUDENTS
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[0]:
#             st.subheader("Current Students")
            
#             # Help expander
#             with st.expander("ℹ️ How to manage students", expanded=False):
#                 st.markdown("""
#                 ### Managing Students:
#                 - **View:** Each student is displayed with their basic information
#                 - **Delete:** Remove a student from the database (requires confirmation)
#                 - **Edit:** Update a student's information directly within the student card
#                 - **Mark Attendance:** Record attendance for today
#                 - **Mark Past Attendance:** Record attendance for a previous date
                
#                 All changes are saved immediately to the database.
#                 """)

#             if students:
#                 st.write(f"Total students: {len(students)}")
                
#                 # Add a search box for filtering students by name
#                 search_term = st.text_input("🔍 Search students by name:", 
#                                            help="Type a name to filter the list of students")
                
#                 # Filter students by search term if provided
#                 if search_term:
#                     filtered_students = [s for s in students if search_term.lower() in s.get("name", "").lower()]
#                     if not filtered_students:
#                         st.info(f"No students found matching '{search_term}'")
#                     students_to_display = filtered_students
#                 else:
#                     students_to_display = students
                
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 # INDIVIDUAL ATTENDANCE LOGIC - Outside the student loop
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 attendance_placeholder = st.empty()
                
#                 for i, s in enumerate(students_to_display):
#                     student_id = s.get("student_id")
#                     name = s.get("name", "")
#                     phone = s.get("phone", "")
#                     contact_email = s.get("contact_email", "")
#                     prog_id = s.get("program_id", None)
#                     grade = s.get("grade", "")
#                     school = s.get("school", "")
                    
#                     # Get program name for display
#                     program_name = prog_map.get(prog_id, f"Program ID: {prog_id}")
                    
#                     # Check if this student is currently being edited
#                     is_editing = st.session_state["editing_student_id"] == student_id

#                     # Create a card-like container for each student
#                     with st.container():
#                         # Use an expander for each student to save space
#                         # Automatically expand if this student is being edited
#                         with st.expander(f"**{name}** - {program_name}", expanded=is_editing):
#                             if not is_editing:
#                                 # Normal view mode
#                                 # Create two columns - one for info, one for actions
#                                 col_info, col_actions = st.columns([3, 1])
                                
#                                 with col_info:
#                                     st.markdown(f"**Student ID:** {student_id}")
#                                     st.markdown(f"**Program:** {program_name}")
#                                     st.markdown(f"**Grade:** {grade}")
#                                     st.markdown(f"**School:** {school}")
#                                     st.markdown(f"**Contact:** {contact_email}")
#                                     st.markdown(f"**Phone:** {phone}")
                                
#                                 with col_actions:
#                                     # Group the buttons into a more organized layout
#                                     st.write("**Actions:**")
                                    
#                                     # Edit Button
#                                     if st.button("✏️ Edit", key=f"btn_edit_{student_id}", 
#                                                 help=f"Edit information for {name}"):
#                                         st.session_state["editing_student_id"] = student_id
#                                         st.session_state["edit_data"] = s
#                                         st.rerun()
                                    
#                                     # Attendance Buttons
#                                     if st.button("✅ Mark Today", key=f"btn_attendance_{student_id}", 
#                                                help=f"Record today's attendance for {name}"):
#                                         st.session_state["attendance_student"] = s
#                                         st.rerun()
                                    
#                                     if st.button("📆 Mark Past", key=f"btn_attendance_past_{student_id}", 
#                                                help=f"Record past attendance for {name}"):
#                                         st.session_state["attendance_student"] = s
#                                         st.session_state["attendance_mode"] = "past"
#                                         st.rerun()
                                    
#                                     # Delete Button - with a different color to indicate danger
#                                     if st.button("🗑️ Delete", key=f"btn_delete_{student_id}", 
#                                                help=f"Permanently delete {name} from the database"):
#                                         # Add a confirmation step to prevent accidental deletions
#                                         st.warning(f"Are you sure you want to delete {name}?")
#                                         col_cancel, col_confirm = st.columns(2)
                                        
#                                         with col_cancel:
#                                             if st.button("Cancel", key=f"cancel_delete_{student_id}"):
#                                                 st.rerun()
                                                
#                                         with col_confirm:
#                                             if st.button("Confirm Delete", key=f"confirm_delete_{student_id}"):
#                                                 # Instructors must only delete if the student's program_id is in permitted_ids
#                                                 if not is_admin:
#                                                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                                                     if prog_id not in perm_ids:
#                                                         st.error("⛔ You are not permitted to delete students in this program.")
#                                                         st.stop()

#                                                 with st.spinner(f"Deleting {name}..."):
#                                                     success = delete_student_record(student_id)
#                                                     if success:
#                                                         st.success(f"✅ Deleted student {name} (ID={student_id}).")
#                                                         st.rerun()
#                                                     else:
#                                                         st.error("❌ Delete failed or no such student.")
#                             else:
#                                 # Edit mode within the expander
#                                 st.subheader(f"✏️ Edit Student Information")
                                
#                                 # Get the student data from session state
#                                 edited_stud = st.session_state["edit_data"]
                                
#                                 # Guard against editing a student in a program the instructor doesn't have
#                                 if not is_admin:
#                                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                                     if edited_stud.get("program_id") not in perm_ids:
#                                         st.error("⛔ You do not have permission to edit students in this program.")
#                                         if st.button("OK"):
#                                             st.session_state["editing_student_id"] = None
#                                             st.rerun()
                                
#                                 with st.form(f"edit_student_form_{student_id}"):
#                                     col1, col2 = st.columns(2)
                                    
#                                     with col1:
#                                         new_name = st.text_input("Name *", value=edited_stud.get("name", ""))
#                                         new_phone = st.text_input("Phone", value=edited_stud.get("phone", ""))
#                                         new_email = st.text_input("Contact Email", value=edited_stud.get("contact_email", ""))
                                    
#                                     with col2:
#                                         new_grade = st.text_input("Grade", value=edited_stud.get("grade", ""))
#                                         new_school = st.text_input("School", value=edited_stud.get("school", ""))
                                        
#                                         # If admin, let them pick a new program
#                                         if is_admin:
#                                             all_progs = list_programs()
#                                             prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                                             prog_ids = list(prog_map.keys())

#                                             current_pid = edited_stud.get("program_id")
#                                             if current_pid not in prog_ids:
#                                                 prog_index = 0
#                                             else:
#                                                 prog_index = prog_ids.index(current_pid)

#                                             selected_id = st.selectbox(
#                                                 "Select Program:",
#                                                 options=prog_ids,
#                                                 format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
#                                                 index=prog_index
#                                             )
#                                             new_program_id = selected_id
#                                         else:
#                                             perm_ids = st.session_state.get("instructor_program_ids", [])
#                                             current_pid = edited_stud.get("program_id")
#                                             if current_pid not in perm_ids and perm_ids:
#                                                 current_pid = perm_ids[0]
#                                             new_program_id = st.selectbox(
#                                                 "Select Program:",
#                                                 options=perm_ids,
#                                                 format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                                                 index=perm_ids.index(current_pid) if current_pid in perm_ids else 0
#                                             )
                                    
#                                     st.markdown("**Required fields are marked with * **")
                                    
#                                     col_cancel, col_save = st.columns(2)
                                    
#                                     with col_cancel:
#                                         cancel_btn = st.form_submit_button("Cancel")
                                        
#                                     with col_save:
#                                         submit_btn = st.form_submit_button("Save Changes")
                                    
#                                     if submit_btn:
#                                         if not new_name.strip():
#                                             st.error("❌ Name is required.")
#                                         else:
#                                             with st.spinner("Updating student information..."):
#                                                 try:
#                                                     msg = update_student_info(
#                                                         student_id=edited_stud["student_id"],
#                                                         new_name=new_name,
#                                                         new_phone=new_phone,
#                                                         new_contact_email=new_email,
#                                                         # program_id=new_program_id,
#                                                         new_grade=new_grade,
#                                                         new_school=new_school
#                                                     )
#                                                     st.success(f"✅ {msg}")
#                                                     st.session_state["editing_student_id"] = None
#                                                     st.rerun()
#                                                 except Exception as e:
#                                                     st.error(f"❌ Error updating student: {e}")
                                    
#                                     if cancel_btn:
#                                         st.session_state["editing_student_id"] = None
#                                         st.rerun()
                        
#                         # Add a visual separator between students
#                         if i < len(students_to_display) - 1:
#                             st.write("---")

#                 # Handle attendance forms - placed outside the student loop to avoid UI conflicts
#                 if "attendance_student" in st.session_state:
#                     with attendance_placeholder.container():
#                         st.write("---")
#                         st.subheader("📝 Attendance Recording")
                        
#                         single_stud = st.session_state["attendance_student"]
#                         mode = st.session_state.get("attendance_mode", "today")
                        
#                         if mode == "today":
#                             with st.form("today_attendance_form"):
#                                 st.write(f"**Recording attendance for: {single_stud['name']}**")
#                                 current_dt = datetime.now()
#                                 st.write(f"Date: {current_dt.strftime('%Y-%m-%d')}")
#                                 st.write(f"Time: {current_dt.strftime('%H:%M')}")
                                
#                                 status_opt = ["Present", "Late", "Absent", "Excused"]
#                                 status_icons = ["✅", "🕒", "❌", "🔖"]
#                                 status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]
                                
#                                 selected_status_idx = st.selectbox(
#                                     "Status:", 
#                                     options=range(len(status_opt)),
#                                     format_func=lambda i: status_options_with_icons[i],
#                                     index=0
#                                 )
#                                 chosen_status = status_opt[selected_status_idx]
                                
#                                 comment_txt = st.text_area("Comment (Optional)", height=100)
                                
#                                 col1, col2 = st.columns(2)
#                                 with col1:
#                                     cancel_btn = st.form_submit_button("Cancel")
                                    
#                                 with col2:
#                                     submit_btn = st.form_submit_button("Submit Attendance")
                                
#                                 if submit_btn:
#                                     with st.spinner("Recording attendance..."):
#                                         try:
#                                             msg = record_student_attendance_in_array(
#                                                 name=single_stud["name"],
#                                                 program_id=single_stud["program_id"],
#                                                 status=chosen_status,
#                                                 comment=comment_txt,
#                                                 attendance_date=current_dt
#                                             )
#                                             st.success(f"✅ Marked {single_stud['name']} as {chosen_status}. {msg}")
#                                         except Exception as e:
#                                             st.error(f"❌ Error: {e}")

#                                         st.session_state.pop("attendance_student")
#                                         st.session_state.pop("attendance_mode", None)
#                                         st.rerun()
                                        
#                                 if cancel_btn:
#                                     st.session_state.pop("attendance_student")
#                                     st.session_state.pop("attendance_mode", None)
#                                     st.info("ℹ️ Individual attendance marking canceled.")
#                                     st.rerun()

#                         elif mode == "past":
#                             with st.form("past_attendance_form_students"):
#                                 st.write(f"**Recording past attendance for: {single_stud['name']}**")
                                
#                                 date_val = st.date_input("Session Date", value=date.today())
#                                 time_val = st.time_input("Session Time", value=time(9, 0))
#                                 combined_dt = datetime.combine(date_val, time_val)
                                
#                                 status_opt = ["Present", "Late", "Absent", "Excused"]
#                                 status_icons = ["✅", "🕒", "❌", "🔖"]
#                                 status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]
                                
#                                 selected_status_idx = st.selectbox(
#                                     "Status:", 
#                                     options=range(len(status_opt)),
#                                     format_func=lambda i: status_options_with_icons[i],
#                                     index=0
#                                 )
#                                 chosen_status = status_opt[selected_status_idx]
                                
#                                 comment_txt = st.text_area("Comment (Optional)", height=100)
                                
#                                 col1, col2 = st.columns(2)
#                                 with col1:
#                                     cancel_btn = st.form_submit_button("Cancel")
                                    
#                                 with col2:
#                                     submit_btn = st.form_submit_button("Submit Past Attendance")
                                
#                                 if submit_btn:
#                                     with st.spinner("Recording past attendance..."):
#                                         try:
#                                             msg = record_student_attendance_in_array(
#                                                 name=single_stud["name"],
#                                                 program_id=single_stud["program_id"],
#                                                 status=chosen_status,
#                                                 comment=comment_txt,
#                                                 attendance_date=combined_dt
#                                             )
#                                             st.success(f"✅ Marked {single_stud['name']} as {chosen_status} on {combined_dt.strftime('%Y-%m-%d %H:%M')}. {msg}")
#                                         except Exception as e:
#                                             st.error(f"❌ Error: {e}")

#                                         st.session_state.pop("attendance_student")
#                                         st.session_state.pop("attendance_mode", None)
#                                         st.rerun()
                                        
#                                 if cancel_btn:
#                                     st.session_state.pop("attendance_student")
#                                     st.session_state.pop("attendance_mode", None)
#                                     st.info("ℹ️ Past attendance marking canceled.")
#                                     st.rerun()
#             # End if students

#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         # TAB 2: ADD OR UPDATE STUDENTS (Single or Bulk)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#         with tabs[1]:
#             st.subheader("Add or Update Students")
            
#             # Help expander
#             with st.expander("ℹ️ How to add students", expanded=False):
#                 st.markdown("""
#                 ### Adding Students:
#                 - **Single Student Entry:** Add one student at a time with complete details
#                 - **Bulk CSV Upload:** Upload multiple students at once using a CSV file
                
#                 #### CSV Format Requirements:
#                 Your CSV file should include these columns:
#                 - First Name
#                 - Last Name
#                 - Number (phone)
#                 - Email
#                 - Grade
#                 - School
                
#                 The program ID will be applied to all students in the CSV.
#                 """)

#             # We keep your radio approach to switch Single / Bulk
#             action = st.radio(
#                 "Choose method:",
#                 ["Single Student Entry", "Bulk CSV Upload"],
#                 horizontal=True,
#                 help="Choose how you want to add students to the system"
#             )

#             if action == "Single Student Entry":
#                 st.write("### Add a New Student")
                
#                 with st.form("student_form"):
#                     col1, col2 = st.columns(2)
                    
#                     with col1:
#                         name_val = st.text_input("Name *", "", help="Student's full name")
#                         phone_val = st.text_input("Phone", "", help="Contact phone number")
#                         contact_val = st.text_input("Contact Email", "", help="Email address for the student or parent")
                    
#                     with col2:
#                         grade_val = st.text_input("Grade", "", help="Student's current grade level")
#                         school_val = st.text_input("School", "", help="Student's school name")
                        
#                         # Program selection based on user role
#                         if is_admin:
#                             all_progs = list_programs()
#                             if not all_progs:
#                                 st.warning("⚠️ No programs found in database.")
#                                 st.stop()

#                             prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                             selected_id = st.selectbox(
#                                 "Select Program *:",
#                                 options=prog_map.keys(),
#                                 format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})"
#                             )
#                             prog_val = selected_id
#                         else:
#                             perm_ids = st.session_state.get("instructor_program_ids", [])
#                             if not perm_ids:
#                                 st.warning("⚠️ No assigned programs available.")
#                                 prog_val = None
#                             else:
#                                 prog_val = st.selectbox(
#                                     "Select Program *:",
#                                     options=perm_ids,
#                                     format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}"
#                                 )
                    
#                     st.markdown("**Required fields are marked with * **")
                    
#                     submitted = st.form_submit_button("Save Student")
#                     if submitted:
#                         if not name_val.strip():
#                             st.error("❌ Name is required.")
#                         elif prog_val is None:
#                             st.error("❌ No valid program selected.")
#                         else:
#                             with st.spinner("Saving student information..."):
#                                 result = store_student_record(
#                                     name_val, phone_val, contact_val, prog_val,
#                                     grade=grade_val, school=school_val
#                                 )
#                                 st.success(f"✅ {result}")
#                                 # Show a button to add another student
#                                 # submitted = st.form_submit_button("Save Student")

#                                 if result!= '':#st.button("Add Another Student", key="add_another_student_unique_key"):
#                                     st.rerun()

#             else:
#                 # Bulk CSV Upload
#                 st.write("### Bulk Upload Students")
                
#                 # Step 1: Select Program
#                 st.markdown("#### 1️⃣ Select Program")
#                 st.write("All students in the CSV will be assigned to this program:")
                
#                 if is_admin:
#                     all_progs = list_programs()
#                     if not all_progs:
#                         st.warning("⚠️ No programs found in database.")
#                         st.stop()

#                     prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=prog_map.keys(),
#                         format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
#                         key="csv_upload_program_selector_admin"  # Add this unique key

#                     )
#                 else:
#                     perm_ids = st.session_state.get("instructor_program_ids", [])
#                     if not perm_ids:
#                         st.warning("⚠️ No assigned programs available.")
#                         st.stop()
#                     selected_prog_id = st.selectbox(
#                         "Select Program for CSV Rows:",
#                         options=perm_ids,
#                         format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
#                         key="csv_upload_program_selector"  # Add this unique key

#                     )
                
#                 # Step 2: Upload File
#                 st.markdown("#### 2️⃣ Upload CSV File")
#                 st.write("Upload a CSV file with student information:")
                
#                 # Sample template
#                 st.markdown("""
#                 Need a template? Here's a sample CSV format:
#                 ```
#                 First Name,Last Name,Number,Email,Grade,School
#                 John,Doe,555-123-4567,john.doe@email.com,10,Lincoln High
#                 Jane,Smith,555-987-6543,jane.smith@email.com,11,Washington High
#                 ```
#                 """)
                
#                 uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])
                
#                 if uploaded_file:
#                     # Step 3: Preview and Process
#                     st.markdown("#### 3️⃣ Preview and Process")
                    
#                     with st.spinner("Reading CSV data..."):
#                         df = pd.read_csv(uploaded_file)
                        
#                     # Preview in a clean format
#                     st.write("Preview of first 5 rows:")
#                     st.dataframe(df.head(), use_container_width=True)
                    
#                     # Check for required columns
#                     required_cols = {"First Name", "Last Name", "Number", "Email", "Grade", "School"}
#                     missing_cols = required_cols - set(df.columns)
                    
#                     if missing_cols:
#                         st.error(f"❌ CSV is missing required columns: {', '.join(missing_cols)}")
#                         st.info(f"Required columns are: {', '.join(required_cols)}")
#                     else:
#                         total_rows = len(df)
#                         st.write(f"Total records to process: {total_rows}")
                        
#                         # Process button with progress indication
#                         if st.button("🔄 Process CSV Data"):
#                             # Progress bar
#                             progress_bar = st.progress(0)
#                             status_text = st.empty()
                            
#                             successes = 0
#                             failures = 0
#                             messages = []

#                             for idx, row in df.iterrows():
#                                 # Update progress
#                                 progress = int((idx + 1) / total_rows * 100)
#                                 progress_bar.progress(progress)
#                                 status_text.text(f"Processing row {idx+1} of {total_rows}...")
                                
#                                 try:
#                                     first_name = str(row["First Name"]).strip()
#                                     last_name = str(row["Last Name"]).strip()
#                                     name_val = f"{first_name} {last_name}".strip()

#                                     phone_val = row["Number"]
#                                     contact_val = row["Email"]
#                                     grade_val = row["Grade"]
#                                     school_val = row["School"]

#                                     # Instructors can only upload if the CSV's program_id is in their assigned list
#                                     if not is_admin:
#                                         perm_ids = st.session_state.get("instructor_program_ids", [])
#                                         if selected_prog_id not in perm_ids:
#                                             message = f"Row {idx+1}: Program ID '{selected_prog_id}' is not in your assigned list."
#                                             messages.append(message)
#                                             failures += 1
#                                             continue

#                                     result_msg = store_student_record(
#                                         name_val, phone_val, contact_val,
#                                         selected_prog_id, grade_val, school_val
#                                     )
                                    
#                                     if ("New student record" in result_msg) or ("updated" in result_msg):
#                                         successes += 1
#                                         messages.append(f"Row {idx+1}: {result_msg}")
#                                     else:
#                                         failures += 1
#                                         messages.append(f"Row {idx+1}: Failed - {result_msg}")
                                        
#                                 except Exception as e:
#                                     failures += 1
#                                     messages.append(f"Row {idx+1}: Error - {str(e)}")
                            
#                             # Final update
#                             progress_bar.progress(100)
#                             status_text.text("Processing complete!")
                            
#                             # Summary
#                             st.success(f"✅ Bulk upload complete. Successes: {successes}, Failures: {failures}")
                            
#                             # Show detailed messages in an expander
#                             if messages:
#                                 with st.expander("View Processing Details", expanded=(failures > 0)):
#                                     for msg in messages:
#                                         if "Failed" in msg or "Error" in msg:
#                                             st.error(msg)
#                                         else:
#                                             st.success(msg)
                            
#                             # Offer to refresh the page
#                             if st.button("View Updated Student List"):
#                                 st.rerun()
