
# main_app.py

import streamlit as st
from streamlit_option_menu import option_menu

# Page imports (same as before)
from pages import (
    page_manage_instructors,
    page_manage_students,
    page_take_attendance,
    page_review_attendance,
    page_generate_reports,
    page_instructor_login,
    page_instructor_change_password,
    page_manage_schedules
)

# Admin check
from students_db import check_admin
# Create instructors table
from instructors_db import create_instructors_table

def admin_login():

    st.subheader("Admin Login (MongoDB Connection)")

    if st.session_state.get("instructor_logged_in", False):
        st.error("An instructor is currently logged in. Please log out as instructor before logging in as admin.")
        return
    
    conn_str = st.text_input("MongoDB Connection String", type="password")
    if st.button("Submit"):
        if check_admin(conn_str):
            st.session_state.is_admin = True
            st.success("Admin access granted!")
            st.rerun()
        else:
            st.error("Invalid connection string. Access denied.")

def main():
    st.set_page_config(layout='wide', page_title='Club Stride Software')
    sidebar_style = """
    <style>
    /* Change the sidebar's overall width */
    [data-testid="stSidebar"] {
        width: 500px !important;
        min-width: 500px !important;
    }
    </style>
    """

    st.markdown(sidebar_style, unsafe_allow_html=True)
  
    
    # st.markdown(control_footer_style, unsafe_allow_html=True)
    hide_footer_style = ''' <style>.reportview-container .main footer {visibility: hidden;} '''
    st.markdown(hide_footer_style, unsafe_allow_html=True)
    hide_menu_style = '''<style> #MainMenu {visibility: hidden;} </style>'''
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    st.title("Club Stride Attendance System")
    

    # Ensure instructors table is created
    create_instructors_table()

    # Initialize session states if not present
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "instructor_logged_in" not in st.session_state:
        st.session_state.instructor_logged_in = False

    # -----------------------------
    # Base menu items
    # -----------------------------
    menu_options = [
        # "Home",
        "Admin Login",
        "Instructor Login",
        "Manage Attendance",
        "Manage Schedules",
        "Generate Reports"
    ]

    # -----------------------------
    # Admin menu additions
    # -----------------------------
    if st.session_state.is_admin:
        # Insert "Manage Instructors" right after Admin Login
        menu_options.insert(2, "Manage Instructors")

    # -----------------------------
    # Instructor menu additions
    # -----------------------------
    # We want instructors to have access to "Manage Students" as well
    if st.session_state.instructor_logged_in:
        # Insert "Manage Students" near the top, after "Instructor Login"
        menu_options.insert(3, "Manage Students")
        # Also allow them to change password + log out
        menu_options.append("Change My Password")
        # menu_options.append("Logout Instructor")

    # Build the final menu
    with st.sidebar:
        choice = option_menu("Main Menu", menu_options, orientation="vertical")
        st.write("---")
          # If user is admin, show Logout Admin button
        if st.session_state.is_admin:
            if st.button("Logout Admin"):
                st.session_state.is_admin = False
                st.warning("Logged out as admin.")
                st.rerun()

        # If user is an instructor, show Logout Instructor button
        if st.session_state.instructor_logged_in:
            if st.button("Logout Instructor"):
                st.session_state.instructor_logged_in = False
                st.session_state.instructor_id = None
                st.session_state.instructor_role = None
                st.session_state.instructor_programs = None
                st.warning("Logged out as instructor.")
                st.rerun()

    # -----------------------------
    # Menu Actions
    # -----------------------------
    if choice == "Home":
        st.write("Welcome to the hybrid system (SQLite for instructors, MongoDB for students).")

    elif choice == "Admin Login":
        admin_login()
        # st.rerun()

    elif choice == "Instructor Login":
        if st.session_state.instructor_logged_in:
            st.info("You are already logged in as an instructor.")
        else:
            page_instructor_login()
            # st.rerun()


    elif choice == "Manage Instructors":
        # Must be admin
        if st.session_state.is_admin:
            page_manage_instructors()
        else:
            st.error("You do not have permission to access this feature.")

    elif choice == "Manage Students":
        # Allow both admin and instructors
        if st.session_state.is_admin or st.session_state.instructor_logged_in:
            page_manage_students()
        else:
            st.error("You do not have permission to access this feature.")
    elif choice == "Generate Reports":
        # Typically an admin-only feature, but adjust as needed
        # if st.session_state.is_admin:
        if st.session_state.is_admin or st.session_state.instructor_logged_in:

            page_generate_reports()
        else:
            st.error("You do not have permission to access this feature.")

    elif choice == "Manage Attendance":
        Attendance_choice = st.radio("Select" , ["Take Attendance", "Review Attendance"],horizontal = True)
        # Let both admin and instructors do attendance
        if Attendance_choice == "Take Attendance":
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_take_attendance()
            else:
                st.error("You do not have permission to access this feature.")
        elif Attendance_choice == "Review Attendance":
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_review_attendance()
            else:
                st.error("You do not have permission to access this feature.")
    
    elif choice == "Change My Password":
        # Must be an instructor
        if st.session_state.instructor_logged_in:
            page_instructor_change_password()
        else:
            st.error("You must be an instructor to change your password.")
    elif choice == "Manage Schedules":
        # Only allow if admin or instructor
        if st.session_state.is_admin or st.session_state.instructor_logged_in:
            page_manage_schedules()
    else:
        st.error("You do not have permission to access this feature.")

if __name__ == "__main__":
    main()
