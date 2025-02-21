# pages.py

import streamlit as st
import pygwalker as pyg
from streamlit_extras.dataframe_explorer import dataframe_explorer
import streamlit.components.v1 as components
import sweetviz
import pandas as pd
from datetime import datetime, time, date

# Import from instructors_db
from instructors_db import (
    create_instructors_table,
    add_instructor,
    list_instructors,
    update_instructor_role,
    update_instructor_programs,
    authenticate_instructor,
    update_instructor_password,
    delete_instructor  
)

# Import from students_db (for student/attendance pages)
from students_db import (
    store_student_record,
    get_all_students,
    record_student_attendance_in_array,
    get_all_attendance_subdocs,
    get_missed_counts_for_all_students,
    delete_student_record,
    fetch_all_attendance_records

)

from schedules_db import (
    create_schedule,
    list_schedules,
    update_schedule,
    delete_schedule
)

def get_permitted_programs():
    """
    Returns a list of permitted programs for the currently logged-in instructor.
    If user is admin, return None (meaning 'no restriction').
    """
    # If admin, allow all
    if st.session_state.get("is_admin", False):
        return None

    raw_programs = st.session_state.get("instructor_programs", "")
    permitted = [p.strip() for p in raw_programs.split(",") if p.strip()]
    return permitted


#####################
# PAGE: Manage Instructors (Admin Only)
#####################
def page_manage_instructors():
    st.header("Manage Instructors")
    # create_instructors_table()  # Ensure table

    with st.expander("Add a New Instructor"):
        uname = st.text_input("Username", key="uname")
        pwd = st.text_input("Password", type="password", key="pwd")
        role = st.selectbox("Role", ["Instructor", "Manager", "Admin"], key="role_select")
        programs = st.text_input("Programs (comma-separated)", key="programs_box")
        if st.button("Create Instructor", key="create_instructor"):
            success = add_instructor(uname, pwd, role, programs)
            if success:
                st.success("Instructor created successfully!")
            else:
                st.error("User might already exist or an error occurred.")

    st.subheader("Current Instructors")
    instructors = list_instructors()
    if not instructors:
        st.write("No instructors found.")
    else:
        for instr in instructors:
            st.write(f"**ID:** {instr['instructor_id']} | **Username:** {instr['username']} | "
                     f"**Role:** {instr['role']} | **Programs:** {instr['programs']}")

            col1, col2 = st.columns(2)
            with col1:
                new_role = st.selectbox(f"Update Role (ID={instr['instructor_id']})",
                                        ["Instructor", "Manager", "Admin"],
                                        index=["Instructor","Manager","Admin"].index(instr['role']),
                                        key=f"role_{instr['instructor_id']}")
                if st.button(f"Set Role - {instr['instructor_id']}", key=f"btn_role_{instr['instructor_id']}"):
                    update_instructor_role(instr["instructor_id"], new_role)
                    st.rerun()

            with col2:
                new_programs = st.text_input(f"Update Programs (ID={instr['instructor_id']})",
                                             value=instr['programs'],
                                             key=f"progs_{instr['instructor_id']}")
                if st.button(f"Set Programs - {instr['instructor_id']}", key=f"btn_progs_{instr['instructor_id']}"):
                    update_instructor_programs(instr["instructor_id"], new_programs)
                    st.rerun()


#####################
# PAGE: Instructor Login (SQLite)
#####################
def page_instructor_login():
    """
    Allows instructors to log in via username/password stored in instructors.db.
    If valid, sets st.session_state with relevant fields.
    """
    st.header("Instructor Login")

    if st.session_state.get("is_admin", False):
        st.error("An admin is currently logged in. Please log out as admin before logging in as an instructor.")
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
            st.session_state.instructor_programs = result["programs"]
            st.success(f"Welcome, {username}! Role = {result['role']}")
        else:
            st.error("Invalid username or password.")


#####################
# PAGE: Instructor Password Change
#####################
def page_instructor_change_password():
    """
    Lets a logged-in instructor change their password.
    We assume st.session_state.instructor_id is set.
    """
    st.header("Change My Password")

    if not st.session_state.get("instructor_logged_in"):
        st.error("You must be logged in as an instructor to change your password.")
        return

    old_pass = st.text_input("Old Password", type="password")
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        # First, re-authenticate with old_pass to ensure correct old password
        username = None
        # We must find the instructor's username from the DB. Let's do a quick approach:
        all_instr = list_instructors()
        for instr in all_instr:
            if instr["instructor_id"] == st.session_state.instructor_id:
                username = instr["username"]
                break

        if not username:
            st.error("Could not find your instructor record. Contact admin.")
            return

        # Check old password
        auth_result = authenticate_instructor(username, old_pass)
        if not auth_result:
            st.error("Old password is incorrect.")
            return

        # Check new passwords match
        if new_pass != confirm_pass:
            st.error("New passwords do not match.")
            return

        # Update DB
        update_instructor_password(st.session_state.instructor_id, new_pass)
        st.success("Password updated successfully!")


#####################
# PAGE: Manage Students (MongoDB)
#####################



def page_manage_students():
    st.header("Manage Students (MongoDB)")

    # 1) Determine if admin or instructor
    is_admin = st.session_state.get("is_admin", False)
    raw_programs = st.session_state.get("instructor_programs", "")
    if not is_admin:
        permitted_programs = [p.strip() for p in raw_programs.split(",") if p.strip()]
    else:
        permitted_programs = None  # Means no filtering
       
    # 2) Student creation form
    with st.form("student_form"):
        name_val = st.text_input("Name *", "")
        phone_val = st.text_input("Phone", "")
        contact_val = st.text_input("Contact Email", "")
        parent_val = st.text_input("Parent Email", "")

        if is_admin:
            # Admin can type any program ID
            prog_val = st.text_input("Program ID *", "")
        else:
            # Instructor can only pick from assigned programs
            prog_val = st.selectbox("Program ID *", permitted_programs)

        submitted = st.form_submit_button("Save Student Info")

    if submitted:
        if not name_val:
            st.error("Name is required.")
        else:
            result = store_student_record(
                name_val, phone_val, contact_val, parent_val, prog_val
            )
            st.success(result)

    # 3) Show existing students
    st.subheader("Current Students")
    students = get_all_students()

    # Filter if instructor
    if not is_admin and permitted_programs:
        students = [s for s in students if s.get("program_id") in permitted_programs]

    if not students:
        st.info("No students found for your assigned programs." if not is_admin else "No students found.")
        return

    # 4) Display and allow deletion
    for s in students:
        student_id = s.get("student_id")
        name = s.get("name", "")
        program_id = s.get("program_id", "")
        phone = s.get("phone", "")

        st.write(f"**Name:** {name}, **ID:** {student_id}, **Program:** {program_id}, **Phone:** {phone}")

        # If the user clicks delete, confirm that the student belongs to an allowed program (if instructor)
        if st.button(f"Delete (ID={student_id})", key=f"btn_delete_{student_id}"):
            if not is_admin and program_id not in permitted_programs:
                st.error("You are not permitted to delete students from this program.")
            else:
                success = delete_student_record(student_id)
                if success:
                    st.success(f"Student {name} (ID={student_id}) deleted.")
                    st.rerun()
                else:
                    st.error("Delete failed or no such student.")

# def page_manage_students():
#     st.header("Manage Students (MongoDB)")

#     # 1) Form to add/edit students
#     with st.form("student_form"):
#         name_val = st.text_input("Name *", "")
#         phone_val = st.text_input("Phone", "")
#         contact_val = st.text_input("Contact Email", "")
#         parent_val = st.text_input("Parent Email", "")
#         prog_val = st.text_input("Program ID *", "")
#         submitted = st.form_submit_button("Save Student Info")

#     if submitted:
#         if not name_val:
#             st.error("Name is required.")
#         else:
#             result = store_student_record(
#                 name_val, phone_val, contact_val, parent_val, prog_val
#             )
#             st.success(result)

#     # 2) Show existing students
#     st.subheader("Current Students")
#     students = get_all_students()
#     if not students:
#         st.info("No students found.")
#     else:
#         for s in students:
#             student_id = s.get("student_id")
#             name = s.get("name", "")
#             program_id = s.get("program_id", "")
#             phone = s.get("phone", "")

#             st.write(f"**Name:** {name}, **ID:** {student_id}, **Program:** {program_id}, **Phone:** {phone}")

#             # Add a delete button for each student
#             if st.button(f"Delete (ID={student_id})", key=f"btn_delete_{student_id}"):
#                 # Optional confirmation - not built into Streamlit, so we skip or do a second step
#                 success = delete_student_record(student_id)
#                 if success:
#                     st.success(f"Student {name} (ID={student_id}) deleted.")
#                     st.rerun()  # Refresh the page to remove them from the list
#                 else:
#                     st.error("Delete failed or no such student.")

#####################
# PAGE: Take Attendance (MongoDB)
#####################
def page_take_attendance():
    st.header("Take Attendance (One-Form Method)")

    # Retrieve all students from MongoDB
    students = get_all_students()  # e.g., [{'name': 'Alice', 'program_id': 'ABC123'}, ...]

    # If no students at all, show a warning
    if not students:
        st.warning("No students found.")
        return

    # Filter by permitted programs if the user is an instructor
    permitted_programs = get_permitted_programs()
    if permitted_programs is not None:
        # Keep only students whose program_id is in the permitted list
        students = [s for s in students if s.get("program_id") in permitted_programs]
        if not students:
            st.warning("No students found for your assigned programs.")
            return

    # Build form to mark attendance for each student
    with st.form("attendance_form"):
        st.write("Mark Attendance for All Students Below")
        attendance_dict = {}

        for s in students:
            student_label = f"{s.get('name','')} | Program: {s.get('program_id','')}"
            status_key = f"status_{s['_id']}"
            comment_key = f"comment_{s['_id']}"

            st.subheader(student_label)
            status_val = st.selectbox("Status", ["Present", "Late", "Absent"], key=status_key)
            comment_val = st.text_input("Comment (Optional)", key=comment_key)

            attendance_dict[s["_id"]] = {
                "name": s.get("name", ""),
                "program_id": s.get("program_id", ""),
                "status": status_val,
                "comment": comment_val
            }

        submitted = st.form_submit_button("Submit All Attendance")

    if submitted:
        for student_id, data in attendance_dict.items():
            name = data["name"]
            prog = data["program_id"]
            status = data["status"]
            comment = data["comment"]

            try:
                result_msg = record_student_attendance_in_array(name, prog, status, comment)
                st.info(f"Marked {name} ({prog}) as {status}. {result_msg}")
            except Exception as e:
                st.error(f"Error marking attendance for {name}: {e}")

#####################
# PAGE: Review Attendance (MongoDB)
#####################

def page_review_attendance():
    st.header("Review Attendance Logs (MongoDB)")

    col1, col2 = st.columns(2)

    # Option 1) Load All Attendance
    if col1.button("Load All Attendance"):
        try:
            all_records = get_all_attendance_subdocs()  
            # e.g. each doc might be:
            # {"student_id": "xxxx", "name": "Alice", "program_id": "ABC123", "attendance": {"date":..., "status":..., "comment":...}}

            # Filter by permitted programs if instructor
            permitted_programs = get_permitted_programs()
            if permitted_programs is not None:
                all_records = [r for r in all_records if r.get("program_id") in permitted_programs]

            st.subheader("Daily Attendance Logs")
            if not all_records:
                st.write("No attendance records found for your assigned programs.")
            else:
                for doc in all_records:
                    att = doc.get("attendance", {})
                    date_val = att.get("date", "")
                    status_val = att.get("status", "")
                    comment_val = att.get("comment", "")
                    st.write(
                        f"**Name:** {doc.get('name','')} "
                        f"| **Program:** {doc.get('program_id','')} "
                        f"| **Date:** {date_val} "
                        f"| **Status:** {status_val} "
                        f"| **Comment:** {comment_val}"
                    )
        except Exception as e:
            st.error(f"Error fetching attendance logs: {e}")

    # Option 2) Load Missed Counts
    if col2.button("Load Missed Counts (All Students)"):
        try:
            missed_data = get_missed_counts_for_all_students()
            # Filter if instructor
            permitted_programs = get_permitted_programs()
            if permitted_programs is not None:
                missed_data = [m for m in missed_data if m.get("program_id") in permitted_programs]

            st.subheader("Missed Counts by Student")
            if not missed_data:
                st.write("No data found for your assigned programs.")
            else:
                for d in missed_data:
                    st.write(
                        f"**Name:** {d.get('name','')} "
                        f"| **Program:** {d.get('program_id','')} "
                        f"| **Missed:** {d.get('sum_missed',0)} "
                        f"| **Phone:** {d.get('phone','')}"
                    )
        except Exception as e:
            st.error(f"Error fetching missed counts: {e}")


def page_manage_instructors():
    st.header("Manage Instructors (SQLite)")
    create_instructors_table()  # Ensure table

    with st.expander("Add a New Instructor"):
        uname = st.text_input("Username", key="uname")
        pwd = st.text_input("Password", type="password", key="pwd")
        role = st.selectbox("Role", ["Instructor", "Manager", "Admin"], key="role_select")
        programs = st.text_input("Programs (comma-separated)", key="programs_box")
        if st.button("Create Instructor", key="create_instructor"):
            success = add_instructor(uname, pwd, role, programs)
            if success:
                st.success("Instructor created successfully!")
            else:
                st.error("User might already exist or an error occurred.")

    st.subheader("Current Instructors")
    instructors = list_instructors()
    if not instructors:
        st.write("No instructors found.")
    else:
        for instr in instructors:
            st.write(
                f"**ID:** {instr['instructor_id']} | **Username:** {instr['username']} | "
                f"**Role:** {instr['role']} | **Programs:** {instr['programs']}"
            )

            # Provide quick editing for role or programs
            col1, col2, col3 = st.columns(3)

            with col1:
                new_role = st.selectbox(
                    f"Update Role (ID={instr['instructor_id']})",
                    ["Instructor", "Manager", "Admin"],
                    index=["Instructor","Manager","Admin"].index(instr['role']),
                    key=f"role_{instr['instructor_id']}"
                )
                if st.button(f"Set Role - {instr['instructor_id']}", key=f"btn_role_{instr['instructor_id']}"):
                    update_instructor_role(instr["instructor_id"], new_role)
                    st.rerun()

            with col2:
                new_programs = st.text_input(
                    f"Update Programs (ID={instr['instructor_id']})",
                    value=instr['programs'],
                    key=f"progs_{instr['instructor_id']}"
                )
                if st.button(f"Set Programs - {instr['instructor_id']}", key=f"btn_progs_{instr['instructor_id']}"):
                    update_instructor_programs(instr["instructor_id"], new_programs)
                    st.rerun()

            with col3:
                # DELETE button
                if st.button(f"Delete (ID={instr['instructor_id']})", key=f"btn_delete_{instr['instructor_id']}"):
                    confirmed = st.confirm_dialog(
                        f"Are you sure you want to delete instructor '{instr['username']}'?"
                    ) if hasattr(st, 'confirm_dialog') else st.warning(
                        "Streamlit doesn't have a built-in confirm dialog; consider a custom approach or proceed."
                    )
                    # If you don't have a custom confirm dialog, you might skip or just do the delete directly:
                    # Optionally just do:
                    # if st.button(...):
                    #     success = delete_instructor(instr["instructor_id"])
                    #     if success:
                    #         st.success(f"Instructor {instr['username']} deleted.")
                    #         st.rerun()
                    #     else:
                    #         st.error("Delete failed or no such user.")
                    
                    # Assuming you skip the confirm dialog for demonstration:
                    success = delete_instructor(instr["instructor_id"])
                    if success:
                        st.success(f"Instructor {instr['username']} deleted.")
                        st.rerun()
                    else:
                        st.error("Delete failed or instructor not found.")


#####################
# PAGE: Generate Reports
#####################


def page_generate_reports():
    st.header("Generate Reports with Pygwalker")

    # 1) Fetch attendance records
    records = fetch_all_attendance_records()
    if not records:
        st.info("No attendance data found.")
        return

    # 2) Flatten each sub-doc so 'attendance' fields become top-level
    flattened = []
    for r in records:
        att = r["attendance"]
        flattened.append({
            "student_id": r.get("student_id"),
            "name": r.get("name"),
            "program_id": r.get("program_id"),
            "date": att.get("date"),
            "status": att.get("status"),
            "comment": att.get("comment", "")
        })

    df = pd.DataFrame(flattened)
    if df.empty:
        st.info("No valid attendance data to display.")
        return

    # Convert date field if it's a string
    # If 'date' is already a datetime in Mongo, you can skip or adjust as needed
    if df["date"].dtype == object:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 3) Launch Pygwalker for interactive exploration
    # The user can create bar charts, line charts, pivot tables, etc. with a GUI
    with st.expander("Data Explorer"):
        dataframe_explorer_results = dataframe_explorer(df, case=False)
        explorer_results_df = pd.DataFrame(dataframe_explorer_results)
        if explorer_results_df.shape[0] == 0:
            st.info("Review Selection")

        st.dataframe(explorer_results_df, use_container_width=True)
    with st.expander("Data Visualizer"):
        components.html(pyg.to_html(explorer_results_df, env="Streamlit"), height=1000, scrolling=True)

    st.subheader("Sweetviz Report")
    st.write("Generate a Sweetviz report on the same data.")

    if st.button("Generate Sweetviz Report"):
        # 1) Create and save the Sweetviz report to an HTML file
        report = sweetviz.analyze(explorer_results_df)
        report_name = "sweetviz_report.html"
        report.show_html(report_name, open_browser=False)
        
        # 2) Display the generated HTML file in Streamlit
        with open(report_name, "r", encoding="utf-8") as f:
            sweetviz_html = f.read()

        # Render the Sweetviz report in an iframe
        components.html(sweetviz_html, height=800, scrolling=True)
        st.subheader("Download Sweetviz HTML")
        st.download_button(
            label="Download Sweetviz HTML",
            data=sweetviz_html,
            file_name="Sweetviz_Report.html",
            mime="text/html",
        )

import streamlit as st
from datetime import date, time, datetime
from dateutil import parser

# Example placeholders for create_schedule, list_schedules, etc.
from schedules_db import create_schedule, list_schedules, update_schedule, delete_schedule

def page_manage_schedules():
    st.header("Manage Class Schedules")

    instructor_id = st.session_state.get("instructor_id", None)
    if not instructor_id:
        st.error("You must be logged in as an instructor to manage schedules.")
        return

    # Determine which programs the instructor can manage
    raw_programs = st.session_state.get("instructor_programs", "")
    permitted_programs = [p.strip() for p in raw_programs.split(",") if p.strip()]
    if not permitted_programs:
        st.warning("You currently have no assigned programs. Contact an admin if you need access.")
        return

    st.subheader("Create New Schedule")

    selected_prog = st.selectbox("Select Program", permitted_programs)
    title = st.text_input("Class Title", "")
    recurrence = st.selectbox("Recurrence", ["None", "Weekly", "Monthly"],
                              help="Choose 'None' for a one-time class, or 'Weekly/Monthly' for recurring classes.")

    notes = st.text_area("Additional Notes/Description")

    days_times = []
    start_dt = None
    end_dt = None

    if recurrence == "None":
        # A one-time class
        chosen_date = st.date_input("Class Date", value=date.today())
        start_t = st.time_input("Start Time", value=time(9, 0))
        end_t = st.time_input("End Time", value=time(10, 0))
        location = st.text_input("Location (e.g., Zoom or Physical Room)")

        # We'll store one-time classes as a single start/end datetime
        # 'days_times' remains empty
        if st.button("Create Schedule"):
            start_dt = datetime.combine(chosen_date, start_t)
            end_dt = datetime.combine(chosen_date, end_t)
            doc = {
                "instructor_id": instructor_id,
                "program_id": selected_prog,
                "title": title,
                "recurrence": "None",
                "notes": notes,
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "days_times": [],  # no multiple day/time objects
                "location": location,  # optional top-level field if you want
            }
            new_id = create_schedule(doc)
            st.success(f"Created one-time schedule with ID: {new_id}")
            st.rerun()

    else:
        # Recurring (Weekly or Monthly)
        st.write("Select multiple days, each with its own time and location.")
        selected_days = st.multiselect("Days of Week", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])

        # Build an array of day/time blocks
        for d in selected_days:
            st.write(f"**Times/Location for {d}**")
            col1, col2 = st.columns(2)
            start_for_day = col1.time_input(f"{d} Start", value=time(9,0), key=f"{d}_start")
            end_for_day = col1.time_input(f"{d} End", value=time(10,0), key=f"{d}_end")
            loc_for_day = col2.text_input(f"{d} Location", value="", key=f"{d}_loc")

            days_times.append({
                "day": d,
                "start_time": str(start_for_day),  # "HH:MM"
                "end_time": str(end_for_day),
                "location": loc_for_day
            })

        if st.button("Create Schedule"):
            doc = {
                "instructor_id": instructor_id,
                "program_id": selected_prog,
                "title": title,
                "recurrence": recurrence,
                "notes": notes,
                # for multi-day classes
                "days_times": days_times,
                # set single day/time fields to None
                "start_datetime": None,
                "end_datetime": None
            }
            new_id = create_schedule(doc)
            st.success(f"Created recurring schedule with ID: {new_id}")
            st.rerun()

    # --- Show existing schedules ---
    st.subheader("Existing Schedules")
    all_schedules = list_schedules(instructor_id=instructor_id)
    if not all_schedules:
        st.info("No schedules found.")
        return

    # filter by assigned programs
    filtered = [sch for sch in all_schedules if sch.get("program_id") in permitted_programs]
    if not filtered:
        st.info("No schedules for your assigned programs.")
        return

    for sch in filtered:
        sid = sch["_id"]
        st.write("---")
        st.write(f"**Title**: {sch.get('title','')} | **Program**: {sch.get('program_id','')}")
        st.write(f"**Recurrence**: {sch.get('recurrence','None')}")
        st.write(f"**Notes**: {sch.get('notes','')}")
        # If the doc has "location" at top level for one-time classes
        if sch.get("location"):
            st.write(f"**Location**: {sch['location']}")

        if sch.get("recurrence") == "None":
            # One-time
            st.write(f"**Date/Time**: {sch.get('start_datetime')} -> {sch.get('end_datetime')}")
        else:
            # Recurring
            dt_list = sch.get("days_times", [])
            if dt_list:
                st.write("**Days/Times**:")
                for d_obj in dt_list:
                    st.write(f"- {d_obj['day']}: {d_obj['start_time']} -> {d_obj['end_time']}, Loc: {d_obj.get('location','')}")
        # Buttons
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"Edit {sid}"):
                st.session_state["editing_schedule"] = sid
                st.rerun()
        with c2:
            if st.button(f"Delete {sid}"):
                if delete_schedule(sid):
                    st.success("Schedule deleted.")
                    st.rerun()
                else:
                    st.error("Delete failed or no such schedule.")

    # --- Edit Form ---
    editing_id = st.session_state.get("editing_schedule")
    if editing_id:
        st.subheader(f"Editing Schedule: {editing_id}")
        schedule_doc = next((x for x in filtered if x["_id"] == editing_id), None)
        if not schedule_doc:
            st.error("Schedule not found or not authorized.")
            return

        old_title = schedule_doc.get("title","")
        old_notes = schedule_doc.get("notes","")
        old_recurrence = schedule_doc.get("recurrence","None")
        old_location = schedule_doc.get("location","")  # for one-time classes
        old_days_times = schedule_doc.get("days_times", [])
        st.write("Program:", schedule_doc.get("program_id",""))  # read-only, or let them choose from permitted_programs

        new_title = st.text_input("Edit Title", value=old_title)
        new_recurrence = st.selectbox("Recurrence", ["None","Weekly","Monthly"], index=["None","Weekly","Monthly"].index(old_recurrence))
        new_notes = st.text_area("Edit Notes", value=old_notes)

        if new_recurrence == "None":
            # One-time
            existing_start = schedule_doc.get("start_datetime")
            existing_end = schedule_doc.get("end_datetime")

            # parse if strings
            if isinstance(existing_start, str):
                existing_start = parser.parse(existing_start)
            if isinstance(existing_end, str):
                existing_end = parser.parse(existing_end)

            start_date_val = existing_start.date() if existing_start else date.today()
            start_time_val = existing_start.time() if existing_start else time(9,0)
            end_date_val = existing_end.date() if existing_end else date.today()
            end_time_val = existing_end.time() if existing_end else time(10,0)

            edited_start_date = st.date_input("Start Date", value=start_date_val)
            edited_start_time = st.time_input("Start Time", value=start_time_val)
            edited_end_date = st.date_input("End Date", value=end_date_val)
            edited_end_time = st.time_input("End Time", value=end_time_val)
            edited_location = st.text_input("Location", value=old_location)

            # days_times not used, but we can set it to []
            new_days_times = []
        else:
            # Recurring
            # parse old days_times
            old_selected_days = [d["day"] for d in old_days_times]
            selected_days = st.multiselect("Days of Week", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], default=old_selected_days)

            new_days_times = []
            for d in selected_days:
                # find existing day info
                existing = next((x for x in old_days_times if x["day"] == d), None)
                default_start = time(9,0)
                default_end = time(10,0)
                default_loc = ""
                if existing:
                    s_split = existing["start_time"].split(":") if "start_time" in existing else ["9","0"]
                    default_start = time(int(s_split[0]), int(s_split[1]))
                    e_split = existing["end_time"].split(":") if "end_time" in existing else ["10","0"]
                    default_end = time(int(e_split[0]), int(e_split[1]))
                    default_loc = existing.get("location","")

                st.write(f"**Times/Location for {d}**")
                col_a, col_b = st.columns(2)
                new_start = col_a.time_input(f"{d} Start", value=default_start, key=f"{editing_id}_{d}_start")
                new_end = col_a.time_input(f"{d} End", value=default_end, key=f"{editing_id}_{d}_end")
                new_loc = col_b.text_input(f"{d} Location", value=default_loc, key=f"{editing_id}_{d}_loc")

                new_days_times.append({
                    "day": d,
                    "start_time": str(new_start),
                    "end_time": str(new_end),
                    "location": new_loc
                })
            # for recurring, no single start/end
            edited_location = None  # or omit this field

        if st.button("Save Changes"):
            updates = {
                "title": new_title,
                "recurrence": new_recurrence,
                "notes": new_notes
            }

            if new_recurrence == "None":
                # single day/time
                updates["days_times"] = []
                # combine date & time
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
                updates.pop("location", None)  # remove if you stored location at top level for one-time

            success = update_schedule(editing_id, updates)
            if success:
                st.success("Schedule updated.")
            else:
                st.error("No changes made or update failed.")
            st.session_state.pop("editing_schedule", None)
            st.rerun()




# def page_take_attendance():
#     st.header("Take Attendance (One-Form Method)")
    
#     # 1) Retrieve students from your MongoDB
#     students = get_all_students()  # e.g. returns a list of dicts: [{'_id': ObjectId(...), 'name': 'Alice', 'program_id': 'ABC'}, ...]

#     # 2) If no students, show a warning and end
#     if not students:
#         st.warning("No students found.")
#         return

#     # 3) Build a single form to collect all statuses & comments
#     with st.form("attendance_form"):
#         st.write("Mark Attendance for All Students Below")

#         # We'll store all statuses in a dictionary for processing after form submission
#         attendance_dict = {}

#         for s in students:
#             student_label = f"{s.get('name', '')} | Program: {s.get('program_id', '')}"
#             # Unique keys for each widget to avoid collisions
#             status_key = f"status_{s['_id']}"
#             comment_key = f"comment_{s['_id']}"

#             st.subheader(student_label)
#             # For each student, we create a selectbox + text_input
#             status_val = st.selectbox(
#                 "Status", ["Present", "Late", "Absent"],
#                 key=status_key
#             )
#             comment_val = st.text_input(
#                 "Comment (Optional)",
#                 key=comment_key
#             )

#             # We'll store in a dict for use after form submission
#             attendance_dict[s["_id"]] = {
#                 "name": s.get("name", ""),
#                 "program_id": s.get("program_id", ""),
#                 "status": status_val,
#                 "comment": comment_val
#             }

#         # Single submit button at the bottom
#         submitted = st.form_submit_button("Submit All Attendance")

#     # 4) If the form is submitted, process each student's data in a loop
#     if submitted:
#         for student_id, data in attendance_dict.items():
#             name = data["name"]
#             prog = data["program_id"]
#             status = data["status"]
#             comment = data["comment"]

#             try:
#                 # This is the function that writes to MongoDB
#                 res = record_student_attendance_in_array(name, prog, status, comment)
#                 st.info(f"Marked {name} ({prog}) as {status}. Result: {res}")
#             except Exception as e:
#                 st.error(f"Error marking attendance for {name}: {e}")

# def page_review_attendance():
#     st.header("Review Attendance Logs (MongoDB)")
#     col1, col2 = st.columns(2)

#     if col1.button("Load All Attendance"):
#         try:
#             all_records = get_all_attendance_subdocs()
#             st.subheader("All Daily Attendance Logs (Unwound Sub-Docs)")
#             if not all_records:
#                 st.write("No attendance records found.")
#             else:
#                 for doc in all_records:
#                     attendance_sub = doc.get("attendance", {})
#                     date_val = attendance_sub.get("date", "")
#                     status_val = attendance_sub.get("status", "")
#                     comment_val = attendance_sub.get("comment", "")
#                     st.write(
#                         f"**Name:** {doc.get('name','')} | **Program:** {doc.get('program_id','')}"
#                         f" | **Date:** {date_val} | **Status:** {status_val} | **Comment:** {comment_val}"
#                     )
#         except Exception as e:
#             st.error(f"Error fetching attendance sub-docs: {e}")

#     if col2.button("Load Missed Counts (All Students)"):
#         try:
#             missed_data = get_missed_counts_for_all_students()
#             st.subheader("Missed Counts by Student")
#             if not missed_data:
#                 st.write("No data found.")
#             else:
#                 for doc in missed_data:
#                     st.write(
#                         f"**Name:** {doc.get('name','')} | **Phone:** {doc.get('phone','')} | "
#                         f"**Program:** {doc.get('program_id','')} | **Missed:** {doc.get('sum_missed',0)}"
#                     )
#         except Exception as e:
#             st.error(f"Error fetching missed counts: {e}")
