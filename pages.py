

# pages.py

import streamlit as st
import pygwalker as pyg
from streamlit_extras.dataframe_explorer import dataframe_explorer
import streamlit.components.v1 as components
import sweetviz
import pandas as pd
from datetime import datetime, time, date,timedelta
from dateutil import parser
import plotly.express as px



from instructors_db import (
    initialize_tables,
    list_instructors,
    list_programs,
    add_program,
    assign_instructor_to_program,
    remove_instructor_from_program,
    list_instructor_programs,
    add_instructor,
    update_instructor_role,
    delete_instructor,
    authenticate_instructor,
    update_instructor_password
)

from students_db import (
    store_student_record,
    get_all_students,
    record_student_attendance_in_array,
    get_all_attendance_subdocs,
    delete_attendance_subdoc,       # <--- Import the new function
    upsert_attendance_subdoc,    
    get_missed_counts_for_all_students,
    delete_student_record,
    update_attendance_subdoc,
    fetch_all_attendance_records,
    update_student_info,
    get_student_count_as_of_last_week,
    get_attendance_subdocs_in_range,        # newly added
    get_attendance_subdocs_last_week 
)

from schedules_db import (
    create_schedule,
    list_schedules,
    update_schedule,
    delete_schedule
)


###################################
# UTILITY: Get permitted program NAMES
###################################


import streamlit as st
from datetime import datetime, time, date

def _format_time_12h(t):
    """
    Safely handle both a time object and a "HH:MM:SS" string.
    Returns a 12-hour formatted string like "9:00 AM".
    """
    from datetime import time

    if isinstance(t, str):
        # Parse "HH:MM:SS" (or "HH:MM") into a time object
        parts = t.split(":")
        if len(parts) == 2:
            hours, minutes = int(parts[0]), int(parts[1])
            seconds = 0
        else:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        t_obj = time(hours, minutes, seconds)
        return t_obj.strftime("%I:%M %p").lstrip("0")
    elif isinstance(t, time):
        # Already a time object
        return t.strftime("%I:%M %p").lstrip("0")
    else:
        # If it's not a str or time, just return it as-is or handle error
        return str(t)

def get_permitted_program_names():
    """
    Returns None if admin, or a list of strings (the program_name values)
    if instructor is logged in.
    """
    if st.session_state.get("is_admin", False):
        return None
    # We stored only a list of program_name strings in session
    return st.session_state.get("instructor_programs", [])


#####################
# PAGE: Manage Instructors
#####################
def page_manage_instructors():
    st.header("Manage Instructors - Normalized Programs")
    initialize_tables()
    Programs_Col, Instructors_Col = st.columns([2,2])
    with Programs_Col:
        with st.expander("Add a New Program"):
        # st.subheader("Add a New Program")
            with st.form("add_program_form"):
                # new_prog_name = st.text_input("New Program Name", "")
                new_prog_name = st.text_input("New Program Name", value="") #, key="prog_name_field"

                submitted_prog = st.form_submit_button("Create Program")

            if submitted_prog:#st.button("Create Program"):
                if new_prog_name.strip():
                    program_id = add_program(new_prog_name.strip())
                    if program_id == -1:
                        st.error("A program with that name already exists.")
                    else:
                        st.success(f"Program created (ID={program_id}).")
                        # st.session_state["prog_name_field"] = ""

                        
                        st.rerun()
                else:
                    st.warning("Program name cannot be empty.")
    with Instructors_Col:
        with st.expander("Add a New Instructor"):
        # st.subheader("Add a New Instructor")
            with st.form("add_instructor_form"):

                uname = st.text_input("Username") #, key="uname"
                pwd = st.text_input("Password", type="password") #, key="pwd"
                role = st.selectbox("Role", ["Instructor", "Manager", "Admin"]) #, key="role_select"
                submitted = st.form_submit_button("Create Instructor")

            if submitted:#st.button("Create Instructor", key="create_instructor"):
                success = add_instructor(uname, pwd, role)
                if success:
                    st.success("Instructor created successfully!")
                    st.rerun()
                    
                else:
                    st.error("User might already exist or an error occurred.")

        # st.subheader("Current Instructors")

    instructors = list_instructors()
    if not instructors:
        st.info("No instructors found.")
        st.stop()

    all_programs = list_programs()
    prog_dict = {p["program_id"]: p["program_name"] for p in all_programs}
    st.subheader("Current Instructors")
    for instr in instructors:
        instr_id = instr["instructor_id"]
        username = instr["username"]
        role = instr["role"]

        # Wrap each instructor’s controls in a collapsible expander
        with st.expander(f"{username} (ID={instr_id} | Role={role})"):
            # st.write(f"{username} (ID={instr_id} | Role={role})")
            
            # 1. Role Update
            st.write("### Update Role")
            col_role, col_mid, col_out = st.columns([3,1,1])
            
            with col_role:
                new_role = st.selectbox(
                    label="Select New Role",
                    options=["Instructor", "Manager", "Admin"],
                    index=["Instructor", "Manager", "Admin"].index(role),
                    key=f"role_{instr_id}"
                )
                if st.button("Update Role", key=f"btn_role_{instr_id}"):
                    update_instructor_role(instr_id, new_role)
                    st.success(f"Updated role for {username} to {new_role}.")
                    st.rerun()
            
            # with col_delete:
            if st.button(f"Delete Instructor", key=f"btn_delete_{instr_id}"):
                success = delete_instructor(instr_id)
                if success:
                    st.success(f"Instructor {username} deleted.")
                else:
                    st.error("Delete failed or instructor not found.")
                st.rerun()

            st.write("---")
            
            # 2. Assigned Programs
            st.write("### Assigned Programs")
            assigned = list_instructor_programs(instr_id)

            if not assigned:
                st.write("No programs assigned yet.")
            else:
                for a in assigned:
                    prog_id = a["program_id"]
                    prog_name = a["program_name"]

                    # One row with program label on left, 'Remove' button on right
                    c1, c2 = st.columns([4,1])
                    with c1:
                        st.write(f"- **{prog_name}** (ID={prog_id})")
                    with c2:
                        if st.button("Remove", key=f"remove_{instr_id}_{prog_id}"):
                            remove_instructor_from_program(instr_id, prog_id)
                            st.warning(f"Removed {prog_name} from {username}")
                            st.rerun()

            st.write("---")
            
            # 3. Assign a New Program
            col_assign, assign_mid, assign_out = st.columns([3,1,1])

            st.write("### Assign a New Program")
            with col_assign:
                selectable_ids = [p["program_id"] for p in all_programs]
                choice = st.selectbox(
                    label="Select a Program to Assign",
                    options=selectable_ids,
                    format_func=lambda x: prog_dict[x],
                    key=f"addprog_{instr_id}"
                )
                if st.button("Assign Program", key=f"btn_assign_{instr_id}"):
                    assign_instructor_to_program(instr_id, choice)
                    st.success(f"Assigned Program {prog_dict[choice]} (ID={choice}) to {username}")
                    st.rerun()



#####################
# PAGE: Instructor Login
#####################
def page_instructor_login():
    col_left, col_center, col_right = st.columns([1, 5, 1])

    with col_center:
        st.header("Instructor Login")

        if st.session_state.get("is_admin", False):
            st.error("An admin is currently logged in. Please log out as admin first.")
            return
        if st.session_state.get("instructor_logged_in"):
            st.info("You are already logged in as an instructor.")
            return

        username = st.text_input("Username (Instructor)")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            result = authenticate_instructor(username, password)
            if result:
                st.session_state.instructor_logged_in = True
                st.session_state.instructor_id = result["instructor_id"]
                st.session_state.instructor_role = result["role"]

                # GET assigned programs from pivot
                assigned_progs = list_instructor_programs(result["instructor_id"])
                # Instead of storing the whole dict, store just the names:
                # permitted_names = [p["program_name"] for p in assigned_progs]  # <-- CHANGED
                # st.session_state.instructor_programs = permitted_names         # <-- CHANGED
                st.session_state.instructor_program_ids = [p["program_id"] for p in assigned_progs]


                st.success(f"Welcome, {username}! Role = {result['role']}")
                st.session_state.menu_choice = "Main Tools"

                st.rerun() 
            else:
                st.error("Invalid username or password.")


#####################
# PAGE: Instructor Password Change
#####################
def page_instructor_change_password():
    col_left, col_center, col_right = st.columns([1, 5, 1])

    with col_center:
        st.header("Change My Password")

        if not st.session_state.get("instructor_logged_in"):
            st.error("You must be logged in as an instructor to change your password.")
            return

        old_pass = st.text_input("Old Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")

        if st.button("Update Password"):
            # Re-auth to check old_pass
            username = None
            all_instr = list_instructors()
            for instr in all_instr:
                if instr["instructor_id"] == st.session_state.instructor_id:
                    username = instr["username"]
                    break
            if not username:
                st.error("Could not find your instructor record. Contact admin.")
                return
            auth_result = authenticate_instructor(username, old_pass)
            if not auth_result:
                st.error("Old password is incorrect.")
                return
            if new_pass != confirm_pass:
                st.error("New passwords do not match.")
                return

            update_instructor_password(st.session_state.instructor_id, new_pass)
            st.success("Password updated successfully!")


#####################
# PAGE: Manage Students (MongoDB)
#####################

def page_manage_students():
    col_left, col_center, col_right = st.columns([1, 5, 1])

    with col_center:
        st.header("Manage Students")
        is_admin = st.session_state.get("is_admin", False)

        # ---------------------------
        # 1) Load all students
        # ---------------------------
        all_students = get_all_students()  # from Mongo
        if not all_students:
            st.info("No students in the database.")
            # return

        # ---------------------------
        # 2) If admin, show all; else filter by numeric program_id
        # ---------------------------
        if is_admin:
            students = all_students
        else:
            permitted_ids = st.session_state.get("instructor_program_ids", [])  # numeric IDs
            # print(permitted_ids)
            students = [s for s in all_students if s.get("program_id") in permitted_ids]

        # if not students:
        #     st.info("No students found for your assigned programs.")
        #     # return

         # st.subheader("Add or Update Students")
        with st.expander("Add or Update Students",expanded=True):

            action = st.radio(
                "Choose method:",
                ["Single Student Entry", "Bulk CSV Upload"],
                horizontal=True
            )

            if action == "Single Student Entry":
                # Let user manually add a single student
                with st.form("student_form"):
                    name_val = st.text_input("Name *", "")
                    phone_val = st.text_input("Phone", "")
                    contact_val = st.text_input("Contact Email", "")
                    # parent_val = st.text_input("Parent Email", "")
                    grade_val = st.text_input("Grade", "")
                    school_val  = st.text_input("School", "")

                    if is_admin:
                        # Admin can pick from all existing programs
                        all_programs = list_programs()  # e.g. [{"program_id": 101, "program_name": "STEM"}]
                        if not all_programs:
                            st.warning("No programs found in Postgres.")
                            st.stop()

                        # Build a dict { program_id -> program_name }
                        prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

                        # Let admin pick by name, but we store program_id
                        selected_id = st.selectbox(
                            "Select Program:",
                            options=prog_map.keys(),
                            format_func=lambda pid: f"{pid} - {prog_map[pid]}"
                        )
                        prog_val = selected_id

                    else:
                        # Instructor picks from assigned program_ids
                        permitted_ids = st.session_state.get("instructor_program_ids", [])
                        if not permitted_ids:
                            st.warning("No assigned programs available.")
                            prog_val = None
                        else:
                            prog_val = st.selectbox(
                                "Select Program ID:",
                                options=permitted_ids,
                                format_func=lambda pid: f"Program ID: {pid}"
                            )

                    submitted = st.form_submit_button("Save Student Info")
                    if submitted:
                        if not name_val.strip():
                            st.error("Name is required.")
                        elif prog_val is None:
                            st.error("No valid program selected.")
                        else:
                            result = store_student_record(name_val, phone_val,
                                                           contact_val, prog_val,
                                                           grade=grade_val, school=school_val)#parent_val,
                            st.success(result)
                            st.rerun()

            else:
                # 6) Bulk CSV Upload
                if is_admin:
                    # Admin can pick from all existing programs
                    all_programs = list_programs()
                    if not all_programs:
                        st.warning("No programs found in Postgres.")
                        st.stop()

                    # Build a dict { program_id -> program_name }
                    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

                    selected_prog_id = st.selectbox(
                        "Select Program for CSV Rows:",
                        options=prog_map.keys(),
                        format_func=lambda pid: f"{pid} - {prog_map[pid]}"
                    )
                else:
                    # Instructor picks from assigned program_ids
                    permitted_ids = st.session_state.get("instructor_program_ids", [])
                    if not permitted_ids:
                        st.warning("No assigned programs available.")
                        st.stop()

                    selected_prog_id = st.selectbox(
                        "Select Program ID for CSV Rows:",
                        options=permitted_ids,
                        format_func=lambda pid: f"Program ID: {pid}"
                    )

                uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])
                if uploaded_file:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview of data:", df.head())

                    required_cols = {"First Name","Last Name",
                                    "Number", "Email",
                                    "Grade", "School"}# "program_id","parent_email",
                    if not required_cols.issubset(df.columns):
                        st.error(f"CSV must have columns: {required_cols}")
                    else:
                        if st.button("Process CSV"):
                            successes = 0
                            failures = 0
                            for idx, row in df.iterrows():
                                # name_val = row["name"]
                                first_name = str(row["First Name"]).strip()
                                last_name = str(row["Last Name"]).strip()
                                name_val = f"{first_name} {last_name}".strip()

                                phone_val = row["Number"]
                                contact_val = row["Email"]
                                # parent_val = row["parent_email"]
                                grade_val = row["Grade"]
                                school_val = row["School"]
                                # prog_val = int(row["program_id"])

                                # If instructor, ensure this numeric program_id is in permitted_ids
                                if not is_admin:
                                    permitted_ids = st.session_state.get("instructor_program_ids", [])
                                    if selected_prog_id not in permitted_ids:
                                        st.warning(f"Row {idx}: Program ID '{selected_prog_id}' is not in your assigned list.")
                                        failures += 1
                                        continue

                                result_msg = store_student_record(
                                    name_val, phone_val, contact_val, selected_prog_id, grade_val, school_val) #parent_val

                                if "New student record" in result_msg or "updated" in result_msg:
                                    successes += 1
                                else:
                                    failures += 1

                            st.success(f"Bulk upload complete. Successes: {successes}, Failures: {failures}")
                            st.rerun()

        with st.expander("Current Students", expanded=True):
        # st.subheader("Current Students")

        # ---------------------------
        # 3) Display each student
        # ---------------------------
            for s in students:
                student_id = s.get("student_id")
                name = s.get("name", "")
                phone = s.get("phone", "")
                contact_email = s.get("contact_email", "")
                # parent_email = s.get("parent_email", "")
                prog_id = s.get("program_id", None)  # numeric program ID
                grade = s.get("grade", "")
                school = s.get("school", "")

                st.write(
                    f"**Name:** {name}, **ID:** {student_id}, **Program ID:** {prog_id}, "
                    f"**Phone:** {phone}, **Contact:** {contact_email}, "
                    f"**Grade:** {grade}, **School:** {school}"
                ) #**Parent:** {parent_email}

                col_del, col_edit = st.columns(2)
                with col_del:
                    if st.button(f"Delete (ID={student_id})", key=f"btn_delete_{student_id}"):
                        # Instructors must only delete if the student's program_id is in permitted_ids
                        if not is_admin:
                            permitted_ids = st.session_state.get("instructor_program_ids", [])
                            if prog_id not in permitted_ids:
                                st.error("You are not permitted to delete students in this program.")
                                st.stop()

                        success = delete_student_record(student_id)
                        if success:
                            st.success(f"Deleted student {name} (ID={student_id}).")
                            st.rerun()
                        else:
                            st.error("Delete failed or no such student.")

                with col_edit:
                    if st.button(f"Edit (ID={student_id})", key=f"btn_edit_{student_id}"):
                        st.session_state["editing_student"] = {
                            "student_id": student_id,
                            "name": name,
                            "phone": phone,
                            "contact_email": contact_email,
                            # "parent_email": parent_email,
                            # We'll store program_id here in case we want to display or verify it
                            "program_id": prog_id,
                            "grade": grade,
                            "school": school
                        }
                        st.rerun()

            # ---------------------------
            # 4) If we clicked Edit, show form
            # ---------------------------
            if "editing_student" in st.session_state:
                editing_data = st.session_state["editing_student"]
                st.subheader(f"Edit Student Record (ID={editing_data['student_id']})")

                with st.form("edit_student_form"):
                    new_name = st.text_input("Name", value=editing_data["name"])
                    new_phone = st.text_input("Phone", value=editing_data["phone"])
                    new_contact_email = st.text_input("Contact Email", value=editing_data["contact_email"])
                    # new_parent_email = st.text_input("Parent Email", value=editing_data["parent_email"])
                    new_grade = st.text_input("Grade", value=editing_data["grade"])
                    new_school = st.text_input("School", value=editing_data["school"])
                    submitted_edit = st.form_submit_button("Save Changes")
                    if submitted_edit:
                        updated = update_student_info(
                            editing_data["student_id"],
                            new_name,
                            new_phone,
                            new_contact_email,
                            new_grade,
                            new_school
                            
                            # new_parent_email
                        )
                        if updated:
                            st.success(f"Student record updated for {new_name}.")
                        else:
                            st.warning("No changes made or update failed.")

                        st.session_state.pop("editing_student")
                        st.rerun()


#####################
# PAGE: Take Attendance
#####################

def page_take_attendance():
    st.subheader("Take Attendance")
    attendance_mode = st.radio(
        "Choose attendance mode:",
        ["Take Attendance (Today)", "Record Past Session"], horizontal=True
    )
    is_admin = st.session_state.get("is_admin", False)

    # 1) Load all students from Mongo.
    all_students = get_all_students()

    # 2) Build a dict {program_id: program_name} from Postgres for display.
    all_programs = list_programs()  # returns e.g. [ { 'program_id': 1, 'program_name': 'STEM' }, ... ]
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

    # 3) Filter students if the user is an instructor.
    if is_admin:
        # Admin sees all students
        students = all_students
    else:
        # Instructor: get assigned program IDs from session_state
        permitted_ids = st.session_state.get("instructor_program_ids", [])
        students = [s for s in all_students if s.get("program_id") in permitted_ids]

    if not students:
        st.info("No students found. (Check whether you have assigned programs or student data.)")
        return

    if attendance_mode == "Take Attendance (Today)":
        st.subheader("Today’s Attendance")
        # 4) Build an attendance form
        with st.form("attendance_form"):
            attendance_dict = {}
            for s in students:
                sid = s.get("student_id")
                name = s.get("name", "")
                pid = s.get("program_id", 0)   # numeric program_id from Mongo

                # Look up program name from our dictionary (fallback if not found)
                prog_name = prog_map.get(pid, f"Program ID={pid}")

                st.subheader(f"{name} – Program: {prog_name}")
                status = st.selectbox(
                    "Status",
                    options=["Present", "Late", "Absent"],
                    key=f"{sid}_status"
                )
                comment = st.text_input("Comment (Optional)", key=f"{sid}_comment")

                attendance_dict[sid] = {
                    "name": name,
                    "program_id": pid,   # store numeric ID so we can record attendance
                    "status": status,
                    "comment": comment
                }

            submitted = st.form_submit_button("Submit Attendance")

        # 5) Process form submissions
        if submitted:
            for sid, data in attendance_dict.items():
                name = data["name"]
                prog_id = data["program_id"]
                status = data["status"]
                comment = data["comment"]

                try:
                    # record_student_attendance_in_array expects (name, program_id, status, comment)
                    result_msg = record_student_attendance_in_array(name, prog_id, status, comment)
                    st.write(f"{name} – Marked {status}: {result_msg}")
                except Exception as e:
                    st.error(f"Error for {name}: {e}")

            st.success("All attendance data submitted!")

    else:
        st.subheader("Record Past Session")
        # 2) Let the user pick the date/time of this past session
        session_date = st.date_input("Session Date", value=date(2025, 1, 7))
        session_time = st.time_input("Session Start Time", value=time(9, 0))
        session_time_past = _format_time_12h(session_time)
        st.write(f"**Date/Time**: {session_date} → {session_time_past}")

        # Combine them into a single datetime
        chosen_datetime = datetime.combine(session_date, session_time)

        # 3) (Optional) "Mark All Present" button for the PAST session
        if "past_defaults" not in st.session_state:
            st.session_state["past_defaults"] = {}

        if st.button("Mark All Present for Past Session"):
            for s in students:
                sid = s.get("student_id")
                st.session_state["past_defaults"][sid] = "Present"
            st.rerun()

        # 4) Build the manual form for final attendance
        with st.form("past_attendance_form"):
            past_attendance = {}
            for s in students:
                sid = s.get("student_id")
                student_name = s.get("name", "")
                prog_id = s.get("program_id", 0)
                program_name = prog_map.get(prog_id, f"ProgID={prog_id}")

                # Default to “Present” if Mark All Present was pressed
                default_status = st.session_state["past_defaults"].get(sid, "Absent")

                st.write(f"**{student_name}** (Program: {program_name})")
                status_choice = st.selectbox(
                    "Status",
                    ["Present", "Late", "Absent", "Excused"],
                    index=["Present", "Late", "Absent", "Excused"].index(default_status),
                    key=f"past_status_{sid}"
                )
                comment_val = st.text_input("Comment (Optional)", key=f"past_comment_{sid}")

                past_attendance[sid] = {
                    "name": student_name,
                    "program_id": prog_id,
                    "status": status_choice,
                    "comment": comment_val
                }

            # 5) Submit button
            submitted = st.form_submit_button("Submit Past Attendance")
        
        # 6) Process submissions
        if submitted:
            for sid, data in past_attendance.items():
                record_student_attendance_in_array(
                    name=data["name"],
                    program_id=data["program_id"],
                    status=data["status"],
                    comment=data["comment"],
                    attendance_date=chosen_datetime  # <— THIS is key
                )
            st.success(f"Past attendance recorded for session on {chosen_datetime}!")
            # Clear any defaults
            st.session_state["past_defaults"] = {}
#####################
# PAGE: Review Attendance
#####################
def show_attendance_logs():
    # 1) If not cached, fetch raw attendance docs from Mongo.
    if st.session_state["attendance_records"] is None:
        try:
            # Each record looks like:
            # {"student_id":..., "name":..., "program_id":..., "attendance":{ "date":..., "status":..., "comment":... }}
            records = get_all_attendance_subdocs()

            # Build dict {program_id: program_name} from Postgres for later display
            prog_map = {p["program_id"]: p["program_name"] for p in list_programs()}

            # Are we an admin or instructor?
            is_admin = st.session_state.get("is_admin", False)
            if not is_admin:
                # Filter by numeric program_id in the instructor's assigned list
                permitted_ids = st.session_state.get("instructor_program_ids", [])
                records = [r for r in records if r.get("program_id") in permitted_ids]

            # Store the program name into each record for easy display
            for r in records:
                pid = r.get("program_id", 0)
                r["program_name"] = prog_map.get(pid, f"Program ID={pid}")

            st.session_state["attendance_records"] = records

        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state["attendance_records"] = []

    # 2) Display the logs
    logs = st.session_state["attendance_records"]
    st.subheader("Daily Attendance Logs")

    if not logs:
        st.info("No attendance records found.")
        return
    
    all_names = sorted({doc.get("name", "Unknown") for doc in logs})
    selected_name = st.selectbox("Focus on One Student:", options=["All Students"] + all_names)
    if selected_name != "All Students":
        logs = [doc for doc in logs if doc.get("name") == selected_name]


    global_idx = 0

    for doc in logs:
        att = doc.get("attendance", {})
        date_val = att.get("date", "")
        status_val = att.get("status", "")
        comment_val = att.get("comment", "")
        s_name = doc.get("name", "")
        p_name = doc.get("program_name", "?")
        student_id = doc.get("student_id", "?")

        st.markdown(
            f"**Name:** {s_name} | **Program:** {p_name} | **Date:** {date_val} "
            f"| **Status:** {status_val} | **Comment:** {comment_val}"
        )

        colB, colC = st.columns([1, 1])

        # DELETE button
        with colB:
            if st.button(f"Delete (Row {global_idx})", key=f"delete_{global_idx}"):
                deleted = delete_attendance_subdoc(student_id, date_val)
                if deleted:
                    st.success("Attendance record deleted.")
                    st.session_state["attendance_records"] = None
                else:
                    st.warning("No matching record found.")
                st.rerun()

        # UPSERT button
        with colC:
            if st.button(f"Upsert (Row {global_idx})", key=f"upsert_{global_idx}"):
                # We store old info in case we want to adjust date or fields
                st.session_state["upsert_data"] = {
                    "student_id": student_id,
                    "student_name": s_name,  # Let's store the name
                    "old_date": date_val,
                    "old_status": status_val,
                    "old_comment": comment_val
                }
                st.rerun()

        st.write("---")
        global_idx += 1  # increment so each record has a unique key

    # 4) If user clicked "Upsert", show the minimal upsert form
    if "upsert_data" in st.session_state:
        record = st.session_state["upsert_data"]
        st.subheader("Upsert Attendance Record (Create or Update)")

        default_dt = record["old_date"]
        if isinstance(default_dt, str):
            default_dt = parser.parse(default_dt)

        with st.form("upsert_form"):
            st.write(f"**Student Name**: {record['student_name']}")
            st.write(f"**Student ID**: {record['student_id']}")
            st.write(f"**Existing Date**: {record['old_date']}")

            # Let user pick a new or same date/time
            new_date = st.date_input("Date", value=default_dt.date())
            new_time = st.time_input("Time", value=default_dt.time() if default_dt.time() else time(9, 0))
            combined_dt = datetime.combine(new_date, new_time)

            status_options = ["Present", "Late", "Absent", "Excused"]
            old_status = record["old_status"]
            try:
                status_index = status_options.index(old_status)
            except ValueError:
                status_index = 0

            final_status = st.selectbox("Status", status_options, index=status_index)
            final_comment = st.text_input("Comment", value=record["old_comment"])

            submitted_upsert = st.form_submit_button("Upsert Attendance")
            if submitted_upsert:
                success = upsert_attendance_subdoc(
                    student_id=record["student_id"],
                    target_date=combined_dt,
                    new_status=final_status,
                    new_comment=final_comment
                )
                if success:
                    st.success(f"Attendance upserted (Date={combined_dt}).")
                    # If date changed, optionally delete old record
                    if combined_dt != parser.parse(str(record["old_date"])):
                        delete_attendance_subdoc(record["student_id"], record["old_date"])
                    st.session_state["attendance_records"] = None
                else:
                    st.warning("No changes made or upsert failed.")

                st.session_state.pop("upsert_data")
                st.rerun()

        if st.button("Cancel Upsert"):
            st.session_state.pop("upsert_data")
            st.info("Upsert cancelled.")
            st.rerun()

def show_missed_counts():
    st.subheader("Missed Counts for All Students")

    # Only fetch missed data once or if the user requests a refresh
    if st.session_state["missed_counts"] is None:
        try:
            # Determine if user is admin or instructor
            is_admin = st.session_state.get("is_admin", False)
            
            if is_admin:
                # Admin sees all programs
                missed_data = get_missed_counts_for_all_students()
            else:
                # Instructor sees only permitted program IDs
                permitted_ids = st.session_state.get("instructor_program_ids", [])
                missed_data = get_missed_counts_for_all_students(program_ids=permitted_ids)
            
            # Build a dict {program_id -> program_name} from Postgres for easy display
            prog_map = {p["program_id"]: p["program_name"] for p in list_programs()}

            # Insert a "program_name" field for display
            for m in missed_data:
                pid = m.get("program_id", 0)
                m["program_name"] = prog_map.get(pid, f"Program ID={pid}")

            # Cache the result in session state
            st.session_state["missed_counts"] = missed_data

        except Exception as e:
            st.error(f"Error fetching missed counts: {e}")
            st.session_state["missed_counts"] = []

    # Actually display the missed counts data
    data = st.session_state["missed_counts"]
    if not data:
        st.info("No missed data found.")
        return

    # Convert to DataFrame for exploration
    MissedCountsdf = pd.DataFrame(data)

    # Use the streamlit_extras.dataframe_explorer
    MissedCountsdf_output = dataframe_explorer(MissedCountsdf)
    MissedCounts_dataframe = pd.DataFrame(MissedCountsdf_output)

    if MissedCounts_dataframe.empty:
        st.info("No data selected in the explorer.")
    else:
        st.dataframe(MissedCounts_dataframe, use_container_width=True)

# def show_missed_counts():
#     # 1) If not cached, fetch missed counts
#     if st.session_state["missed_counts"] is None:
#         try:
#             # Each item looks like:
#             # {"student_id":..., "name":..., "phone":..., "program_id":..., "sum_missed":... }
#             missed_data = get_missed_counts_for_all_students()

#             # Build dict {program_id: program_name} for display
#             prog_map = {p["program_id"]: p["program_name"] for p in list_programs()}

#             is_admin = st.session_state.get("is_admin", False)
#             if not is_admin:
#                 permitted_ids = st.session_state.get("instructor_program_ids", [])
#                 missed_data = [m for m in missed_data if m.get("program_id") in permitted_ids]

#             # Insert a "program_name" field for display
#             for m in missed_data:
#                 pid = m.get("program_id", 0)
#                 m["program_name"] = prog_map.get(pid, f"Program ID={pid}")

#             st.session_state["missed_counts"] = missed_data

#         except Exception as e:
#             st.error(f"Error fetching missed counts: {e}")
#             st.session_state["missed_counts"] = []

#     # 2) Display the data
#     data = st.session_state["missed_counts"]
#     st.subheader("Missed Counts for All Students")
#     if not data:
#         st.info("No missed data found.")
#     else:
#         MissedCountsdf = pd.DataFrame(data)
#         MissedCountsdf_output= dataframe_explorer(MissedCountsdf) 
#         MissedCounts_dataframe= pd.DataFrame(MissedCountsdf_output)
#         if MissedCounts_dataframe.empty:
#             st.info("No data selected in the explorer.")
#         else:
#             st.dataframe(MissedCounts_dataframe, use_container_width=True)
#         # st.dataframe(df, use_container_width=True)

def show_last_week_attendance():
    """
    Display the logs for the last 7 days only,
    reusing a similar approach to show_attendance_logs().
    """
    if st.session_state["attendance_records"] is None:
        try:
            # Use the new function from students_db
            records = get_attendance_subdocs_last_week()

            # If you're also filtering by instructor's permitted IDs:
            is_admin = st.session_state.get("is_admin", False)
            if not is_admin:
                permitted_ids = st.session_state.get("instructor_program_ids", [])
                records = [r for r in records if r.get("program_id") in permitted_ids]

            # Optionally label them with program names, similar to show_attendance_logs
            prog_map = {p["program_id"]: p["program_name"] for p in list_programs()}
            for r in records:
                pid = r.get("program_id", 0)
                r["program_name"] = prog_map.get(pid, f"Program ID={pid}")

            st.session_state["attendance_records"] = records

        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state["attendance_records"] = []

    # Now we display them
    logs = st.session_state["attendance_records"]
    st.subheader("Attendance from the Last 7 Days")
    if not logs:
        st.write("No attendance records found for the last 7 days.")
    else:
        for idx, doc in enumerate(logs):
            att = doc.get("attendance", {})
            date_val = att.get("date", "")
            status_val = att.get("status", "")
            comment_val = att.get("comment", "")
            s_name = doc.get("name", "")
            p_name = doc.get("program_name", "?")

            st.write(
                f"**Name:** {s_name} | **Program:** {p_name} | **Date:** {date_val} "
                f"| **Status:** {status_val} | **Comment:** {comment_val}"
            )
            if st.button(f"Edit (Last7 - Row {idx})"):
                st.session_state["editing_attendance"] = {
                    "student_id": doc.get("student_id", "?"),
                    "old_date": date_val,
                    "old_status": status_val,
                    "old_comment": comment_val
                }
                st.rerun()

    # If user clicks "Edit", you can reuse the same logic as show_attendance_logs
    if "editing_attendance" in st.session_state:
        st.subheader("Edit Attendance Record")
        record = st.session_state["editing_attendance"]

        st.write(f"**Student ID**: {record['student_id']}")
        st.write(f"**Original Date**: {record['old_date']}")

        status_options = ["Present", "Late", "Absent"]
        try:
            status_index = status_options.index(record["old_status"])
        except ValueError:
            status_index = 0

        new_status = st.selectbox("New Status", status_options, index=status_index)
        new_comment = st.text_input("New Comment", value=record["old_comment"])

        if st.button("Save Changes"):
            try:
                updated = update_attendance_subdoc(
                    student_id=record["student_id"],
                    old_date=record["old_date"],
                    new_status=new_status,
                    new_comment=new_comment
                )
                if updated:
                    st.success("Attendance updated successfully!")
                    # Force refetch
                    st.session_state["attendance_records"] = None
                else:
                    st.warning("No records were updated.")
            except Exception as e:
                st.error(f"Error updating attendance: {e}")

            st.session_state.pop("editing_attendance")
            st.rerun()

def page_review_attendance():
    st.header("Review Attendance Logs")

    ############################################
    # A) Show st.metric for "This Week" vs. "Last Week"
    ############################################
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # 1) "This Week" = last 7 days
    subdocs_this_week = get_attendance_subdocs_in_range(seven_days_ago, now)
    total_this_week = len(subdocs_this_week)

    # 2) "Last Week" = from 14 days ago until 7 days ago
    subdocs_last_week = get_attendance_subdocs_in_range(fourteen_days_ago, seven_days_ago)
    total_last_week = len(subdocs_last_week)

    attendance_delta = total_this_week - total_last_week

    # --- Only fetch students in permitted programs (if instructor) ---
    is_admin = st.session_state.get("is_admin", False)
    if is_admin:
        all_students = get_all_students()  # returns ALL students
    else:
        # gather instructor_program_ids from session
        program_ids = st.session_state.get("instructor_program_ids", [])
        # fetch only those students in the instructor’s assigned programs
        all_students = get_all_students(program_ids=program_ids)

    # all_students = get_all_students()
    total_students = len(all_students)

    # Use our new function to get last week's count from ObjectId logic
    last_week_count = get_student_count_as_of_last_week()

    # Calculate the difference
    student_delta = total_students - last_week_count


    col1, col2, col3= st.columns(3)
    with col1:
        st.metric(
            label="Attendance This Week",
            value=total_this_week,
            delta=f"{attendance_delta} compared to previous week"
        )

    # Add a second metric if you want, e.g. "Absent This Week" vs. "Absent Last Week"
    # We'll count how many in subdocs_this_week have status == "Absent"
    absent_this_week = sum(1 for r in subdocs_this_week if r["attendance"]["status"] == "Absent")
    absent_last_week = sum(1 for r in subdocs_last_week if r["attendance"]["status"] == "Absent")
    delta_absent = absent_this_week - absent_last_week
    with col2:
        st.metric(
            label="Absences This Week",
            value=absent_this_week,
            delta=f"{delta_absent} from last week"
        )

    with col3:
        st.metric(
            label="Total Students",
            value=total_students,
            delta=f"{student_delta} from last week"
        )


    st.write("---")  # visual separator

    ############################################
    # B) Original Buttons: Load All, Missed, etc.
    ############################################
    if "review_mode" not in st.session_state:
        st.session_state["review_mode"] = "none"

    # Prepare containers for logs & missed counts if not present
    if "attendance_records" not in st.session_state:
        st.session_state["attendance_records"] = None
    if "missed_counts" not in st.session_state:
        st.session_state["missed_counts"] = None

    # Show two or three buttons
    colA, colB = st.columns(2)
    if colA.button("Load All Attendance"):
        st.session_state["review_mode"] = "attendance"
        st.session_state["attendance_records"] = None
        st.session_state["missed_counts"] = None
    if colB.button("Load Missed Counts"):
        st.session_state["review_mode"] = "missed"
        st.session_state["attendance_records"] = None
        st.session_state["missed_counts"] = None

    # Display whichever mode is selected
    if st.session_state["review_mode"] == "attendance":
        show_attendance_logs()  # your existing function
    elif st.session_state["review_mode"] == "missed":
        show_missed_counts()    # your existing function
    else:
        st.info("Choose an option to display data.")
        

#####################
# PAGE: Generate Reports with Pygwalker
#####################
def page_generate_reports():
    st.header("Generate Reports")

    # 1) Determine if user is admin or instructor
    is_admin = st.session_state.get("is_admin", False)

    # 2) Build a dict {program_id -> program_name} from Postgres
    all_programs = list_programs()  # e.g. [ {"program_id": 1, "program_name": "STEM"}, ... ]
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
        # Get current total

    # 3) If instructor, get a list of permitted program IDs
    if is_admin:
        permitted_ids = None   # Admin sees all
    else:
        permitted_ids = st.session_state.get("instructor_program_ids", [])

    # 4) Fetch raw attendance records from Mongo
    #    Each item has {"student_id", "name", "program_id", "attendance": {date, status, comment}}
    records = fetch_all_attendance_records()
    if not records:
        st.info("No attendance data found.")
        return

    # 5) Filter by numeric program_id if not admin
    if permitted_ids is not None:
        records = [r for r in records if r.get("program_id") in permitted_ids]
        if not records:
            st.info("No attendance data found for your assigned programs.")
            return

    # 6) Flatten each record so 'attendance' sub-doc fields become top-level
    flattened = []
    for r in records:
        att = r["attendance"]
        pid = r.get("program_id", 0)   # Numeric program_id from Mongo

        new_row = {
            "student_id": r.get("student_id"),
            "name": r.get("name"),
            "program_id": pid,
            # Look up friendly program name from our dict
            "program_name": prog_map.get(pid, f"Program ID={pid}"),
            "date": att.get("date"),
            "status": att.get("status"),
            "comment": att.get("comment", "")
        }
        flattened.append(new_row)

    if not flattened:
        st.info("No valid attendance data to display.")
        return

    df = pd.DataFrame(flattened)
    if df.empty:
        st.info("No valid attendance data to display.")
        return


    # st.help("Below are some prebuilt charts on the dataset.")
    with st.expander("Visualizations of Full Attendance Data"):
    # 1) Convert 'status' to numeric: Present=1, Late=0.5, Absent=0
        def status_to_numeric(s):
            if s == "Present":
                return 1
            elif s == "Late":
                return 0.5
            else:
                return 0

        df["attendance_value"] = df["status"].apply(status_to_numeric)

        # 2) Group by program_name -> compute average attendance
        ranking_df = df.groupby("program_name", as_index=False)["attendance_value"].mean()
        ranking_df.rename(columns={"attendance_value": "avg_attendance_score"}, inplace=True)
        ranking_df.sort_values("avg_attendance_score", ascending=False, inplace=True)

        st.subheader("Program Ranking by Average Attendance")
        st.table(ranking_df)

        # PLOT #1: Bar chart of average attendance by program
        fig_bar = px.bar(
            ranking_df,
            x="program_name",
            y="avg_attendance_score",
            title="Average Attendance Score by Program"
        )
        # st.plotly_chart(fig_bar, use_container_width=True)

        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]

        # st.subheader("Proportion of Attendance Statuses")
        # st.write("A quick look at the distribution of Present, Late, and Absent overall. "
        #         "Remember that pie charts can be misleading if too many slices are present.")
        
        fig_pie = px.pie(
            status_counts,
            values="count",
            names="status",
            title="Distribution of Attendance Statuses",
            hole=0.4  # optional "donut" style
        )
        fig_pie.update_layout(
            width=500,   # adjust as needed
            height=500   # adjust as needed
        )
        # st.plotly_chart(fig_pie, use_container_width=True)

        # 3) Time series: overall attendance over time
        # Ensure df["date"] is properly typed
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        daily_df = df.groupby("date", as_index=False)["attendance_value"].mean()

        fig_line = px.line(
            daily_df,
            x="date",
            y="attendance_value",
            title="Average Attendance Over Time (All Programs)"
        )
        fig_line.update_traces(line=dict(width=4))

        # st.plotly_chart(fig_line, use_container_width=True)

        # 4) Multi-line time series, color-coded by program
        multi_df = (
            df.groupby(["date", "program_name"], as_index=False)["attendance_value"]
                .mean()
        )
        fig_multi = px.line(
            multi_df,
            x="date",
            y="attendance_value",
            color="program_name",
            title="Attendance Over Time by Program"
        )
        fig_multi.update_traces(line=dict(width=3))

        # st.plotly_chart(fig_multi, use_container_width=True)

        # First row: fig_bar (left), fig_pie (right)
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("Average Attendance Score by Program")
            st.plotly_chart(fig_bar, use_container_width=True)

        with row1_col2:
            st.subheader("Proportion of Attendance Statuses")
            # st.write(
            #     "A quick look at the distribution of Present, Late, and Absent overall. "
            #     "Remember that pie charts can be misleading if too many slices are present."
            # )
            st.plotly_chart(fig_pie, use_container_width=True)

        st.write("---")
        # Second row: fig_line (left), fig_multi (right)
        # row2_col1, row2_col2 = st.columns(2)

        # with row2_col1:
        st.subheader("Average Attendance Over Time (All Programs)")
        st.plotly_chart(fig_line, use_container_width=True)

        # with row2_col2:
        st.subheader("Attendance Over Time by Program")
        st.plotly_chart(fig_multi, use_container_width=True)




        # st.subheader("Histogram of Attendance Values")
        # st.write("Displays the distribution of numeric attendance values (Present=1, Late=0.5, Absent=0).")
        # fig_hist = px.histogram(
        #     df,
        #     x="attendance_value",
        #     nbins=30,  # since we effectively have 3 distinct values
        #     title="Histogram of Attendance Value Distribution"
        # )
        # st.plotly_chart(fig_hist, use_container_width=True)

    # 7) Let users explore the data with dataframe_explorer
    with st.expander("Data Explorer"):
        explorer_output = dataframe_explorer(df, case=False)
        explorer_df = pd.DataFrame(explorer_output)
        if explorer_df.empty:
            st.info("No data selected in the explorer.")
        else:
            st.dataframe(explorer_df, use_container_width=True)

    # 8) Visualize with PyGWalker
    try:
        with st.expander("Data Visualizer"):
            components.html(
                pyg.to_html(explorer_df, env="Streamlit"),
                height=1000,
                scrolling=True
            )
    except Exception as e:
        st.info("No data selected in the visualizer.")
    # 9) Generate Sweetviz report on the subset (explorer_df)

    # After flattening 'df' with attendance data
    
    if st.button("Generate Sweetviz Report"):
        report = sweetviz.analyze(explorer_df)
        report_name = "sweetviz_report.html"
        report.show_html(report_name, open_browser=False)

        with open(report_name, "r", encoding="utf-8") as f:
            sweetviz_html = f.read()

        components.html(sweetviz_html, height=800, scrolling=True)
        st.subheader("Download Sweetviz HTML")
        st.download_button(
            label="Download Sweetviz HTML",
            data=sweetviz_html,
            file_name="Sweetviz_Report.html",
            mime="text/html",
        )
#####################
# PAGE: Manage Schedules
#####################


def page_manage_schedules():
    """
    Page for an instructor (or admin) to create, view, edit, and delete schedules.
    Stores numeric program_id in Mongo, but *displays* times in 12-hour AM/PM.
    """

    instructor_id = st.session_state.get("instructor_id", None)
    is_admin = st.session_state.get("is_admin", False)
    if not instructor_id and not is_admin:
        st.error("You must be logged in as an instructor or admin to manage schedules.")
        return

    # 2) Build a map { program_id -> program_name } from Postgres
    all_programs = list_programs()  
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

    # 3) Determine which program IDs the user can manage
    if is_admin:
        program_id_options = list(prog_map.keys())  # admin can see all
    else:
        program_id_options = st.session_state.get("instructor_program_ids", [])
        if not program_id_options:
            st.warning("You have no assigned programs. Contact an admin for access.")
            return

    # col_left, col_center, col_right = st.columns([1, 5, 1])
    # with col_center:
    st.header("Manage Class Schedules")
    with st.expander("Create a New Schedule", expanded=True):
        # with st.form("create_schedule_form"):
        if program_id_options:
            selected_prog_id = st.selectbox(
            "Select Program",
            options=program_id_options,
            format_func=lambda pid: prog_map.get(pid, f"Unknown (ID={pid})"))
        else:
            st.warning("No assigned programs available.")
            return

        title = st.text_input("Class Title", "")
        notes = st.text_area("Additional Notes/Description")

        recurrence = st.selectbox(
            "Recurrence",
            ["None", "Weekly", "Monthly"],
            help="Choose 'None' for a one-time class, or 'Weekly/Monthly' for recurring classes."
        )

        # days_times = []
        location = ""
        days_times = []
        start_dt = None
        end_dt = None

        if recurrence == "None":
            # One-time class
            chosen_date = st.date_input("Class Date", value=date.today())
            None_recurrence_timecol1, None_recurrence_timecol2 = st.columns(2)
            with None_recurrence_timecol1:
                start_t = st.time_input("Start Time", value=time(9, 0))
                st.write(f"Selected Start: **{start_t.strftime('%I:%M %p')}**")  # 12-hour display
            with None_recurrence_timecol2:
                end_t = st.time_input("End Time", value=time(10, 0))
                st.write(f"Ends at: **{end_t.strftime('%I:%M %p').lstrip('0')}**")

            location = st.text_input("Location (Zoom or Physical Room)")
            
        # elif recurrence == "Weekly":
        else:

            # Weekly or Monthly
            st.write("Select multiple days, each with its own time and location.")
            selected_days = st.multiselect(
                "Days of Week",
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            )
            for d in selected_days:
                st.write(f"**Times/Location for {d}**")
                col1, col2 = st.columns(2)
                start_for_day = col1.time_input(f"{d} Start", value=time(9, 0))
                col1.write(f"Starts at: **{start_for_day.strftime('%I:%M %p').lstrip('0')}**")

                end_for_day = col2.time_input(f"{d} End", value=time(10, 0))
                col2.write(f"Ends at: **{end_for_day.strftime('%I:%M %p').lstrip('0')}**")

                loc_for_day = st.text_input(f"{d} Location", "", key=f"{d}_loc")

                days_times.append({
                    "day": d,
                    # store in 24-hour format "HH:MM:SS"
                    "start_time": str(start_for_day),
                    "end_time": str(end_for_day),
                    "location": loc_for_day
                })

        # submitted = st.form_submit_button("Create Schedule")

        if st.button("Create Schedule"):
            if recurrence == "None":
                # build one-time doc
                start_dt = datetime.combine(chosen_date, start_t)
                end_dt = datetime.combine(chosen_date, end_t)
                doc = {
                    "instructor_id": instructor_id,
                    "program_id": selected_prog_id,
                    "title": title,
                    "recurrence": "None",
                    "notes": notes,
                    "start_datetime": start_dt,
                    "end_datetime": end_dt,
                    "days_times": [],
                    "location": location}
            else:
            # build weekly/monthly doc
                doc = {
                    "instructor_id": instructor_id,
                    "program_id": selected_prog_id,
                    "title": title,
                    "recurrence": recurrence,
                    "notes": notes,
                    "days_times": days_times,
                    "start_datetime": None,
                    "end_datetime": None
                }

            new_id = create_schedule(doc)
            st.success(f"Created schedule with ID: {new_id}")
            st.rerun()

        # 5) Show Existing Schedules
    st.subheader("Existing Schedules")
    
    # with st.expander("Existing Schedules", expanded=True):

    # If admin wants to see all schedules, they'd omit instructor_id from here
    all_schedules = list_schedules(instructor_id=instructor_id)
    if not all_schedules:
        st.info("No schedules found.")
        return

    # Filter schedules to only programs the user can manage
    filtered = [sch for sch in all_schedules if sch.get("program_id") in program_id_options]
    if not filtered:
        st.info("No schedules for your assigned programs.")
        return

    for sch in filtered:
        sid = sch["_id"]  # from Mongo
        pid = sch.get("program_id", None)
        prog_name = prog_map.get(pid, f"Unknown (ID={pid})")

        st.write("---")
        st.write(f"**Title**: {sch.get('title', '')} | **Program**: {prog_name}")
        st.write(f"**Recurrence**: {sch.get('recurrence', 'None')}")
        st.write(f"**Notes**: {sch.get('notes', '')}")

        if sch.get("recurrence") == "None":
            # Display start/end in 12-hour format
            start_text = _format_time_12h(sch.get("start_datetime"))
            end_text = _format_time_12h(sch.get("end_datetime"))
            st.write(f"**Date/Time**: {start_text} → {end_text}")

            if sch.get("location"):
                st.write(f"**Location**: {sch['location']}")
        else:
            # Recurring
            dt_list = sch.get("days_times", [])
            if dt_list:
                st.write("**Days/Times**:")
                for d_obj in dt_list:
                    day = d_obj["day"]
                    s_24 = d_obj["start_time"]  # e.g. "09:00:00"
                    e_24 = d_obj["end_time"]
                    # Convert to 12-hour
                    s_12 = _format_time_12h(s_24)
                    e_12 = _format_time_12h(e_24)
                    loc = d_obj.get("location", "")
                    st.write(f"- {day}: {s_12} → {e_12}, Loc: {loc}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Edit {sid}"):
                st.session_state["editing_schedule"] = sid
                st.rerun()
        with col2:
            if st.button(f"Delete {sid}"):
                if delete_schedule(sid):
                    st.success("Schedule deleted.")
                    st.rerun()
                else:
                    st.error("Delete failed or no such schedule.")

        # 6) Edit Form
        editing_id = st.session_state.get("editing_schedule")
        if editing_id:
            st.subheader(f"Editing Schedule: {editing_id}")
            schedule_doc = next((x for x in filtered if x["_id"] == editing_id), None)
            if not schedule_doc:
                st.error("Schedule not found or not authorized.")
                return

            old_title = schedule_doc.get("title", "")
            old_notes = schedule_doc.get("notes", "")
            old_recurrence = schedule_doc.get("recurrence", "None")
            old_location = schedule_doc.get("location", "")
            old_days_times = schedule_doc.get("days_times", [])
            old_program_id = schedule_doc.get("program_id", None)

            st.write("**Program**:", prog_map.get(old_program_id, f"Unknown (ID={old_program_id})"))

            new_title = st.text_input("Edit Title", value=old_title)
            new_recurrence = st.selectbox(
                "Recurrence",
                ["None", "Weekly", "Monthly"],
                index=["None", "Weekly", "Monthly"].index(old_recurrence)
            )
            new_notes = st.text_area("Edit Notes", value=old_notes)

            if new_recurrence == "None":
                # One-time class
                existing_start = schedule_doc.get("start_datetime")
                existing_end = schedule_doc.get("end_datetime")

                if isinstance(existing_start, str):
                    existing_start = parser.parse(existing_start)
                if isinstance(existing_end, str):
                    existing_end = parser.parse(existing_end)

                start_date_val = existing_start.date() if existing_start else date.today()
                start_time_val = existing_start.time() if existing_start else time(9, 0)
                end_date_val = existing_end.date() if existing_end else date.today()
                end_time_val = existing_end.time() if existing_end else time(10, 0)

                edited_start_date = st.date_input("Start Date", value=start_date_val)
                edited_start_time = st.time_input("Start Time", value=start_time_val)
                edited_end_date = st.date_input("End Date", value=end_date_val)
                edited_end_time = st.time_input("End Time", value=end_time_val)
                edited_location = st.text_input("Location", value=old_location)
                new_days_times = []

            else:
                # Recurring
                old_selected_days = [d["day"] for d in old_days_times]
                selected_days = st.multiselect(
                    "Days of Week",
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    default=old_selected_days
                )

                new_days_times = []
                for d in selected_days:
                    existing = next((x for x in old_days_times if x["day"] == d), None)
                    default_start = time(9, 0)
                    default_end = time(10, 0)
                    default_loc = ""

                    if existing:
                        # parse existing strings e.g. "09:00:00"
                        if "start_time" in existing:
                            try:
                                hh, mm, ss = existing["start_time"].split(":")
                                default_start = time(int(hh), int(mm))
                            except:
                                pass
                        if "end_time" in existing:
                            try:
                                hh, mm, ss = existing["end_time"].split(":")
                                default_end = time(int(hh), int(mm))
                            except:
                                pass
                        default_loc = existing.get("location", "")

                    st.write(f"**Times/Location for {d}**")
                    col_a, col_b = st.columns(2)
                    new_start = col_a.time_input(
                        f"{editing_id}_{d}_start",
                        value=default_start
                    )
                    col_a.write(f"Starts at: **{new_start.strftime('%I:%M %p').lstrip('0')}**")

                    new_end = col_a.time_input(
                        f"{editing_id}_{d}_end",
                        value=default_end
                    )
                    col_a.write(f"Ends at: **{new_end.strftime('%I:%M %p').lstrip('0')}**")

                    new_loc = col_b.text_input(
                        f"{editing_id}_{d}_loc",
                        value=default_loc
                    )

                    new_days_times.append({
                        "day": d,
                        "start_time": str(new_start),  # store "HH:MM:SS"
                        "end_time": str(new_end),
                        "location": new_loc
                    })
                edited_location = None

            if st.button("Save Changes"):
                updates = {
                    "title": new_title,
                    "recurrence": new_recurrence,
                    "notes": new_notes
                }

                if new_recurrence == "None":
                    # single day/time
                    updates["days_times"] = []
                    s_dt = datetime.combine(edited_start_date, edited_start_time)
                    e_dt = datetime.combine(edited_end_date, edited_end_time)
                    updates["start_datetime"] = s_dt
                    updates["end_datetime"] = e_dt
                    updates["location"] = edited_location
                else:
                    # multi day/time
                    updates["days_times"] = new_days_times
                    updates["start_datetime"] = None
                    updates["end_datetime"] = None
                    updates.pop("location", None)  # remove if used only for one-time

                success = update_schedule(editing_id, updates)
                if success:
                    st.success("Schedule updated.")
                else:
                    st.error("No changes made, or update failed.")

                st.session_state.pop("editing_schedule", None)
                st.rerun()
