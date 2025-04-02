# main_app.py

import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from PIL import Image
# from . import page_manage_documents
# Page imports (same as before)
from pages import (
    page_manage_instructors,
    page_manage_students,
    page_take_attendance,
    page_manage_documents,
    page_review_attendance,
    page_generate_reports,
    page_help,
    page_my_settings,
    page_instructor_change_password,
    page_manage_schedules,
    page_unified_login,
    page_dashboard
)

# Admin check
from students_db import check_admin
# Create instructors table
from instructors_db import create_instructors_table #authenticate_instructor, list_instructor_programs

# def admin_login():
#     col_left, col_center, col_right = st.columns([1, 5, 1])
#     with col_center:
#         st.header("Admin Login")

#         if st.session_state.get("instructor_logged_in", False):
#             st.error("An instructor is currently logged in. Please log out as instructor before logging in as admin.")
#             return
        
#         conn_str = st.text_input("MongoDB Connection String", type="password")
#         if st.button("Submit"):
#             if check_admin(conn_str):
#                 st.session_state.is_admin = True
#                 st.success("Admin access granted!")
#                 st.session_state.menu_choice = "Manage Instructors"
#                 st.rerun()
#             else:
#                 st.error("Invalid connection string. Access denied.")


def main():
    st.set_page_config(layout='wide', page_title='Club Stride Software')
    advanced_react_css = """
        <style>
        /************************************************
        0) IMPORT FONTS & GLOBAL RESETS
        ************************************************/
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            scroll-behavior: smooth;
            transition: all 0.3s ease-in-out;
        }
        table, th, td {
            font-family: 'Inter', sans-serif; /* Consistent table text */
        }
        body {
            background-color: #FFFFFF !important;
            color: #1F2937; /* Darker text for better contrast */
        }

        /************************************************
        1) MAIN CONTENT FADE-SLIDE IN
        ************************************************/
        .main .block-container {
            animation: fadeSlideIn 0.5s ease-out both;
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 1200px; /* Wider content area */
        }
        @keyframes fadeSlideIn {
            0% {
                opacity: 0;
                transform: translateY(20px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /************************************************
        2) MODERN BLACK SIDEBAR WITH SUBTLE ACCENT
        ************************************************/
        [data-testid="stSidebar"] {
            width: 300px !important;
            min-width: 300px !important;
            background: #111827 !important; /* Dark, almost black background */
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden; /* For the accent line */
        }

        /* Modern accent line on the side */
        [data-testid="stSidebar"]::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #8A4FFF 0%, #EC4899 50%, #FF8A00 100%);
            opacity: 0.8;
        }

        /* Brighten sidebar content for better contrast */
        [data-testid="stSidebar"] .sidebar-content {
            color: #F3F4F6 !important;
        }

        /* Sidebar hover effect */
        [data-testid="stSidebar"]:hover {
            filter: brightness(1.05);
        }

        /************************************************
        3) TITLE STYLING
        ************************************************/
        .title-container {
            text-align: center;
            padding: 20px 0;
        }
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin: 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /************************************************
        4) MOBILE RESPONSIVENESS
        ************************************************/
        @media only screen and (max-width: 768px) {
            [data-testid="stSidebar"] {
                width: 100% !important;
                min-width: 100% !important;
                border-right: none;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
            
            [data-testid="stSidebar"]::after {
                width: 100%;
                height: 4px;
                top: 0;
                left: 0;
            }
            
            .main .block-container {
                padding: 1rem !important;
            }
        }

        /************************************************
        5) SCROLLBARS (SLEEK DESIGN)
        ************************************************/
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #F1F1F1;
            border-radius: 6px;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #111827;
            border-radius: 6px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: #374151;
        }

        /************************************************
        6) BUTTONS & INTERACTIVE WIDGETS
        ************************************************/
        .stButton button, div[role="button"] {
            background: #111827 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            transition: all 0.2s ease;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton button:hover, div[role="button"]:hover {
            background: #374151 !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        }
        .stButton button:active, div[role="button"]:active {
            transform: scale(0.98);
        }

        /* Form controls */
        [role="slider"] {
            background-color: #111827 !important;
            box-shadow: none !important;
        }
        input[type="checkbox"], input[type="radio"] {
            accent-color: #111827 !important;
            transform: scale(1.1);
            cursor: pointer;
        }

        /* Input fields */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {
            border-radius: 6px !important;
            border: 1px solid #D1D5DB !important;
            padding: 0.5rem !important;
            transition: all 0.2s ease;
        }
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTimeInput input:focus {
            border-color: #111827 !important;
            box-shadow: 0 0 0 2px rgba(17, 24, 39, 0.2) !important;
        }

        /************************************************
        7) HEADERS, TABLES, TEXT SELECTION
        ************************************************/
        ::selection {
            background: #111827;
            color: #FFFFFF;
        }

        /* Table styling */
        table {
            border-collapse: separate !important;
            border-spacing: 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
        }
        th {
            background-color: #F9FAFB !important;
            color: #111827 !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.5px !important;
        }
        tbody tr:nth-child(even) {
            background-color: #F3F4F6;
        }
        tbody tr:hover {
            background-color: rgba(17, 24, 39, 0.05);
        }

        /* Headers */
        h1, h2, h3 {
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: #111827;
            font-weight: 700;
            line-height: 1.2;
        }
        h1 {
            font-size: 2rem;
            border-bottom: 2px solid #F3F4F6;
            padding-bottom: 0.5rem;
        }
        h2 {
            font-size: 1.5rem;
        }
        h3 {
            font-size: 1.25rem;
            color: #374151;
        }

        /************************************************
        8) EXPANDER & CARD ANIMATIONS
        ************************************************/
        .st-expanderContent {
            animation: expandIn 0.3s ease-in-out;
            transform-origin: top;
            border-radius: 0 0 8px 8px;
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

        /* Card-like elements */
        .element-container, .stAlert {
            border-radius: 8px !important;
            overflow: hidden !important;
            transition: all 0.3s ease;
        }
        .element-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.05);
        }

        /************************************************
        9) CUSTOM TITLE COMPONENT
        ************************************************/
        .custom-title {
            background-color: #111827;
            padding: 1.5rem;
            border-radius: 0 0 12px 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        .custom-title h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            padding: 0;
            border: none;
            text-transform: uppercase;
            text-align: center;
            letter-spacing: 1px;
        }
        .custom-title::after {
            content: "";
            position: absolute;
            bottom: 0;
            left: 25%;
            right: 25%;
            height: 3px;
            background: linear-gradient(90deg, #8A4FFF, #EC4899, #FF8A00);
            border-radius: 3px 3px 0 0;
        }
        </style>

        <!-- Title Component HTML -->
        <div class="custom-title">
        <h1>Club Stride Attendance System</h1>
        </div>
        """
    # components.html(advanced_react_css)
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
    # menu_options = [
    #     "Home",
    #     "Admin Login",
    #     "Instructor Login",
    #     "Student Management Suite"
    # ]
    menu_options = ["Home"]
    # menu_options.append("Dashboard")

    # 2) Show "Login" only if no one is logged in
    if not st.session_state.is_admin and not st.session_state.instructor_logged_in:
        menu_options.append("Login")
    # If admin -> insert "Manage Instructors" after "Admin Login"

    # 3) If admin -> show "Manage Instructors"
    if st.session_state.is_admin:
        menu_options.append("Dashboard")
        menu_options.append("Manage Instructors")
        menu_options.append("Student Management Suite")
        menu_options.append("My Settings")

    # 4) If instructor -> show "Student Management Suite" + "Change My Password"
    if st.session_state.instructor_logged_in:
        menu_options.append("Dashboard")
        menu_options.append("Student Management Suite")
        menu_options.append("My Settings")
        # menu_options.append("Change My Password")
    # if st.session_state.is_admin:
    #     menu_options.insert(2, "Manage Instructors")

    # # If instructor logged in -> add "Change My Password" at the end
    # if st.session_state.instructor_logged_in:
    #     menu_options.append("Change My Password")
    menu_options.append("Help / User Guide")  # <--- Add a new top-level menu
    

    # Sidebar menu
    logo = Image.open("assets/Club-Stride-Logo.png")

    with st.sidebar:
        
        # st.title("Club Stride Attendance System")

        # choice = option_menu("Main Menu", menu_options, orientation="vertical")
        if "menu_choice" not in st.session_state:
            st.session_state.menu_choice = "Home"

        try:
            default_idx = menu_options.index(st.session_state.menu_choice)
        except ValueError:
            default_idx = 0  # Default to Home if not found
        
    #     choice = option_menu("Main Menu", menu_options, orientation="vertical",
    #                  default_index=menu_options.index(st.session_state.menu_choice), styles={
    #     "nav-link": {
    #         "font-size": "15px",
    #         "text-align": "left",
    #         "margin":"0px",
    #         "--hover-color": "#F0F2F6",
    #     },
    #     "nav-link-selected": {
    #         "font-weight": "700",  # Make it bold
    #         "background-color": "#E0E7FF",  # Subtle highlight
    #         "color": "#4B5563",  # text color
    #     }
    # })

        choice = option_menu(
            "Main Menu", 
            menu_options, 
            orientation="vertical",
            default_index=default_idx,  # Use calculated index instead of direct lookup
            styles={
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "rgba(255, 255, 255, 0.2)",
                    "color": "white",
                },
                "nav-link-selected": {
                    "font-weight": "700",
                    "background-color": "rgba(255, 255, 255, 0.2)",
                    "color": "white",
                }
            }
        )
        
        # Only update session state if choice actually changed
        if choice != st.session_state.menu_choice:
            st.session_state.menu_choice = choice
            st.rerun()

        st.sidebar.markdown("### Current Login Status")

        if st.session_state.get("is_admin", False):
            st.sidebar.write("**Admin**")
        # elif st.session_state.get("instructor_logged_in", False):
        elif st.session_state.instructor_logged_in:

            # Optionally show the instructor role or ID if you wish
            instructor_role = st.session_state.get("instructor_role", "Instructor")
            instructor_id = st.session_state.get("instructor_id", "Unknown")
            instructor_username =  st.session_state.get("instructor_username", "Admin").strip()

            st.sidebar.write(f"**{instructor_role}** (ID={instructor_username})")
        else:
            st.sidebar.write("**No user logged in**")
        # st.markdown("---")    

        # Single "Logout" button if admin or instructor


        # if st.session_state.is_admin or st.session_state.instructor_logged_in:
        #     if st.button("Logout"):
        #         # Reset session state
        #         st.session_state.is_admin = False
        #         st.session_state.instructor_logged_in = False
        #         st.session_state.instructor_id = None
        #         st.session_state.instructor_role = None
        #         st.session_state.instructor_username = None
        #         st.session_state.menu_choice = "Home"
        #         st.success("Logged out successfully.")
        #         st.rerun()

        # Logout admin if applicable
        # if st.session_state.is_admin:
        #     if st.button("Logout Admin"):
        #         st.session_state.is_admin = False
        #         st.session_state.menu_choice = "Home"
        #         st.warning("Logged out as admin.")
        #         st.rerun()

        # # Logout instructor if applicable
        # if st.session_state.instructor_logged_in:
        #     if st.button("Logout Instructor"):
        #         st.session_state.instructor_logged_in = False
        #         st.session_state.instructor_id = None
        #         st.session_state.instructor_role = None
        #         st.session_state.instructor_programs = None
        #         st.session_state.menu_choice = "Home"
        #         st.warning("Logged out as instructor.")
        #         st.rerun()
        
        col1, col2, col3 = st.columns([1, 5, 1])

        
        # with col2:
        st.divider()
        st.image(logo, caption="© 2025 Club Stride Inc", use_container_width=True)
    st.session_state.menu_choice = choice

    # -----------------------------
    # Menu Actions
    # -----------------------------
    if choice == "Home":
        hero_html = """
            <div style="
                padding: 2rem; 
                background: linear-gradient(90deg, #FDE68A 0%, #FCD34D 100%);
                border-radius: 0.5rem;
                margin-bottom: 1rem;">
            <h2 style="
                margin-bottom: 0.5rem; 
                font-family: sans-serif;
                color: #374151;">
                Welcome to the Club Stride Attendance System!
            </h2>
            <p style="
                margin: 0; 
                color: #4B5563; 
                font-size: 1.1rem;">
                Streamlined attendance tracking, automated notifications, and insightful reporting at your fingertips.
            </p>
            </div>
            """
        st.markdown(hero_html, unsafe_allow_html=True)

        # Create a 3-column layout highlighting major features
        col2, col3 = st.columns(2)

        with col2:
            st.subheader("Effortless Attendance")
            st.write("""
            - Mark Present, Late, or Absent  
            - Bulk check-in for entire classes  
            - Excuse management via forms
            """)

        with col3:
            st.subheader("Powerful Reporting")
            st.write("""
            - Real-time attendance metrics  
            - Missed count summaries  
            - Exportable data records
            """)
        # st.write('Place Holder')

    elif choice == "Dashboard":
        page_dashboard()  # <--- Show the new dashboard

    elif choice == "Login":
        page_unified_login()

    # elif choice == "Instructor Login":
    #     if st.session_state.instructor_logged_in:
    #         st.info("You are already logged in as an instructor.")
    #     else:
    #         page_instructor_login()

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

    elif choice == "Student Management Suite":
        # Show tabs for the four tools: Manage Students, Manage Attendance,
        # Manage Schedules, Generate Reports
        
        SMStabs = st.tabs(["Manage Students", "Attendance & Scheduling", "Reports & Analytics"])#"Document Management"

        # ----- TAB 1: Manage Students -----
        with SMStabs[0]:
            # st.header("Manage Students")
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_manage_students()
            else:
                st.error("You do not have permission to access this feature.")

        # ----- TAB 2: Manage Attendance -----
        with SMStabs[1]:
            # col_left, col_center, col_right = st.columns([1, 5, 1])

            # with col_center:
            st.header("Manage Attendance & Scheduling")
            # Reuse your existing radio approach inside the tab
            tab_labels = ["Take Attendance", "Review Attendance", "Manage Schedules"]
            tabs = st.tabs(tab_labels)

            # if Attendance_choice == "Take Attendance":
            with tabs[0]:
                if st.session_state.is_admin or st.session_state.instructor_logged_in:
                    page_take_attendance()
                else:
                    st.error("You do not have permission.")
            # else:
            with tabs[1]:
                if st.session_state.is_admin or st.session_state.instructor_logged_in:
                    page_review_attendance()
                else:
                    st.error("You do not have permission.")

            with tabs[2]:
                if st.session_state.is_admin or st.session_state.instructor_logged_in:
                    page_manage_schedules()
                else:
                    st.error("You do not have permission to access this feature.")
                    
        # ----- TAB 3: Manage Schedules -----
        with SMStabs[2]:
            # st.header("Generate Reports")
            if st.session_state.is_admin or st.session_state.instructor_logged_in:
                page_generate_reports()
            else:
                st.error("You do not have permission to access this feature.")

        # with SMStabs[3]:  # New tab for Document Management
        #     if st.session_state.is_admin or st.session_state.instructor_logged_in:
        #         page_manage_documents()
        #     else:
        #         st.error("You do not have permission to access this feature.")

    elif choice == "Help / User Guide":
        page_help()  # We'll define page_help() below
    elif choice == "My Settings":
        # We'll open a new function that merges change-password + logout
        page_my_settings()
   # with tabs[2]:
            # st.header("Manage Schedules")
            # if st.session_state.is_admin or st.session_state.instructor_logged_in:
            #     page_manage_schedules()
            # else:
            #     st.error("You do not have permission to access this feature.")

        # ----- TAB 4: Generate Reports -----
    # else:
    #     # Fallback if something unexpected
    #     st.write("...")

if __name__ == "__main__":
    main()
