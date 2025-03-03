# main_app.py

import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

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
    col_left, col_center, col_right = st.columns([1, 5, 1])
    with col_center:
        st.header("Admin Login")

        if st.session_state.get("instructor_logged_in", False):
            st.error("An instructor is currently logged in. Please log out as instructor before logging in as admin.")
            return
        
        conn_str = st.text_input("MongoDB Connection String", type="password")
        if st.button("Submit"):
            if check_admin(conn_str):
                st.session_state.is_admin = True
                st.success("Admin access granted!")
                st.session_state.menu_choice = "Main Tools"

                st.rerun()
            else:
                st.error("Invalid connection string. Access denied.")


def main():
    st.set_page_config(layout='wide', page_title='Club Stride Software')
     # 1) Global HTML snippet with a top banner and some styling
    global_layout_html = """
    <div style="background: linear-gradient(90deg, #FF6E6E 0%, #FFD36E 100%);
                padding: 20px; color: white; text-align: center;
                font-family: sans-serif;">
      <h1>Club Stride Attendance System</h1>
    </div>
    """

    # 2) Inject the HTML using st.components.v1.html
    #    Note: scrolling=False means we rely on the main page scroll, not an iframe scroll
    components.html(global_layout_html, height=150, scrolling=False)

    # Medium layout hack
    medium_layout_css = """
    <style>
    @media (min-width: 700px) {
        .main .block-container {
            max-width: 900px !important;  /* Adjust as desired (e.g., 1000px) */
            margin: 0 auto;              /* Center horizontally */
        }
    }
    </style>
    """
    st.markdown(medium_layout_css, unsafe_allow_html=True)

    # Advanced React-like CSS
    advanced_react_css = """
    <style>
    /************************************************
     0) IMPORT FONTS & GLOBAL RESETS
    ************************************************/
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Open Sans', sans-serif;
        margin: 0;
        padding: 0;
        scroll-behavior: smooth;
        transition: all 0.3s ease-in-out;
    }
    body {
        background-color: #FFFFFF !important;  /* White main area */
        color: #374151; /* Dark gray text color */
    }

    /************************************************
     1) MAIN CONTENT FADE-SLIDE IN
    ************************************************/
    .main .block-container {
        animation: fadeSlideIn 0.4s ease-out both;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    @keyframes fadeSlideIn {
        0% {
            opacity: 0;
            transform: translateY(15px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /************************************************
     2) WIDE SIDEBAR WITH OPENAI-STYLE GRADIENT
    ************************************************/
    [data-testid="stSidebar"] {
        width: 300px !important;
        min-width: 300px !important;
        background: linear-gradient(90deg, #8A4FFF 0%, #EC4899 40%, #FF8A00 100%) !important;
        box-shadow: 1px 0 4px rgba(0, 0, 0, 0.1);
        border-right: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stSidebar"]:hover {
        filter: brightness(1.03);
    }

    /************************************************
     3) MOBILE RESPONSIVENESS
    ************************************************/
    @media only screen and (max-width: 600px) {
        [data-testid="stSidebar"] {
            position: relative !important;
            width: 100% !important;
            min-width: 100% !important;
            border-right: none;
            box-shadow: none;
        }
    }

    /************************************************
     4) SCROLLBARS (PURPLE THUMB)
    ************************************************/
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #D1D5DB;
    }
    ::-webkit-scrollbar-thumb {
        background-color: #8B5CF6;
        border-radius: 8px;
        border: 1px solid #D1D5DB;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: #6D28D9;
    }

    /************************************************
     5) BUTTONS & INTERACTIVE WIDGETS
    ************************************************/
    .stButton button, div[role="button"] {
        background: #FFFFFF !important;
        color: #374151 !important;
        border: none !important;
        border-radius: 4px !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease;
        font-weight: 600 !important;
    }
    .stButton button:hover, div[role="button"]:hover {
        background: #F3F4F6 !important;
        transform: translateY(-1px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.15) !important;
    }
    .stButton button:active, div[role="button"]:active {
        transform: scale(0.98);
    }
    [role="slider"] {
        background-color: #8B5CF6 !important;
        box-shadow: none !important;
    }
    input[type="checkbox"], input[type="radio"] {
        accent-color: #8B5CF6 !important;
        transform: scale(1.1);
        cursor: pointer;
    }

    /************************************************
     6) HEADERS, TABLES, TEXT SELECTION
    ************************************************/
    ::selection {
        background: #8B5CF6;
        color: #FFFFFF;
    }
    table, th, td {
        transition: background-color 0.2s;
    }
    tbody tr:hover {
        background-color: rgba(139, 92, 246, 0.05);
    }
    h1, h2, h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #2D3748;
    }

    /************************************************
     7) EXPANDER ANIMATION
    ************************************************/
    .st-expanderContent {
        animation: expandIn 0.3s ease-in-out;
        transform-origin: top;
    }
    @keyframes expandIn {
        0% {
            max-height: 0;
            opacity: 0;
        }
        100% {
            max-height: 999px;
            opacity: 1;
        }
    }
    </style>
    """
    st.markdown(advanced_react_css, unsafe_allow_html=True)

    # Hide Streamlit footer & menu
    hide_footer_style = ''' <style>.reportview-container .main footer {visibility: hidden;} </style>'''
    st.markdown(hide_footer_style, unsafe_allow_html=True)
    hide_menu_style = '''<style>#MainMenu {visibility: hidden;}</style>'''
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    # Ensure instructors table is created
    create_instructors_table()

    # Initialize session states if not present
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "instructor_logged_in" not in st.session_state:
        st.session_state.instructor_logged_in = False

    # -----------------------------
    # Base menu items: removing direct "Manage Attendance", "Manage Schedules",
    # "Generate Reports", and "Manage Students" from the side menu
    # and adding a single "Main Tools" item in their place.
    # -----------------------------
    menu_options = [
        "Admin Login",
        "Instructor Login",
        "Main Tools"
    ]

    # If admin -> insert "Manage Instructors" after "Admin Login"
    if st.session_state.is_admin:
        menu_options.insert(2, "Manage Instructors")

    # If instructor logged in -> add "Change My Password" at the end
    if st.session_state.instructor_logged_in:
        menu_options.append("Change My Password")

    # Sidebar menu
    with st.sidebar:
        # st.title("Club Stride Attendance System")

        # choice = option_menu("Main Menu", menu_options, orientation="vertical")
        if "menu_choice" not in st.session_state:
            st.session_state.menu_choice = "Admin Login"

        choice = option_menu("Main Menu", menu_options, orientation="vertical",
                     default_index=menu_options.index(st.session_state.menu_choice))


        st.write("---")
        # Logout admin if applicable
        if st.session_state.is_admin:
            if st.button("Logout Admin"):
                st.session_state.is_admin = False
                st.warning("Logged out as admin.")
                st.rerun()

        # Logout instructor if applicable
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
    if choice == "Admin Login":
        admin_login()

    elif choice == "Instructor Login":
        if st.session_state.instructor_logged_in:
            st.info("You are already logged in as an instructor.")
        else:
            page_instructor_login()

    elif choice == "Manage Instructors":
        # Must be admin
        if st.session_state.is_admin:
            page_manage_instructors()
        else:
            st.error("You do not have permission to access this feature.")

    elif choice == "Change My Password":
        # Must be an instructor
        if st.session_state.instructor_logged_in:
            page_instructor_change_password()
        else:
            st.error("You must be an instructor to change your password.")

    elif choice == "Main Tools":
        # Show tabs for the four tools: Manage Students, Manage Attendance,
        # Manage Schedules, Generate Reports
        
        tabs = st.tabs(["Manage Students", "Manage Attendance", "Manage Schedules", "Generate Reports"])

        # ----- TAB 1: Manage Students -----
        with tabs[0]:
            # st.header("Manage Students")
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_manage_students()
            else:
                st.error("You do not have permission to access this feature.")

        # ----- TAB 2: Manage Attendance -----
        with tabs[1]:
            col_left, col_center, col_right = st.columns([1, 5, 1])

            with col_center:
                st.header("Manage Attendance")
                # Reuse your existing radio approach inside the tab
                Attendance_choice = st.radio("Select", ["Take Attendance", "Review Attendance"], horizontal=True)
                if Attendance_choice == "Take Attendance":
                    if st.session_state.is_admin or st.session_state.instructor_logged_in:
                        page_take_attendance()
                    else:
                        st.error("You do not have permission.")
                else:
                    if st.session_state.is_admin or st.session_state.instructor_logged_in:
                        page_review_attendance()
                    else:
                        st.error("You do not have permission.")

        # ----- TAB 3: Manage Schedules -----
        with tabs[2]:
            # st.header("Manage Schedules")
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_manage_schedules()
            else:
                st.error("You do not have permission to access this feature.")

        # ----- TAB 4: Generate Reports -----
        with tabs[3]:
            st.header("Generate Reports")
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_generate_reports()
            else:
                st.error("You do not have permission to access this feature.")

    else:
        # Fallback if something unexpected
        st.write("Welcome! Select an option from the side.")

if __name__ == "__main__":
    main()
