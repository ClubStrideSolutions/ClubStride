
# import pygwalker as pyg
# import streamlit.components.v1 as components
# import sweetviz
# pages.py

import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
import pandas as pd
from datetime import datetime, time, date,timedelta
from dateutil import parser
import plotly.express as px
from pathlib import Path
import openai
from openai import OpenAI
from datetime import datetime, time, date
import pandas as pd
import plotly.express as px
import io, os
from collections import Counter


from instructors_db import (
    initialize_tables, list_instructors, list_programs, add_program,
    assign_instructor_to_program, remove_instructor_from_program, list_instructor_programs,
    add_instructor, update_instructor_email, get_instructor_email,
    update_program, update_instructor_role, delete_instructor,
    authenticate_instructor, update_instructor_password, delete_program
)

from students_db import (
    store_student_record, get_all_students, record_student_attendance_in_array,
    get_all_attendance_subdocs, delete_attendance_subdoc, upsert_attendance_subdoc,    
    get_missed_counts_for_all_students, delete_student_record, update_attendance_subdoc,
    fetch_all_attendance_records, update_student_info, check_admin,
    get_student_count_as_of_last_week, get_attendance_subdocs_in_range, get_attendance_subdocs_last_week 
)

from schedules_db import (
    create_schedule, list_schedules, list_schedules_by_program,
    update_schedule, notify_schedule_change,delete_schedule)

from documents_db import (
    create_document, list_documents, create_document_instance,
    send_document, update_document_status, get_document_status_counts,
    send_reminder, get_documents_for_recipient, search_documents_by_recipient, 
    delete_document, check_document_instance_exists
)
from document_storage import save_uploaded_document, get_document_file_path

# Admin check


###################################
# UTILITY: Get permitted program NAMES
###################################

def handle_mark_attendance_today(single_stud):
    with st.form("today_attendance_form"):
        st.write(f"**Recording attendance for: {single_stud['name']}**")
        current_dt = datetime.now()
        st.write(f"Date: {current_dt.strftime('%Y-%m-%d')}")
        st.write(f"Time: {current_dt.strftime('%H:%M')}")

        status_opt = ["Present", "Late", "Absent", "Excused"]
        status_icons = ["✅", "🕒", "❌", "🔖"]
        status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]

        selected_status_idx = st.selectbox(
            "Status:",
            options=range(len(status_opt)),
            format_func=lambda i: status_options_with_icons[i],
            index=0
        )
        chosen_status = status_opt[selected_status_idx]

        comment_txt = st.text_area("Comment (Optional)", height=100)

        col1, col2 = st.columns(2)
        with col1:
            cancel_btn = st.form_submit_button("Cancel")

        with col2:
            submit_btn = st.form_submit_button("Submit Attendance")

        if submit_btn:
            with st.spinner("Recording attendance..."):
                try:
                    # Pass the student_id directly to avoid regenerating it
                    msg = record_student_attendance_in_array(
                        name=single_stud["name"],
                        program_id=single_stud["program_id"],
                        status=chosen_status,
                        comment=comment_txt,
                        attendance_date=current_dt,
                        student_id=single_stud["student_id"]  # Pass the existing student_id
                    )
                    st.success(f"✅ Marked {single_stud['name']} as {chosen_status}. {msg}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

                st.session_state.pop("attendance_student", None)
                st.session_state.pop("attendance_mode", None)
                st.rerun()

        if cancel_btn:
            st.session_state.pop("attendance_student", None)
            st.session_state.pop("attendance_mode", None)
            st.info("ℹ️ Individual attendance marking canceled.")
            st.rerun()


# Similarly, for the "Mark Past" attendance form:
def handle_mark_attendance_past(single_stud):
    with st.form("past_attendance_form_students"):
        st.write(f"**Recording past attendance for: {single_stud['name']}**")

        date_val = st.date_input("Session Date", value=date.today())
        time_val = st.time_input("Session Time", value=time(9, 0))
        combined_dt = datetime.combine(date_val, time_val)

        status_opt = ["Present", "Late", "Absent", "Excused"]
        status_icons = ["✅", "🕒", "❌", "🔖"]
        status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opt)]

        selected_status_idx = st.selectbox(
            "Status:",
            options=range(len(status_opt)),
            format_func=lambda i: status_options_with_icons[i],
            index=0
        )
        chosen_status = status_opt[selected_status_idx]

        comment_txt = st.text_area("Comment (Optional)", height=100)

        col1, col2 = st.columns(2)
        with col1:
            cancel_btn = st.form_submit_button("Cancel")

        with col2:
            submit_btn = st.form_submit_button("Submit Past Attendance")

        if submit_btn:
            with st.spinner("Recording past attendance..."):
                try:
                    # Pass the student_id directly to avoid regenerating it
                    msg = record_student_attendance_in_array(
                        name=single_stud["name"],
                        program_id=single_stud["program_id"],
                        status=chosen_status,
                        comment=comment_txt,
                        attendance_date=combined_dt,
                        student_id=single_stud["student_id"]  # Pass the existing student_id
                    )
                    st.success(
                        f"✅ Marked {single_stud['name']} as {chosen_status} on "
                        f"{combined_dt.strftime('%Y-%m-%d %H:%M')}. {msg}"
                    )
                except Exception as e:
                    st.error(f"❌ Error: {e}")

                st.session_state.pop("attendance_student", None)
                st.session_state.pop("attendance_mode", None)
                st.rerun()

        if cancel_btn:
            st.session_state.pop("attendance_student", None)
            st.session_state.pop("attendance_mode", None)
            st.info("ℹ️ Past attendance marking canceled.")
            st.rerun()


def _format_time_12h(t):
    """
    Safely handle both a time object and a "HH:MM:SS" string.
    Returns a 12-hour formatted string like "9:00 AM".
    """
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


# ------------------------------------
# pages.py
# ------------------------------------

# Make sure you have these helper imports or adapt them to your structure:


# pages.py

def page_dashboard():
    st.header("Program Dashboard")

    # --------------------------------------------------------
    # 1) Ensure user is logged in (admin or instructor)
    # --------------------------------------------------------
    is_admin = st.session_state.get("is_admin", False)
    instructor_logged_in = st.session_state.get("instructor_logged_in", False)
    if not (is_admin or instructor_logged_in):
        st.error("You must be logged in to view the Dashboard.")
        return

    # --------------------------------------------------------
    # 2) Determine permitted program IDs if instructor
    # --------------------------------------------------------
    if is_admin:
        permitted_ids = None  # Admin sees all
    else:
        permitted_ids = st.session_state.get("instructor_program_ids", [])
        if not permitted_ids:
            st.warning("No assigned programs found. Please contact an admin.")
            return

    # --------------------------------------------------------
    # 3) Compute "This Week" vs. "Last Week" attendance
    # --------------------------------------------------------
    now = datetime.utcnow()
    last_7_days = now - timedelta(days=7)
    prev_7_days = now - timedelta(days=14)

    # Fetch subdocs for the last 7 days
    subdocs_this_week = get_attendance_subdocs_in_range(last_7_days, now)
    # Fetch subdocs for the previous 7-day window
    subdocs_last_week = get_attendance_subdocs_in_range(prev_7_days, last_7_days)

    # If instructor, filter out data not in assigned programs
    if permitted_ids is not None:
        subdocs_this_week = [doc for doc in subdocs_this_week if doc["program_id"] in permitted_ids]
        subdocs_last_week = [doc for doc in subdocs_last_week if doc["program_id"] in permitted_ids]

    # Total attendance records each week
    total_this_week = len(subdocs_this_week)
    total_last_week = len(subdocs_last_week)
    attendance_delta = total_this_week - total_last_week

    # --------------------------------------------------------
    # 4) Load students (admin = all, instructor = assigned)
    # --------------------------------------------------------
    if is_admin:
        students = get_all_students()
    else:
        students = get_all_students(program_ids=permitted_ids)
    total_students = len(students)

    # --------------------------------------------------------
    # 5) Absences This Week & Attendance Rate
    # --------------------------------------------------------
    absences_this_week = sum(1 for doc in subdocs_this_week if doc["attendance"]["status"] == "Absent")

    # Convert status to “attended” or not
    def is_attended(status):
        return status in ["Present", "Late"]

    # This week’s possible vs. attended
    possible_this_week = len(subdocs_this_week)  
    attended_this_week = sum(is_attended(d["attendance"]["status"]) for d in subdocs_this_week)
    rate_this_week = (attended_this_week / possible_this_week * 100) if possible_this_week else 0

    # Last week’s possible vs. attended
    possible_last_week = len(subdocs_last_week)
    attended_last_week = sum(is_attended(d["attendance"]["status"]) for d in subdocs_last_week)
    rate_last_week = (attended_last_week / possible_last_week * 100) if possible_last_week else 0

    # Compare rates
    rate_delta = rate_this_week - rate_last_week

    # --------------------------------------------------------
    # 6) Display Attendance Rate metric
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 7) Mark At-Risk Students (≥ 2 absences this week)
    # --------------------------------------------------------
    st.subheader("Absences & At-Risk Alerts")
    absent_counter = Counter()
    for doc in subdocs_this_week:
        if doc["attendance"]["status"] == "Absent":
            absent_counter[doc["student_id"]] += 1

    at_risk_threshold = 2
    at_risk_students = [sid for sid, count in absent_counter.items() if count >= at_risk_threshold]

    if at_risk_students:
        st.warning(f"{len(at_risk_students)} student(s) have ≥ {at_risk_threshold} absences this week!")
        st.write("**At-Risk Student IDs**:")
        for sid in at_risk_students:
            st.write(f"- ID: {sid} (Absences = {absent_counter[sid]})")
    else:
        st.success("No students reached the at-risk absence threshold this week.")

    # --------------------------------------------------------
    # 8) Display Key Metrics Row
    # --------------------------------------------------------
    st.write("### Key Metrics")
    colA, colB, colC, colD = st.columns(4)
    with colA:
        st.metric(
            label="Attendance This Week",
            value=total_this_week,
            delta=f"{attendance_delta} vs. last week"
        )
    with colD:
        st.metric("Total Students", total_students)
    with colC:
        st.metric("Absences This Week", absences_this_week)
    with colB:
            # st.subheader("Attendance Rate & Comparison")
        st.metric(
            label="Attendance Rate (This Week)",
            value=f"{rate_this_week:.1f}%",
            delta=f"{rate_delta:+.1f}% vs. last week"
        )


    # --------------------------------------------------------
    # 10) Top Absent Students (This Week)
    # --------------------------------------------------------
    name_counter = Counter()
    for doc in subdocs_this_week:
        if doc["attendance"]["status"] == "Absent":
            name_counter[doc["name"]] += 1

    if name_counter:
        st.write("### Top Absent Students (This Week)")
        top_abs = name_counter.most_common(5)
        for name, count in top_abs:
            st.write(f"- **{name}**: {count} absence(s)")
    else:
        st.info("No absences so far this week.")

    # --------------------------------------------------------
    # 11) Quick Chart of Status Distribution (Last 7 Days)
    # --------------------------------------------------------
    if subdocs_this_week:
        rows = []
        for d in subdocs_this_week:
            rows.append({
                "name": d["name"],
                "status": d["attendance"]["status"],
                "date": d["attendance"]["date"]
            })
        df = pd.DataFrame(rows)

        # st.dataframe(df, use_container_width=True)
        group_data = df.groupby(["name", "status"]).size().reset_index(name="count")

            # 2) Plot a grouped bar chart
        fig_bar = px.bar(
                group_data,
                x="name",
                y="count",
                color="status",
                barmode="group",  # or "stack" if you prefer a stacked bar
                title="Attendance Distribution by Student (Last 7 Days)"
            )

        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No attendance records found for this week.")

    
    st.write("---")
    st.info("Use the sidebar for additional navigation and tools.")

def page_my_settings():
    st.header("My Settings")

    # If no one is logged in, block access:
    if not (st.session_state.get("is_admin") or st.session_state.get("instructor_logged_in")):
        st.error("You must be logged in to access My Settings.")
        return

    # Let’s do a radio for the two actions:
    setting_choice = st.radio(
        "Choose an action",
        ["Logout","Change My Password"],
        horizontal=True
    )

    if setting_choice == "Change My Password":
        _render_change_password()
    else:
        _render_logout_button()


def _render_change_password():
    st.subheader("Change My Password")

    # If no instructor is logged in, or if user is admin-only (no instructor ID), block it
    if not st.session_state.get("instructor_logged_in"):
        st.info("Only an instructor can change a password here.")
        return

    old_pass = st.text_input("Old Password", type="password")
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        # ... do your re-auth check, then update_instructor_password logic ...        
        # Find username from session
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


def _render_logout_button():
    st.subheader("Logout")
    st.write("Click below to log out from the system.")

    if st.button("Logout Now"):
        st.session_state.is_admin = False
        st.session_state.instructor_logged_in = False
        st.session_state.instructor_id = None
        st.session_state.instructor_role = None
        st.session_state.instructor_username = None
        st.session_state.menu_choice = "Home"

        st.success("You have been logged out.")
        st.rerun()

def page_help():
    """
    A comprehensive "Help / User Guide" page that explains how to use the 
    Club Stride Attendance System. It references major workflows found 
    elsewhere in the code: logging in, managing students, taking attendance, 
    schedules, instructors, reports, etc.
    """
    st.header("📚 Help & User Guide")
    
    # Update the welcome banner with better contrast
    st.markdown("""
    <div style="padding: 15px; border-radius: 5px; border-left: 5px solid #4682B4; 
         background-color: #e6f3ff; margin-bottom: 20px; border: 1px solid #c0d8f0;">
    <h3 style="color: #2c5282; margin-top: 0;">Welcome to the Club Stride Attendance System</h3>
    <p style="color: #2d3748;">This guide will help you navigate and use all features of the system effectively. 
    Select any topic below to learn more about that feature.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Guide Contents")
    
    # Create a table of contents with icons - add background for better visibility
    st.markdown("""
    <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
    <table style="width: 100%; color: #2d3748;">
    <thead>
    <tr>
        <th>Section</th>
        <th>Description</th>
    </tr>
    </thead>
    <tbody>
    <tr>
        <td>🔑 <a href="#login" style="color: #3182ce;">Login</a></td>
        <td>How to access the system as an Admin or Instructor</td>
    </tr>
    <tr>
        <td>📊 <a href="#dashboard" style="color: #3182ce;">Dashboard</a></td>
        <td>Navigating the main dashboard and viewing metrics</td>
    </tr>
    <tr>
        <td>👨‍🎓 <a href="#students" style="color: #3182ce;">Students</a></td>
        <td>Adding, editing, and managing student records</td>
    </tr>
    <tr>
        <td>📝 <a href="#attendance" style="color: #3182ce;">Attendance</a></td>
        <td>Recording daily attendance and past sessions</td>
    </tr>
    <tr>
        <td>📋 <a href="#review" style="color: #3182ce;">Review</a></td>
        <td>Reviewing past attendance and identifying missed sessions</td>
    </tr>
    <tr>
        <td>📅 <a href="#schedules" style="color: #3182ce;">Schedules</a></td>
        <td>Creating and managing class schedules</td>
    </tr>
    <tr>
        <td>📈 <a href="#reports" style="color: #3182ce;">Reports</a></td>
        <td>Generating attendance reports and analysis</td>
    </tr>
    <tr>
        <td>🔒 <a href="#password" style="color: #3182ce;">Password</a></td>
        <td>Changing your login credentials</td>
    </tr>
    <tr>
        <td>👨‍🏫 <a href="#instructors" style="color: #3182ce;">Instructors</a></td>
        <td>Managing instructor accounts (Admin only)</td>
    </tr>
    <tr>
        <td>🚪 <a href="#logout" style="color: #3182ce;">Logout</a></td>
        <td>Securely exiting the system</td>
    </tr>
    </tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")

    # Update all expanders with better contrast
    # 1) Logging In
    st.markdown('<a name="login"></a>', unsafe_allow_html=True)
    with st.expander("🔑 Logging In (Admin or Instructor)"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">🔐</h1>
                <p style="color: #2d3748;"><strong>System Access</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Admin Login</h3>
            <ol style="color: #2d3748;">
                <li>From the sidebar, select <strong>Login</strong></li>
                <li>Choose the radio option <strong>Admin</strong></li>
                <li>Enter your MongoDB connection string</li>
                <li>If valid, you'll see "Admin access granted"</li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Instructor Login</h3>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>From the sidebar, select <strong>Login</strong></li>
                <li>Choose the radio option <strong>Instructor</strong></li>
                <li>Enter your <strong>Username</strong> and <strong>Password</strong></li>
                <li>If correct, you'll see "Welcome, [username]!" and be redirected to the Dashboard</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
            
        st.info("💡 **Tip**: Only Administrators can create instructor accounts or assign programs.")

    # 2) Navigating the Dashboard
    st.markdown('<a name="dashboard"></a>', unsafe_allow_html=True)
    with st.expander("📊 Navigating the Dashboard"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">📈</h1>
                <p style="color: #2d3748;"><strong>Key Metrics</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Dashboard Overview</h3>
            <p style="color: #2d3748;">After logging in, click on <strong>Dashboard</strong> in the sidebar menu to see:</p>
            
            <ul style="color: #2d3748; margin-bottom: 0;">
                <li><strong>This Week's Attendance</strong> - Total attendance records for the current week</li>
                <li><strong>Absences</strong> - Number of absence records in the current week</li>
                <li><strong>At-Risk Students</strong> - Students with excessive absences (≥ 2 absences)</li>
                <li><strong>Attendance Distribution</strong> - Chart showing attendance patterns in the last 7 days</li>
            </ul>
            
            <p style="color: #2d3748; margin-top: 10px; margin-bottom: 0;">The Dashboard provides a quick overview of critical attendance statistics without replacing the detailed reporting features.</p>
            </div>
            """, unsafe_allow_html=True)

    # 3) Managing Students
    st.markdown('<a name="students"></a>', unsafe_allow_html=True)
    with st.expander("👨‍🎓 Managing Students"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">👩‍🎓</h1>
                <p style="color: #2d3748;"><strong>Student Records</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Viewing & Managing Students</h3>
            <ol style="color: #2d3748;">
                <li>Go to <strong>Student Management Suite</strong> → <strong>Manage Students</strong></li>
                <li>You'll see a list of current students with these actions:
                   <ul>
                       <li><strong>Edit</strong> ✏️ - Update student information</li>
                       <li><strong>Delete</strong> 🗑️ - Remove the student from the database</li>
                       <li><strong>Mark Attendance</strong> ✅ - Record today's attendance</li>
                       <li><strong>Mark Past</strong> 📆 - Record attendance for a previous date</li>
                   </ul>
                </li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Adding New Students</h3>
            <p style="color: #2d3748;">Click the <strong>Add or Update Students</strong> tab to create new records:</p>
            
            <h4 style="color: #2c5282; margin-top: 10px;">Single Student Entry</h4>
            <p style="color: #2d3748;">Fill out the form with name, contact info, program, etc.</p>
            
            <h4 style="color: #2c5282; margin-top: 10px;">Bulk CSV Upload</h4>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>Prepare a CSV with these columns:
                   <ul>
                       <li>First Name, Last Name, Number, Email, Grade, School</li>
                   </ul>
                </li>
                <li>Select the Program for these students</li>
                <li>Upload your CSV file</li>
                <li>Review and process the data</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
            
        st.warning("⚠️ **Note**: Instructors will only see students from programs assigned to them.")

    # 4) Taking Attendance
    st.markdown('<a name="attendance"></a>', unsafe_allow_html=True)
    with st.expander("📝 Taking Attendance"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">📋</h1>
                <p style="color: #2d3748;"><strong>Daily Records</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Recording Today's Attendance</h3>
            <ol style="color: #2d3748;">
                <li>Go to <strong>Student Management Suite</strong> → <strong>Attendance & Scheduling</strong> → <strong>Take Attendance</strong></li>
                <li>Select the program (Admin) or view your assigned programs (Instructor)</li>
                <li>For each student, select their status:
                   <ul>
                       <li>✅ <strong>Present</strong> - Student attended class</li>
                       <li>🕒 <strong>Late</strong> - Student arrived late</li>
                       <li>❌ <strong>Absent</strong> - Student did not attend</li>
                       <li>🤝 <strong>Excused</strong> (if available) - Absence with valid reason</li>
                   </ul>
                </li>
                <li>Add any comments as needed</li>
                <li>Click <strong>Submit Attendance</strong></li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Recording Past Attendance</h3>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>Select the <strong>Past Session</strong> tab</li>
                <li>Choose the date and time of the session</li>
                <li>Mark each student's status and add comments</li>
                <li>Click <strong>Submit Past Attendance</strong></li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
            
        st.info("💡 **Tip**: You can use the Quick Select options to mark all students as Present or Absent at once.")
        st.warning("⚠️ **Duplicate Check**: If you've already recorded attendance for the same day, the system will show a warning.")

    # 5) Reviewing Attendance & Missed Counts
    st.markdown('<a name="review"></a>', unsafe_allow_html=True)
    with st.expander("📋 Reviewing Attendance & Missed Counts"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">🔍</h1>
                <p style="color: #2d3748;"><strong>Review Records</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Attendance Records</h3>
            <ol style="color: #2d3748;">
                <li>Go to <strong>Student Management Suite</strong> → <strong>Attendance & Scheduling</strong> → <strong>Review Attendance</strong></li>
                <li>View summary metrics:
                   <ul>
                       <li>Attendance This Week</li>
                       <li>Absences This Week</li>
                       <li>Active Students</li>
                   </ul>
                </li>
                <li>The <strong>All Attendance Records</strong> tab shows a complete attendance history
                   <ul>
                       <li>Filter by Program or Student Name</li>
                       <li>Sort records by date, student, or status</li>
                       <li>Edit or delete individual records</li>
                   </ul>
                </li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Missed Sessions</h3>
            <p style="color: #2d3748;">The <strong>Missed Sessions</strong> tab shows absence patterns:</p>
            <ul style="color: #2d3748; margin-bottom: 0;">
                <li>See which students have the most absences</li>
                <li>Identify attendance trends</li>
                <li>Highlight students who may need intervention</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.success("✅ **Pro Tip**: Use filters to focus on specific programs or students when reviewing records.")

    # 6) Managing Schedules
    st.markdown('<a name="schedules"></a>', unsafe_allow_html=True)
    with st.expander("📅 Managing Schedules"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">🗓️</h1>
                <p style="color: #2d3748;"><strong>Class Schedules</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Creating New Schedules</h3>
            <ol style="color: #2d3748;">
                <li>Navigate to <strong>Student Management Suite</strong> → <strong>Attendance & Scheduling</strong> → <strong>Manage Schedules</strong></li>
                <li>Click <strong>Create a New Schedule</strong></li>
                <li>Enter the Title and select a Program</li>
                <li>Choose a Recurrence Pattern:
                   <ul>
                       <li><strong>One-Time</strong> - Single class session on a specific date</li>
                       <li><strong>Weekly</strong> - Regular sessions on certain days each week</li>
                   </ul>
                </li>
                <li>For One-Time sessions:
                   <ul>
                       <li>Select the date, start time, end time, and location</li>
                   </ul>
                </li>
                <li>For Weekly sessions:
                   <ul>
                       <li>Select which days of the week (Mon, Tue, Wed, etc.)</li>
                       <li>Set start time, end time, and location for each day</li>
                   </ul>
                </li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Managing Existing Schedules</h3>
            <ul style="color: #2d3748; margin-bottom: 0;">
                <li>View all schedules for your assigned programs</li>
                <li>Edit any schedule you created (or any schedule if you're an Admin)</li>
                <li>Delete schedules that are no longer needed</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.info("💡 **Notification**: The system can email students in the associated program about new or changed schedules.")

    # 7) Generating Reports
    st.markdown('<a name="reports"></a>', unsafe_allow_html=True)
    with st.expander("📈 Generating Reports"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">📊</h1>
                <p style="color: #2d3748;"><strong>Data Analysis</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Visualizations</h3>
            <ol style="color: #2d3748;">
                <li>Go to <strong>Student Management Suite</strong> → <strong>Generate Reports</strong></li>
                <li>The <strong>Visualizations</strong> tab shows:
                   <ul>
                       <li>Overall attendance rates</li>
                       <li>Present/absent percentages</li>
                       <li>Program rankings</li>
                       <li>Attendance trends over time</li>
                   </ul>
                </li>
            </ol>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Data Explorer</h3>
            <p style="color: #2d3748;">The <strong>Data Explorer</strong> tab lets you:</p>
            <ul style="color: #2d3748;">
                <li>Filter data by various criteria</li>
                <li>Create custom visualizations</li>
                <li>Export filtered data as CSV</li>
            </ul>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Report Generator</h3>
            <p style="color: #2d3748;">The <strong>Generate Reports</strong> tab allows you to:</p>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>Select a specific program</li>
                <li>Generate a pivot table showing attendance by student and date</li>
                <li>Identify students with excessive absences</li>
                <li>Download a complete Excel report with summary statistics</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
            
        st.success("✅ **Pro Tip**: Regular reporting helps identify attendance patterns early and enables timely interventions for at-risk students.")

    # 8) Changing Your Password
    st.markdown('<a name="password"></a>', unsafe_allow_html=True)
    with st.expander("🔒 Changing Your Password (Instructors)"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">🔑</h1>
                <p style="color: #2d3748;"><strong>Account Security</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Password Management</h3>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>If you're logged in as an Instructor, click <strong>Change My Password</strong> in the sidebar</li>
                <li>Enter your current password</li>
                <li>Enter your new password twice (for confirmation)</li>
                <li>Click <strong>Update Password</strong></li>
            </ol>
            
            <p style="color: #2d3748; margin-top: 10px; margin-bottom: 0;">The system will verify your current password and then securely update your credentials.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.warning("⚠️ **Security Tip**: Choose a strong password with at least 8 characters, including numbers, letters, and special characters.")

    # 9) Managing Instructors (Admin Only)
    st.markdown('<a name="instructors"></a>', unsafe_allow_html=True)
    with st.expander("👨‍🏫 Managing Instructors (Admin Only)"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">👩‍🏫</h1>
                <p style="color: #2d3748;"><strong>Staff Management</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Instructor Management (Admins Only)</h3>
            <ol style="color: #2d3748;">
                <li>Log in as an Admin</li>
                <li>Click <strong>Manage Instructors</strong> in the sidebar</li>
                <li>From this page, you can:</li>
            </ol>
            
            <h4 style="color: #2c5282; margin-top: 10px;">Create New Instructors</h4>
            <ul style="color: #2d3748;">
                <li>Set username, password, and role (Instructor, Manager, or Admin)</li>
            </ul>
            
            <h4 style="color: #2c5282; margin-top: 10px;">Manage Existing Instructors</h4>
            <ul style="color: #2d3748;">
                <li>Edit roles and permissions</li>
                <li>Reset passwords</li>
                <li>Delete instructor accounts</li>
            </ul>
            
            <h4 style="color: #2c5282; margin-top: 10px;">Program Assignment</h4>
            <ul style="color: #2d3748; margin-bottom: 0;">
                <li>Link instructors to specific programs</li>
                <li>Determine which students and attendance data they can access</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.error("⛔ **Warning**: Deleting instructors or programs cannot be easily undone. Proceed with caution.")

    # 10) Logging Out
    st.markdown('<a name="logout"></a>', unsafe_allow_html=True)
    with st.expander("🚪 Logging Out"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">🔓</h1>
                <p style="color: #2d3748;"><strong>Exit System</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">Secure Logout</h3>
            <ol style="color: #2d3748; margin-bottom: 0;">
                <li>Click the <strong>Logout</strong> button in the sidebar menu</li>
                <li>The system will clear your session data including:
                   <ul>
                       <li>Your user role</li>
                       <li>Assigned programs</li>
                       <li>Authentication status</li>
                   </ul>
                </li>
                <li>You'll be returned to the Home screen</li>
            </ol>
            
            <p style="color: #2d3748; margin-top: 10px; margin-bottom: 0;">Always log out when you're finished using the system, especially on shared computers.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.info("💡 **Security Tip**: For maximum security, close your browser after logging out.")

    # 11) Additional Admin Tools (Optional)
    with st.expander("🛠️ Additional Admin Tools"):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("""
            <div style="text-align: center; background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
                <h1 style="font-size: 48px; color: #2c5282;">⚙️</h1>
                <p style="color: #2d3748;"><strong>Advanced Options</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background-color: #e2e8f0; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e0;">
            <h3 style="color: #2c5282; margin-top: 0;">MongoDB Connection</h3>
            <ul style="color: #2d3748;">
                <li>When logging in as Admin, you provide the connection string for the database</li>
                <li>This connection enables all Admin-level operations</li>
            </ul>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Program Management</h3>
            <ul style="color: #2d3748;">
                <li>Create new programs for different classes or locations</li>
                <li>Delete programs that are no longer active</li>
                <li>Reassign programs between instructors</li>
            </ul>
            
            <h3 style="color: #2c5282; margin-top: 15px;">Data Administration</h3>
            <ul style="color: #2d3748; margin-bottom: 0;">
                <li>Monitor system usage and performance</li>
                <li>Perform database maintenance tasks</li>
                <li>Manage backups and data integrity</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.error("⛔ **Warning**: Advanced admin tools should only be used by users with proper training and authorization.")

    st.write("---")
    
    # Contact Information and Footer - update with better contrast
    st.markdown("""
    <div style="padding: 15px; border-radius: 5px; background-color: #e2e8f0; border: 1px solid #cbd5e0; text-align: center;">
    <h3 style="color: #2c5282; margin-top: 0;">Need Additional Help?</h3>
    <p style="color: #2d3748;">If you have any questions or need assistance, please contact:</p>
    <p style="color: #2d3748;"><strong>✉️ Email:</strong> <a href="mailto:javier@clubstride.org" style="color: #3182ce;">javier@clubstride.org</a></p>
    <p style="color: #4a5568; font-style: italic; margin-bottom: 0;">Club Stride Attendance System • Version 1.0</p>
    </div>
    """, unsafe_allow_html=True)

def page_unified_login():
    st.header("🔑 Login")
    
    # Create a nice info card for the login page with better visibility
    st.markdown("""
    <div style="padding: 15px; border-radius: 5px; border-left: 5px solid #4682B4; 
         background-color: #e6f3ff; margin-bottom: 20px; border: 1px solid #c0d8f0;">
    <h3 style="color: #2c5282; margin-top: 0;">Welcome to Club Stride</h3>
    <p style="color: #2d3748;">Please select your role and enter your credentials to access the system.</p>
    </div>
    """, unsafe_allow_html=True)

    # If either admin or instructor is already logged in, block re-login
    if st.session_state.get("is_admin", False) or st.session_state.get("instructor_logged_in", False):
        st.info("✅ You are already logged in. You can use the navigation menu to access features.")
        return

    # Create columns for better layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Provide a role selection with better styling
        st.markdown("### Select Role:")
        role_choice = st.radio(
            "",  # Empty label as we already have the markdown header
            ("Admin", "Instructor"),
            horizontal=True,
            index=1,  # Default to Instructor as it's more common
            help="Choose your role to see the appropriate login form"
        )
        
        # Add role descriptions with better background colors
        if role_choice == "Admin":
            st.markdown("""
            <div style="padding: 10px; background-color: #e2e8f0; border-radius: 5px; margin-top: 10px; 
                 border: 1px solid #cbd5e0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <p style="color: #2d3748;"><strong>👑 Administrator</strong></p>
                <p style="font-size: 0.9em; margin-bottom: 0; color: #4a5568;">
                    Full access to system features including user management and program administration.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 10px; background-color: #e2e8f0; border-radius: 5px; margin-top: 10px; 
                 border: 1px solid #cbd5e0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <p style="color: #2d3748;"><strong>👤 Instructor</strong></p>
                <p style="font-size: 0.9em; margin-bottom: 0; color: #4a5568;">
                    Access to attendance tracking, student management, and reporting for assigned programs.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Add a visual separator
        st.markdown('<div style="border-left: 1px solid #a0aec0; height: 100%;"></div>', unsafe_allow_html=True)
        
        # If user chooses Admin
        if role_choice == "Admin":
            st.subheader("👑 Admin Login")
            conn_str = st.text_input(
                "MongoDB Connection String", 
                type="password",
                help="Enter your database connection credentials"
            )
            if st.button("🔐 Login as Admin", use_container_width=True):
                with st.spinner("Verifying credentials..."):
                    if check_admin(conn_str):
                        st.session_state.is_admin = True
                        st.session_state.instructor_logged_in = False
                        st.success("✅ Admin access granted!")
                        # Optionally set a default menu choice so the user sees the admin page
                        st.session_state.menu_choice = "Dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid connection string. Access denied.")
                        
            # Add some guidance for admin login with better styling
            with st.expander("Need Help?"):
                st.markdown("""
                <div style="background-color: #e2e8f0; padding: 10px; border-radius: 5px; margin-top: 5px;">
                <ul style="margin-bottom: 0; padding-left: 20px; color: #2d3748;">
                    <li>Admin login requires a valid MongoDB connection string</li>
                    <li>If you don't have admin credentials, please use instructor login</li>
                    <li>For assistance, contact the system administrator</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

        # If user chooses Instructor
        else:
            st.subheader("👤 Instructor Login")
            
            # Create a card-like container for the login form with better contrast
            st.markdown("""
            <div style="padding: 15px; background-color: #e2e8f0; border-radius: 5px; margin-bottom: 15px; 
                 border: 1px solid #cbd5e0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            """, unsafe_allow_html=True)
            
            username = st.text_input(
                "Username", 
                placeholder="Enter your username",
                help="Your assigned username for the Club Stride system"
            )
            password = st.text_input(
                "Password", 
                type="password", 
                placeholder="Enter your password",
                help="Your account password"
            )
            
            # Add remember me checkbox (for visual design - not functional in this implementation)
            remember_me = st.checkbox("Remember me", value=False, help="Keep me logged in on this device")
            
            login_col1, login_col2 = st.columns([2, 1])
            with login_col2:
                login_button = st.button("🔑 Login", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if login_button:
                if not username or not password:
                    st.warning("⚠️ Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        result = authenticate_instructor(username, password)
                        if result:
                            st.session_state.instructor_logged_in = True
                            st.session_state.is_admin = False
                            st.session_state.instructor_id = result["instructor_id"]
                            st.session_state.instructor_username = username
                            st.session_state.instructor_role = result["role"]
                            
                            # GET assigned programs from pivot
                            assigned_progs = list_instructor_programs(result["instructor_id"])
                            st.session_state.instructor_program_ids = [p["program_id"] for p in assigned_progs]
                            
                            st.success(f"✅ Welcome, {username}! You are logged in as: {result['role']}")
                            
                            # Provide immediate guidance
                            st.info(f"🔍 You have access to {len(assigned_progs)} assigned programs.")
                            
                            # Optionally set a default menu choice
                            st.session_state.menu_choice = "Dashboard"
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password.")
            
            # Add some guidance for instructor login with better styling
            with st.expander("Forgot Password?"):
                st.markdown("""
                <div style="background-color: #e2e8f0; padding: 10px; border-radius: 5px;">
                <p style="color: #2d3748; margin-top: 0;">If you've forgotten your password:</p>
                <ol style="margin-bottom: 0; padding-left: 20px; color: #2d3748;">
                    <li>Contact your administrator</li>
                    <li>They can reset your password in the system</li>
                    <li>You'll receive temporary credentials to log in</li>
                </ol>
                <p style="color: #2d3748; margin-top: 10px; margin-bottom: 0;">
                    Alternatively, email support at <a href="mailto:javier@clubstride.org" style="color: #3182ce;">javier@clubstride.org</a>
                </p>
                </div>
                """, unsafe_allow_html=True)

    # Add a helpful footer with better contrast
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; background-color: #e2e8f0; padding: 10px; border-radius: 5px; 
         border: 1px solid #cbd5e0;">
        <p style="color: #4a5568; margin-bottom: 0;">
            Having trouble logging in? Contact 
            <a href="mailto:javier@clubstride.org" style="color: #3182ce;">javier@clubstride.org</a> 
            for assistance.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add security notice with better contrast
    st.markdown("""
    <div style="background-color: #fef3c7; padding: 10px; border-radius: 5px; margin-top: 20px; 
         border-left: 4px solid #f59e0b; border: 1px solid #fcd34d;">
        <h4 style="color: #92400e; margin-top: 0;">🔒 Security Notice</h4>
        <p style="color: #92400e; margin-bottom: 0; font-size: 0.9em;">
            Always log out when you're finished using the system, especially on shared computers.
            Never share your password with others.
        </p>
    </div>
    """, unsafe_allow_html=True)
####################
# PAGE: Manage Instructors
####################

def page_manage_instructors():
    st.header("Manage Instructors - Normalized Programs")
    initialize_tables()

    # Track which program is being edited (None = no active edits)
    if "editing_program_id" not in st.session_state:
        st.session_state["editing_program_id"] = None

    Programs_Col, Instructors_Col = st.columns([2, 2])

    ##################################################
    # LEFT COLUMN: MANAGE PROGRAMS
    ##################################################
    with Programs_Col:
        with st.expander("Manage Programs"):
            # --- CREATE NEW PROGRAM ---
            with st.form("add_program_form"):
                new_prog_name = st.text_input("New Program Name", value="")
                submitted_prog = st.form_submit_button("Create Program")

            if submitted_prog:
                if new_prog_name.strip():
                    program_id = add_program(new_prog_name.strip())
                    if program_id == -1:
                        st.error("A program with that name already exists.")
                    else:
                        st.success(f"Program created (ID={program_id}).")
                        st.rerun()
                else:
                    st.warning("Program name cannot be empty.")

            st.subheader("Current Programs")
            all_programs = list_programs()  # e.g. [{"program_id":..., "program_name":...}, ...]

            if not all_programs:
                st.info("No programs found.")
            else:
                for prog in all_programs:
                    pid = prog["program_id"]
                    pname = prog["program_name"]

                    colA, colB, colC = st.columns([2, 1, 1])
                    with colA:
                        st.write(f"- **{pname}** (ID={pid})")

                    # --- EDIT BUTTON ---
                    with colB:
                        if st.button(f"Edit", key=f"edit_prog_{pid}"):
                            st.session_state["editing_program_id"] = pid
                            st.rerun()

                    # --- DELETE BUTTON ---
                    with colC:
                        if st.button(f"Delete", key=f"delete_prog_{pid}"):
                            if delete_program(pid):
                                st.success(f"Program '{pname}' deleted.")
                            else:
                                st.error(f"Could not delete program {pname}.")
                            st.rerun()

                    # --- IF THIS PROGRAM IS BEING EDITED, SHOW A RENAME FIELD ---
                    if st.session_state["editing_program_id"] == pid:
                        new_name = st.text_input(
                            "Rename Program",
                            value=pname,
                            key=f"rename_prog_{pid}"
                        )
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.button("Save Name", key=f"save_rename_{pid}"):
                                if not new_name.strip():
                                    st.error("Program name cannot be empty.")
                                else:
                                    success = update_program(pid, new_name.strip())
                                    if success:
                                        st.success(f"Renamed program to '{new_name}'")
                                    else:
                                        st.error("Rename failed (maybe duplicate name or invalid ID).")
                                # Clear edit state & refresh
                                st.session_state["editing_program_id"] = None
                                st.rerun()

                        with cancel_col:
                            if st.button("Cancel", key=f"cancel_rename_{pid}"):
                                st.session_state["editing_program_id"] = None
                                st.info("Edit canceled.")
                                st.rerun()

    ##################################################
    # RIGHT COLUMN: MANAGE INSTRUCTORS
    ##################################################
    with Instructors_Col:
        with st.expander("Add a New Instructor"):
            with st.form("add_instructor_form"):
                uname = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                email = st.text_input("Email Address", help="Email for notifications")

                role = st.selectbox("Role", ["Instructor", "Manager", "Admin"])
                submitted = st.form_submit_button("Create Instructor")

            if submitted:
                success = add_instructor(uname, pwd, role)
                if success:
                    if email.strip():
                        instructors = list_instructors()
                        for instr in instructors:
                            if instr["username"] == uname:
                                update_instructor_email(instr["instructor_id"], email)
                                break
                        st.success("Instructor created successfully!")
                        st.rerun()
                else:
                    st.error("User might already exist or an error occurred.")

    instructors = list_instructors()
    if not instructors:
        st.info("No instructors found.")
        st.stop()

    all_programs = list_programs()
    prog_dict = {p["program_id"]: p["program_name"] for p in all_programs}
    st.subheader("Current Instructors")

    # ----------------------------------------------------
    # For each instructor, show actions in an expander
    # ----------------------------------------------------
    for instr in instructors:
        instr_id = instr["instructor_id"]
        username = instr["username"]
        role = instr["role"]

        with st.expander(f"{username} (ID={instr_id} | Role={role})"):
            # (1) Update Role
            st.write("### Update Role")
            col_role, col_spacer, col_del = st.columns([3, 1, 1])
            with col_role:
                new_role = st.selectbox(
                    "Select New Role",
                    ["Instructor", "Manager", "Admin"],
                    index=["Instructor", "Manager", "Admin"].index(role),
                    key=f"role_{instr_id}"
                )
                if st.button("Update Role", key=f"btn_role_{instr_id}"):
                    update_instructor_role(instr_id, new_role)
                    st.success(f"Updated role for {username} to {new_role}.")
                    st.rerun()

            # (2) Delete Instructor
            with col_del:
                if st.button("Delete Instructor", key=f"btn_delete_{instr_id}"):
                    success = delete_instructor(instr_id)
                    if success:
                        st.success(f"Instructor {username} deleted.")
                    else:
                        st.error("Delete failed or instructor not found.")
                    st.rerun()

            st.write("---")

            st.write("### Email Address")
            current_email = get_instructor_email(instr_id)
            new_email = st.text_input(
                "Email Address", 
                value=current_email,
                key=f"email_{instr_id}",
                help="Email for program assignment notifications"
            )
            if st.button("Update Email", key=f"btn_email_{instr_id}"):
                if update_instructor_email(instr_id, new_email):
                    st.success(f"Email updated for {username}")
                else:
                    st.error("Failed to update email")
            # (3) Assigned Programs
            st.write("### Assigned Programs")
            assigned = list_instructor_programs(instr_id)
            if not assigned:
                st.write("No programs assigned yet.")
            else:
                for a in assigned:
                    prog_id = a["program_id"]
                    prog_name = a["program_name"]
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"- **{prog_name}** (ID={prog_id})")
                    with c2:
                        if st.button("Remove", key=f"remove_{instr_id}_{prog_id}"):
                            remove_instructor_from_program(instr_id, prog_id)
                            st.warning(f"Removed {prog_name} from {username}")
                            st.rerun()

            st.write("---")

            # (4) Reset Password
            st.write("Set a new password for this instructor.")
            new_pass = st.text_input("New Password", type="password", key=f"pwd_reset_{instr_id}")
            if st.button("Confirm Password Reset", key=f"confirm_reset_{instr_id}"):
                if not new_pass.strip():
                    st.error("Password cannot be empty.")
                else:
                    update_instructor_password(instr_id, new_pass)
                    st.success(f"Password reset for {username}.")

            st.write("---")

            # (5) Assign a New Program
            st.write("### Assign a New Program")
            col_assign, _, _ = st.columns([3, 1, 1])
            with col_assign:
                selectable_ids = [p["program_id"] for p in all_programs]
                choice = st.selectbox(
                    "Select a Program to Assign",
                    options=selectable_ids,
                    format_func=lambda x: prog_dict[x],
                    key=f"addprog_{instr_id}"
                )
                if st.button("Assign Program", key=f"btn_assign_{instr_id}"):
                    assign_instructor_to_program(instr_id, choice)
                    st.success(f"Assigned Program {prog_dict[choice]} (ID={choice}) to {username}")
                    st.rerun()

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
    # Initialize edit state if not already done
    if "editing_student_id" not in st.session_state:
        st.session_state["editing_student_id"] = None

    # We’ll also store a deletion candidate in session state for the two-step flow
    if "delete_candidate_id" not in st.session_state:
        st.session_state["delete_candidate_id"] = None
    if "delete_candidate_name" not in st.session_state:
        st.session_state["delete_candidate_name"] = None
    if "delete_candidate_prog" not in st.session_state:
        st.session_state["delete_candidate_prog"] = None

    # 1) Must be logged in (admin or instructor)
    if not st.session_state.get("instructor_logged_in", False) and not st.session_state.get("is_admin", False):
        st.error("🔒 You must be logged in to access this page.")
        return

    # We'll keep your center column layout if you prefer
    # col_left, col_center, col_right = st.columns([1, 5, 1])
    # with col_center:
    st.header("👨‍🎓 Manage Students")

    is_admin = st.session_state.get("is_admin", False)
    user_role = "Administrator" if is_admin else "Instructor"
    st.write(f"*Logged in as: {user_role}*")

    # ----------------------------------------------------------
    # A) Program Filter for Admin with improved UI
    # ----------------------------------------------------------
    st.markdown("### 🔍 Filter Students")

    # Get all programs for reference
    all_programs = list_programs()  # from instructors_db
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

    if is_admin:
        # Build a list of (program_id, "program_name") pairs
        program_choices = [(None, "All Programs")] + [
            (p["program_id"], p["program_name"]) for p in all_programs
        ]

        with st.container():
            selected_prog_id = st.selectbox(
                "Select Program to View:",
                options=[pc[0] for pc in program_choices],
                format_func=lambda pid: "All Programs" if pid is None else f"{prog_map[pid]} (ID: {pid})",
                help="As an admin, you can view students from all programs or filter by a specific program"
            )

        if selected_prog_id is None:
            # Admin sees all students
            students = get_all_students()
            st.success("Showing all students from all programs")
        else:
            # Admin sees only students in the chosen program
            students = get_all_students(program_ids=[selected_prog_id])
            st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")

    else:
        # Instructors see only their assigned programs
        permitted_ids = st.session_state.get("instructor_program_ids", [])
        if not permitted_ids:
            st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
            return

        # Show a filter for instructors with multiple programs
        if len(permitted_ids) > 1:
            program_choices = [(None, "All My Programs")] + [
                (pid, prog_map.get(pid, f"Program ID: {pid}")) for pid in permitted_ids
            ]

            selected_prog_id = st.selectbox(
                "Filter by Program:",
                options=[pc[0] for pc in program_choices],
                format_func=lambda pid: "All My Programs" if pid is None else f"{prog_map.get(pid, f'Program ID: {pid}')}",
                help="Select a specific program or view all your assigned programs"
            )

            if selected_prog_id is None:
                # Instructor sees all their permitted programs
                students = get_all_students(program_ids=permitted_ids)
                program_names = [prog_map.get(pid, f"Program {pid}") for pid in permitted_ids]
                st.success(f"Showing students from all your assigned programs: {', '.join(program_names)}")
            else:
                # Instructor sees only the selected program
                students = get_all_students(program_ids=[selected_prog_id])
                st.success(f"Showing students from: {prog_map.get(selected_prog_id, 'Unknown Program')}")
        else:
            # Instructor has only one program, so show all students from that program
            students = get_all_students(program_ids=permitted_ids)
            program_name = prog_map.get(permitted_ids[0], f"Program {permitted_ids[0]}")
            st.success(f"Showing students from your assigned program: {program_name}")

    st.write("---")

    if not students:
        st.info("📌 No students found matching your criteria.")

    # ----------------------------------------------------------
    # B) Create Tabs: [ "View & Manage" | "Add / Update" ]
    # ----------------------------------------------------------
    tab_labels = ["👀 View & Manage", "➕ Add or Update"]
    tabs = st.tabs(tab_labels)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TAB 1: VIEW & MANAGE CURRENT STUDENTS
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    with tabs[0]:
        st.subheader("Current Students")

        # Help expander
        with st.expander("ℹ️ How to manage students", expanded=False):
            st.markdown("""
            ### Managing Students:
            - **View:** Each student is displayed with their basic information
            - **Delete:** Remove a student from the database (requires confirmation)
            - **Edit:** Update a student's information directly within the student card
            - **Mark Attendance:** Record attendance for today
            - **Mark Past Attendance:** Record attendance for a previous date

            All changes are saved immediately to the database.
            """)

        if students:
            st.write(f"Total students: {len(students)}")

            # Add a search box for filtering students by name
            search_term = st.text_input(
                "🔍 Search students by name:",
                help="Type a name to filter the list of students"
            )

            # Filter students by search term if provided
            if search_term:
                filtered_students = [s for s in students if search_term.lower() in s.get("name", "").lower()]
                if not filtered_students:
                    st.info(f"No students found matching '{search_term}'")
                students_to_display = filtered_students
            else:
                students_to_display = students

            # Placeholder for attendance forms outside the loop
            attendance_placeholder = st.empty()

            for i, s in enumerate(students_to_display):
                student_id = s.get("student_id")
                name = s.get("name", "")
                phone = s.get("phone", "")
                contact_email = s.get("contact_email", "")
                prog_id = s.get("program_id", None)
                grade = s.get("grade", "")
                school = s.get("school", "")

                # Get program name for display
                program_name = prog_map.get(prog_id, f"Program ID: {prog_id}")

                # Check if this student is currently being edited
                is_editing = (st.session_state["editing_student_id"] == student_id)

                # Create a container/expander for each student
                with st.container():
                    with st.expander(f"**{name}** - {program_name}", expanded=is_editing):
                        if not is_editing:
                            # Normal view mode: info + actions
                            col_info, col_actions = st.columns([3, 1])

                            with col_info:
                                st.markdown(f"**Student ID:** {student_id}")
                                st.markdown(f"**Program:** {program_name}")
                                st.markdown(f"**Grade:** {grade}")
                                st.markdown(f"**School:** {school}")
                                st.markdown(f"**Contact:** {contact_email}")
                                st.markdown(f"**Phone:** {phone}")

                            with col_actions:
                                # EDIT button
                                if st.button("✏️ Edit", key=f"btn_edit_{student_id}",
                                                help=f"Edit information for {name}"):
                                    st.session_state["editing_student_id"] = student_id
                                    st.session_state["edit_data"] = s
                                    st.rerun()

                                # ATTENDANCE buttons
                                if st.button("✅ Mark Today", key=f"btn_attendance_{student_id}",
                                                help=f"Record today's attendance for {name}"):
                                    st.session_state["attendance_student"] = s
                                    st.rerun()

                                if st.button("📆 Mark Past", key=f"btn_attendance_past_{student_id}",
                                                help=f"Record past attendance for {name}"):
                                    st.session_state["attendance_student"] = s
                                    st.session_state["attendance_mode"] = "past"
                                    st.rerun()

                                # -----------------------------
                                # DELETE: Two-step confirmation
                                # -----------------------------
                                delete_candidate_id = st.session_state.get("delete_candidate_id")
                                delete_candidate_name = st.session_state.get("delete_candidate_name")
                                delete_candidate_prog = st.session_state.get("delete_candidate_prog")

                                if delete_candidate_id == student_id:
                                    # We've already clicked Delete on this student in a previous run
                                    st.warning(f"Are you sure you want to delete {delete_candidate_name}?")

                                    # No columns here - just two separate buttons
                                    cancel_delete = st.button("Cancel Delete", key=f"cancel_delete_{student_id}")
                                    confirm_delete = st.button("Confirm Delete", key=f"confirm_delete_{student_id}")

                                    if cancel_delete:
                                        st.session_state["delete_candidate_id"] = None
                                        st.session_state["delete_candidate_name"] = None
                                        st.session_state["delete_candidate_prog"] = None
                                        st.rerun()

                                    if confirm_delete:
                                        # Check instructor permissions
                                        if not is_admin:
                                            perm_ids = st.session_state.get("instructor_program_ids", [])
                                            if delete_candidate_prog not in perm_ids:
                                                st.error("⛔ You are not permitted to delete students in this program.")
                                                st.stop()

                                        with st.spinner(f"Deleting {delete_candidate_name}..."):
                                            success = delete_student_record(delete_candidate_id)
                                            if success:
                                                st.success(f"✅ Deleted student {delete_candidate_name} (ID={delete_candidate_id}).")
                                                # Clear the candidate & re-run
                                                st.session_state["delete_candidate_id"] = None
                                                st.session_state["delete_candidate_name"] = None
                                                st.session_state["delete_candidate_prog"] = None
                                                st.rerun()
                                            else:
                                                st.error("❌ Delete failed or no such student.")
                                else:
                                    # If we're not already in a delete-confirm step, show the 'Delete' button
                                    if st.button("🗑️ Delete", key=f"btn_delete_{student_id}",
                                                    help=f"Permanently delete {name} from the database"):
                                        # Store this student as the candidate in session state
                                        st.session_state["delete_candidate_id"] = student_id
                                        st.session_state["delete_candidate_name"] = name
                                        st.session_state["delete_candidate_prog"] = prog_id
                                        st.rerun()
                        else:
                            # EDIT MODE
                            st.subheader("✏️ Edit Student Information")

                            edited_stud = st.session_state["edit_data"]

                            # Guard against editing a student in a program the instructor doesn't have
                            if not is_admin:
                                perm_ids = st.session_state.get("instructor_program_ids", [])
                                if edited_stud.get("program_id") not in perm_ids:
                                    st.error("⛔ You do not have permission to edit students in this program.")
                                    if st.button("OK"):
                                        st.session_state["editing_student_id"] = None
                                        st.rerun()

                            with st.form(f"edit_student_form_{student_id}"):
                                col1, col2 = st.columns(2)

                                with col1:
                                    new_name = st.text_input("Name *", value=edited_stud.get("name", ""))
                                    new_phone = st.text_input("Phone", value=edited_stud.get("phone", ""))
                                    new_email = st.text_input("Contact Email", value=edited_stud.get("contact_email", ""))

                                with col2:
                                    new_grade = st.text_input("Grade", value=edited_stud.get("grade", ""))
                                    new_school = st.text_input("School", value=edited_stud.get("school", ""))

                                    # If admin, let them pick a new program
                                    if is_admin:
                                        all_progs = list_programs()
                                        prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
                                        prog_ids = list(prog_map.keys())

                                        current_pid = edited_stud.get("program_id")
                                        if current_pid not in prog_ids:
                                            prog_index = 0
                                        else:
                                            prog_index = prog_ids.index(current_pid)

                                        selected_id = st.selectbox(
                                            "Select Program:",
                                            options=prog_ids,
                                            format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
                                            index=prog_index
                                        )
                                        new_program_id = selected_id
                                    else:
                                        perm_ids = st.session_state.get("instructor_program_ids", [])
                                        current_pid = edited_stud.get("program_id")
                                        if current_pid not in perm_ids and perm_ids:
                                            current_pid = perm_ids[0]
                                        new_program_id = st.selectbox(
                                            "Select Program:",
                                            options=perm_ids,
                                            format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
                                            index=perm_ids.index(current_pid) if current_pid in perm_ids else 0
                                        )

                                st.markdown("**Required fields are marked with * **")

                                col_cancel, col_save = st.columns(2)
                                with col_cancel:
                                    cancel_btn = st.form_submit_button("Cancel")

                                with col_save:
                                    submit_btn = st.form_submit_button("Save Changes")

                                if submit_btn:
                                    if not new_name.strip():
                                        st.error("❌ Name is required.")
                                    else:
                                        with st.spinner("Updating student information..."):
                                            try:
                                                msg = update_student_info(
                                                    student_id=edited_stud["student_id"],
                                                    new_name=new_name,
                                                    new_phone=new_phone,
                                                    new_contact_email=new_email,
                                                    # If you want to store the updated program:
                                                    # program_id=new_program_id,
                                                    new_grade=new_grade,
                                                    new_school=new_school
                                                )
                                                st.success(f"✅ {msg}")
                                                st.session_state["editing_student_id"] = None
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error updating student: {e}")

                                if cancel_btn:
                                    st.session_state["editing_student_id"] = None
                                    st.rerun()

                    # Separator line between each student
                    if i < len(students_to_display) - 1:
                        st.write("---")

            # Handle attendance forms (outside the loop to avoid UI conflicts)
            if "attendance_student" in st.session_state:
                with attendance_placeholder.container():
                    st.write("---")
                    st.subheader("📝 Attendance Recording")

                    single_stud = st.session_state["attendance_student"]
                    mode = st.session_state.get("attendance_mode", "today")

                    if mode == "today":
                        handle_mark_attendance_today(single_stud)
                        
                    elif mode == "past":
                        handle_mark_attendance_past(single_stud)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TAB 2: ADD OR UPDATE STUDENTS (Single or Bulk)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    with tabs[1]:
        st.subheader("Add or Update Students")

        # Help expander
        with st.expander("ℹ️ How to add students", expanded=False):
            st.markdown("""
            ### Adding Students:
            - **Single Student Entry:** Add one student at a time with complete details
            - **Bulk CSV Upload:** Upload multiple students at once using a CSV file

            #### CSV Format Requirements:
            Your CSV file should include these columns:
            - First Name
            - Last Name
            - Number (phone)
            - Email
            - Grade
            - School

            The program ID will be applied to all students in the CSV.
            """)

        action = st.radio(
            "Choose method:",
            ["Single Student Entry", "Bulk CSV Upload"],
            horizontal=True,
            help="Choose how you want to add students to the system"
        )

        if action == "Single Student Entry":
            st.write("### Add a New Student")

            with st.form("student_form"):
                col1, col2 = st.columns(2)

                with col1:
                    name_val = st.text_input("Name *", "", help="Student's full name")
                    phone_val = st.text_input("Phone", "", help="Contact phone number")
                    contact_val = st.text_input("Contact Email", "", help="Email address for the student or parent")

                with col2:
                    grade_val = st.text_input("Grade", "", help="Student's current grade level")
                    school_val = st.text_input("School", "", help="Student's school name")

                    # Program selection based on user role
                    if is_admin:
                        all_progs = list_programs()
                        if not all_progs:
                            st.warning("⚠️ No programs found in database.")
                            st.stop()

                        prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
                        selected_id = st.selectbox(
                            "Select Program *:",
                            options=prog_map.keys(),
                            format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})"
                        )
                        prog_val = selected_id
                    else:
                        perm_ids = st.session_state.get("instructor_program_ids", [])
                        if not perm_ids:
                            st.warning("⚠️ No assigned programs available.")
                            prog_val = None
                        else:
                            prog_val = st.selectbox(
                                "Select Program *:",
                                options=perm_ids,
                                format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}"
                            )

                st.markdown("**Required fields are marked with * **")

                submitted = st.form_submit_button("Save Student")
                if submitted:
                    if not name_val.strip():
                        st.error("❌ Name is required.")
                    elif prog_val is None:
                        st.error("❌ No valid program selected.")
                    else:
                        with st.spinner("Saving student information..."):
                            result = store_student_record(
                                name_val, phone_val, contact_val, prog_val,
                                grade=grade_val, school=school_val
                            )
                            st.success(f"✅ {result}")
                            if result != '':
                                st.rerun()

        else:
            # Bulk CSV Upload
            st.write("### Bulk Upload Students")

            # Step 1: Select Program
            st.markdown("#### 1️⃣ Select Program")
            st.write("All students in the CSV will be assigned to this program:")

            if is_admin:
                all_progs = list_programs()
                if not all_progs:
                    st.warning("⚠️ No programs found in database.")
                    st.stop()

                prog_map = {p["program_id"]: p["program_name"] for p in all_progs}
                selected_prog_id = st.selectbox(
                    "Select Program for CSV Rows:",
                    options=prog_map.keys(),
                    format_func=lambda pid: f"{prog_map[pid]} (ID: {pid})",
                    key="csv_upload_program_selector_admin"
                )
            else:
                perm_ids = st.session_state.get("instructor_program_ids", [])
                if not perm_ids:
                    st.warning("⚠️ No assigned programs available.")
                    st.stop()
                selected_prog_id = st.selectbox(
                    "Select Program for CSV Rows:",
                    options=perm_ids,
                    format_func=lambda pid: f"{prog_map.get(pid, f'Program ID: {pid}')}",
                    key="csv_upload_program_selector"
                )

            # Step 2: Upload File
            st.markdown("#### 2️⃣ Upload CSV File")
            st.write("Upload a CSV file with student information:")

            st.markdown("""
            Need a template? Here's a sample CSV format:
            ```
            First Name,Last Name,Number,Email,Grade,School
            John,Doe,555-123-4567,john.doe@email.com,10,Lincoln High
            Jane,Smith,555-987-6543,jane.smith@email.com,11,Washington High
            ```
            """)

            uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])

            if uploaded_file:
                # Step 3: Preview and Process
                st.markdown("#### 3️⃣ Preview and Process")

                with st.spinner("Reading CSV data..."):
                    df = pd.read_csv(uploaded_file)

                # Preview in a clean format
                st.write("Preview of first 5 rows:")
                st.dataframe(df.head(), use_container_width=True)

                # Check for required columns
                required_cols = {"First Name", "Last Name", "Number", "Email", "Grade", "School"}
                missing_cols = required_cols - set(df.columns)

                if missing_cols:
                    st.error(f"❌ CSV is missing required columns: {', '.join(missing_cols)}")
                    st.info(f"Required columns are: {', '.join(required_cols)}")
                else:
                    total_rows = len(df)
                    st.write(f"Total records to process: {total_rows}")

                    if st.button("🔄 Process CSV Data"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        successes = 0
                        failures = 0
                        messages = []

                        for idx, row in df.iterrows():
                            # Update progress
                            progress = int((idx + 1) / total_rows * 100)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing row {idx+1} of {total_rows}...")

                            try:
                                first_name = str(row["First Name"]).strip()
                                last_name = str(row["Last Name"]).strip()
                                name_val = f"{first_name} {last_name}".strip()

                                phone_val = row["Number"]
                                contact_val = row["Email"]
                                grade_val = row["Grade"]
                                school_val = row["School"]

                                # Instructors can only upload if the CSV's program_id is in their assigned list
                                if not is_admin:
                                    perm_ids = st.session_state.get("instructor_program_ids", [])
                                    if selected_prog_id not in perm_ids:
                                        message = (f"Row {idx+1}: Program ID '{selected_prog_id}' "
                                                    "is not in your assigned list.")
                                        messages.append(message)
                                        failures += 1
                                        continue

                                result_msg = store_student_record(
                                    name_val, phone_val, contact_val,
                                    selected_prog_id, grade_val, school_val
                                )

                                if ("New student record" in result_msg) or ("updated" in result_msg):
                                    successes += 1
                                    messages.append(f"Row {idx+1}: {result_msg}")
                                else:
                                    failures += 1
                                    messages.append(f"Row {idx+1}: Failed - {result_msg}")

                            except Exception as e:
                                failures += 1
                                messages.append(f"Row {idx+1}: Error - {str(e)}")

                        # Final update
                        progress_bar.progress(100)
                        status_text.text("Processing complete!")

                        # Summary
                        st.success(f"✅ Bulk upload complete. Successes: {successes}, Failures: {failures}")

                        # Show detailed messages in an expander
                        if messages:
                            with st.expander("View Processing Details", expanded=(failures > 0)):
                                for msg in messages:
                                    if "Failed" in msg or "Error" in msg:
                                        st.error(msg)
                                    else:
                                        st.success(msg)

                        # Offer to refresh the page
                        if st.button("View Updated Student List"):
                            st.rerun()


def page_take_attendance():
    st.header("📋 Take Attendance")
    
    # Help expander
    with st.expander("ℹ️ How to take attendance", expanded=False):
        st.markdown("""
        ### Taking Attendance:
        - **Today's Attendance**: Record attendance for the current day
        - **Past Session**: Record attendance for a previous date and time
        - Select status (Present, Late, Absent, or Excused) for each student
        - Add optional comments as needed
        - Submit all attendance records at once with the button at the bottom
        """)

    # -----------------------------------------------------------------
    # 1) Determine if user is admin or instructor; filter programs
    # -----------------------------------------------------------------
    is_admin = st.session_state.get("is_admin", False)
    all_programs = list_programs()  # e.g. from instructors_db
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
    
    st.markdown("### 🔍 Select Program")

    if is_admin:
        # Admin can pick any program or "All"
        program_choices = [(None, "All Programs")] + [(p["program_id"], p["program_name"]) for p in all_programs]
        selected_prog_id = st.selectbox(
            "Select Program:",
            options=[pc[0] for pc in program_choices],
            format_func=lambda pid: "All Programs" if pid is None else f"{prog_map[pid]} (ID: {pid})",
            help="Choose which program's students to display",
            key="take_attendance_program_selector"  # Add this unique key

        )

        if selected_prog_id is None:
            # Admin sees all students
            students = get_all_students()
            st.success(f"Showing all students from all programs")
        else:
            # Admin sees only students in the chosen program
            students = get_all_students(program_ids=[selected_prog_id])
            program_name = prog_map.get(selected_prog_id, f"Program ID: {selected_prog_id}")
            st.success(f"Showing students from: {program_name}")

    else:
        # Instructor sees only their assigned programs
        permitted_ids = st.session_state.get("instructor_program_ids", [])
        if not permitted_ids:
            st.warning("⚠️ No assigned programs found. Contact an admin for access.")
            return
            
        # Show a filter for instructors with multiple programs
        if len(permitted_ids) > 1:
            program_choices = [(None, "All My Programs")] + [
                (pid, prog_map.get(pid, f"Program ID: {pid}")) for pid in permitted_ids
            ]
            
            selected_prog_id = st.selectbox(
                "Filter by Program:",
                options=[pc[0] for pc in program_choices],
                format_func=lambda pid: "All My Programs" if pid is None else f"{prog_map.get(pid, f'Program ID: {pid}')}",
                help="Select a specific program or view all your assigned programs"
            )
            
            if selected_prog_id is None:
                # Instructor sees all their permitted programs
                students = get_all_students(program_ids=permitted_ids)
                program_names = [prog_map.get(pid, f"Program {pid}") for pid in permitted_ids]
                st.success(f"Showing students from all your assigned programs: {', '.join(program_names)}")
            else:
                # Instructor sees only the selected program
                students = get_all_students(program_ids=[selected_prog_id])
                program_name = prog_map.get(selected_prog_id, f"Program ID: {selected_prog_id}")
                st.success(f"Showing students from: {program_name}")
        else:
            # Instructor has only one program
            students = get_all_students(program_ids=permitted_ids)
            program_name = prog_map.get(permitted_ids[0], f"Program {permitted_ids[0]}")
            st.success(f"Showing students from your assigned program: {program_name}")

    if not students:
        st.info("📌 No students found. (Check whether you have assigned programs or student data.)")
        return
        
    st.write(f"Total students: {len(students)}")
    st.write("---")

    # -----------------------------------------------------------------
    # 2) Create Tabs: [ "Attendance (Today)" | "Record Past Session" ]
    # -----------------------------------------------------------------
    tab_labels = ["📅 Today's Attendance", "🗓️ Past Session"]
    tabs = st.tabs(tab_labels)

    # --------------- TAB 1: Attendance (Today) ---------------
    with tabs[0]:
        st.subheader("Today's Attendance")
        st.write(f"**Date**: {datetime.now().strftime('%A, %B %d, %Y')}")
        st.write(f"**Time**: {datetime.now().strftime('%I:%M %p')}")

        # We'll use a color-coded or emoji-labeled radio for statuses
        status_options_today = ["✅ Present", "🕑 Late", "🚫 Absent"]
        status_map_today = {
            "✅ Present": "Present",
            "🕑 Late": "Late",
            "🚫 Absent": "Absent"
        }

        # Quick selection tools
        quick_select = st.radio(
            "Quick Select:",
            ["Set Individually", "Mark All Present", "Mark All Absent"],
            horizontal=True,
            help="Quickly set all students to the same status, or set individually"
        )
        
        # Initialize session state for default selections
        if "today_defaults" not in st.session_state:
            st.session_state["today_defaults"] = {}
            
        # Apply quick selections
        if quick_select == "Mark All Present":
            for s in students:
                st.session_state["today_defaults"][s["student_id"]] = "✅ Present"
        elif quick_select == "Mark All Absent":
            for s in students:
                st.session_state["today_defaults"][s["student_id"]] = "🚫 Absent"

        # Build a form to handle all students at once
        with st.form("attendance_today_form"):
            attendance_dict = {}
            
            # Group students by program for better organization
            students_by_program = {}
            for s in students:
                pid = s.get("program_id", 0)
                if pid not in students_by_program:
                    students_by_program[pid] = []
                students_by_program[pid].append(s)
            
            # For each program, show students in that program
            for pid, program_students in students_by_program.items():
                prog_name = prog_map.get(pid, f"Program ID={pid}")
                st.markdown(f"### Program: {prog_name}")
                
                # Create a table-like layout with columns
                cols = st.columns([3, 2, 3])
                cols[0].markdown("**Student Name**")
                cols[1].markdown("**Status**")
                cols[2].markdown("**Comment**")
                
                for s in program_students:
                    sid = s.get("student_id")
                    name = s.get("name", "")
                    
                    # Get default from session state or use "Present"
                    default_status = st.session_state["today_defaults"].get(sid, "✅ Present")
                    default_index = status_options_today.index(default_status)
                    
                    cols = st.columns([3, 2, 3])
                    
                    # Column 1: Student name
                    cols[0].write(f"**{name}**")
                    
                    # Column 2: Status selection
                    chosen_emoji_label = cols[1].radio(
                        "Status:",
                        options=status_options_today,
                        index=default_index,
                        key=f"{sid}_radio_today",
                        label_visibility="collapsed"
                    )
                    
                    # Column 3: Comment field
                    comment = cols[2].text_input(
                        "Comment (Optional)", 
                        key=f"{sid}_comment_today",
                        label_visibility="collapsed",
                        placeholder="Add comment..."
                    )

                    # Convert from emoji-labeled to DB status
                    final_status = status_map_today[chosen_emoji_label]

                    attendance_dict[sid] = {
                        "name": name,
                        "program_id": pid,
                        "status": final_status,
                        "comment": comment
                    }
                
                # Add separator between programs
                st.write("---")

            col1, col2 = st.columns([4, 1])
            with col2:
                submitted_today = st.form_submit_button("📝 Submit Attendance")

        if submitted_today:
            # Process each student's chosen status
            success_count = 0
            error_count = 0
            
            # Create progress bar
            progress_text = st.empty()
            progress_bar = st.progress(0)
            total_students = len(attendance_dict)
            
            # Result containers
            success_container = st.empty()
            error_container = st.empty()
            success_messages = []
            error_messages = []
            
            for i, (sid, data) in enumerate(attendance_dict.items()):
                name = data["name"]
                prog_id = data["program_id"]
                status = data["status"]
                comment = data["comment"]
                
                # Update progress
                progress = int((i + 1) / total_students * 100)
                progress_bar.progress(progress)
                progress_text.text(f"Processing {i+1} of {total_students} students...")

                try:
                    result_msg = record_student_attendance_in_array(name, prog_id, status, comment)
                    success_count += 1
                    status_emoji = "✅" if status == "Present" else "🕑" if status == "Late" else "🚫"
                    success_messages.append(f"{status_emoji} {name} – Marked {status}")
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Error for {name}: {e}")
            
            # Final progress update and summary
            progress_bar.progress(100)
            progress_text.text("Processing complete!")
            
            if success_count > 0:
                success_container.success(f"✅ Recorded attendance for {success_count} students!")
                
                # Show success details in expander
                with st.expander("View submission details", expanded=False):
                    for msg in success_messages:
                        st.write(msg)
            
            if error_count > 0:
                error_container.error(f"❌ Failed to record attendance for {error_count} students.")
                
                # Show error details
                with st.expander("View errors", expanded=True):
                    for msg in error_messages:
                        st.error(msg)
            
            # Clear defaults after submission
            st.session_state["today_defaults"] = {}

    # --------------- TAB 2: Record Past Session ---------------
    with tabs[1]:
        st.subheader("Record Past Session")
        
        # Help text
        st.markdown("""
        Use this form to record attendance for a previous session. First select the date and time,
        then mark each student's status and any comments.
        """)

        # Let user pick date/time
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("Session Date", value=date.today())
        with col2:
            session_time = st.time_input("Session Start Time", value=time(9, 0))
        chosen_datetime = datetime.combine(session_date, session_time)

        st.write(f"**Selected Date/Time**: {session_date.strftime('%A, %B %d, %Y')} at {session_time.strftime('%I:%M %p')}")

        # Past statuses can include "Excused" as well
        status_options_past = ["✅ Present", "🕑 Late", "🚫 Absent", "🤝 Excused"]
        status_map_past = {
            "✅ Present": "Present",
            "🕑 Late": "Late",
            "🚫 Absent": "Absent",
            "🤝 Excused": "Excused"
        }

        # Optional "Mark All..." tools
        if "past_defaults" not in st.session_state:
            st.session_state["past_defaults"] = {}

        quick_past = st.radio(
            "Quick Select:",
            ["Set Individually", "Mark All Present", "Mark All Absent", "Mark All Excused"],
            horizontal=True,
            help="Quickly set all students to the same status, or set individually"
        )
        
        # Apply quick selections
        if quick_past == "Mark All Present":
            for s in students:
                st.session_state["past_defaults"][s["student_id"]] = "✅ Present"
            st.success("All students marked Present - you can adjust individual statuses below")
        elif quick_past == "Mark All Absent":
            for s in students:
                st.session_state["past_defaults"][s["student_id"]] = "🚫 Absent"
            st.info("All students marked Absent - you can adjust individual statuses below")
        elif quick_past == "Mark All Excused":
            for s in students:
                st.session_state["past_defaults"][s["student_id"]] = "🤝 Excused"
            st.info("All students marked Excused - you can adjust individual statuses below")

        # Build a form to finalize each student's status
        with st.form("past_attendance_form_attendance"):
            past_data = {}
            
            # Group students by program for better organization
            students_by_program = {}
            for s in students:
                pid = s.get("program_id", 0)
                if pid not in students_by_program:
                    students_by_program[pid] = []
                students_by_program[pid].append(s)
            
            # For each program, show students in that program
            for pid, program_students in students_by_program.items():
                prog_name = prog_map.get(pid, f"Program ID={pid}")
                st.markdown(f"### Program: {prog_name}")
                
                # Create a table-like layout with columns
                cols = st.columns([3, 2, 3])
                cols[0].markdown("**Student Name**")
                cols[1].markdown("**Status**")
                cols[2].markdown("**Comment**")
                
                for s in program_students:
                    sid = s.get("student_id")
                    name = s.get("name", "")
                    
                    # Get default from session state or use "Absent"
                    default_status = st.session_state["past_defaults"].get(sid, "🚫 Absent")
                    default_index = status_options_past.index(default_status)
                    
                    cols = st.columns([3, 2, 3])
                    
                    # Column 1: Student name
                    cols[0].write(f"**{name}**")
                    
                    # Column 2: Status selection
                    chosen_emoji_label = cols[1].radio(
                        "Status",
                        options=status_options_past,
                        index=default_index,
                        key=f"past_{sid}_radio",
                        label_visibility="collapsed"
                    )
                    
                    # Column 3: Comment field
                    comment_val = cols[2].text_input(
                        "Comment (Optional)", 
                        key=f"past_comment_{sid}",
                        label_visibility="collapsed",
                        placeholder="Add comment..."
                    )

                    final_status = status_map_past[chosen_emoji_label]
                    past_data[sid] = {
                        "name": name,
                        "program_id": pid,
                        "status": final_status,
                        "comment": comment_val
                    }
                
                # Add separator between programs
                st.write("---")

            col1, col2 = st.columns([4, 1])
            with col2:
                submitted_past = st.form_submit_button("📝 Submit Past Attendance")

        if submitted_past:
            # Process each student's chosen status for the selected datetime
            success_count = 0
            error_count = 0
            
            # Create progress bar
            progress_text = st.empty()
            progress_bar = st.progress(0)
            total_students = len(past_data)
            
            # Result containers
            success_container = st.empty()
            error_container = st.empty()
            success_messages = []
            error_messages = []
            
            for i, (sid, data) in enumerate(past_data.items()):
                # Update progress
                progress = int((i + 1) / total_students * 100)
                progress_bar.progress(progress)
                progress_text.text(f"Processing {i+1} of {total_students} students...")
                
                try:
                    result_msg = record_student_attendance_in_array(
                        name=data["name"],
                        program_id=data["program_id"],
                        status=data["status"],
                        comment=data["comment"],
                        attendance_date=chosen_datetime
                    )
                    success_count += 1
                    status_emoji = "✅" if data["status"] == "Present" else "🕑" if data["status"] == "Late" else "🚫" if data["status"] == "Absent" else "🤝"
                    success_messages.append(f"{status_emoji} {data['name']} – Marked {data['status']}")
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Error for {data['name']}: {e}")
            
            # Final progress update and summary
            progress_bar.progress(100)
            progress_text.text("Processing complete!")
            
            if success_count > 0:
                success_container.success(f"✅ Recorded past attendance for {success_count} students on {chosen_datetime.strftime('%Y-%m-%d %H:%M')}!")
                
                # Show success details in expander
                with st.expander("View submission details", expanded=False):
                    for msg in success_messages:
                        st.write(msg)
            
            if error_count > 0:
                error_container.error(f"❌ Failed to record attendance for {error_count} students.")
                
                # Show error details
                with st.expander("View errors", expanded=True):
                    for msg in error_messages:
                        st.error(msg)
            
            # Clear defaults after submission
            st.session_state["past_defaults"] = {}


#####################
# PAGE: Review Attendance
#####################


def page_review_attendance():
    st.header("📊 Review Attendance Logs")
    
    # Help expander
    with st.expander("ℹ️ How to review attendance", expanded=False):
        st.markdown("""
        ### Reviewing Attendance:
        - **Attendance Records**: View, edit, or delete individual attendance records
        - **Missed Counts**: See a summary of absent/missed sessions by student
        - Use the filters to narrow down records by program or student name

        You can edit any record by clicking the Edit button in its panel.
        """)

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

    # Get last week's student count from your custom logic
    last_week_count = get_student_count_as_of_last_week()
    student_delta = total_students - last_week_count

    # Compare absences this vs. last week
    absent_this_week = sum(1 for r in subdocs_this_week if r["attendance"]["status"] == "Absent")
    absent_last_week = sum(1 for r in subdocs_last_week if r["attendance"]["status"] == "Absent")
    delta_absent = absent_this_week - absent_last_week

    # -------------------------------------------------------------
    # B) Display top-level metrics
    # -------------------------------------------------------------
    st.markdown("### Summary Metrics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            label="Attendance Records This Week",
            value=total_this_week,
            delta=f"{attendance_delta}" if attendance_delta != 0 else None,
            delta_color="normal" if attendance_delta >= 0 else "inverse"
        )
    with c2:
        st.metric(
            label="Absences This Week",
            value=absent_this_week,
            delta=f"{delta_absent}" if delta_absent != 0 else None,
            delta_color="inverse"  # Fewer absences is good (green)
        )
    with c3:
        st.metric(
            label="Total Active Students",
            value=total_students,
            delta=f"{student_delta}" if student_delta != 0 else None,
            delta_color="normal" if student_delta >= 0 else "inverse"
        )

    st.write("---")

    # -------------------------------------------------------------
    # C) Show tabs: [All Attendance], [Missed Sessions]
    # -------------------------------------------------------------
    tab1, tab2 = st.tabs(["📋 All Attendance Records", "🚫 Missed Sessions"])
    
    with tab1:
        st.subheader("Attendance Records")
        show_attendance_logs()  # Detailed logic below

    with tab2:
        st.subheader("Students with Missed Sessions")
        show_missed_counts()    # Provided by your code elsewhere


def show_attendance_logs():
    # Track which record is in edit mode
    if "edit_record_key" not in st.session_state:
        st.session_state["edit_record_key"] = None

    # Track which record is pending deletion
    if "delete_candidate" not in st.session_state:
        st.session_state["delete_candidate"] = None

    # ---------------------------------------------------------
    # 1) Load or refresh attendance records from DB
    # ---------------------------------------------------------
    if "attendance_records" not in st.session_state or st.session_state["attendance_records"] is None:
        try:
            with st.spinner("Loading attendance records..."):
                records = get_all_attendance_subdocs()
                st.session_state["attendance_records"] = records
        except Exception as e:
            st.error(f"❌ Error fetching attendance logs: {e}")
            st.session_state["attendance_records"] = []
            return

    logs = st.session_state["attendance_records"]
    if not logs:
        st.info("📌 No attendance records found.")
        return

    # ---------------------------------------------------------
    # 2) Program-based filtering
    # ---------------------------------------------------------
    st.markdown("### 🔍 Filter Records")
    
    col1, col2 = st.columns(2)
    
    with col1:
        all_programs = list_programs()
        prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
        is_admin = st.session_state.get("is_admin", False)

        if is_admin:
            # Admin sees a program filter
            program_choices = [(None, "All Programs")] + [
                (p["program_id"], p["program_name"]) for p in all_programs
            ]
            selected_prog_id = st.selectbox(
                "Filter by Program:",
                options=[pc[0] for pc in program_choices],
                format_func=lambda pid: "All Programs" if pid is None else f"{prog_map[pid]} (ID: {pid})",
                help="Select a program to filter attendance records"
            )
            if selected_prog_id is not None:
                logs = [
                    r for r in logs
                    if (r["program_id"] == selected_prog_id or selected_prog_id is None)
                ]
        else:
            # Instructor sees only assigned programs
            permitted_ids = st.session_state.get("instructor_program_ids", [])
            logs = [r for r in logs if r.get("program_id") in permitted_ids]
            
            # If multiple programs, allow a filter
            if len(permitted_ids) > 1:
                program_choices = [(None, "All My Programs")] + [
                    (pid, prog_map.get(pid, f"Program ID: {pid}")) for pid in permitted_ids
                ]
                selected_prog_id = st.selectbox(
                    "Filter by Program:",
                    options=[pc[0] for pc in program_choices],
                    format_func=lambda pid: "All My Programs" if pid is None else f"{prog_map.get(pid, f'Program ID: {pid}')}"
                )
                if selected_prog_id is not None:
                    logs = [
                        r for r in logs
                        if (r["program_id"] == selected_prog_id or selected_prog_id is None)
                    ]

    # ---------------------------------------------------------
    # 3) Student Name filter
    # ---------------------------------------------------------
    with col2:
        all_names = sorted({doc.get("name", "Unknown") for doc in logs})
        name_choice = st.selectbox(
            "Filter by Student:",
            options=["All Students"] + all_names,
            help="Select a student to view only their attendance records"
        )
        if name_choice != "All Students":
            logs = [doc for doc in logs if doc.get("name") == name_choice]

    if not logs:
        st.info("📌 No attendance records found for that filter.")
        return

    st.success(f"Showing {len(logs)} attendance records")

    # ---------------------------------------------------------
    # 4) Sorting
    # ---------------------------------------------------------
    sort_options = [
        "Date (Newest First)",
        "Date (Oldest First)",
        "Student Name",
        "Program",
        "Status",
    ]
    sort_choice = st.selectbox(
        "Sort by:",
        options=sort_options,
        index=0,
        help="Choose how to sort the attendance records"
    )
    
    # Apply sorting
    def get_date_str(record):
        """Return date as a string for sorting."""
        att_date = record.get("attendance", {}).get("date", "")
        # If it's a datetime, convert to iso. If string, just use it
        if isinstance(att_date, datetime):
            return att_date.isoformat()
        else:
            return str(att_date)

    if sort_choice == "Date (Newest First)":
        logs = sorted(logs, key=lambda x: get_date_str(x), reverse=True)
    elif sort_choice == "Date (Oldest First)":
        logs = sorted(logs, key=lambda x: get_date_str(x))
    elif sort_choice == "Student Name":
        logs = sorted(logs, key=lambda x: x.get("name", ""))
    elif sort_choice == "Program":
        logs = sorted(logs, key=lambda x: prog_map.get(x.get("program_id", 0), ""))
    elif sort_choice == "Status":
        logs = sorted(logs, key=lambda x: x.get("attendance", {}).get("status", ""))

    st.write("---")

    # ---------------------------------------------------------
    # 5) Display each record in an expander
    # ---------------------------------------------------------
    emoji_map = {
        "Present": "✅ Present",
        "Late": "🕑 Late",
        "Absent": "🚫 Absent",
        "Excused": "🤝 Excused"
    }

    for idx, doc in enumerate(logs):
        att = doc.get("attendance", {})
        raw_date = att.get("date", "")
        status_val = att.get("status", "")
        comment_val = att.get("comment", "")

        # 1) Convert the date to a stable string for the record key
        if isinstance(raw_date, datetime):
            date_str = raw_date.isoformat()
        else:
            date_str = str(raw_date)  # fallback if it's already a string or empty

        s_name = doc.get("name", "")
        p_id = doc.get("program_id", 0)
        student_id = doc.get("student_id", "?")

        program_name = prog_map.get(p_id, f"Program ID={p_id}")
        display_status = emoji_map.get(status_val, status_val)

        # Build a stable record_key from (student_id + iso_date_str)
        record_key = f"{student_id}_{date_str}"
        is_editing = (st.session_state["edit_record_key"] == record_key)

        # Prepare the label for the expander
        expander_label = f"{s_name} | {program_name} | {date_str} | {display_status}"
        
        with st.expander(expander_label, expanded=is_editing):
            # Check if this record is the same as the "delete candidate"
            # for two-step deletion
            if st.session_state["delete_candidate"] == record_key:
                st.warning(f"⚠️ Are you sure you want to delete {s_name}'s record on {date_str}?")

                # Confirm or Cancel
                if st.button("Cancel Delete", key=f"cancel_delete_{idx}"):
                    st.session_state["delete_candidate"] = None
                    st.rerun()
                if st.button("Confirm Delete", key=f"confirm_delete_{idx}"):
                    with st.spinner("Deleting record..."):
                        deleted = delete_attendance_subdoc(student_id, date_str)
                        if deleted:
                            st.success("✅ Attendance record deleted.")
                            # Force re-fetch next time
                            st.session_state["attendance_records"] = None
                        else:
                            st.warning("⚠️ No matching record found.")
                        st.session_state["delete_candidate"] = None
                        st.rerun()
                # Skip the rest of the expander if we’re in delete confirm mode
                continue

            # If not editing:
            if not is_editing:
                # Normal view mode
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px;">
                        <strong>Student:</strong> {s_name} (ID: {student_id})<br>
                        <strong>Program:</strong> {program_name}<br>
                        <strong>Date:</strong> {date_str}<br>
                        <strong>Status:</strong> {display_status}<br>
                        { f"**Comment:** {comment_val}" if comment_val else "" }
                    </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.write("**Actions:**")
                    
                    # Edit Button
                    if st.button("✏️ Edit", key=f"edit_btn_{idx}"):
                        # Store info in session for the next run
                        st.session_state["edit_record_key"] = record_key
                        st.session_state["edit_student_id"] = student_id
                        st.session_state["edit_student_name"] = s_name
                        st.session_state["edit_date"] = date_str
                        st.session_state["edit_status"] = status_val
                        st.session_state["edit_comment"] = comment_val
                        st.rerun()

                    # Delete Button (two-step approach)
                    if st.button("🗑️ Delete", key=f"delete_btn_{idx}"):
                        # Mark this record as the "delete candidate"
                        st.session_state["delete_candidate"] = record_key
                        st.rerun()

            else:
                # Edit mode
                st.subheader("✏️ Edit Attendance Record")

                # Parse the date string back into a datetime (if possible)
                default_dt_str = st.session_state["edit_date"]
                try:
                    default_dt = datetime.fromisoformat(default_dt_str)
                except ValueError:
                    # fallback if it's not parseable
                    default_dt = datetime.now()

                with st.form(f"edit_form_{idx}"):
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.write(f"**Student Name**: {st.session_state['edit_student_name']}")
                        st.write(f"**Student ID**: {st.session_state['edit_student_id']}")
                        st.write(f"**Original Date**: {default_dt_str}")

                    with right_col:
                        new_date = st.date_input("New Date", value=default_dt.date())
                        new_time = st.time_input("New Time", value=default_dt.time())

                    combined_dt = datetime.combine(new_date, new_time)

                    status_opts = ["Present", "Late", "Absent", "Excused"]
                    status_icons = ["✅", "🕒", "🚫", "🤝"]
                    status_options_with_icons = [f"{icon} {status}" for icon, status in zip(status_icons, status_opts)]
                    
                    # figure out the default index
                    try:
                        default_idx = status_opts.index(st.session_state["edit_status"])
                    except ValueError:
                        default_idx = 0

                    selected_status_idx = st.selectbox(
                        "Status:", 
                        options=range(len(status_opts)),
                        format_func=lambda i: status_options_with_icons[i],
                        index=default_idx
                    )
                    new_status = status_opts[selected_status_idx]

                    new_comment = st.text_area(
                        "Comment",
                        value=st.session_state["edit_comment"],
                        height=100
                    )

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        cancel_btn = st.form_submit_button("Cancel")
                    with c2:
                        save_btn = st.form_submit_button("Save Changes")
                    
                    if save_btn:
                        with st.spinner("Updating attendance record..."):
                            success = upsert_attendance_subdoc(
                                student_id=st.session_state["edit_student_id"],
                                target_date=combined_dt,
                                new_status=new_status,
                                new_comment=new_comment,
                                old_date=old_date_parsed if 'old_date_parsed' in locals() else None
                            )
                    
                            if success:
                                st.success("✅ Attendance updated successfully.")

                                # If the date changed, remove old record
                                old_date_str = st.session_state["edit_date"]
                                if isinstance(old_date_str, str):
                                    try:
                                        old_date_parsed = datetime.fromisoformat(old_date_str)
                                    except ValueError:
                                        old_date_parsed = None
                                    if old_date_parsed and old_date_parsed != combined_dt:
                                        delete_attendance_subdoc(
                                            st.session_state["edit_student_id"],
                                            old_date_str
                                        )

                               
                                if "selected_prog_id" in st.session_state:
                                    current_program = st.session_state["selected_prog_id"]
                                if "selected_student" in st.session_state:  
                                    current_student = st.session_state["selected_student"]

                                # Clear attendance data to force refresh
                                st.session_state["attendance_records"] = None
                                st.session_state["edit_record_key"] = None

                                # Rerun with stored filters
                                st.rerun()
                            else:
                                st.error("❌ Failed to update attendance record.")

                    if cancel_btn:
                        st.session_state["edit_record_key"] = None
                        st.rerun()
#####################
# PAGE: Take Attendance
#####################

   
def show_missed_counts():
    st.subheader("Missed Counts for All Students")

    # Only fetch missed data once or if the user requests a refresh
    if "missed_counts" not in st.session_state:
        st.session_state["missed_counts"] = None

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

#####################
# PAGE: Manage Schedules
#####################
def page_manage_schedules():
    """
    Page for an instructor (or admin) to create, view, edit, and delete schedules,
    with a streamlined recurrence pattern selection for "One-Time" or "Weekly."
    """
    # Initialize edit state if not already done
    if "editing_schedule_id" not in st.session_state:
        st.session_state["editing_schedule_id"] = None

    # 1) Check login
    instructor_id = st.session_state.get("instructor_id", None)
    is_admin = st.session_state.get("is_admin", False)
    if not instructor_id and not is_admin:
        st.error("🔒 You must be logged in as an instructor or admin to manage schedules.")
        return

    # 2) Build a program map from Postgres
    all_programs = list_programs()
    prog_map = {p["program_id"]: p["program_name"] for p in all_programs}

    # 3) Determine which program IDs this user can manage
    if is_admin:
        program_id_options = list(prog_map.keys())
        user_type = "Administrator"
    else:
        program_id_options = st.session_state.get("instructor_program_ids", [])
        if not program_id_options:
            st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
            return
        user_type = "Instructor"

    st.header("📅 Manage Class Schedules")
    st.write(f"*Logged in as: {user_type}*")
    
    # Help expander
    with st.expander("ℹ️ How to manage schedules", expanded=False):
        st.markdown("""
        ### Managing Class Schedules:
        - **Create a New Schedule**: Add a one-time or recurring class schedule
        - **View Existing Schedules**: See all schedules for your assigned programs
        - **Edit Schedules**: Update details of existing schedules
        - **Delete Schedules**: Remove schedules that are no longer needed
        
        Only instructors who created a schedule (or admins) can edit or delete it.
        """)

    # --------------------------------------------------------------------------
    # A) Create a New Schedule
    # --------------------------------------------------------------------------
    with st.expander("➕ Create a New Schedule", expanded=True):
        st.subheader("Create a New Class Schedule")
        
        if program_id_options:
            selected_prog_id = st.selectbox(
                "Select Program",
                options=program_id_options,
                format_func=lambda pid: f"{prog_map.get(pid, f'Unknown')} (ID: {pid})",
                key="select_program_for_new_schedule",
                help="Choose which program this schedule will belong to"
            )
        else:
            st.warning("⚠️ No assigned programs available.")
            return

        # Create column layout for better organization
        col1, col2 = st.columns(2)
        
        # Basic fields
        with col1:
            title = st.text_input("Class Title *", "", key="new_schedule_title", 
                                 help="Enter a descriptive title for this class")
        
        with col2:
            # ***** Recurrence radio: Only "One-Time" or "Weekly" *****
            recurrence_choice = st.radio(
                "Recurrence Pattern",
                ["One-Time", "Weekly"],  # "Monthly" removed
                horizontal=True,
                help="Choose how often this session occurs"
            )
        
        notes = st.text_area("Additional Notes/Description", key="new_schedule_notes",
                            help="Add any relevant details about this class")

        # We'll store location/time/days in these variables
        location = ""
        days_times = []
        start_dt = None
        end_dt = None

        # --------- One-Time vs Weekly (Monthly lines are commented out) ---------
        st.write("---")
        if recurrence_choice == "One-Time":
            st.subheader("📆 One-Time Session Details")
            
            col_date, col_loc = st.columns(2)
            with col_date:
                chosen_date = st.date_input("Class Date", value=date.today(), 
                                          help="Select the date when this class will occur")
            
            with col_loc:
                location = st.text_input("Location", placeholder="Zoom link or room number",
                                       help="Enter where this class will take place")
            
            col_start, col_end = st.columns(2)
            with col_start:
                start_t = st.time_input("Start Time", value=time(9, 0),
                                      help="Select when the class begins")
                st.write(f"Class begins at: **{start_t.strftime('%I:%M %p').lstrip('0')}**")
            
            with col_end:
                end_t = st.time_input("End Time", value=time(10, 0),
                                    help="Select when the class ends")
                st.write(f"Class ends at: **{end_t.strftime('%I:%M %p').lstrip('0')}**")

        elif recurrence_choice == "Weekly":
            st.subheader("🔄 Weekly Recurring Schedule")
            st.write("Select which days of the week this class meets, and specify times for each day.")
            
            selected_days = st.multiselect(
                "Days of Week",
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                help="Select all days when this class meets weekly"
            )
            
            if not selected_days:
                st.info("👆 Please select at least one day of the week above")
            
            for d in selected_days:
                with st.container():
                    st.write(f"**📆 {d} Schedule**")
                    col1, col2 = st.columns(2)

                    with col1:
                        start_for_day = st.time_input(
                            f"{d} Start Time",
                            value=time(9, 0),
                            key=f"{d}_start_time",
                            help=f"When does the class start on {d}?"
                        )
                        st.write(f"Starts at: **{start_for_day.strftime('%I:%M %p').lstrip('0')}**")
                        
                        end_for_day = st.time_input(
                            f"{d} End Time",
                            value=time(10, 0),
                            key=f"{d}_end_time",
                            help=f"When does the class end on {d}?"
                        )
                        st.write(f"Ends at: **{end_for_day.strftime('%I:%M %p').lstrip('0')}**")
                    
                    with col2:
                        loc_for_day = st.text_input(
                            f"Location for {d}",
                            placeholder="Zoom link or room number",
                            key=f"{d}_loc",
                            help=f"Where does the class meet on {d}?"
                        )
                    
                    days_times.append({
                        "day": d,
                        "start_time": str(start_for_day),
                        "end_time": str(end_for_day),
                        "location": loc_for_day
                    })
                    
                    # Add a separator between days
                    if d != selected_days[-1]:
                        st.write("---")

        # -------------- "Create Schedule" button --------------
        st.write("---")
        create_col1, create_col2 = st.columns([3, 1])
        
        with create_col2:
            create_button = st.button("✅ Create Schedule", 
                                     help="Save this schedule to the database")
        
        if create_button:
            # Validate inputs
            if not title.strip():
                st.error("❌ Class title is required")
            elif recurrence_choice == "Weekly" and not days_times:
                st.error("❌ Please select at least one day of the week")
            else:
                with st.spinner("Creating schedule..."):
                    if recurrence_choice == "One-Time":
                        start_dt = datetime.combine(chosen_date, start_t)
                        end_dt = datetime.combine(chosen_date, end_t)
                        doc = {
                            "instructor_id": instructor_id,
                            "program_id": selected_prog_id,
                            "title": title,
                            "recurrence": "None",  # internally store as "None"
                            "notes": notes,
                            "start_datetime": start_dt,
                            "end_datetime": end_dt,
                            "days_times": [],
                            "location": location,
                            "created_by_username": st.session_state.get("instructor_username", "Admin"),
                            "created_at": datetime.utcnow()
                        }
                    else:  # "Weekly" only
                        doc = {
                            "instructor_id": instructor_id,
                            "program_id": selected_prog_id,
                            "title": title,
                            "recurrence": "Weekly",
                            "notes": notes,
                            "days_times": days_times,
                            "start_datetime": None,
                            "end_datetime": None,
                            "created_by_username": st.session_state.get("instructor_username", "Admin"),
                            "created_at": datetime.utcnow()
                        }

                    new_id = create_schedule(doc)
                    st.success(f"✅ Created schedule with ID: {new_id}")
                    notify_schedule_change(selected_prog_id, doc, event_type="created")
                    st.rerun()

    # --------------------------------------------------------------------------
    # B) Show Existing Schedules
    # --------------------------------------------------------------------------
    st.write("---")
    st.subheader("📋 Existing Schedules")
    
    # Fetch schedules
    with st.spinner("Loading schedules..."):
        schedules_for_programs = list_schedules_by_program(program_id_options)

    if not schedules_for_programs:
        st.info("📌 No schedules found for your assigned programs.")
        return
    
    # Add program filter if there are multiple programs
    unique_programs = list(set(sch.get("program_id") for sch in schedules_for_programs))
    if len(unique_programs) > 1:
        filter_options = [None] + unique_programs
        selected_filter = st.selectbox(
            "Filter by Program:",
            options=filter_options,
            format_func=lambda pid: "All Programs" if pid is None else prog_map.get(pid, f"Unknown (ID: {pid})"),
            help="Choose a specific program to view only its schedules"
        )
        
        if selected_filter is not None:
            schedules_for_programs = [sch for sch in schedules_for_programs if sch.get("program_id") == selected_filter]
    
    # Add a count of schedules
    st.write(f"Showing {len(schedules_for_programs)} schedules")
    
    # Process each schedule
    for idx, sch in enumerate(schedules_for_programs):
        sid = sch["_id"]
        pid = sch.get("program_id", None)
        prog_name = prog_map.get(pid, f"Unknown (ID={pid})")
        
        # Check if this schedule is being edited
        is_editing = st.session_state["editing_schedule_id"] == sid
        
        # Determine who can edit this schedule
        schedule_creator = sch.get("instructor_id")
        user_can_edit = is_admin or (schedule_creator == instructor_id)
        
        # Color background based on recurrence type
        # bg_color = "#e6f3ff" if sch.get("recurrence") == "None" else "#e6ffe6"  # light blue for one-time, light green for recurring
        # No background color, just use borders
        bg_color = "transparent"  # no background color
        # Create an expander for each schedule, auto-expanded if being edited
        with st.expander(f"**{sch.get('title', '')}** | {prog_name} | {sch.get('recurrence', 'None').replace('None', 'One-Time')}", expanded=is_editing):
            if not is_editing:
                # Normal view mode
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    # Use HTML for better formatting with background color
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px; background-color: {bg_color};">
                        <strong>Title:</strong> {sch.get('title', '')}<br>
                        <strong>Program:</strong> {prog_name}<br>
                        <strong>Recurrence:</strong> {sch.get('recurrence', 'None').replace('None', 'One-Time')}<br>
                        <strong>Notes:</strong> {sch.get('notes', '')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Created/Updated information
                    created_by = sch.get("created_by_username", "N/A")
                    created_at = sch.get("created_at", "N/A")
                    updated_by = sch.get("updated_by_username", "N/A")
                    updated_at = sch.get("updated_at", "N/A")

                    st.write(f"**Created by:** {created_by} at {created_at}")
                    if updated_by != "N/A":
                        st.write(f"**Last Updated by:** {updated_by} at {updated_at}")
                    
                    # Show schedule details based on recurrence type
                    if sch.get("recurrence") == "None":
                        # One-time schedule
                        start_text = _format_time_12h(sch.get("start_datetime"))
                        end_text = _format_time_12h(sch.get("end_datetime"))
                        st.write(f"**Date/Time:** {start_text} → {end_text}")
                        if sch.get("location"):
                            st.write(f"**Location:** {sch['location']}")
                    elif sch.get("recurrence") == "Weekly":
                        # Weekly schedule
                        dt_list = sch.get("days_times", [])
                        if dt_list:
                            st.write("**Weekly Schedule:**")
                            for d_obj in dt_list:
                                day = d_obj["day"]
                                s_24 = d_obj["start_time"]
                                e_24 = d_obj["end_time"]
                                s_12 = _format_time_12h(s_24)
                                e_12 = _format_time_12h(e_24)
                                loc = d_obj.get("location", "")
                                st.write(f"- **{day}:** {s_12} → {e_12}, Location: {loc}")
                
                # Action buttons column
                with col_actions:
                    if user_can_edit:
                        st.write("**Actions:**")
                        
                        # Edit button
                        if st.button("✏️ Edit", key=f"btn_edit_{sid}", 
                                   help=f"Edit this schedule"):
                            st.session_state["editing_schedule_id"] = sid
                            st.rerun()
                        
                        # Delete button
                        if st.button("🗑️ Delete", key=f"btn_delete_{sid}", 
                                   help=f"Delete this schedule"):
                            # Add confirmation step
                            st.warning(f"⚠️ Are you sure you want to delete this schedule?")
                            col_cancel, col_confirm = st.columns(2)
                            
                            with col_cancel:
                                if st.button("Cancel", key=f"cancel_delete_{sid}"):
                                    st.rerun()
                                    
                            with col_confirm:
                                if st.button("Confirm Delete", key=f"confirm_delete_{sid}"):
                                    with st.spinner("Deleting schedule..."):
                                        if delete_schedule(sid):
                                            st.success("✅ Schedule deleted.")
                                            st.rerun()
                                        else:
                                            st.error("❌ Delete failed or no such schedule.")
                    else:
                        st.info("ℹ️ You can view this schedule but cannot edit or delete it.")
            else:
                # Edit mode within the expander
                schedule_doc = next((x for x in schedules_for_programs if x["_id"] == sid), None)
                if not schedule_doc:
                    st.error("❌ Schedule not found or not authorized.")
                    return

                st.subheader(f"✏️ Edit Schedule")
                
                old_title = schedule_doc.get("title", "")
                old_notes = schedule_doc.get("notes", "")
                old_recurrence = schedule_doc.get("recurrence", "None")
                old_location = schedule_doc.get("location", "")
                old_days_times = schedule_doc.get("days_times", [])
                old_program_id = schedule_doc.get("program_id", None)
                
                # Show program information
                st.write(f"**Program:** {prog_map.get(old_program_id, f'Unknown (ID={old_program_id})')}")
                
                # Basic fields
                col1, col2 = st.columns(2)
                
                with col1:
                    new_title = st.text_input(
                        "Title *",
                        value=old_title,
                        key=f"edit_title_{sid}",
                        help="Class title"
                    )
                
                with col2:
                    new_recurrence = st.selectbox(
                        "Recurrence",
                        ["None", "Weekly"],  # Removed "Monthly"
                        index=["None", "Weekly"].index(old_recurrence),
                        key=f"edit_recurrence_{sid}",
                        help="How often this class occurs"
                    )
                
                new_notes = st.text_area(
                    "Notes",
                    value=old_notes,
                    key=f"edit_notes_{sid}",
                    help="Additional information about this class"
                )
                
                st.write("---")
                
                # Time and location fields based on recurrence type
                if new_recurrence == "None":
                    st.subheader("📆 One-Time Session Details")
                    
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

                    col_date, col_loc = st.columns(2)
                    with col_date:
                        edited_start_date = st.date_input(
                            "Date",
                            value=start_date_val,
                            key=f"edit_start_date_{sid}",
                            help="When this class occurs"
                        )
                    
                    with col_loc:
                        edited_location = st.text_input(
                            "Location",
                            value=old_location,
                            key=f"edit_location_{sid}",
                            help="Where this class meets"
                        )
                    
                    col_start, col_end = st.columns(2)
                    with col_start:
                        edited_start_time = st.time_input(
                            "Start Time",
                            value=start_time_val,
                            key=f"edit_start_time_{sid}",
                            help="When class begins"
                        )
                        st.write(f"Starts at: **{edited_start_time.strftime('%I:%M %p').lstrip('0')}**")
                    
                    with col_end:
                        edited_end_time = st.time_input(
                            "End Time",
                            value=end_time_val,
                            key=f"edit_end_time_{sid}",
                            help="When class ends"
                        )
                        st.write(f"Ends at: **{edited_end_time.strftime('%I:%M %p').lstrip('0')}**")
                    
                    # Maintain same date for start and end
                    edited_end_date = edited_start_date
                    new_days_times = []
                    
                else:  # Weekly recurrence
                    st.subheader("🔄 Weekly Schedule")
                    
                    old_selected_days = [d["day"] for d in old_days_times]
                    selected_days = st.multiselect(
                        "Days of Week",
                        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        default=old_selected_days,
                        key=f"edit_selected_days_{sid}",
                        help="Which days this class meets each week"
                    )
                    
                    if not selected_days:
                        st.info("👆 Please select at least one day of the week")

                    new_days_times = []
                    for d in selected_days:
                        existing = next((x for x in old_days_times if x["day"] == d), None)
                        default_start = time(9, 0)
                        default_end = time(10, 0)
                        default_loc = ""

                        if existing:
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

                        with st.container():
                            st.write(f"**📆 {d} Schedule**")
                            col_a, col_b = st.columns(2)

                            with col_a:
                                new_start = st.time_input(
                                    f"{d} Start Time",
                                    value=default_start,
                                    key=f"{sid}_{d}_start_key",
                                    help=f"When class starts on {d}"
                                )
                                st.write(f"Starts at: **{new_start.strftime('%I:%M %p').lstrip('0')}**")

                                new_end = st.time_input(
                                    f"{d} End Time",
                                    value=default_end,
                                    key=f"{sid}_{d}_end_key",
                                    help=f"When class ends on {d}"
                                )
                                st.write(f"Ends at: **{new_end.strftime('%I:%M %p').lstrip('0')}**")

                            with col_b:
                                new_loc = st.text_input(
                                    f"Location for {d}",
                                    value=default_loc,
                                    key=f"{sid}_{d}_loc_key",
                                    help=f"Where class meets on {d}"
                                )

                            new_days_times.append({
                                "day": d,
                                "start_time": str(new_start),
                                "end_time": str(new_end),
                                "location": new_loc
                            })
                            
                            # Add separator between days
                            if d != selected_days[-1]:
                                st.write("---")
                    
                    edited_location = None
                
                # Bottom buttons
                st.write("---")
                save_col, cancel_col = st.columns(2)

                # Save Changes button
                with save_col:
                    if st.button("💾 Save Changes", key=f"save_changes_btn_{sid}"):
                        # Validate inputs
                        if not new_title.strip():
                            st.error("❌ Class title is required")
                        elif new_recurrence != "None" and not new_days_times:
                            st.error("❌ Please select at least one day of the week")
                        else:
                            with st.spinner("Updating schedule..."):
                                updates = {
                                    "title": new_title,
                                    "recurrence": new_recurrence,
                                    "notes": new_notes,
                                    "updated_by_username": st.session_state.get("username", "Unknown"),
                                    "updated_at": datetime.utcnow()
                                }

                                if new_recurrence == "None":
                                    updates["days_times"] = []
                                    s_dt = datetime.combine(edited_start_date, edited_start_time)
                                    e_dt = datetime.combine(edited_end_date, edited_end_time)
                                    updates["start_datetime"] = s_dt
                                    updates["end_datetime"] = e_dt
                                    updates["location"] = edited_location
                                else:
                                    updates["days_times"] = new_days_times
                                    updates["start_datetime"] = None
                                    updates["end_datetime"] = None
                                    updates.pop("location", None)

                                success = update_schedule(sid, updates)
                                if success:
                                    st.success("✅ Schedule updated successfully.")

                                    # Build a doc for the notification email
                                    updated_doc = {
                                        "program_id": old_program_id,
                                        "title": new_title,
                                        "recurrence": new_recurrence,
                                        "notes": new_notes,
                                        "days_times": new_days_times if new_recurrence != "None" else [],
                                        "location": edited_location if new_recurrence == "None" else None,
                                    }
                                    notify_schedule_change(
                                        program_id=old_program_id,
                                        schedule_doc=updated_doc,
                                        event_type="updated"
                                    )
                                else:
                                    st.error("❌ No changes made, or update failed.")

                                st.session_state["editing_schedule_id"] = None
                                st.rerun()
                
                with cancel_col:
                    if st.button("❌ Cancel", key=f"cancel_edit_btn_{sid}"):
                        # Remove the editing flag from session state
                        st.session_state["editing_schedule_id"] = None
                        st.success("✅ Edit canceled")
                        st.rerun()
        
        # Add a separator between schedules
        if idx < len(schedules_for_programs) - 1:
            st.write("---")
            

def highlight_high_absences(row):
    """
    Called by df.style.apply() to highlight entire row if "Total Absences" > threshold.
    Returns a list of style strings or '' for each cell in the row.
    """
    threshold = 3
    if row.get("Total Absences", 0) > threshold:
        return ["background-color: #ffcccc"] * len(row)
    else:
        return [""] * len(row)
def highlight_high_absences(row):
    """
    Called by df.style.apply() to highlight entire row if "Total Absences" > threshold.
    Returns a list of style strings or '' for each cell in the row.
    """
    threshold = 3
    if row.get("Total Absences", 0) > threshold:
        return ["background-color: #ffcccc"] * len(row)
    else:
        return [""] * len(row)

def display_document_sending_form(is_admin):
    """Display the form for sending a document to recipients."""
    st.subheader("📤 Send Document")
    
    # In the document sending UI section - now with improved URL handling
    with st.form("send_document_form"):
        st.subheader(f"Send Document: {st.session_state.get('selected_document_title', '')}")
        
        # Get recipient information
        recipient_type = st.selectbox(
            "Recipient Type", 
            ["Student", "Instructor", "Parent", "Other"]
        )
        
        # Dynamically load recipients based on type
        if recipient_type == "Student":
            # For students, load from your database
            students = get_all_students()
            if not students:
                st.warning("No students found in the database.")
                st.stop()
                
            student_options = [(s["student_id"], s["name"]) for s in students]
            
            selected_student_id = st.selectbox(
                "Select Student",
                options=[so[0] for so in student_options],
                format_func=lambda sid: next((s[1] for s in student_options if s[0] == sid), "Unknown")
            )
            
            # Get the selected student's details
            selected_student = next((s for s in students if s["student_id"] == selected_student_id), None)
            if selected_student:
                recipient_id = selected_student_id
                recipient_name = selected_student["name"]
                recipient_email = selected_student.get("contact_email", "")
                
                # Show email and allow editing
                recipient_email = st.text_input("Recipient Email", value=recipient_email)
        
        elif recipient_type == "Instructor":
            # For instructors, load from your database
            instructors = list_instructors()
            if not instructors:
                st.warning("No instructors found in the database.")
                st.stop()
                
            instructor_options = [(i["instructor_id"], i["username"]) for i in instructors]
            
            selected_instructor_id = st.selectbox(
                "Select Instructor",
                options=[io[0] for io in instructor_options],
                format_func=lambda iid: next((i[1] for i in instructor_options if i[0] == iid), "Unknown")
            )
            
            recipient_id = selected_instructor_id
            recipient_name = next((i[1] for i in instructor_options if i[0] == selected_instructor_id), "Unknown")
            recipient_email = st.text_input("Recipient Email", value="")
        
        else:
            # For other types, allow manual entry
            recipient_id = "manual"
            recipient_name = st.text_input("Recipient Name")
            recipient_email = st.text_input("Recipient Email")
        
        # URL Configuration Section with visual separation
        st.markdown("---")
        st.markdown("### 🌐 Document Access Configuration")
        
        # Add base URL input field with default value and more prominent display
        col1, col2 = st.columns([3, 1])
        with col1:
            default_base_url = st.session_state.get("base_url", "https://clubstride.org")
            base_url = st.text_input(
                "Base URL for Document Link",
                value=default_base_url,
                help="The complete domain for document signing links (e.g., https://clubstride.org)"
            )
        
        with col2:
            # Display URL format information
            st.write("URL format will be verified on submission")
        
        # Additional URL options
        url_expiration = st.slider(
            "Link Expiration (days)",
            min_value=1,
            max_value=90,
            value=30,
            help="How many days until the signing link expires"
        )
        
        # Store base URL in session for future use
        if base_url != default_base_url:
            st.session_state["base_url"] = base_url
        
        # Email customization option
        customize_email = st.checkbox("Customize Email Message", value=False)
        if customize_email:
            email_subject = st.text_input(
                "Email Subject", 
                value=f"Please sign: {st.session_state.get('selected_document_title', 'Document')}"
            )
            email_message = st.text_area(
                "Additional Message",
                value="",
                placeholder="Enter any additional text you'd like to include in the email...",
                height=100
            )
        else:
            email_subject = f"Please sign: {st.session_state.get('selected_document_title', 'Document')}"
            email_message = ""
        
        # Option to override duplicate check
        skip_duplicate_check = False
        if is_admin:
            skip_duplicate_check = st.checkbox(
                "Skip duplicate check", 
                value=False,
                help="Send document even if recipient has already received it"
            )
            
        # Submit button
        submit_send = st.form_submit_button("Send Document")
    
    # Process form submission (outside the form)
    if submit_send:
        # Validate inputs
        if not base_url.startswith(("http://", "https://")):
            st.warning("URL should start with http:// or https://")
        elif not recipient_email:
            st.error("Recipient email is required.")
        elif not recipient_name:
            st.error("Recipient name is required.")
        elif not base_url:
            st.error("Base URL is required for document access.")
        else:
            with st.spinner("Checking for duplicates and sending document..."):
                document_id = st.session_state.get("selected_document_id")
                
                # Check for duplicate document instances
                if not skip_duplicate_check and check_document_instance_exists(document_id, recipient_email):
                    st.warning(f"⚠️ This document has already been sent to {recipient_email}.")
                    
                    # Ask if user wants to send anyway
                    if st.button("Send anyway"):
                        # Proceed with sending
                        skip_duplicate_check = True
                    else:
                        # Stop here
                        return
                
                # Create document instance with expiration based on slider
                instance_id = create_document_instance(
                    document_id=document_id,
                    recipient_id=recipient_id,
                    recipient_type=recipient_type.lower(),
                    recipient_name=recipient_name,
                    recipient_email=recipient_email,
                    expiration_days=url_expiration
                )
                
                if instance_id:
                    # Send the document with the specified base URL and custom message if provided
                    success = send_document(
                        instance_id=instance_id, 
                        base_url=base_url,
                        email_subject=email_subject,
                        email_message=email_message
                    )
                    
                    if success:
                        st.success(f"✅ Document sent successfully to {recipient_name}!")
                        
                        # Show link details for reference
                        st.info(f"A unique signing link was sent to {recipient_email}. The link will expire in {url_expiration} days.")
                        
                        # Options for next actions
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Send to Another Recipient"):
                                st.session_state["sending_to_another"] = True
                                st.rerun()
                        
                        with col2:
                            if st.button("Return to Documents"):
                                st.session_state.pop("selected_document_id", None)
                                st.session_state.pop("selected_document_title", None)
                                st.rerun()
                    else:
                        st.error("Failed to send document. Please check email configuration and try again.")
                else:
                    st.error("Failed to create document instance. Please try again.")
                    
def display_document_tracking():
    """Display the document tracking interface in the Track Documents tab."""
    st.subheader("Document Tracking")
    
    # 1. Search interface
    st.write("### 🔍 Search Documents by Recipient")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Search by recipient name or email:",
            help="Enter a name or email to find documents sent to specific recipients"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 Search", use_container_width=True)
    
    # Display results when search is performed
    if search_term or search_button:
        if not search_term:
            st.warning("⚠️ Please enter a search term.")
        else:
            with st.spinner(f"Searching for documents sent to '{search_term}'..."):
                results = search_documents_by_recipient(search_term)
                
                if not results:
                    st.info(f"📌 No documents found for '{search_term}'.")
                else:
                    st.success(f"Found {len(results)} document(s) sent to recipients matching '{search_term}'.")
                    
                    # Display the results in a nice format
                    for idx, item in enumerate(results):
                        instance = item["instance"]
                        document = item["document"]
                        
                        with st.expander(f"**{document.get('title', 'Untitled')}** - sent to {instance.get('recipient_name', 'Unknown')}"):
                            col_info, col_status = st.columns([2, 1])
                            
                            with col_info:
                                st.markdown(f"**Document:** {document.get('title', 'Untitled')}")
                                st.markdown(f"**Type:** {document.get('document_type', 'Unknown').replace('_', ' ').title()}")
                                st.markdown(f"**Recipient:** {instance.get('recipient_name', 'Unknown')}")
                                st.markdown(f"**Email:** {instance.get('recipient_email', 'Unknown')}")
                                
                                # Display dates if available
                                if instance.get("sent_at_formatted"):
                                    st.markdown(f"**Sent:** {instance.get('sent_at_formatted')}")
                                if instance.get("viewed_at_formatted"):
                                    st.markdown(f"**Viewed:** {instance.get('viewed_at_formatted')}")
                                if instance.get("signed_at_formatted"):
                                    st.markdown(f"**Signed:** {instance.get('signed_at_formatted')}")
                                if instance.get("expiration_date_formatted"):
                                    st.markdown(f"**Expires:** {instance.get('expiration_date_formatted')}")
                            
                            with col_status:
                                status = instance.get("status", "unknown")
                                if status == "sent":
                                    st.markdown("**Status:** 📤 Sent")
                                elif status == "viewed":
                                    st.markdown("**Status:** 👁️ Viewed")
                                elif status == "signed":
                                    st.markdown("**Status:** ✅ Signed")
                                elif status == "declined":
                                    st.markdown("**Status:** ❌ Declined")
                                elif status == "expired":
                                    st.markdown("**Status:** ⏱️ Expired")
                                else:
                                    st.markdown(f"**Status:** {status.capitalize()}")
                                
                                # Action buttons
                                if status in ["sent", "viewed"]:
                                    if st.button("📧 Send Reminder", key=f"remind_{idx}"):
                                        if send_reminder(instance["instance_id"]):
                                            st.success("✅ Reminder sent successfully!")
                                        else:
                                            st.error("❌ Failed to send reminder. Please try again.")
                                
                                # View document link if available
                                # file_location = document.get("file_location")
                                # if file_location:
                                #     file_path = get_document_file_path(file_location)
                                #     if file_path and os.path.exists(file_path):
                                #         if document.get("file_type") == "application/pdf":
                                #             with open(file_path, "rb") as f:
                                #                 pdf_bytes = f.read()
                                #             st.download_button(
                                #                 label="📄 View Document",
                                #                 data=pdf_bytes,
                                #                 file_name=f"{document.get('title', 'document')}.pdf",
                                #                 mime="application/pdf",
                                #                 key=f"download_{idx}"
                                #             )
                                #         else:
                                #             st.info("File preview not available.")
                            
                            # Activity log in an expander
                            activity_log = instance.get("activity_log", [])
                            if activity_log:
                                with st.expander("View Activity Log"):
                                    for activity in activity_log:
                                        timestamp = activity.get("timestamp")
                                        if timestamp and isinstance(timestamp, datetime):
                                            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                        else:
                                            timestamp_str = str(timestamp)
                                        
                                        action = activity.get("action", "unknown")
                                        details = activity.get("details", "")
                                        
                                        if action == "created":
                                            st.markdown(f"**{timestamp_str}:** 🆕 Document created - {details}")
                                        elif action == "sent":
                                            st.markdown(f"**{timestamp_str}:** 📤 Document sent - {details}")
                                        elif action == "viewed":
                                            st.markdown(f"**{timestamp_str}:** 👁️ Document viewed - {details}")
                                        elif action == "signed":
                                            st.markdown(f"**{timestamp_str}:** ✅ Document signed - {details}")
                                        elif action == "declined":
                                            st.markdown(f"**{timestamp_str}:** ❌ Document declined - {details}")
                                        elif action == "reminder_sent":
                                            st.markdown(f"**{timestamp_str}:** 📧 Reminder sent - {details}")
                                        else:
                                            st.markdown(f"**{timestamp_str}:** {action.capitalize()} - {details}")
                
                    # Add a "Clear Results" button
                    if st.button("🔄 Clear Results"):
                        st.rerun()

    # 2. Advanced filters section
    with st.expander("Advanced Filters", expanded=False):
        st.write("Filter documents by additional criteria:")
        
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Document Status", 
                ["sent", "viewed", "signed", "declined", "expired"],
                default=None,
                help="Filter by document status"
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=[],
                help="Filter by date sent"
            )
        
        if st.button("Apply Filters"):
            st.info("Advanced filtering will be implemented in a future update.")

    # 3. Helpful resources
    with st.expander("Tips for Document Tracking", expanded=False):
        st.markdown("""
        ### 📋 Document Tracking Tips
        
        - **Search by Name or Email**: Enter a recipient's name or email address to find documents sent to them
        - **Send Reminders**: You can send reminder emails for documents that haven't been signed yet
        - **Check Status**: See whether documents have been viewed, signed, or declined
        - **View Activity**: Each document has an activity log showing its complete history
        
        Need more help? Contact the administrator for assistance.
        """)

def page_manage_documents():
    st.header("📄 Document Management")
    
    # Check permissions
    is_admin = st.session_state.get("is_admin", False)
    instructor_id = st.session_state.get("instructor_id")
    
    if not (is_admin or instructor_id):
        st.error("You must be logged in to access this page.")
        return
    
    # Check if we're in document sending mode
    if "selected_document_id" in st.session_state and not st.session_state.get("sending_to_another"):
        # Show document sending form
        display_document_sending_form(is_admin)
        
        # Add a back button at the bottom of the form
        if st.button("← Back to Documents", key="back_from_sending"):
            # Clear the selected document
            st.session_state.pop("selected_document_id", None)
            st.session_state.pop("selected_document_title", None)
            st.rerun()
        return  # Exit early, only show the sending form
    
    # Create tabs for different document functions
    tab1, tab2, tab3 = st.tabs([
        "📄 My Documents", 
        "➕ Upload Document", 
        "📊 Document Status", 
        # "🔍 Track Documents"
    ])
    
    # ------------------------------------
    # TAB 1: View Existing Documents
    # ------------------------------------

    with tab1:
        st.subheader("My Documents")
        
        # Initialize session state for delete confirmation
        if "delete_document_id" not in st.session_state:
            st.session_state["delete_document_id"] = None
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            doc_type_filter = st.selectbox(
                "Filter by Document Type:",
                ["All Types", "Waiver", "Permission Slip", "Registration Form", "Other"]
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All Statuses", "Active", "Draft", "Archived"]
            )
        
        # Get documents based on filters
        query_params = {}
        
        # Apply owner filter (admin can see all)
        if not is_admin:
            query_params["owner_id"] = instructor_id
        
        # Apply document type filter
        if doc_type_filter != "All Types":
            query_params["document_type"] = doc_type_filter.lower().replace(" ", "_")
        
        # Apply status filter
        if status_filter != "All Statuses":
            query_params["status"] = status_filter.lower()
        
        documents = list_documents(**query_params)
        
        if not documents:
            st.info("No documents found. Upload a document to get started.")
        else:
            # Display documents in a nice format
            for doc in documents:
                with st.expander(f"**{doc['title']}** ({doc['document_type']})"):
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.write(f"**Description:** {doc['description']}")
                        st.write(f"**Created:** {doc['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Status:** {doc['status'].capitalize()}")
                        
                        # Get program name if applicable
                        if doc.get("program_id"):
                            program_name = "Unknown Program"
                            for p in list_programs():
                                if p["program_id"] == doc["program_id"]:
                                    program_name = p["program_name"]
                                    break
                            st.write(f"**Program:** {program_name}")
                    
                    with col_b:
                        st.write("**Actions:**")
                        
                        # View document button
                        if st.button("View Document", key=f"view_{doc['document_id']}"):
                            file_path = get_document_file_path(doc["file_location"])
                            
                            # For PDF files, use Streamlit's PDF display
                            if doc["file_type"] == "application/pdf":
                                with open(file_path, "rb") as f:
                                    pdf_bytes = f.read()
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"{doc['title']}.pdf",
                                    mime="application/pdf"
                                )
                            else:
                                st.info(f"File format ({doc['file_type']}) preview not available. Please download.")
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()
                                st.download_button(
                                    label="Download File",
                                    data=file_bytes,
                                    file_name=os.path.basename(doc["file_location"]),
                                    mime=doc["file_type"]
                                )
                        
                        # Send document button
                        if st.button("Send Document", key=f"send_{doc['document_id']}"):
                            st.session_state["selected_document_id"] = doc["document_id"]
                            st.session_state["selected_document_title"] = doc["title"]
                            st.session_state.pop("sending_to_another", None)
                            st.rerun()
                        
                        # Delete document button with confirmation
                        if st.session_state["delete_document_id"] == doc["document_id"]:
                            # Show confirmation dialog
                            st.warning(f"Are you sure you want to delete '{doc['title']}'? This cannot be undone.")
                            
                            conf_col1, conf_col2 = st.columns(2)
                            with conf_col1:
                                if st.button("Cancel", key=f"cancel_delete_{doc['document_id']}"):
                                    st.session_state["delete_document_id"] = None
                                    st.rerun()
                            
                            with conf_col2:
                                if st.button("Confirm Delete", key=f"confirm_delete_{doc['document_id']}"):
                                    with st.spinner("Deleting document..."):
                                        success = delete_document(doc["document_id"])
                                        if success:
                                            st.success(f"Document '{doc['title']}' deleted successfully.")
                                            st.session_state["delete_document_id"] = None
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete document. Please try again.")
                                            st.session_state["delete_document_id"] = None
                        else:
                            # Show delete button
                            if st.button("Delete Document", key=f"delete_{doc['document_id']}"):
                                st.session_state["delete_document_id"] = doc["document_id"]
                                st.rerun()
        st.write("---")
        st.write("### 📨 Send to Program Participants")
        st.write("Send documents to all participants in a specific program.")

        # Program selection
        program_options = list_programs()
        if not is_admin:
            permitted_ids = st.session_state.get("instructor_program_ids", [])
            program_options = [p for p in program_options if p["program_id"] in permitted_ids]

        if program_options:
            # Select program
            selected_program_id = st.selectbox(
                "Select Program",
                options=[p["program_id"] for p in program_options],
                format_func=lambda pid: next((p["program_name"] for p in program_options if p["program_id"] == pid), "Unknown")
            )
            
            # Select document to send
            documents = list_documents(
                owner_id=None if is_admin else instructor_id,
                program_id=selected_program_id
            )
            
            if documents:
                document_id = st.selectbox(
                    "Select Document to Send",
                    options=[d["document_id"] for d in documents],
                    format_func=lambda did: next((d["title"] for d in documents if d["document_id"] == did), "Unknown")
                )
                
                # Option to skip duplicate check
                skip_duplicate_check = st.checkbox(
                    "Skip duplicate check", 
                    value=False,
                    help="Send to all participants even if they've already received this document"
                )
                
                # Confirmation button
                if st.button("Send to All Program Participants"):
                    # Get all students in the program
                    students = get_all_students(program_ids=[selected_program_id])
                    
                    if students:
                        with st.spinner(f"Sending document to {len(students)} participants..."):
                            success_count = 0
                            skipped_count = 0
                            failed_count = 0
                            
                            # Progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, student in enumerate(students):
                                # Update progress
                                progress = int((i + 1) / len(students) * 100)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing {i+1} of {len(students)} participants...")
                                
                                # Check if student has an email
                                if student.get("contact_email"):
                                    # Check if this student already has this document
                                    if not skip_duplicate_check and check_document_instance_exists(document_id, student["contact_email"]):
                                        skipped_count += 1
                                        continue
                                        
                                    # Create document instance for this student
                                    instance_id = create_document_instance(
                                        document_id=document_id,
                                        recipient_id=student["student_id"],
                                        recipient_type="student",
                                        recipient_name=student["name"],
                                        recipient_email=student["contact_email"],
                                        expiration_days=30  # Default 30 days
                                    )
                                    
                                    if instance_id:
                                        # Send the document
                                        if send_document(instance_id):
                                            success_count += 1
                                        else:
                                            failed_count += 1
                                    else:
                                        failed_count += 1
                                else:
                                    # Student has no email
                                    failed_count += 1
                            
                            # Final status update
                            progress_bar.progress(100)
                            status_text.text("Processing complete!")
                            
                            # Show summary
                            if success_count > 0:
                                st.success(f"✅ Document sent successfully to {success_count} participants!")
                            if skipped_count > 0:
                                st.info(f"ℹ️ Skipped {skipped_count} participants who already received this document.")
                            if failed_count > 0:
                                st.warning(f"⚠️ Failed to send to {failed_count} participants (missing email or error).")
                    else:
                        st.warning("No participants found in this program.")
            else:
                st.warning("No documents available for this program.")
        else:
            st.warning("No programs available. Please create a program first.")

    
    # ------------------------------------
    # TAB 2: Upload New Document
    # -----------------------------------
    
    with tab2:
        st.subheader("Add New Document")
        
        with st.form("upload_document_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Document Title *")
                doc_type = st.selectbox(
                    "Document Type *",
                    ["Waiver", "Permission Slip", "Registration Form", "Other"]
                )
            
            with col2:
                # Program selection
                program_options = list_programs()
                
                # If instructor, filter to only show assigned programs
                if not is_admin:
                    permitted_ids = st.session_state.get("instructor_program_ids", [])
                    program_options = [p for p in program_options if p["program_id"] in permitted_ids]
                
                program_choices = [(None, "No Specific Program")] + [
                    (p["program_id"], p["program_name"]) for p in program_options
                ]
                
                selected_program = st.selectbox(
                    "Associated Program (Optional)",
                    options=[pc[0] for pc in program_choices],
                    format_func=lambda pid: "No Specific Program" if pid is None else next(
                        (p[1] for p in program_choices if p[0] == pid), "Unknown"
                    )
                )
                
                is_template = st.checkbox("Save as Template", value=False, 
                                        help="Templates can be reused for multiple recipients")
            
            description = st.text_area("Description", placeholder="Briefly describe this document")

            document_url = st.text_input(
                "Document URL *", 
                placeholder="https://docs.google.com/document/d/...",
                help="Enter the URL where this document can be accessed"
            )

            # URL validation message
            if document_url:
                if not (document_url.startswith("http://") or document_url.startswith("https://")):
                    st.warning("URL should start with http:// or https://")     
            
            col_a, col_b = st.columns(2)
            with col_a:
                # Required signatures
                required_roles = st.multiselect(
                    "Required Signatures",
                    ["Student", "Parent/Guardian", "Instructor", "Admin"],
                    default=["Student"]
                )
            
            with col_b:
                # Expiration setting
                has_expiration = st.checkbox("Document Expires", value=True)
                if has_expiration:
                    expiration_days = st.number_input(
                        "Expires After (Days)",
                        min_value=1,
                        max_value=365,
                        value=30
                    )
            
            # Add option to skip duplicate checking (for admin use)
            skip_duplicate_check = False
            if is_admin:
                skip_duplicate_check = st.checkbox("Skip Duplicate Checking", 
                                                value=False,
                                                help="Allow creating duplicate documents (admin only)")
            
            submit_btn = st.form_submit_button("Add Document")
            
            if submit_btn:
                if not title or not document_url:
                    st.error("Please provide a title and document URL.")
                elif not (document_url.startswith("http://") or document_url.startswith("https://")):
                    st.error("Please enter a valid URL starting with http:// or https://")
                else:
                    with st.spinner("Adding document..."):
                        # Save file
                        owner_id = instructor_id if instructor_id else "admin"
                        owner_type = "instructor" if instructor_id else "admin"
                        try:
                            # Calculate expiration
                            expiration_date = None
                            if has_expiration:
                                expiration_date = datetime.utcnow() + timedelta(days=expiration_days)
                            
                            # Format required signatures
                            required_signatures = []
                            for role in required_roles:
                                required_signatures.append({
                                    "role": role.lower().replace("/", "_"),
                                    "name": "",
                                    "id": ""
                                })
                            
                            # Create document record with duplicate checking
                            document_id = create_document(
                                title=title,
                                description=description,
                                document_type=doc_type.lower().replace(" ", "_"),
                                owner_id=owner_id,
                                owner_type=owner_type,
                                document_url=document_url,  # Pass URL instead of file info
                                program_id=selected_program,
                                expiration_date=expiration_date,
                                is_template=is_template,
                                required_signatures=required_signatures,
                                check_duplicates=not skip_duplicate_check  # Use the admin option
                            )
                            
                            if document_id == "duplicate":
                                st.error("⚠️ A document with this title or URL already exists. Please use a different title or URL.")
                            elif document_id:
                                st.success(f"Document added successfully! Document ID: {document_id}")
                                
                                # Store document ID in session state for later use
                                st.session_state["temp_document_id"] = document_id
                                st.session_state["temp_document_title"] = title
                                
                                # NOTE: We're not asking about sending here - will handle that outside the form
                            else:
                                st.error("Failed to add document. Please try again.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            print(e)

            # Add this code OUTSIDE the form, after the form block ends
            # This handles the "Send now" functionality

            # Check if we just created a document successfully
            if "temp_document_id" in st.session_state:
                document_id = st.session_state["temp_document_id"]
                document_title = st.session_state["temp_document_title"]
                
                # Ask if user wants to send the document now
                send_choice = st.radio(
                    "Would you like to send this document to recipients now?",
                    ["Yes, send now", "No, I'll do it later"],
                    index=1,
                    key="send_choice_radio"
                )
                
                # Handle send choice
                if send_choice == "Yes, send now":
                    if st.button("Continue to send"):
                        # Prepare for sending
                        st.session_state["selected_document_id"] = document_id
                        st.session_state["selected_document_title"] = document_title
                        st.session_state.pop("sending_to_another", None)
                        st.session_state.pop("temp_document_id", None)
                        st.session_state.pop("temp_document_title", None)
                        st.rerun()
                elif send_choice == "No, I'll do it later":
                    # REPLACE THIS LINE (it's using a button inside a form):
                    # if st.button("Return to documents list"):
                    
                    # WITH THIS CODE INSTEAD (outside the form):
                    return_to_list = st.checkbox("Return to documents list", key="return_to_list_btn")
                    if return_to_list:
                        # Clear temporary variables
                        st.session_state.pop("temp_document_id", None)
                        st.session_state.pop("temp_document_title", None)
                        st.rerun()
            # if "temp_document_id" in st.session_state:
            #     document_id = st.session_state["temp_document_id"]
            #     document_title = st.session_state["temp_document_title"]
                
            #     # Ask if user wants to send the document now
            #     send_choice = st.radio(
            #         "Would you like to send this document to recipients now?",
            #         ["Yes, send now", "No, I'll do it later"],
            #         index=1,
            #         key="send_choice_radio"
            #     )
                
            #     # Handle send choice
            #     if send_choice == "Yes, send now":
            #         if st.button("Continue to send"):
            #             # Prepare for sending
            #             st.session_state["selected_document_id"] = document_id
            #             st.session_state["selected_document_title"] = document_title
            #             st.session_state.pop("sending_to_another", None)
            #             st.session_state.pop("temp_document_id", None)
            #             st.session_state.pop("temp_document_title", None)
            #             st.rerun()
            #     elif send_choice == "No, I'll do it later":
            #         if st.button("Return to documents list"):
            #             # Clear temporary variables
            #             st.session_state.pop("temp_document_id", None)
            #             st.session_state.pop("temp_document_title", None)
            #             st.rerun()
                            
    # with tab2:
    #     st.subheader("Upload New Document")
        
    #     with st.form("upload_document_form"):
    #         col1, col2 = st.columns(2)
            
    #         with col1:
    #             title = st.text_input("Document Title *")
    #             doc_type = st.selectbox(
    #                 "Document Type *",
    #                 ["Waiver", "Permission Slip", "Registration Form", "Other"]
    #             )
            
    #         with col2:
    #             # Program selection
    #             program_options = list_programs()
                
    #             # If instructor, filter to only show assigned programs
    #             if not is_admin:
    #                 permitted_ids = st.session_state.get("instructor_program_ids", [])
    #                 program_options = [p for p in program_options if p["program_id"] in permitted_ids]
                
    #             program_choices = [(None, "No Specific Program")] + [
    #                 (p["program_id"], p["program_name"]) for p in program_options
    #             ]
                
    #             selected_program = st.selectbox(
    #                 "Associated Program (Optional)",
    #                 options=[pc[0] for pc in program_choices],
    #                 format_func=lambda pid: "No Specific Program" if pid is None else next(
    #                     (p[1] for p in program_choices if p[0] == pid), "Unknown"
    #                 )
    #             )
                
    #             is_template = st.checkbox("Save as Template", value=False, 
    #                                      help="Templates can be reused for multiple recipients")
            
    #         description = st.text_area("Description", placeholder="Briefly describe this document")

    #         document_url = st.text_input(
    #         "Document URL *", 
    #         placeholder="https://docs.google.com/document/d/...",
    #         help="Enter the URL where this document can be accessed")

    #         if document_url:
    #             if not (document_url.startswith("http://") or document_url.startswith("https://")):
    #                 st.warning("URL should start with http:// or https://")     
    #         # uploaded_file = st.file_uploader(
    #         #     "Upload Document *", 
    #         #     type=["pdf", "doc", "docx", "txt"],
    #         #     help="Upload the document file"
    #         # )
            
    #         col_a, col_b = st.columns(2)
    #         with col_a:
    #             # Required signatures
    #             required_roles = st.multiselect(
    #                 "Required Signatures",
    #                 ["Student", "Parent/Guardian", "Instructor", "Admin"],
    #                 default=["Student"]
    #             )
            
    #         with col_b:
    #             # Expiration setting
    #             has_expiration = st.checkbox("Document Expires", value=True)
    #             if has_expiration:
    #                 expiration_days = st.number_input(
    #                     "Expires After (Days)",
    #                     min_value=1,
    #                     max_value=365,
    #                     value=30
    #                 )
            
    #         submit_btn = st.form_submit_button("Upload Document")
            
    #         if submit_btn:
    #             if not title or not document_url:
    #                 st.error("Please provide a title and document URL.")
    #             elif not (document_url.startswith("http://") or document_url.startswith("https://")):
    #                 st.error("Please enter a valid URL starting with http:// or https://")
    #             else:
    #                 with st.spinner("Adding  document..."):
    #                     # Save file
    #                     owner_id = instructor_id if instructor_id else "admin"
    #                     owner_type = "instructor" if instructor_id else "admin"
    #                     try:
    #                     # Calculate expiration
    #                         expiration_date = None
    #                         if has_expiration:
    #                             expiration_date = datetime.utcnow() + timedelta(days=expiration_days)
                            
    #                         # Format required signatures
    #                         required_signatures = []
    #                         for role in required_roles:
    #                             required_signatures.append({
    #                                 "role": role.lower().replace("/", "_"),
    #                                 "name": "",
    #                                 "id": ""
    #                             })
                            
    #                         # Create document record
    #                         document_id = create_document(
    #                             title=title,
    #                             description=description,
    #                             document_type=doc_type.lower().replace(" ", "_"),
    #                             owner_id=owner_id,
    #                             owner_type=owner_type,
    #                             document_url=document_url,  # Pass URL instead of file info
    #                             program_id=selected_program,
    #                             expiration_date=expiration_date,
    #                             is_template=is_template,
    #                             required_signatures=required_signatures
    #                         )
                            
    #                         if document_id:
    #                             st.success(f"Document added successfully! Document ID: {document_id}")
                                
    #                             # Ask if user wants to send the document now
    #                             send_now = st.radio(
    #                                 "Would you like to send this document to recipients now?",
    #                                 ["Yes, send now", "No, I'll do it later"],
    #                                 index=1
    #                             )
                                
    #                             if send_now == "Yes, send now":
    #                                 # Provide quick send option
    #                                 st.session_state["selected_document_id"] = document_id
    #                                 st.session_state["selected_document_title"] = title
    #                                 st.session_state.pop("sending_to_another", None)
    #                                 st.rerun()
    #                         else:
    #                             st.error("Failed to add document. Please try again.")
    #                     except Exception as e:
    #                         st.error(f"Error: {str(e)}")
    #                         print(e)
                        
                        # try:
                        #     # Save the file
                        #     file_location, file_type, file_size = save_uploaded_document(
                        #         uploaded_file, owner_id, doc_type.lower().replace(" ", "_")
                        #     )
                            
                        #     # Calculate expiration
                        #     expiration_date = None
                        #     if has_expiration:
                        #         expiration_date = datetime.utcnow() + timedelta(days=expiration_days)
                            
                        #     # Format required signatures
                        #     required_signatures = []
                        #     for role in required_roles:
                        #         required_signatures.append({
                        #             "role": role.lower().replace("/", "_"),
                        #             "name": "",
                        #             "id": ""
                        #         })
                            
                        #     # Create document record
                        #     document_id = create_document(
                        #         title=title,
                        #         description=description,
                        #         document_type=doc_type.lower().replace(" ", "_"),
                        #         owner_id=owner_id,
                        #         owner_type=owner_type,
                        #         file_location=file_location,
                        #         file_type=file_type,
                        #         file_size=file_size,
                        #         program_id=selected_program,
                        #         expiration_date=expiration_date,
                        #         is_template=is_template,
                        #         required_signatures=required_signatures
                        #     )
                            
                        #     if document_id:
                        #         st.success(f"Document uploaded successfully! Document ID: {document_id}")
                                
                        #         # Ask if user wants to send the document now
                        #         send_now = st.radio(
                        #             "Would you like to send this document to recipients now?",
                        #             ["Yes, send now", "No, I'll do it later"],
                        #             index=1
                        #         )
                                
                        #         if send_now == "Yes, send now":
                        #             # Provide quick send option
                        #             st.session_state["selected_document_id"] = document_id
                        #             st.session_state["selected_document_title"] = title
                        #             st.session_state.pop("sending_to_another", None)
                        #             st.rerun()
                        #     else:
                        #         st.error("Failed to upload document. Please try again.")
                        # except Exception as e:
                        #     st.error(f"Error: {str(e)}")
                        #     print(e)
    
    # ------------------------------------
    # TAB 3: Document Status
    # ------------------------------------
    with tab3:
        st.subheader("Document Status Dashboard")
        
        # Get documents and instances
        if is_admin:
            documents = list_documents()
        else:
            documents = list_documents(owner_id=instructor_id)
        
        if not documents:
            st.info("No documents found to track status.")
        else:
            # Create a status summary
            total_documents = len(documents)
            st.write(f"**Total Documents:** {total_documents}")
            
            # Select document to view status
            doc_options = [(d["document_id"], d["title"]) for d in documents]
            selected_doc_id = st.selectbox(
                "Select Document to View Status",
                options=[do[0] for do in doc_options],
                format_func=lambda did: next((d[1] for d in doc_options if d[0] == did), "Unknown")
            )
            
            # Get status counts for selected document
            if selected_doc_id:
                status_counts = get_document_status_counts(selected_doc_id)
                
                # Display counts as metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Sent", status_counts.get("sent", 0))
                with col2:
                    st.metric("Viewed", status_counts.get("viewed", 0))
                with col3:
                    st.metric("Signed", status_counts.get("signed", 0))
                with col4:
                    st.metric("Declined", status_counts.get("declined", 0) + status_counts.get("expired", 0))
                
                # Option to send reminders for unsigned documents
                st.subheader("Send Reminders")
                
                if st.button("Send Reminders to Unsigned Recipients"):
                    # Implementation for sending reminders
                    # This would use your send_reminder function
                    st.info("Reminder functionality will be implemented here.")
    
    
    # ------------------------------------
    # TAB 4: Track Documents
    # ------------------------------------
    # This code should be placed inside the TAB 4 section of page_manage_documents.py

    # with tab4:
    #     st.subheader("Document Tracking")
        
    #     # 1. Search interface
    #     st.write("### 🔍 Search Documents by Recipient")
        
    #     col1, col2 = st.columns([3, 1])
        
    #     with col1:
    #         search_term = st.text_input(
    #             "Enter recipient name or email:",
    #             placeholder="e.g., John Smith or john@example.com",
    #             help="Search for documents sent to a specific recipient"
    #         )
        
    #     with col2:
    #         st.write("")
    #         st.write("")
    #         search_button = st.button("🔍 Search", use_container_width=True)
        
    #     # Show results when search is performed
    #     if search_term and search_button:
    #         with st.spinner(f"Searching for documents sent to '{search_term}'..."):
    #             results = search_documents_by_recipient(search_term)
                
    #             if not results:
    #                 st.info(f"No documents found for recipient: '{search_term}'")
    #             else:
    #                 st.success(f"Found {len(results)} document(s) for recipient: '{search_term}'")
                    
    #                 # Display results in a visually appealing way
    #                 for idx, item in enumerate(results):
    #                     instance = item["instance"]
    #                     document = item["document"]
                        
    #                     # Create a card-like container for each result
    #                     status = instance.get("status", "unknown")
    #                     status_emoji = "✅" if status == "signed" else "👁️" if status == "viewed" else "❌" if status == "declined" else "⏱️" if status == "expired" else "📤"
                        
    #                     # Create a nice card-like container with a border
    #                     st.markdown(f"""
    #                     <div style="border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:15px;">
    #                         <h3>{document.get('title', 'Untitled Document')}</h3>
    #                     </div>
    #                     """, unsafe_allow_html=True)
                        
    #                     col1, col2 = st.columns([3, 1])
                        
    #                     with col1:
    #                         st.markdown(f"**Type:** {document.get('document_type', '').replace('_', ' ').title()}")
    #                         st.markdown(f"**Recipient:** {instance.get('recipient_name', 'Unknown')}")
    #                         st.markdown(f"**Email:** {instance.get('recipient_email', 'Unknown')}")
                            
    #                         # Show document URL if available
    #                         if document.get("document_url"):
    #                             st.markdown(f"**Document URL:** [Open Document]({document.get('document_url')})")
                            
    #                         # Format dates for better readability
    #                         if instance.get("sent_at_formatted"):
    #                             st.markdown(f"**Sent:** {instance.get('sent_at_formatted')}")
    #                         if instance.get("viewed_at_formatted"):
    #                             st.markdown(f"**Viewed:** {instance.get('viewed_at_formatted')}")
    #                         if instance.get("signed_at_formatted"):
    #                             st.markdown(f"**Signed:** {instance.get('signed_at_formatted')}")
    #                         if instance.get("expiration_date_formatted"):
    #                             st.markdown(f"**Expires:** {instance.get('expiration_date_formatted')}")
                        
    #                     with col2:
    #                         st.markdown(f"**Status:** {status_emoji} {status.capitalize()}")
                            
    #                         # Add action buttons based on document status
    #                         if status in ["sent", "viewed"]:
    #                             if st.button("📧 Send Reminder", key=f"remind_{idx}"):
    #                                 reminder_sent = send_reminder(instance["instance_id"])
    #                                 if reminder_sent:
    #                                     st.success("✅ Reminder sent successfully!")
    #                                 else:
    #                                     st.error("❌ Failed to send reminder.")
                        
    #                     # Show activity log in an expander
    #                     with st.expander("View Activity History", expanded=False):
    #                         activity_log = instance.get("activity_log", [])
    #                         if activity_log:
    #                             for activity in sorted(activity_log, key=lambda x: x.get("timestamp", datetime.min), reverse=True):
    #                                 timestamp = activity.get("timestamp")
    #                                 action = activity.get("action", "")
    #                                 details = activity.get("details", "")
                                    
    #                                 if isinstance(timestamp, datetime):
    #                                     timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    #                                 else:
    #                                     timestamp_str = str(timestamp)
                                    
    #                                 action_emoji = "🆕" if action == "created" else "📤" if action == "sent" else "👁️" if action == "viewed" else "✅" if action == "signed" else "❌" if action == "declined" else "📧" if action == "reminder_sent" else "⏱️" if action == "expired" else ""
                                    
    #                                 st.markdown(f"{action_emoji} **{timestamp_str}**: {action.capitalize()} - {details}")
    #                         else:
    #                             st.write("No activity recorded for this document.")
                        
    #                     # Add a divider between results
    #                     st.markdown("---")
                    
    #                 # Add a clear results button
    #                 if st.button("🔄 Clear Results"):
    #                     st.rerun()
        
    #     # 2. Advanced search options
    #     with st.expander("Advanced Search Options", expanded=False):
    #         st.write("Filter documents by additional criteria:")
            
    #         col1, col2 = st.columns(2)
            
    #         with col1:
    #             status_filter = st.multiselect(
    #                 "Document Status",
    #                 ["sent", "viewed", "signed", "declined", "expired"],
    #                 default=None,
    #                 help="Filter by document status"
    #             )
            
    #         with col2:
    #             date_range = st.date_input(
    #                 "Date Range",
    #                 value=[],
    #                 help="Filter by sent date"
    #             )
            
    #         program_filter = st.selectbox(
    #             "Filter by Program",
    #             options=["All Programs"] + [p["program_name"] for p in list_programs()],
    #             help="Filter documents by their associated program"
    #         )
            
    #         if st.button("Apply Filters"):
    #             st.info("Advanced filtering will be implemented in a future update.")
        
       # 3. Feature to send documents to all participants in a program
           # st.write("---")
        # st.write("### 📨 Send to Program Participants")
        # st.write("Send documents to all participants in a specific program.")
        
        # # Program selection
        # program_options = list_programs()
        # if not is_admin:
        #     permitted_ids = st.session_state.get("instructor_program_ids", [])
        #     program_options = [p for p in program_options if p["program_id"] in permitted_ids]
        
        # if program_options:
        #     # Select program
        #     selected_program_id = st.selectbox(
        #         "Select Program",
        #         options=[p["program_id"] for p in program_options],
        #         format_func=lambda pid: next((p["program_name"] for p in program_options if p["program_id"] == pid), "Unknown")
        #     )
            
        #     # Select document to send
        #     documents = list_documents(
        #         owner_id=None if is_admin else instructor_id,
        #         program_id=selected_program_id
        #     )
            
        #     if documents:
        #         document_id = st.selectbox(
        #             "Select Document to Send",
        #             options=[d["document_id"] for d in documents],
        #             format_func=lambda did: next((d["title"] for d in documents if d["document_id"] == did), "Unknown")
        #         )
                
        #         # Confirmation button
        #         if st.button("Send to All Program Participants"):
        #             # Get all students in the program
        #             students = get_all_students(program_ids=[selected_program_id])
                    
        #             if students:
        #                 with st.spinner(f"Sending document to {len(students)} participants..."):
        #                     success_count = 0
        #                     for student in students:
        #                         # Create document instance for each student
        #                         if student.get("contact_email"):  # Only send to students with emails
        #                             instance_id = create_document_instance(
        #                                 document_id=document_id,
        #                                 recipient_id=student["student_id"],
        #                                 recipient_type="student",
        #                                 recipient_name=student["name"],
        #                                 recipient_email=student["contact_email"],
        #                                 expiration_days=30  # Default 30 days
        #                             )
                                    
        #                             if instance_id:
        #                                 # Send the document
        #                                 if send_document(instance_id):
        #                                     success_count += 1
                            
        #                     if success_count > 0:
        #                         st.success(f"✅ Document sent successfully to {success_count} participants!")
        #                     else:
        #                         st.error("Failed to send documents. Please check participant email addresses.")
        #             else:
        #                 st.warning("No participants found in this program.")
        #     else:
        #         st.warning("No documents available for this program.")
        # else:
        #     st.warning("No programs available. Please create a program first.")
        
        # 4. Help and tips
        with st.expander("Help & Tips", expanded=False):
            st.markdown("""
            ### 📋 Document Tracking Help
            
            **What you can do here:**
            - Search for documents by recipient name or email
            - See document status (sent, viewed, signed, declined)
            - Send reminders for unsigned documents
            - View the complete activity log for each document
            - Send a document to all participants in a program at once
            
            **Tips:**
            - Use clear document titles to easily identify them later
            - Add detailed descriptions to help recipients understand what they're signing
            - Send reminders for important documents that haven't been signed
            - Check activity logs to see when documents were viewed or signed
            """)
    # st.subheader("Document Tracking")
    
    # # 1. Search interface
    # st.write("### 🔍 Search Documents by Recipient")
    
    # col1, col2 = st.columns([3, 1])
    
    # with col1:
    #     search_term = st.text_input(
    #         "Enter recipient name or email:",
    #         placeholder="e.g., John Smith or john@example.com",
    #         help="Search for documents sent to a specific recipient"
    #     )
    
    # with col2:
    #     st.write("")
    #     st.write("")
    #     search_button = st.button("🔍 Search", use_container_width=True)
    
    # # Show results when search is performed
    # if search_term and search_button:
    #     with st.spinner(f"Searching for documents sent to '{search_term}'..."):
    #         results = search_documents_by_recipient(search_term)
            
    #         if not results:
    #             st.info(f"No documents found for recipient: '{search_term}'")
    #         else:
    #             st.success(f"Found {len(results)} document(s) for recipient: '{search_term}'")
                
    #             # Display results in a visually appealing way
    #             for idx, item in enumerate(results):
    #                 instance = item["instance"]
    #                 document = item["document"]
                    
    #                 # Create a card-like container for each result
    #                 status = instance.get("status", "unknown")
    #                 status_emoji = "✅" if status == "signed" else "👁️" if status == "viewed" else "❌" if status == "declined" else "⏱️" if status == "expired" else "📤"
                    
    #                 st.markdown(f"### {document.get('title', 'Untitled Document')}")
                    
    #                 col1, col2 = st.columns([3, 1])
                    
    #                 with col1:
    #                     st.markdown(f"**Type:** {document.get('document_type', '').replace('_', ' ').title()}")
    #                     st.markdown(f"**Recipient:** {instance.get('recipient_name', 'Unknown')}")
    #                     st.markdown(f"**Email:** {instance.get('recipient_email', 'Unknown')}")
                        
    #                     # Format dates for better readability
    #                     if instance.get("sent_at_formatted"):
    #                         st.markdown(f"**Sent:** {instance.get('sent_at_formatted')}")
    #                     if instance.get("viewed_at_formatted"):
    #                         st.markdown(f"**Viewed:** {instance.get('viewed_at_formatted')}")
    #                     if instance.get("signed_at_formatted"):
    #                         st.markdown(f"**Signed:** {instance.get('signed_at_formatted')}")
    #                     if instance.get("expiration_date_formatted"):
    #                         st.markdown(f"**Expires:** {instance.get('expiration_date_formatted')}")
                    
    #                 with col2:
    #                     st.markdown(f"**Status:** {status_emoji} {status.capitalize()}")
                        
    #                     # Add action buttons based on document status
    #                     if status in ["sent", "viewed"]:
    #                         if st.button("📧 Send Reminder", key=f"remind_{idx}"):
    #                             reminder_sent = send_reminder(instance["instance_id"])
    #                             if reminder_sent:
    #                                 st.success("✅ Reminder sent successfully!")
    #                             else:
    #                                 st.error("❌ Failed to send reminder.")
                        
    #                     # Show download button if available
    #                     # file_path = get_document_file_path(document.get("file_location", ""))
    #                     # if os.path.exists(file_path):
    #                     #     with open(file_path, "rb") as f:
    #                     #         file_data = f.read()
    #                     #         file_name = os.path.basename(file_path)
    #                     #         st.download_button(
    #                     #             "📄 Download",
    #                     #             data=file_data,
    #                     #             file_name=file_name,
    #                     #             mime=document.get("file_type", "application/octet-stream"),
    #                     #             key=f"download_{idx}"
    #                     #         )
                    
    #                 # Show activity log in an expander
    #                 with st.expander("View Activity History", expanded=False):
    #                     activity_log = instance.get("activity_log", [])
    #                     if activity_log:
    #                         for activity in sorted(activity_log, key=lambda x: x.get("timestamp", datetime.min), reverse=True):
    #                             timestamp = activity.get("timestamp")
    #                             action = activity.get("action", "")
    #                             details = activity.get("details", "")
                                
    #                             if isinstance(timestamp, datetime):
    #                                 timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    #                             else:
    #                                 timestamp_str = str(timestamp)
                                
    #                             action_emoji = "🆕" if action == "created" else "📤" if action == "sent" else "👁️" if action == "viewed" else "✅" if action == "signed" else "❌" if action == "declined" else "📧" if action == "reminder_sent" else "⏱️" if action == "expired" else ""
                                
    #                             st.markdown(f"{action_emoji} **{timestamp_str}**: {action.capitalize()} - {details}")
    #                     else:
    #                         st.write("No activity recorded for this document.")
                    
    #                 # Add a divider between results
    #                 st.markdown("---")
                
    #             # Add a clear results button
    #             if st.button("🔄 Clear Results"):
    #                 st.rerun()

def get_nonprofit_prompts():
    """
    Return a dictionary of nonprofit assessment prompts with analysis descriptions
    and sample program objectives
    """
    return {
        "🌱 Community Impact Assessment": {
            "description": "Leverage qualitative and quantitative methods to evaluate the effectiveness of programs and measure tangible community improvements. Develop impact metrics and KPIs tailored to your community outreach initiatives, facilitating clear reporting and ongoing enhancement of program strategies.",
            "sample_objective": "Our program aims to develop youth leadership skills and improve academic outcomes through mentorship, workshops, and community service opportunities. We primarily serve underrepresented students from local schools who need additional support to reach their full potential."
        },
        "📊 Program Efficiency & Optimization": {
            "description": "Apply operational data analytics to assess nonprofit program delivery, identify efficiency gaps, and propose actionable improvements. Generate reports outlining cost-saving measures, improved resource allocation, and increased effectiveness aligned with mission goals.",
            "sample_objective": "Our program delivers essential skills training through weekly sessions, guest speakers, and hands-on projects. We focus on maximizing impact with limited resources, ensuring that our operations remain sustainable while delivering high-quality programming to participants."
        },
        "📈 Stakeholder Engagement Metrics": {
            "description": "Design comprehensive stakeholder analysis using engagement data and feedback mechanisms. Create detailed reports highlighting stakeholder participation, satisfaction, and recommendations for strengthening stakeholder relationships through targeted engagement strategies.",
            "sample_objective": "Our program engages multiple stakeholders including students, parents, school administrators, and community partners. We aim to create a collaborative ecosystem where all parties feel valued and contribute to the successful development of our youth participants."
        },
        "🔄 Project Lifecycle & Outcome Tracking": {
            "description": "Develop a robust system for tracking projects from inception through completion, using data-driven methodologies to assess outcomes versus goals. Generate clear and transparent progress reports emphasizing lessons learned, impact achieved, and areas for improvement.",
            "sample_objective": "Our program implements a structured curriculum with clear milestones and outcome measures. We track participant progress throughout the program cycle, from initial assessment through completion, measuring both quantitative metrics and qualitative growth indicators."
        },
        "🚦 Risk Management & Mitigation": {
            "description": "Conduct thorough risk assessments to identify potential project and operational vulnerabilities. Generate risk management plans with actionable mitigation steps, continuously updated with real-time data to safeguard project deliverables and nonprofit resources.",
            "sample_objective": "Our program operates in complex environments with various potential challenges. We aim to identify, assess, and mitigate risks to ensure continuity of services, safety of participants, and achievement of organizational goals despite constraints or unexpected obstacles."
        },
        "📣 Advocacy & Communication Impact": {
            "description": "Utilize data insights to measure the reach and effectiveness of advocacy campaigns and communication strategies. Produce compelling reports demonstrating advocacy outcomes, narrative effectiveness, and areas for strategic improvement to enhance public awareness and policy influence.",
            "sample_objective": "Our program includes a significant advocacy component aimed at raising awareness about youth issues and influencing positive policy changes. We communicate through various channels to educate the public, engage decision-makers, and amplify the voices of the communities we serve."
        }
    }


# Modify the report generation function to better handle custom approaches
def generate_ai_enhanced_report(pivot_df, program_name, project_description, analysis_method):
    """
    Generate a professional impact assessment report for nonprofit projects,
    enhanced with actual attendance data analysis.
    
    Args:
        pivot_df: DataFrame containing the attendance pivot data
        program_name: Name of the program being analyzed
        project_description: Text describing the project objectives and impact
        analysis_method: The selected analysis method/framework
        
    Returns:
        Generated impact assessment report text with data-driven insights
    """
    try:
        # Initialize OpenAI client
        openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
        if not openai_api_key:
            st.error("OpenAI API Key not found in secrets. Please configure it in Streamlit secrets.")
            return None
            
        client = OpenAI(api_key=openai_api_key)
        
        # Extract key metrics from the pivot_df to include in the report
        if pivot_df is not None:
            # Calculate overall attendance metrics
            total_students = len(pivot_df.index)
            avg_absences = pivot_df["Total Absences"].mean() if "Total Absences" in pivot_df.columns else 0
            max_absences = pivot_df["Total Absences"].max() if "Total Absences" in pivot_df.columns else 0
            
            # Identify students with high absence counts
            absence_threshold = 3
            high_risk_count = len(pivot_df[pivot_df["Total Absences"] > absence_threshold]) if "Total Absences" in pivot_df.columns else 0
            high_risk_percentage = (high_risk_count / total_students * 100) if total_students > 0 else 0
            
            # Get most common status values for better insights
            status_counts = {}
            for col in pivot_df.columns:
                if col != "Total Absences":
                    for status in pivot_df[col].value_counts().items():
                        status_value, count = status
                        if status_value not in status_counts:
                            status_counts[status_value] = 0
                        status_counts[status_value] += count
            
            status_summary = ", ".join([f"{status}: {count}" for status, count in status_counts.items()])
            
            # Create a data summary for the AI
            data_summary = f"""
            Program: {program_name}
            Total Students: {total_students}
            Average Absences Per Student: {avg_absences:.2f}
            Maximum Absences for Any Student: {max_absences}
            Students with Excessive Absences (>{absence_threshold}): {high_risk_count} ({high_risk_percentage:.1f}%)
            Status Distribution: {status_summary}
            """
            
            # Get details on high-risk students if any
            if high_risk_count > 0:
                high_risk_details = "High-Risk Students:\n"
                high_risk_students = pivot_df[pivot_df["Total Absences"] > absence_threshold]
                for student_name, absences in zip(high_risk_students.index, high_risk_students["Total Absences"]):
                    high_risk_details += f"- {student_name}: {absences} absences\n"
                data_summary += f"\n{high_risk_details}"
                
        else:
            data_summary = "No attendance data available for analysis."
        
        # Get the method name without the emoji for standard frameworks
        if analysis_method.startswith("🌱") or analysis_method.startswith("📊") or analysis_method.startswith("📈") or analysis_method.startswith("🔄") or analysis_method.startswith("🚦") or analysis_method.startswith("📣"):
            method_name = analysis_method.split(" ", 1)[1] if " " in analysis_method else analysis_method
        else:
            # For custom approaches, use the full text
            method_name = analysis_method
        
        # Create system prompt based on analysis method and attendance data
        system_prompt = f"""You are a professional AI analyst specializing in nonprofit impact measurement and program evaluation for Club Stride. 
        
Given the program description, attendance data, and analysis framework, generate a comprehensive assessment that addresses:

1. Context & Program Definition: 
   Briefly summarize the program's objectives and target participants based on the description provided.

2. Attendance Data Analysis: 
   - Provide an interpretation of the attendance metrics
   - Identify patterns, strengths, and areas of concern
   - Connect attendance patterns to potential program effectiveness

3. {method_name} Framework Analysis: 
   - Apply the specified analytical framework to evaluate the program
   - Identify key metrics and strategic insights based on this framework
   - Use the attendance data to support your analysis

4. Recommendations & Next Steps: 
   - Provide actionable recommendations to improve attendance
   - Suggest specific approaches to better track and measure impact
   - Outline immediate and long-term steps to enhance program effectiveness

Format your report in a professional, clear style with headings and bullet points where appropriate.
Make specific references to the attendance data provided to support your insights and recommendations."""
        
        # Generate the report using OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
                Program Description:
                {project_description}
                
                Attendance Data Analysis:
                {data_summary}
                
                Selected Analysis Framework: {method_name}
                """}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Extract and return the generated report
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            st.error("Failed to generate report: No content returned from API")
            return None
            
    except Exception as e:
        st.error(f"Error generating impact report: {str(e)}")
        return None



def page_generate_reports():
    # -------------------------------------------------------------------------
    # Page Header with Description
    # -------------------------------------------------------------------------
    st.header("📊 Attendance Reports & Analytics")
    st.write("Generate insights, visualizations, and downloadable reports from attendance data.")
    
    # Progress indicator for initial data loading
    with st.spinner("Loading attendance data..."):
        # 1) Admin or Instructor check
        is_admin = st.session_state.get("is_admin", False)
        user_type = "Admin" if is_admin else "Instructor"
        
        # 2) Build program map from Postgres
        all_programs = list_programs()  # e.g. [{"program_id":1,"program_name":"STEM"}, ...]
        prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
        
        # 3) Determine permitted program IDs
        if is_admin:
            program_id_options = [p["program_id"] for p in all_programs]  # admin sees all
        else:
            program_id_options = st.session_state.get("instructor_program_ids", [])
            if not program_id_options:
                st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
                return
        
        # 4) Fetch attendance records from Mongo
        records = fetch_all_attendance_records()
        if not records:
            st.info("ℹ️ No attendance data found.")
            return
        
        # 5) Filter by permitted program IDs
        filtered_records = [r for r in records if r.get("program_id") in program_id_options]
        if not filtered_records:
            st.info("ℹ️ No attendance data found for your assigned programs.")
            return
        
        # 6) Flatten records
        flattened = []
        for r in filtered_records:
            att = r["attendance"]
            pid = r.get("program_id", 0)
            flattened.append({
                "student_id": r.get("student_id"),
                "name": r.get("name"),
                "program_id": pid,
                "program_name": prog_map.get(pid, f"Program ID={pid}"),
                "date": att.get("date"),
                "status": att.get("status"),
                "comment": att.get("comment", "")
            })
        
        if not flattened:
            st.info("ℹ️ No valid attendance data to display.")
            return
        
        df = pd.DataFrame(flattened)
        if df.empty:
            st.info("ℹ️ No valid attendance data to display.")
            return

    # Display data summary
    st.success(f"✅ Loaded attendance data for {len(df['name'].unique())} students across {len(df['program_id'].unique())} programs.")
    
    # Create tabs for better organization - REMOVED THE 4th TAB
    tab1, tab2, tab3 = st.tabs(["📈 Visualizations", "🔍 Data Explorer", "📑 Program Report Generator"])
    
    with tab1:
        # [TAB 1 CONTENT UNCHANGED]
        # -------------------------------------------------------------------------
        # A) Admin-Only Visualizations (Overview)
        # -------------------------------------------------------------------------
        if is_admin:
            st.subheader("📊 Admin Overview Dashboard")
            st.write("These visualizations provide a high-level overview of attendance across all programs.")
            
            with st.expander("Admin Visualizations of Full Attendance Data", expanded=True):
                def status_to_numeric(s):
                    if s == "Present":
                        return 1
                    elif s == "Late":
                        return 0.5
                    else:
                        return 0
                
                df["attendance_value"] = df["status"].apply(status_to_numeric)
                
                # Add a metric summary at the top
                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                with col_metrics1:
                    avg_attendance = df["attendance_value"].mean() * 100
                    st.metric("Overall Attendance Rate", f"{avg_attendance:.1f}%")
                
                with col_metrics2:
                    present_rate = (df["status"] == "Present").mean() * 100
                    st.metric("Present Rate", f"{present_rate:.1f}%")
                
                with col_metrics3:
                    absent_rate = (df["status"] == "Absent").mean() * 100
                    st.metric("Absence Rate", f"{absent_rate:.1f}%")
                
                # Ranking by average attendance
                ranking_df = df.groupby("program_name", as_index=False)["attendance_value"].mean()
                ranking_df.rename(columns={"attendance_value": "avg_attendance_score"}, inplace=True)
                ranking_df.sort_values("avg_attendance_score", ascending=False, inplace=True)
                
                st.subheader("Program Ranking by Average Attendance")
                st.dataframe(ranking_df.style.highlight_max(subset=["avg_attendance_score"]), use_container_width=True)
                
                # Bar chart: average attendance score
                fig_bar = px.bar(
                    ranking_df,
                    x="program_name",
                    y="avg_attendance_score",
                    title="Average Attendance Score by Program",
                    color="avg_attendance_score",
                    color_continuous_scale="blues"
                )
                fig_bar.update_layout(xaxis_title="Program", yaxis_title="Average Attendance Score")
                
                # Pie chart: overall status distribution
                status_counts = df["status"].value_counts().reset_index()
                status_counts.columns = ["status", "count"]
                fig_pie = px.pie(
                    status_counts,
                    values="count",
                    names="status",
                    title="Distribution of Attendance Statuses",
                    hole=0.4,
                    color="status",
                    color_discrete_map={
                        "Present": "#28a745", 
                        "Late": "#ffc107", 
                        "Absent": "#dc3545", 
                        "Excused": "#6c757d"
                    }
                )
                
                # Time-series
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                daily_df = df.groupby("date", as_index=False)["attendance_value"].mean()
                fig_line = px.line(
                    daily_df,
                    x="date",
                    y="attendance_value",
                    title="Average Attendance Over Time (All Programs)",
                    markers=True
                )
                fig_line.update_layout(xaxis_title="Date", yaxis_title="Attendance Score")
                
                # Multi-line by program
                multi_df = df.groupby(["date", "program_name"], as_index=False)["attendance_value"].mean()
                fig_multi = px.line(
                    multi_df,
                    x="date",
                    y="attendance_value",
                    color="program_name",
                    title="Attendance Over Time by Program",
                    markers=True
                )
                fig_multi.update_layout(xaxis_title="Date", yaxis_title="Attendance Score", legend_title="Program")
                
                colA, colB = st.columns(2)
                with colA:
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with colB:
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.write("---")
                
                st.plotly_chart(fig_line, use_container_width=True)
                st.plotly_chart(fig_multi, use_container_width=True)
                
                # Download buttons for visualizations
                st.download_button(
                    label="📥 Download Attendance Summary CSV",
                    data=ranking_df.to_csv(index=False).encode('utf-8'),
                    file_name="attendance_summary.csv",
                    mime="text/csv"
                )
        else:
            # For instructors, show a simpler view
            st.subheader("📊 Attendance Overview")
            # Get instructor's programs
            instructor_programs = [prog_map.get(pid, f"Program {pid}") for pid in program_id_options]
            st.write(f"You have access to the following programs: {', '.join(instructor_programs)}")
            
            # Simple metrics for instructor
            instructor_df = df.copy()
            
            def status_to_numeric(s):
                if s == "Present":
                    return 1
                elif s == "Late":
                    return 0.5
                else:
                    return 0
            
            instructor_df["attendance_value"] = instructor_df["status"].apply(status_to_numeric)
            
            # Add metrics
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            with col_metrics1:
                avg_attendance = instructor_df["attendance_value"].mean() * 100
                st.metric("Overall Attendance Rate", f"{avg_attendance:.1f}%")
            
            with col_metrics2:
                present_rate = (instructor_df["status"] == "Present").mean() * 100
                st.metric("Present Rate", f"{present_rate:.1f}%")
            
            with col_metrics3:
                absent_rate = (instructor_df["status"] == "Absent").mean() * 100
                st.metric("Absence Rate", f"{absent_rate:.1f}%")
            
            # Simple charts for instructor
            status_counts = instructor_df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig_pie = px.pie(
                status_counts,
                values="count",
                names="status",
                title="Distribution of Attendance Statuses",
                hole=0.4,
                color="status",
                color_discrete_map={
                    "Present": "#28a745", 
                    "Late": "#ffc107", 
                    "Absent": "#dc3545", 
                    "Excused": "#6c757d"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab2:
        # [TAB 2 CONTENT UNCHANGED]
        # -------------------------------------------------------------------------
        # B) Data Explorer + Chart Building from Filtered Data
        # -------------------------------------------------------------------------
        st.subheader("🔍 Data Explorer & Custom Charts")
        st.write("Filter and visualize attendance data using various criteria.")
        
        with st.expander("How to use the Data Explorer", expanded=False):
            st.write("""
            1. Use the filter controls below to select specific data
            2. The table will update to show only matching records
            3. Choose a chart type to visualize the filtered data
            4. The chart will update automatically based on your selection
            """)
        
        explorer_output = dataframe_explorer(df, case=False)
        explorer_df = pd.DataFrame(explorer_output)
        
        if explorer_df.empty:
            st.info("ℹ️ No data matches your filter criteria. Try adjusting the filters.")
        else:
            st.write(f"**Showing {len(explorer_df)} records that match your criteria**")
            st.dataframe(explorer_df, use_container_width=True)
            
            # Add download button for filtered data
            st.download_button(
                label="📥 Download Filtered Data CSV",
                data=explorer_df.to_csv(index=False).encode('utf-8'),
                file_name="filtered_attendance_data.csv",
                mime="text/csv"
            )
            
            st.markdown("### 📈 Build a Custom Chart")
            st.write("Create visualizations from your filtered data")
            
            chart_type = st.selectbox(
                "Select Chart Type",
                [
                    "Bar - Status Counts",
                    "Line - Attendance Over Time",
                    "Bar - Student Attendance",
                    "Pie - Status Distribution",
                ],
                help="Choose the type of chart you want to create from your filtered data"
            )
            
            # Convert 'date' to datetime if needed
            explorer_df["date"] = pd.to_datetime(explorer_df["date"], errors="coerce")
            
            # Chart container with loading indicator
            chart_container = st.container()
            with chart_container:
                with st.spinner("Generating chart..."):
                    if chart_type == "Bar - Status Counts":
                        status_counts = explorer_df["status"].value_counts().reset_index()
                        status_counts.columns = ["status", "count"]
                        fig_bar_filter = px.bar(
                            status_counts,
                            x="status",
                            y="count",
                            title="Status Counts in Filtered Data",
                            color="status",
                            color_discrete_map={
                                "Present": "#28a745", 
                                "Late": "#ffc107", 
                                "Absent": "#dc3545", 
                                "Excused": "#6c757d"
                            }
                        )
                        st.plotly_chart(fig_bar_filter, use_container_width=True)
                    
                    elif chart_type == "Line - Attendance Over Time":
                        def status_to_numeric(s):
                            if s == "Present":
                                return 1
                            elif s == "Late":
                                return 0.5
                            else:
                                return 0
                        explorer_df["attendance_value"] = explorer_df["status"].apply(status_to_numeric)
                        daily_mean = explorer_df.groupby("date", as_index=False)["attendance_value"].mean().sort_values("date")
                        fig_line_filter = px.line(
                            daily_mean,
                            x="date",
                            y="attendance_value",
                            title="Average Attendance Over Time (Filtered Data)",
                            markers=True
                        )
                        fig_line_filter.update_layout(xaxis_title="Date", yaxis_title="Attendance Score")
                        st.plotly_chart(fig_line_filter, use_container_width=True)
                    
                    elif chart_type == "Bar - Student Attendance":
                        group_data = explorer_df.groupby(["name", "status"]).size().reset_index(name="count")
                        fig_bar_student = px.bar(
                            group_data,
                            x="name",
                            y="count",
                            color="status",
                            barmode="group",
                            title="Attendance by Student (Filtered Data)",
                            color_discrete_map={
                                "Present": "#28a745", 
                                "Late": "#ffc107", 
                                "Absent": "#dc3545", 
                                "Excused": "#6c757d"
                            }
                        )
                        fig_bar_student.update_layout(xaxis_title="Student Name", yaxis_title="Count")
                        st.plotly_chart(fig_bar_student, use_container_width=True)
                    
                    elif chart_type == "Pie - Status Distribution":
                        status_counts = explorer_df["status"].value_counts().reset_index()
                        status_counts.columns = ["status", "count"]
                        fig_pie_filter = px.pie(
                            status_counts,
                            values="count",
                            names="status",
                            title="Status Distribution (Filtered Data)",
                            hole=0.4,
                            color="status",
                            color_discrete_map={
                                "Present": "#28a745", 
                                "Late": "#ffc107", 
                                "Absent": "#dc3545", 
                                "Excused": "#6c757d"
                            }
                        )
                        st.plotly_chart(fig_pie_filter, use_container_width=True)
    
    with tab3:
        # -------------------------------------------------------------------------
        # C) Program-Specific XLSX (with advanced insights)
        # -------------------------------------------------------------------------
        st.subheader("📑 Program Attendance Report Generator")
        st.write("Create detailed attendance reports with insights and export to Excel.")
        
        # Instructions expander
        with st.expander("How to Create Reports", expanded=False):
            st.write("""
            1. Select a program from the dropdown
            2. Click "Create Pivot + Insights" to generate the report
            3. Review the report summary and pivot table
            4. Click "Create Downloadable XLSX" to download the Excel file
            5. Optionally, use the AI Impact Analysis to generate a comprehensive report
            """)
        
        # Program selection card
        st.markdown("### 1️⃣ Select Program")
        
        # Let user pick a program from df
        selectable_pids = sorted(df["program_id"].unique())
        selected_pid = st.selectbox(
            "Select a Program to Export/Analyze",
            options=selectable_pids,
            format_func=lambda pid: prog_map.get(pid, f"Program ID={pid}"),
            help="Choose which program's attendance data to analyze"
        )
        
        # Initialize session state for pivot data
        if "pivot_df" not in st.session_state:
            st.session_state["pivot_df"] = None
        
        # Create a nice card-like container for the report generation button
        st.markdown("### 2️⃣ Generate Report")
        if st.button("🔄 Create Pivot + Insights", help="Click to generate the attendance report"):
            with st.spinner("Generating report..."):
                # Filter DF to chosen program
                sub_df = df[df["program_id"] == selected_pid].copy()
                if sub_df.empty:
                    st.warning("⚠️ No attendance data for that program!")
                    return
                
                program_name = prog_map.get(selected_pid, f"Program ID={selected_pid}")
                st.session_state["selected_program_name"] = program_name
                
                sub_df["date"] = pd.to_datetime(sub_df["date"], errors="coerce").dt.date
                pivot_df = sub_df.pivot(index="name", columns="date", values="status").fillna("Missed")
                
                # Count absences
                def count_absences(row):
                    return sum(x in ["Absent", "Missed"] for x in row)
                pivot_df["Total Absences"] = pivot_df.apply(count_absences, axis=1)
                
                date_columns = [col for col in pivot_df.columns if col != "Total Absences"]
                # Create new column order with "Total Absences" as the second column
                new_column_order = ["Total Absences"] + date_columns
                # Reindex the DataFrame with the new column order
                pivot_df = pivot_df[new_column_order]
                st.session_state["pivot_df"] = pivot_df
                
                # Success message after report generation
                st.success(f"✅ Report generated successfully for {program_name}")
        
        # Only show insights if pivot data exists
        if st.session_state["pivot_df"] is not None:
            st.markdown("### 3️⃣ Report Summary")
            
            # Get program name from session state
            program_name = st.session_state.get("selected_program_name", "Selected Program")
            
            pivot_df = st.session_state["pivot_df"]
            
            # ---- Additional Summaries/Insights ----
            total_students = len(pivot_df.index)
            average_absences = pivot_df["Total Absences"].mean()
            max_absences = pivot_df["Total Absences"].max()
            
            # Use columns for a nicer layout of metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Program", program_name)
            with col2:
                st.metric("Total Students", total_students)
            with col3:
                st.metric("Avg. Absences", f"{average_absences:.2f}")
            
            # "High-risk" threshold with a visual indicator
            absence_threshold = 3
            high_risk_count = len(pivot_df[pivot_df["Total Absences"] > absence_threshold])
            
            # Progress bar to visualize attendance health
            if high_risk_count > 0:
                risk_percent = (high_risk_count / total_students) * 100
                st.warning(f"⚠️ {high_risk_count} of {total_students} students ({risk_percent:.1f}%) have excessive absences")
                
                # Show detailed high risk information
                high_risk_students = pivot_df[pivot_df["Total Absences"] > absence_threshold].index.tolist()
                with st.expander(f"View {high_risk_count} Students with Excessive Absences", expanded=True):
                    for s in high_risk_students:
                        st.write(f"- **{s}**: {pivot_df.loc[s, 'Total Absences']} absences")
            else:
                st.success(f"✅ No students have more than {absence_threshold} absences. Great job!")
            
            st.markdown("### 4️⃣ Attendance Pivot Table")
            st.write("The table below shows attendance status for each student by date, with high absence counts highlighted in red.")
            
            # highlight rows above threshold
            pivot_styled = st.session_state["pivot_df"].style.apply(
                highlight_high_absences, axis=1
            )
            st.dataframe(pivot_styled, use_container_width=True)
            
            # Add a nice download button with icon
            excel_button_container = st.container()
            with excel_button_container:
                download_col1, download_col2 = st.columns([3, 1])
                with download_col1:
                    st.markdown("### 5️⃣ Export Report")
                    st.write("Download the complete report as an Excel file.")
                
                with download_col2:
                    if st.button("📥 Create XLSX", help="Generate an Excel file with the attendance data"):
                        with st.spinner("Creating Excel file..."):
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                                st.session_state["pivot_df"].to_excel(writer, sheet_name="Attendance Pivot")
                                
                                workbook = writer.book
                                worksheet = writer.sheets["Attendance Pivot"]
                                red_format = workbook.add_format({"font_color": "red"})
                                row_count, col_count = st.session_state["pivot_df"].shape
                                worksheet.conditional_format(
                                    1, 1, row_count, col_count,
                                    {
                                        "type": "text",
                                        "criteria": "containing",
                                        "value": "Missed",
                                        "format": red_format
                                    }
                                )
                                
                                # Add a summary sheet
                                summary_df = pd.DataFrame({
                                    "Metric": ["Program", "Total Students", "Average Absences", "Max Absences", "Students with Excessive Absences"],
                                    "Value": [
                                        program_name, 
                                        total_students, 
                                        f"{average_absences:.2f}", 
                                        max_absences,
                                        high_risk_count
                                    ]
                                })
                                summary_df.to_excel(writer, sheet_name="Summary", index=False)
                            
                            excel_data = output.getvalue()
                            
                            file_name = f"{program_name.replace(' ', '_').lower()}_attendance.xlsx"
                            st.download_button(
                                label="💾 Download Excel Report",
                                data=excel_data,
                                file_name=file_name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            st.success("✅ Excel file created successfully!")
            
            # -------------------------------------------------------------------------
            # D) NEW: AI-Enhanced Program Impact Analysis (Now within the Generate Reports tab)
            # -------------------------------------------------------------------------
            st.write("---")
            st.subheader("6️⃣ AI-Enhanced Program Impact Analysis")
            st.write("Generate a comprehensive impact report that incorporates your attendance data")

            # Get the prompts dictionary
            prompts_dict = get_nonprofit_prompts()

            # Add option to choose between pre-defined or custom approach
            analysis_option = st.radio(
                "Choose analysis type:",
                ["Pre-defined Framework", "Custom Analysis Approach"],
                horizontal=True,
                help="Select a standard framework or define your own custom approach"
            )
            # AI-Enhanced Program Impact Analysis section with custom approach option
# Place this within the existing Generate Reports tab after the Excel export functionality

# -------------------------------------------------------------------------
# D) AI-Enhanced Program Impact Analysis with Custom Option (Two-Column Layout)
# -------------------------------------------------------------------------
        st.write("---")
        st.subheader("6️⃣ AI-Enhanced Program Impact Analysis")
        st.write("Generate a comprehensive impact report that incorporates your attendance data")

        # Get the prompts dictionary
        prompts_dict = get_nonprofit_prompts()

        # Add option to choose between pre-defined or custom approach
        analysis_option = st.radio(
            "Choose analysis type:",
            ["Pre-defined Framework", "Custom Analysis Approach"],
            horizontal=True,
            key="impact_analysis_type",  # Added unique key parameter

            help="Select a standard framework or define your own custom approach"
        )

        # Create two columns for better layout
        col1, col2 = st.columns([3, 1])

        with col1:
            if analysis_option == "Pre-defined Framework":
                # Standard framework selection
                st.markdown("### Select Impact Framework:")
                selected_approach = st.selectbox(
                    "Choose analysis approach:",
                    options=list(prompts_dict.keys()),
                    help="Each framework focuses on different aspects of impact measurement"
                )
                
                # Display the explanation for the selected approach
                st.info(prompts_dict[selected_approach]["description"])
                
                # Get the framework name without emoji for reporting
                framework_name = selected_approach.split(" ", 1)[1] if " " in selected_approach else selected_approach
                
                # Create the appropriate context automatically based on selected framework
                template_objective = prompts_dict[selected_approach]["sample_objective"]
                custom_context = None  # No custom context when using pre-defined frameworks
                
            else:  # Custom Analysis Approach
                st.markdown("### Define Your Custom Analysis Approach")
                
                # Provide explanation and placeholder for custom approach
                custom_context = st.text_area(
                    "Describe your analysis framework:",
                    value="""Define how you want your program to be evaluated. For example:
                    "This analysis should focus on measuring how our program impacts student academic performance, 
                    social-emotional development, and long-term educational outcomes. The analysis should identify 
                    key metrics for tracking improvement, evaluate our current progress, and suggest strategic 
                    enhancements to maximize impact."
                    """,
                    height=150,
                    max_chars=1000,
                    help="Outline the focus areas, key metrics, and specific aspects you want analyzed"
                )
                
                # Set placeholder values for the reporting
                selected_approach = "Custom Analysis Approach"
                framework_name = "Custom Analysis"

        with col2:
            st.markdown("### Framework Focus:")
            
            # Display focus areas based on the selected approach or custom
            if analysis_option == "Pre-defined Framework":
                # Different focus areas for each pre-defined framework
                if "Community Impact" in selected_approach:
                    st.markdown("#### 🌱 Focus Areas:")
                    st.markdown("• Community outcomes\n• Program effectiveness\n• Stakeholder impact")
                elif "Efficiency" in selected_approach:
                    st.markdown("#### 📊 Focus Areas:")
                    st.markdown("• Resource optimization\n• Cost-benefit analysis\n• Operational improvements")
                elif "Stakeholder" in selected_approach:
                    st.markdown("#### 📈 Focus Areas:")
                    st.markdown("• Engagement metrics\n• Feedback analysis\n• Relationship strength")
                elif "Lifecycle" in selected_approach:
                    st.markdown("#### 🔄 Focus Areas:")
                    st.markdown("• Progress tracking\n• Milestone achievement\n• Outcome measurement")
                elif "Risk" in selected_approach:
                    st.markdown("#### 🚦 Focus Areas:")
                    st.markdown("• Vulnerability assessment\n• Mitigation strategies\n• Contingency planning")
                elif "Advocacy" in selected_approach:
                    st.markdown("#### 📣 Focus Areas:")
                    st.markdown("• Message effectiveness\n• Outreach impact\n• Policy influence")
            else:
                # For custom analysis, show generic focus areas as a guide
                st.markdown("#### 🔍 Custom Analysis Areas")
                st.markdown("Consider including:")
                st.markdown("• Program-specific metrics\n• Key outcomes to measure\n• Success indicators\n• Impact evaluation methods")
                st.markdown("")
                st.markdown("Your custom approach will analyze attendance data through the lens of your defined framework.")

        # Generate report button with more prominent styling
        if st.button("🧠 Generate AI-Enhanced Impact Report", 
                    use_container_width=True,
                    help="Create a comprehensive analysis using attendance data and the selected framework"):
            
            # Check that we have pivot data to work with
            if "pivot_df" not in st.session_state or st.session_state["pivot_df"] is None:
                st.warning("⚠️ Please generate the attendance pivot table first by selecting a program above.")
            else:
                program_name = st.session_state.get("selected_program_name", "Selected Program")
                
                # Determine which context to use
                if analysis_option == "Pre-defined Framework":
                    # Get the template objective for this approach and customize it with the program name
                    template_objective = prompts_dict[selected_approach]["sample_objective"]
                    customized_objective = template_objective.replace("Our program", f"Our {program_name} program")
                else:
                    # Use the custom context provided by the user
                    customized_objective = custom_context.replace("our program", f"our {program_name} program")
                
                with st.spinner(f"Generating your {framework_name} analysis..."):
                    report_content = generate_ai_enhanced_report(
                        st.session_state["pivot_df"],
                        program_name,
                        customized_objective,
                        selected_approach
                    )
                    
                    if report_content:
                        st.success(f"✅ Impact analysis report generated successfully!")
                        
                        # Create a container for the report with better styling
                        with st.expander("📋 View AI-Enhanced Impact Report", expanded=True):
                            st.markdown(f"""
                            <div style="padding: 20px; border-radius: 5px; border-left: 5px solid #4682B4; background-color: #f8f9fa;">
                                <h2 style="color: #2c5282;">{program_name}: Program Impact Analysis</h2>
                                <p><strong>Analysis Framework:</strong> {framework_name}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown("---")
                            st.markdown(report_content)
                        
                        # Create download options in a nicer layout
                        col_download1, col_download2 = st.columns(2)
                        
                        with col_download1:
                            # Plain text download
                            st.download_button(
                                label="📄 Download Report as Text",
                                data=report_content,
                                file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.txt",
                                mime="text/plain"
                            )
                        
                        with col_download2:
                            # Formatted report content for Word/PDF
                            formatted_report = f"""# {program_name}: Program Impact Analysis
                            
                            Analysis Framework: {framework_name}

                            {report_content}

                            ---
                            Generated by Club Stride | Date: {datetime.now().strftime('%Y-%m-%d')}
                            """
                            # Word-compatible download
                            st.download_button(
                                label="📝 Download as Document",
                                data=formatted_report,
                                file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
            # if analysis_option == "Pre-defined Framework":
            #     # Standard framework selection
            #     st.markdown("### Select Impact Framework:")
            #     selected_approach = st.selectbox(
            #         "Choose analysis approach:",
            #         options=list(prompts_dict.keys()),
            #         help="Each framework focuses on different aspects of impact measurement"
            #     )
                
            #     # Display the explanation for the selected approach
            #     st.info(prompts_dict[selected_approach]["description"])
                
            #     # Add a visual icon based on the framework
            #     framework_name = selected_approach.split(" ", 1)[1] if " " in selected_approach else selected_approach
                
            #     # Create the appropriate context automatically based on selected framework
            #     template_objective = prompts_dict[selected_approach]["sample_objective"]
            #     custom_context = None  # No custom context when using pre-defined frameworks
                
            # else:  # Custom Analysis Approach
            #     st.markdown("### Define Your Custom Analysis Approach")
                
            #     # Provide explanation and placeholder for custom approach
            #     custom_context = st.text_area(
            #         "Describe your analysis framework:",
            #         value="""Define how you want your program to be evaluated. For example:
            #         "This analysis should focus on measuring how our program impacts student academic performance, 
            #         social-emotional development, and long-term educational outcomes. The analysis should identify 
            #         key metrics for tracking improvement, evaluate our current progress, and suggest strategic 
            #         enhancements to maximize impact."
            #         """,
            #         height=150,
            #         max_chars=1000,
            #         help="Outline the focus areas, key metrics, and specific aspects you want analyzed"
            #     )
                
            #     # Set placeholder values for the reporting
            #     selected_approach = "Custom Analysis Approach"
            #     framework_name = "Custom Analysis"

            # # Generate report button with more prominent styling
            # if st.button("🧠 Generate AI-Enhanced Impact Report", 
            #             use_container_width=True,
            #             help="Create a comprehensive analysis using attendance data and the selected framework"):
                
            #     # Check that we have pivot data to work with
            #     if "pivot_df" not in st.session_state or st.session_state["pivot_df"] is None:
            #         st.warning("⚠️ Please generate the attendance pivot table first by selecting a program above.")
            #     else:
            #         program_name = st.session_state.get("selected_program_name", "Selected Program")
                    
            #         # Determine which context to use
            #         if analysis_option == "Pre-defined Framework":
            #             # Get the template objective for this approach and customize it with the program name
            #             template_objective = prompts_dict[selected_approach]["sample_objective"]
            #             customized_objective = template_objective.replace("Our program", f"Our {program_name} program")
            #         else:
            #             # Use the custom context provided by the user
            #             customized_objective = custom_context.replace("our program", f"our {program_name} program")
                    
            #         with st.spinner(f"Generating your {framework_name} analysis..."):
            #             report_content = generate_ai_enhanced_report(
            #                 st.session_state["pivot_df"],
            #                 program_name,
            #                 customized_objective,
            #                 selected_approach
            #             )
                        
            #             if report_content:
            #                 st.success(f"✅ Impact analysis report generated successfully!")
                            
            #                 # Create a container for the report with better styling
            #                 with st.expander("📋 View AI-Enhanced Impact Report", expanded=True):
            #                     st.markdown(f"""
            #                     <div style="padding: 20px; border-radius: 5px; border-left: 5px solid #4682B4; background-color: #f8f9fa;">
            #                         <h2 style="color: #2c5282;">{program_name}: Program Impact Analysis</h2>
            #                         <p><strong>Analysis Framework:</strong> {framework_name}</p>
            #                     </div>
            #                     """, unsafe_allow_html=True)
            #                     st.markdown("---")
            #                     st.markdown(report_content)
                            
            #                 # Create download options in a nicer layout
            #                 col_download1, col_download2 = st.columns(2)
                            
            #                 with col_download1:
            #                     # Plain text download
            #                     st.download_button(
            #                         label="📄 Download Report as Text",
            #                         data=report_content,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.txt",
            #                         mime="text/plain"
            #                     )
                            
            #                 with col_download2:
            #                     # Formatted report content for Word/PDF
            #                     formatted_report = f"""# {program_name}: Program Impact Analysis
                                
            #                     Analysis Framework: {framework_name}

            #                     {report_content}

            #                     ---
            #                     Generated by Club Stride | Date: {datetime.now().strftime('%Y-%m-%d')}
            #                     """
            #                     # Word-compatible download
            #                     st.download_button(
            #                         label="📝 Download as Document",
            #                         data=formatted_report,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.docx",
            #                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            #                     )


# AI-enhanced report generator function
# def generate_ai_enhanced_report(pivot_df, program_name, project_description, analysis_method):
#     """
#     Generate a professional impact assessment report for nonprofit projects,
#     enhanced with actual attendance data analysis.
    
#     Args:
#         pivot_df: DataFrame containing the attendance pivot data
#         program_name: Name of the program being analyzed
#         project_description: Text describing the project objectives and impact
#         analysis_method: The selected analysis method/framework
        
#     Returns:
#         Generated impact assessment report text with data-driven insights
#     """
#     try:
#         # Initialize OpenAI client
#         openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
#         if not openai_api_key:
#             st.error("OpenAI API Key not found in secrets. Please configure it in Streamlit secrets.")
#             return None
            
#         client = OpenAI(api_key=openai_api_key)
        
#         # Extract key metrics from the pivot_df to include in the report
#         if pivot_df is not None:
#             # Calculate overall attendance metrics
#             total_students = len(pivot_df.index)
#             avg_absences = pivot_df["Total Absences"].mean() if "Total Absences" in pivot_df.columns else 0
#             max_absences = pivot_df["Total Absences"].max() if "Total Absences" in pivot_df.columns else 0
            
#             # Identify students with high absence counts
#             absence_threshold = 3
#             high_risk_count = len(pivot_df[pivot_df["Total Absences"] > absence_threshold]) if "Total Absences" in pivot_df.columns else 0
#             high_risk_percentage = (high_risk_count / total_students * 100) if total_students > 0 else 0
            
#             # Get most common status values for better insights
#             status_counts = {}
#             for col in pivot_df.columns:
#                 if col != "Total Absences":
#                     for status in pivot_df[col].value_counts().items():
#                         status_value, count = status
#                         if status_value not in status_counts:
#                             status_counts[status_value] = 0
#                         status_counts[status_value] += count
            
#             status_summary = ", ".join([f"{status}: {count}" for status, count in status_counts.items()])
            
#             # Create a data summary for the AI
#             data_summary = f"""
#             Program: {program_name}
#             Total Students: {total_students}
#             Average Absences Per Student: {avg_absences:.2f}
#             Maximum Absences for Any Student: {max_absences}
#             Students with Excessive Absences (>{absence_threshold}): {high_risk_count} ({high_risk_percentage:.1f}%)
#             Status Distribution: {status_summary}
#             """
#         else:
#             data_summary = "No attendance data available for analysis."
        
#         # Get the method name without the emoji
#         method_name = analysis_method.split(" ", 1)[1] if " " in analysis_method else analysis_method
        
#         # Create system prompt based on analysis method and attendance data
#         system_prompt = f"""You are a professional AI analyst specializing in nonprofit impact measurement, project management, and report generation for Club Stride. Given the program description, chosen analysis method of {method_name}, and ACTUAL ATTENDANCE DATA provided, generate a comprehensive, professional assessment addressing the following:

#         1. Context & Program Definition: Briefly restate the program's primary objectives, target communities, and main challenges as described.
        
#         2. Attendance Data Analysis: 
#            - Provide an interpretation of the provided attendance metrics
#            - Identify patterns and potential concerns
#            - Connect attendance patterns to program effectiveness
        
#         3. {method_name} Analysis: 
#            - Provide an insightful analysis based on the selected approach
#            - Highlight key metrics, methodologies, and strategic insights
#            - Incorporate the real attendance data to support your analysis
        
#         4. Recommendations & Next Steps: 
#            - Outline clear, actionable recommendations to improve attendance
#            - Suggest specific approaches to better track and measure impact
#            - Propose steps that Club Stride can take immediately and long-term to achieve their desired impact
        
#         Ensure clarity, professionalism, and actionable depth to support decision-making and future reporting.
#         Make specific references to the attendance data provided when formulating your analysis and recommendations."""
        
#         # Generate the report using OpenAI
#         response = client.chat.completions.create(
#             model="gpt-4-turbo-preview",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": f"""
#                 Program Description:
#                 {project_description}
                
#                 Attendance Data Analysis:
#                 {data_summary}
                
#                 Selected Analysis Method: {method_name}
#                 """}
#             ],
#             max_tokens=1500,
#             temperature=0.7
#         )
        
#         # Extract and return the generated report
#         if response.choices and len(response.choices) > 0:
#             return response.choices[0].message.content
#         else:
#             st.error("Failed to generate report: No content returned from API")
#             return None
            
#     except Exception as e:
#         st.error(f"Error generating impact report: {str(e)}")
#         return None

# def page_generate_reports():
#     # -------------------------------------------------------------------------
#     # Page Header with Description
#     # -------------------------------------------------------------------------
#     st.header("📊 Attendance Reports & Analytics")
#     st.write("Generate insights, visualizations, and downloadable reports from attendance data.")
    
#     # Progress indicator for initial data loading
#     with st.spinner("Loading attendance data..."):
#         # 1) Admin or Instructor check
#         is_admin = st.session_state.get("is_admin", False)
#         user_type = "Admin" if is_admin else "Instructor"
        
#         # 2) Build program map from Postgres
#         all_programs = list_programs()  # e.g. [{"program_id":1,"program_name":"STEM"}, ...]
#         prog_map = {p["program_id"]: p["program_name"] for p in all_programs}
        
#         # 3) Determine permitted program IDs
#         if is_admin:
#             program_id_options = [p["program_id"] for p in all_programs]  # admin sees all
#         else:
#             program_id_options = st.session_state.get("instructor_program_ids", [])
#             if not program_id_options:
#                 st.warning("⚠️ You have no assigned programs. Contact an admin for access.")
#                 return
        
#         # 4) Fetch attendance records from Mongo
#         records = fetch_all_attendance_records()
#         if not records:
#             st.info("ℹ️ No attendance data found.")
#             return
        
#         # 5) Filter by permitted program IDs
#         filtered_records = [r for r in records if r.get("program_id") in program_id_options]
#         if not filtered_records:
#             st.info("ℹ️ No attendance data found for your assigned programs.")
#             return
        
#         # 6) Flatten records
#         flattened = []
#         for r in filtered_records:
#             att = r["attendance"]
#             pid = r.get("program_id", 0)
#             flattened.append({
#                 "student_id": r.get("student_id"),
#                 "name": r.get("name"),
#                 "program_id": pid,
#                 "program_name": prog_map.get(pid, f"Program ID={pid}"),
#                 "date": att.get("date"),
#                 "status": att.get("status"),
#                 "comment": att.get("comment", "")
#             })
        
#         if not flattened:
#             st.info("ℹ️ No valid attendance data to display.")
#             return
        
#         df = pd.DataFrame(flattened)
#         if df.empty:
#             st.info("ℹ️ No valid attendance data to display.")
#             return

#     # Display data summary
#     st.success(f"✅ Loaded attendance data for {len(df['name'].unique())} students across {len(df['program_id'].unique())} programs.")
    
#     # Create tabs for better organization - REMOVED THE 4th TAB
#     tab1, tab2, tab3 = st.tabs(["📈 Visualizations", "🔍 Data Explorer", "📑 Generate Reports"])
    
#     with tab1:
#         # [TAB 1 CONTENT UNCHANGED]
#         # -------------------------------------------------------------------------
#         # A) Admin-Only Visualizations (Overview)
#         # -------------------------------------------------------------------------
#         if is_admin:
#             st.subheader("📊 Admin Overview Dashboard")
#             st.write("These visualizations provide a high-level overview of attendance across all programs.")
            
#             with st.expander("Admin Visualizations of Full Attendance Data", expanded=True):
#                 def status_to_numeric(s):
#                     if s == "Present":
#                         return 1
#                     elif s == "Late":
#                         return 0.5
#                     else:
#                         return 0
                
#                 df["attendance_value"] = df["status"].apply(status_to_numeric)
                
#                 # Add a metric summary at the top
#                 col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
#                 with col_metrics1:
#                     avg_attendance = df["attendance_value"].mean() * 100
#                     st.metric("Overall Attendance Rate", f"{avg_attendance:.1f}%")
                
#                 with col_metrics2:
#                     present_rate = (df["status"] == "Present").mean() * 100
#                     st.metric("Present Rate", f"{present_rate:.1f}%")
                
#                 with col_metrics3:
#                     absent_rate = (df["status"] == "Absent").mean() * 100
#                     st.metric("Absence Rate", f"{absent_rate:.1f}%")
                
#                 # Ranking by average attendance
#                 ranking_df = df.groupby("program_name", as_index=False)["attendance_value"].mean()
#                 ranking_df.rename(columns={"attendance_value": "avg_attendance_score"}, inplace=True)
#                 ranking_df.sort_values("avg_attendance_score", ascending=False, inplace=True)
                
#                 st.subheader("Program Ranking by Average Attendance")
#                 st.dataframe(ranking_df.style.highlight_max(subset=["avg_attendance_score"]), use_container_width=True)
                
#                 # Bar chart: average attendance score
#                 fig_bar = px.bar(
#                     ranking_df,
#                     x="program_name",
#                     y="avg_attendance_score",
#                     title="Average Attendance Score by Program",
#                     color="avg_attendance_score",
#                     color_continuous_scale="blues"
#                 )
#                 fig_bar.update_layout(xaxis_title="Program", yaxis_title="Average Attendance Score")
                
#                 # Pie chart: overall status distribution
#                 status_counts = df["status"].value_counts().reset_index()
#                 status_counts.columns = ["status", "count"]
#                 fig_pie = px.pie(
#                     status_counts,
#                     values="count",
#                     names="status",
#                     title="Distribution of Attendance Statuses",
#                     hole=0.4,
#                     color="status",
#                     color_discrete_map={
#                         "Present": "#28a745", 
#                         "Late": "#ffc107", 
#                         "Absent": "#dc3545", 
#                         "Excused": "#6c757d"
#                     }
#                 )
                
#                 # Time-series
#                 df["date"] = pd.to_datetime(df["date"], errors="coerce")
#                 daily_df = df.groupby("date", as_index=False)["attendance_value"].mean()
#                 fig_line = px.line(
#                     daily_df,
#                     x="date",
#                     y="attendance_value",
#                     title="Average Attendance Over Time (All Programs)",
#                     markers=True
#                 )
#                 fig_line.update_layout(xaxis_title="Date", yaxis_title="Attendance Score")
                
#                 # Multi-line by program
#                 multi_df = df.groupby(["date", "program_name"], as_index=False)["attendance_value"].mean()
#                 fig_multi = px.line(
#                     multi_df,
#                     x="date",
#                     y="attendance_value",
#                     color="program_name",
#                     title="Attendance Over Time by Program",
#                     markers=True
#                 )
#                 fig_multi.update_layout(xaxis_title="Date", yaxis_title="Attendance Score", legend_title="Program")
                
#                 colA, colB = st.columns(2)
#                 with colA:
#                     st.plotly_chart(fig_bar, use_container_width=True)
                
#                 with colB:
#                     st.plotly_chart(fig_pie, use_container_width=True)
                
#                 st.write("---")
                
#                 st.plotly_chart(fig_line, use_container_width=True)
#                 st.plotly_chart(fig_multi, use_container_width=True)
                
#                 # Download buttons for visualizations
#                 st.download_button(
#                     label="📥 Download Attendance Summary CSV",
#                     data=ranking_df.to_csv(index=False).encode('utf-8'),
#                     file_name="attendance_summary.csv",
#                     mime="text/csv"
#                 )
#         else:
#             # For instructors, show a simpler view
#             st.subheader("📊 Attendance Overview")
#             # Get instructor's programs
#             instructor_programs = [prog_map.get(pid, f"Program {pid}") for pid in program_id_options]
#             st.write(f"You have access to the following programs: {', '.join(instructor_programs)}")
            
#             # Simple metrics for instructor
#             instructor_df = df.copy()
            
#             def status_to_numeric(s):
#                 if s == "Present":
#                     return 1
#                 elif s == "Late":
#                     return 0.5
#                 else:
#                     return 0
            
#             instructor_df["attendance_value"] = instructor_df["status"].apply(status_to_numeric)
            
#             # Add metrics
#             col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
#             with col_metrics1:
#                 avg_attendance = instructor_df["attendance_value"].mean() * 100
#                 st.metric("Overall Attendance Rate", f"{avg_attendance:.1f}%")
            
#             with col_metrics2:
#                 present_rate = (instructor_df["status"] == "Present").mean() * 100
#                 st.metric("Present Rate", f"{present_rate:.1f}%")
            
#             with col_metrics3:
#                 absent_rate = (instructor_df["status"] == "Absent").mean() * 100
#                 st.metric("Absence Rate", f"{absent_rate:.1f}%")
            
#             # Simple charts for instructor
#             status_counts = instructor_df["status"].value_counts().reset_index()
#             status_counts.columns = ["status", "count"]
#             fig_pie = px.pie(
#                 status_counts,
#                 values="count",
#                 names="status",
#                 title="Distribution of Attendance Statuses",
#                 hole=0.4,
#                 color="status",
#                 color_discrete_map={
#                     "Present": "#28a745", 
#                     "Late": "#ffc107", 
#                     "Absent": "#dc3545", 
#                     "Excused": "#6c757d"
#                 }
#             )
#             st.plotly_chart(fig_pie, use_container_width=True)
    
#     with tab2:
#         # [TAB 2 CONTENT UNCHANGED]
#         # -------------------------------------------------------------------------
#         # B) Data Explorer + Chart Building from Filtered Data
#         # -------------------------------------------------------------------------
#         st.subheader("🔍 Data Explorer & Custom Charts")
#         st.write("Filter and visualize attendance data using various criteria.")
        
#         with st.expander("How to use the Data Explorer", expanded=False):
#             st.write("""
#             1. Use the filter controls below to select specific data
#             2. The table will update to show only matching records
#             3. Choose a chart type to visualize the filtered data
#             4. The chart will update automatically based on your selection
#             """)
        
#         explorer_output = dataframe_explorer(df, case=False)
#         explorer_df = pd.DataFrame(explorer_output)
        
#         if explorer_df.empty:
#             st.info("ℹ️ No data matches your filter criteria. Try adjusting the filters.")
#         else:
#             st.write(f"**Showing {len(explorer_df)} records that match your criteria**")
#             st.dataframe(explorer_df, use_container_width=True)
            
#             # Add download button for filtered data
#             st.download_button(
#                 label="📥 Download Filtered Data CSV",
#                 data=explorer_df.to_csv(index=False).encode('utf-8'),
#                 file_name="filtered_attendance_data.csv",
#                 mime="text/csv"
#             )
            
#             st.markdown("### 📈 Build a Custom Chart")
#             st.write("Create visualizations from your filtered data")
            
#             chart_type = st.selectbox(
#                 "Select Chart Type",
#                 [
#                     "Bar - Status Counts",
#                     "Line - Attendance Over Time",
#                     "Bar - Student Attendance",
#                     "Pie - Status Distribution",
#                 ],
#                 help="Choose the type of chart you want to create from your filtered data"
#             )
            
#             # Convert 'date' to datetime if needed
#             explorer_df["date"] = pd.to_datetime(explorer_df["date"], errors="coerce")
            
#             # Chart container with loading indicator
#             chart_container = st.container()
#             with chart_container:
#                 with st.spinner("Generating chart..."):
#                     if chart_type == "Bar - Status Counts":
#                         status_counts = explorer_df["status"].value_counts().reset_index()
#                         status_counts.columns = ["status", "count"]
#                         fig_bar_filter = px.bar(
#                             status_counts,
#                             x="status",
#                             y="count",
#                             title="Status Counts in Filtered Data",
#                             color="status",
#                             color_discrete_map={
#                                 "Present": "#28a745", 
#                                 "Late": "#ffc107", 
#                                 "Absent": "#dc3545", 
#                                 "Excused": "#6c757d"
#                             }
#                         )
#                         st.plotly_chart(fig_bar_filter, use_container_width=True)
                    
#                     elif chart_type == "Line - Attendance Over Time":
#                         def status_to_numeric(s):
#                             if s == "Present":
#                                 return 1
#                             elif s == "Late":
#                                 return 0.5
#                             else:
#                                 return 0
#                         explorer_df["attendance_value"] = explorer_df["status"].apply(status_to_numeric)
#                         daily_mean = explorer_df.groupby("date", as_index=False)["attendance_value"].mean().sort_values("date")
#                         fig_line_filter = px.line(
#                             daily_mean,
#                             x="date",
#                             y="attendance_value",
#                             title="Average Attendance Over Time (Filtered Data)",
#                             markers=True
#                         )
#                         fig_line_filter.update_layout(xaxis_title="Date", yaxis_title="Attendance Score")
#                         st.plotly_chart(fig_line_filter, use_container_width=True)
                    
#                     elif chart_type == "Bar - Student Attendance":
#                         group_data = explorer_df.groupby(["name", "status"]).size().reset_index(name="count")
#                         fig_bar_student = px.bar(
#                             group_data,
#                             x="name",
#                             y="count",
#                             color="status",
#                             barmode="group",
#                             title="Attendance by Student (Filtered Data)",
#                             color_discrete_map={
#                                 "Present": "#28a745", 
#                                 "Late": "#ffc107", 
#                                 "Absent": "#dc3545", 
#                                 "Excused": "#6c757d"
#                             }
#                         )
#                         fig_bar_student.update_layout(xaxis_title="Student Name", yaxis_title="Count")
#                         st.plotly_chart(fig_bar_student, use_container_width=True)
                    
#                     elif chart_type == "Pie - Status Distribution":
#                         status_counts = explorer_df["status"].value_counts().reset_index()
#                         status_counts.columns = ["status", "count"]
#                         fig_pie_filter = px.pie(
#                             status_counts,
#                             values="count",
#                             names="status",
#                             title="Status Distribution (Filtered Data)",
#                             hole=0.4,
#                             color="status",
#                             color_discrete_map={
#                                 "Present": "#28a745", 
#                                 "Late": "#ffc107", 
#                                 "Absent": "#dc3545", 
#                                 "Excused": "#6c757d"
#                             }
#                         )
#                         st.plotly_chart(fig_pie_filter, use_container_width=True)
    
#     with tab3:
#         # -------------------------------------------------------------------------
#         # C) Program-Specific XLSX (with advanced insights)
#         # -------------------------------------------------------------------------
#         st.subheader("📑 Attendance Report Generator")
#         st.write("Create detailed attendance reports with insights and export to Excel.")
        
#         # Instructions expander
#         with st.expander("How to Create Reports", expanded=False):
#             st.write("""
#             1. Select a program from the dropdown
#             2. Click "Create Pivot + Insights" to generate the report
#             3. Review the report summary and pivot table
#             4. Click "Create Downloadable XLSX" to download the Excel file
#             5. Optionally, use the AI Impact Analysis to generate a comprehensive report
#             """)
        
#         # Program selection card
#         st.markdown("### 1️⃣ Select Program")
        
#         # Let user pick a program from df
#         selectable_pids = sorted(df["program_id"].unique())
#         selected_pid = st.selectbox(
#             "Select a Program to Export/Analyze",
#             options=selectable_pids,
#             format_func=lambda pid: prog_map.get(pid, f"Program ID={pid}"),
#             help="Choose which program's attendance data to analyze"
#         )
        
#         # Initialize session state for pivot data
#         if "pivot_df" not in st.session_state:
#             st.session_state["pivot_df"] = None
        
#         # Create a nice card-like container for the report generation button
#         st.markdown("### 2️⃣ Generate Report")
        
#         if st.button("🔄 Create Pivot + Insights", help="Click to generate the attendance report"):
#             with st.spinner("Generating report..."):
#                 # Filter DF to chosen program
#                 sub_df = df[df["program_id"] == selected_pid].copy()
#                 if sub_df.empty:
#                     st.warning("⚠️ No attendance data for that program!")
#                     return
                
#                 program_name = prog_map.get(selected_pid, f"Program ID={selected_pid}")
#                 st.session_state["selected_program_name"] = program_name
                
#                 sub_df["date"] = pd.to_datetime(sub_df["date"], errors="coerce").dt.date
#                 pivot_df = sub_df.pivot(index="name", columns="date", values="status").fillna("Missed")
                
#                 # Count absences
#                 def count_absences(row):
#                     return sum(x in ["Absent", "Missed"] for x in row)
#                 pivot_df["Total Absences"] = pivot_df.apply(count_absences, axis=1)
                
#                 date_columns = [col for col in pivot_df.columns if col != "Total Absences"]
#                 # Create new column order with "Total Absences" as the second column
#                 new_column_order = ["Total Absences"] + date_columns
#                 # Reindex the DataFrame with the new column order
#                 pivot_df = pivot_df[new_column_order]
#                 st.session_state["pivot_df"] = pivot_df
                
#                 # Success message after report generation
#                 st.success(f"✅ Report generated successfully for {program_name}")
        
#         # Only show insights if pivot data exists
#         if st.session_state["pivot_df"] is not None:
#             st.markdown("### 3️⃣ Report Summary")
            
#             # Get program name from session state
#             program_name = st.session_state.get("selected_program_name", "Selected Program")
            
#             pivot_df = st.session_state["pivot_df"]
            
#             # ---- Additional Summaries/Insights ----
#             total_students = len(pivot_df.index)
#             average_absences = pivot_df["Total Absences"].mean()
#             max_absences = pivot_df["Total Absences"].max()
            
#             # Use columns for a nicer layout of metrics
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Program", program_name)
#             with col2:
#                 st.metric("Total Students", total_students)
#             with col3:
#                 st.metric("Avg. Absences", f"{average_absences:.2f}")
            
#             # "High-risk" threshold with a visual indicator
#             absence_threshold = 3
#             high_risk_count = len(pivot_df[pivot_df["Total Absences"] > absence_threshold])
            
#             # Progress bar to visualize attendance health
#             if high_risk_count > 0:
#                 risk_percent = (high_risk_count / total_students) * 100
#                 st.warning(f"⚠️ {high_risk_count} of {total_students} students ({risk_percent:.1f}%) have excessive absences")
                
#                 # Show detailed high risk information
#                 high_risk_students = pivot_df[pivot_df["Total Absences"] > absence_threshold].index.tolist()
#                 with st.expander(f"View {high_risk_count} Students with Excessive Absences", expanded=True):
#                     for s in high_risk_students:
#                         st.write(f"- **{s}**: {pivot_df.loc[s, 'Total Absences']} absences")
#             else:
#                 st.success(f"✅ No students have more than {absence_threshold} absences. Great job!")
            
#             st.markdown("### 4️⃣ Attendance Pivot Table")
#             st.write("The table below shows attendance status for each student by date, with high absence counts highlighted in red.")
            
#             # highlight rows above threshold
#             pivot_styled = st.session_state["pivot_df"].style.apply(
#                 highlight_high_absences, axis=1
#             )
#             st.dataframe(pivot_styled, use_container_width=True)
            
#             # Add a nice download button with icon
#             excel_button_container = st.container()
#             with excel_button_container:
#                 download_col1, download_col2 = st.columns([3, 1])
#                 with download_col1:
#                     st.markdown("### 5️⃣ Export Report")
#                     st.write("Download the complete report as an Excel file.")
                
#                 with download_col2:
#                     if st.button("📥 Create XLSX", help="Generate an Excel file with the attendance data"):
#                         with st.spinner("Creating Excel file..."):
#                             output = io.BytesIO()
#                             with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
#                                 st.session_state["pivot_df"].to_excel(writer, sheet_name="Attendance Pivot")
                                
#                                 workbook = writer.book
#                                 worksheet = writer.sheets["Attendance Pivot"]
#                                 red_format = workbook.add_format({"font_color": "red"})
#                                 row_count, col_count = st.session_state["pivot_df"].shape
#                                 worksheet.conditional_format(
#                                     1, 1, row_count, col_count,
#                                     {
#                                         "type": "text",
#                                         "criteria": "containing",
#                                         "value": "Missed",
#                                         "format": red_format
#                                     }
#                                 )
                                
#                                 # Add a summary sheet
#                                 summary_df = pd.DataFrame({
#                                     "Metric": ["Program", "Total Students", "Average Absences", "Max Absences", "Students with Excessive Absences"],
#                                     "Value": [
#                                         program_name, 
#                                         total_students, 
#                                         f"{average_absences:.2f}", 
#                                         max_absences,
#                                         high_risk_count
#                                     ]
#                                 })
#                                 summary_df.to_excel(writer, sheet_name="Summary", index=False)
                            
#                             excel_data = output.getvalue()
                            
#                             file_name = f"{program_name.replace(' ', '_').lower()}_attendance.xlsx"
#                             st.download_button(
#                                 label="💾 Download Excel Report",
#                                 data=excel_data,
#                                 file_name=file_name,
#                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                             )
                            
#                             st.success("✅ Excel file created successfully!")
            
#             # -------------------------------------------------------------------------
#             # D) NEW: AI-Enhanced Program Impact Analysis (Now within the Generate Reports tab)
#             # -------------------------------------------------------------------------
#             st.write("---")
#             st.subheader("6️⃣ AI-Enhanced Program Impact Analysis")
#             st.write("Generate a comprehensive impact report that incorporates your attendance data")

#             # Get the prompts dictionary
#             prompts_dict = get_nonprofit_prompts()

#             # Add option to choose between pre-defined or custom approach
#             analysis_option = st.radio(
#                 "Choose analysis type:",
#                 ["Pre-defined Framework", "Custom Analysis Approach"],
#                 horizontal=True,
#                 help="Select a standard framework or define your own custom approach"
#             )

#             if analysis_option == "Pre-defined Framework":
#                 # Standard framework selection
#                 st.markdown("### Select Impact Framework:")
#                 selected_approach = st.selectbox(
#                     "Choose analysis approach:",
#                     options=list(prompts_dict.keys()),
#                     help="Each framework focuses on different aspects of impact measurement"
#                 )
                
#                 # Display the explanation for the selected approach
#                 st.info(prompts_dict[selected_approach]["description"])
                
#                 # Add a visual icon based on the framework
#                 framework_name = selected_approach.split(" ", 1)[1] if " " in selected_approach else selected_approach
                
#                 # Create the appropriate context automatically based on selected framework
#                 template_objective = prompts_dict[selected_approach]["sample_objective"]
#                 custom_context = None  # No custom context when using pre-defined frameworks
                
#             else:  # Custom Analysis Approach
#                 st.markdown("### Define Your Custom Analysis Approach")
                
#                 # Provide explanation and placeholder for custom approach
#                 custom_context = st.text_area(
#                     "Describe your analysis framework:",
#                     value="""Define how you want your program to be evaluated. For example:
#                     "This analysis should focus on measuring how our program impacts student academic performance, 
#                     social-emotional development, and long-term educational outcomes. The analysis should identify 
#                     key metrics for tracking improvement, evaluate our current progress, and suggest strategic 
#                     enhancements to maximize impact."
#                     """,
#                     height=150,
#                     max_chars=1000,
#                     help="Outline the focus areas, key metrics, and specific aspects you want analyzed"
#                 )
                
#                 # Set placeholder values for the reporting
#                 selected_approach = "Custom Analysis Approach"
#                 framework_name = "Custom Analysis"

#             # Generate report button with more prominent styling
#             if st.button("🧠 Generate AI-Enhanced Impact Report", 
#                         use_container_width=True,
#                         help="Create a comprehensive analysis using attendance data and the selected framework"):
                
#                 # Check that we have pivot data to work with
#                 if "pivot_df" not in st.session_state or st.session_state["pivot_df"] is None:
#                     st.warning("⚠️ Please generate the attendance pivot table first by selecting a program above.")
#                 else:
#                     program_name = st.session_state.get("selected_program_name", "Selected Program")
                    
#                     # Determine which context to use
#                     if analysis_option == "Pre-defined Framework":
#                         # Get the template objective for this approach and customize it with the program name
#                         template_objective = prompts_dict[selected_approach]["sample_objective"]
#                         customized_objective = template_objective.replace("Our program", f"Our {program_name} program")
#                     else:
#                         # Use the custom context provided by the user
#                         customized_objective = custom_context.replace("our program", f"our {program_name} program")
                    
#                     with st.spinner(f"Generating your {framework_name} analysis..."):
#                         report_content = generate_ai_enhanced_report(
#                             st.session_state["pivot_df"],
#                             program_name,
#                             customized_objective,
#                             selected_approach
#                         )
                        
#                         if report_content:
#                             st.success(f"✅ Impact analysis report generated successfully!")
                            
#                             # Create a container for the report with better styling
#                             with st.expander("📋 View AI-Enhanced Impact Report", expanded=True):
#                                 st.markdown(f"""
#                                 <div style="padding: 20px; border-radius: 5px; border-left: 5px solid #4682B4; background-color: #f8f9fa;">
#                                     <h2 style="color: #2c5282;">{program_name}: Program Impact Analysis</h2>
#                                     <p><strong>Analysis Framework:</strong> {framework_name}</p>
#                                 </div>
#                                 """, unsafe_allow_html=True)
#                                 st.markdown("---")
#                                 st.markdown(report_content)
                            
#                             # Create download options in a nicer layout
#                             col_download1, col_download2 = st.columns(2)
                            
#                             with col_download1:
#                                 # Plain text download
#                                 st.download_button(
#                                     label="📄 Download Report as Text",
#                                     data=report_content,
#                                     file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.txt",
#                                     mime="text/plain"
#                                 )
                            
#                             with col_download2:
#                                 # Formatted report content for Word/PDF
#                                 formatted_report = f"""# {program_name}: Program Impact Analysis
                                
#                                 Analysis Framework: {framework_name}

#                                 {report_content}

#                                 ---
#                                 Generated by Club Stride | Date: {datetime.now().strftime('%Y-%m-%d')}
#                                 """
#                                 # Word-compatible download
#                                 st.download_button(
#                                     label="📝 Download as Document",
#                                     data=formatted_report,
#                                     file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.docx",
#                                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                                 )
            # st.write("---")
            # st.subheader("6️⃣ AI-Enhanced Program Impact Analysis")
            # st.write("Generate a comprehensive program impact report that incorporates your attendance data")
            
            # # Get the prompts dictionary
            # prompts_dict = get_nonprofit_prompts()

            # col1, col2 = st.columns([3, 1])

            # with col1:
            #     # Analysis method selection
            #     st.markdown("### Select Impact Framework:")
            #     selected_approach = st.selectbox(
            #         "Choose analysis approach:",
            #         options=list(prompts_dict.keys()),
            #         help="Each framework focuses on different aspects of impact measurement"
            #     )
                
            #     # Display the explanation for the selected approach
            #     st.info(prompts_dict[selected_approach]["description"])

            # with col2:
            #     st.markdown("### Framework Details:")
                
            #     # Get the actual framework name without emoji
            #     framework_name = selected_approach.split(" ", 1)[1] if " " in selected_approach else selected_approach
                
            #     # Add a visual icon based on the framework
            #     if "Community Impact" in selected_approach:
            #         st.markdown("#### 🌱 Focus Areas:")
            #         st.markdown("• Community outcomes\n• Program effectiveness\n• Stakeholder impact")
            #     elif "Efficiency" in selected_approach:
            #         st.markdown("#### 📊 Focus Areas:")
            #         st.markdown("• Resource optimization\n• Cost-benefit analysis\n• Operational improvements")
            #     elif "Stakeholder" in selected_approach:
            #         st.markdown("#### 📈 Focus Areas:")
            #         st.markdown("• Engagement metrics\n• Feedback analysis\n• Relationship strength")
            #     elif "Lifecycle" in selected_approach:
            #         st.markdown("#### 🔄 Focus Areas:")
            #         st.markdown("• Progress tracking\n• Milestone achievement\n• Outcome measurement")
            #     elif "Risk" in selected_approach:
            #         st.markdown("#### 🚦 Focus Areas:")
            #         st.markdown("• Vulnerability assessment\n• Mitigation strategies\n• Contingency planning")
            #     elif "Advocacy" in selected_approach:
            #         st.markdown("#### 📣 Focus Areas:")
            #         st.markdown("• Message effectiveness\n• Outreach impact\n• Policy influence")

            # # Generate report button with more prominent styling
            # if st.button("🧠 Generate AI-Enhanced Impact Report", 
            #             use_container_width=True,
            #             help="Create a comprehensive analysis using attendance data and the selected framework"):
                
            #     # Check that we have pivot data to work with
            #     if "pivot_df" not in st.session_state or st.session_state["pivot_df"] is None:
            #         st.warning("⚠️ Please generate the attendance pivot table first by selecting a program above.")
            #     else:
            #         program_name = st.session_state.get("selected_program_name", "Selected Program")
                    
            #         # Get the template objective for this approach and customize it with the program name
            #         template_objective = prompts_dict[selected_approach]["sample_objective"]
            #         customized_objective = template_objective.replace("Our program", f"Our {program_name} program")
                    
            #         with st.spinner(f"Generating your {framework_name} analysis..."):
            #             report_content = generate_ai_enhanced_report(
            #                 st.session_state["pivot_df"],
            #                 program_name,
            #                 customized_objective,
            #                 selected_approach
            #             )
                        
            #             if report_content:
            #                 st.success(f"✅ {framework_name} report generated successfully!")
                            
            #                 # Create a container for the report with better styling
            #                 with st.expander("📋 View AI-Enhanced Impact Report", expanded=True):
            #                     st.markdown(f"""
            #                     <div style="padding: 20px; border-radius: 5px; border-left: 5px solid #4682B4; background-color: #f8f9fa;">
            #                         <h2 style="color: #2c5282;">{program_name}: Program Impact Analysis</h2>
            #                         <p><strong>Analysis Framework:</strong> {framework_name}</p>
            #                     </div>
            #                     """, unsafe_allow_html=True)
            #                     st.markdown("---")
            #                     st.markdown(report_content)
                            
            #                 # Create download options in a nicer layout
            #                 col_download1, col_download2 = st.columns(2)
                            
            #                 with col_download1:
            #                     # Plain text download
            #                     st.download_button(
            #                         label="📄 Download Report as Text",
            #                         data=report_content,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_{framework_name.replace(' ', '_').lower()}_report.txt",
            #                         mime="text/plain"
            #                     )
                            
            #                 with col_download2:
            #                     # Formatted report content for Word/PDF
            #                     formatted_report = f"""# {program_name}: Program Impact Analysis
                                
            #                     Analysis Framework: {framework_name}

            #                     {report_content}

            #                     ---
            #                     Generated by Club Stride | Date: {datetime.now().strftime('%Y-%m-%d')}
            #                     """
            #                     # Word-compatible download
            #                     st.download_button(
            #                         label="📝 Download as Document",
            #                         data=formatted_report,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_{framework_name.replace(' ', '_').lower()}_report.docx",
            #                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            #                     )
            
            # Analysis method selection
            # st.markdown("### Select Impact Framework:")
            # selected_approach = st.selectbox(
            #     "Choose analysis approach:",
            #     options=list(prompts_dict.keys()),
            #     help="Each approach focuses on different aspects of impact measurement"
            # )
            
            # # Display the explanation for the selected approach
            # with st.expander("About this framework", expanded=True):
            #     st.info(prompts_dict[selected_approach]["description"])
            
            # # Create two columns for program description
            # col1, col2 = st.columns([1, 1])
            
            # with col1:
            #     use_template = st.checkbox("Use template description", value=True, 
            #                               help="Use a pre-written template as a starting point")
            
            # with col2:
            #     if use_template:
            #         st.success("Using template - you can edit it below")
            
            # # Create the input area for program description
            # if use_template:
            #     # Use the sample objective from the selected approach
            #     template_text = prompts_dict[selected_approach]["sample_objective"]
            #     # Replace generic program name with actual program name
            #     template_text = template_text.replace("Our program", f"Our {program_name} program")
            # else:
            #     # If not using template, provide a minimal starter
            #     template_text = f"Our {program_name} program aims to..."
            
            # # Set session state for project description
            # if 'nonprofit_project_description' not in st.session_state or st.session_state['nonprofit_project_description'] != template_text:
            #     st.session_state['nonprofit_project_description'] = template_text
            
            # project_description = st.text_area(
            #     "Program Description:",
            #     value=st.session_state['nonprofit_project_description'],
            #     height=120,
            #     max_chars=800,
            #     help="Describe your program's objectives, target participants, and desired outcomes"
            # )
            
            # # Generate report button
            # if st.button("🧠 Generate AI-Enhanced Impact Report", use_container_width=True):
            #     # Save the project description for future use
            #     st.session_state['nonprofit_project_description'] = project_description
                
            #     # Check that we have pivot data to work with (already confirmed earlier)
            #     if project_description.strip() == "":
            #         st.warning("Please provide a description of your program before generating a report.")
            #     else:
            #         program_name = st.session_state.get("selected_program_name", "Selected Program")
                    
            #         with st.spinner("Generating your AI-enhanced impact report..."):
            #             report_content = generate_ai_enhanced_report(
            #                 st.session_state["pivot_df"],
            #                 program_name,
            #                 project_description,
            #                 selected_approach
            #             )
                        
            #             if report_content:
            #                 st.success("✅ AI-enhanced impact report generated successfully!")
                            
            #                 # Create a container for the report
            #                 with st.expander("📋 View AI-Enhanced Impact Report", expanded=True):
            #                     st.markdown(f"## {program_name}: Program Impact Analysis")
            #                     st.markdown(f"**Analysis Framework:** {selected_approach}")
            #                     st.markdown("---")
            #                     st.markdown(report_content)
                            
            #                 # Create download options
            #                 col_download1, col_download2 = st.columns(2)
                            
            #                 with col_download1:
            #                     # Plain text download
            #                     st.download_button(
            #                         label="📄 Download Report as Text",
            #                         data=report_content,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.txt",
            #                         mime="text/plain"
            #                     )
                            
            #                 with col_download2:
            #                     # Formatted report content for Word/PDF
            #                     formatted_report = f"""# {program_name}: Program Impact Analysis
                                
            #                     Analysis Framework: {selected_approach}

            #                     {report_content}

            #                     ---
            #                     Generated by Club Stride | Date: {datetime.now().strftime('%Y-%m-%d')}
            #                     """
            #                     # Word-compatible download
            #                     st.download_button(
            #                         label="📝 Download as Document",
            #                         data=formatted_report,
            #                         file_name=f"{program_name.replace(' ', '_').lower()}_impact_report.docx",
            #                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            #                     )    

