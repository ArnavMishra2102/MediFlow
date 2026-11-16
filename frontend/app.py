
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MediFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8000"
IST = ZoneInfo("Asia/Kolkata")


# =========================================================
# 2. SESSION STATE
# =========================================================

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None


# =========================================================
# 3. CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0e1117;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Dashboard header */

.hero {
    padding: 30px;
    border-radius: 16px;
    background: linear-gradient(120deg, #123c69, #2a9d8f);
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    font-size: 38px;
    font-weight: 700;
}

.hero p {
    color: #eaf6f6;
    font-size: 17px;
}

/* Metric cards */

div[data-testid="stMetric"] {
    background: #1e293b !important;
    color: #ffffff !important;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #334155;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

div[data-testid="stMetric"] label {
    color: #cbd5e1 !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 30px;
    font-weight: 700;
}

div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: #4ade80 !important;
}

/* Buttons */

.stButton button {
    border-radius: 9px;
    font-weight: 600;
    transition: 0.2s;
}

.stButton button:hover {
    border-color: #2a9d8f;
    color: #2a9d8f;
}

/* Containers */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
}

/* Tabs */

button[data-baseweb="tab"] {
    font-weight: 600;
}

/* Dataframes */

div[data-testid="stDataFrame"] {
    border-radius: 10px;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #252831;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. COMMON FUNCTIONS
# =========================================================

def show_header(title, subtitle):

    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_datetime(selected_date, selected_time):

    return datetime.combine(
        selected_date,
        selected_time,
        tzinfo=IST,
    ).isoformat()


def display_datetime(value):

    if not value:
        return "Not available"

    try:

        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)

        return parsed.astimezone(IST).strftime(
            "%d %b %Y, %I:%M %p"
        )

    except (ValueError, TypeError, AttributeError):

        return str(value)


def api_request(method, endpoint, json=None, params=None):

    headers = {}

    if st.session_state.token:

        headers["Authorization"] = (
            f"Bearer {st.session_state.token}"
        )

    try:

        response = requests.request(
            method=method,
            url=f"{API_URL}{endpoint}",
            headers=headers,
            json=json,
            params=params,
            timeout=15,
        )

        if not response.ok:

            try:
                error_data = response.json()
                message = error_data.get("detail", error_data)

            except ValueError:
                message = response.text or "Request failed."

            st.error(
                f"API Error ({response.status_code}): {message}"
            )

            return None

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "Cannot connect to MediFlow API. "
            "Make sure FastAPI is running."
        )

        return None

    except requests.exceptions.Timeout:

        st.error("The API request timed out.")

        return None

    except requests.exceptions.RequestException as error:

        st.error(f"Request failed: {error}")

        return None


def logout():

    st.session_state.token = None
    st.session_state.user = None

    st.rerun()


def show_logout():

    with st.sidebar:

        st.divider()

        st.write(
            f"**Logged in as:** "
            f"{st.session_state.user['full_name']}"
        )

        st.write(
            f"**Role:** "
            f"{st.session_state.user['role'].title()}"
        )

        if st.button(
            "Logout",
            use_container_width=True,
        ):

            logout()


def show_appointment_chart(appointments):

    if not appointments:

        st.info("No appointment data available yet.")

        return

    df = pd.DataFrame(appointments)

    if "status" not in df.columns:
        return

    status_counts = (
        df["status"]
        .fillna("unknown")
        .value_counts()
        .reset_index()
    )

    status_counts.columns = [
        "Status",
        "Appointments",
    ]

    fig = px.pie(
        status_counts,
        names="Status",
        values="Appointments",
        hole=0.55,
        title="Appointment Status Distribution",
        color="Status",
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )

    fig.update_layout(
        height=380,
        legend_title="Status",
        template="plotly_dark",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# 5. LOGIN AND REGISTRATION
# =========================================================

def login_page():

    show_header(
        "MediFlow 🏥",
        "Your healthcare appointment management platform",
    )

    left, right = st.columns([1.1, 1])

    with left:

        st.subheader("Healthcare, made simpler")

        st.write(
            "MediFlow connects patients, doctors, and "
            "administrators through one appointment "
            "management platform."
        )

        st.markdown("""
        - 📅 Book and manage appointments
        - 👨‍⚕️ Manage doctor availability
        - 🏥 Administer doctors and appointment slots
        - 📊 View interactive appointment analytics
        """)

        st.image(
            "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1000&q=80",
            use_container_width=True,
        )

    with right:

        login_tab, register_tab = st.tabs(
            ["Login", "Patient Registration"]
        )

        # LOGIN

        with login_tab:

            st.subheader("Welcome back")

            with st.form("login_form"):

                email = st.text_input("Email address")

                password = st.text_input(
                    "Password",
                    type="password",
                )

                login_button = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                )

            if login_button:

                if not email.strip() or not password:

                    st.warning(
                        "Please enter your email and password."
                    )

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/auth/login",
                            data={
                                "username": email.strip().lower(),
                                "password": password,
                            },
                            timeout=15,
                        )

                        if response.status_code != 200:

                            try:
                                detail = response.json().get(
                                    "detail",
                                    "Login failed.",
                                )

                            except ValueError:
                                detail = "Login failed."

                            st.error(detail)

                        else:

                            token = response.json()["access_token"]

                            user_response = requests.get(
                                f"{API_URL}/auth/me",
                                headers={
                                    "Authorization": f"Bearer {token}"
                                },
                                timeout=15,
                            )

                            if user_response.status_code == 200:

                                user = user_response.json()

                                st.session_state.token = token
                                st.session_state.user = user

                                st.success("Login successful!")

                                st.rerun()

                            else:

                                st.error(
                                    "Could not load your user profile. "
                                    "Check the /auth/me endpoint."
                                )

                    except requests.exceptions.RequestException:

                        st.error(
                            "Cannot connect to the backend. "
                            "Start FastAPI first."
                        )

        # REGISTRATION

        with register_tab:

            st.subheader("Create a patient account")

            with st.form("register_form"):

                full_name = st.text_input("Full name")

                new_email = st.text_input("Email address")

                new_password = st.text_input(
                    "Password",
                    type="password",
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                )

                register_button = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                )

            if register_button:

                if not full_name.strip() or not new_email.strip():

                    st.warning("Please fill in all fields.")

                elif len(new_password) < 8:

                    st.warning(
                        "Password must contain at least 8 characters."
                    )

                elif new_password != confirm_password:

                    st.error("Passwords do not match.")

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/auth/register",
                            json={
                                "full_name": full_name.strip(),
                                "email": new_email.strip().lower(),
                                "password": new_password,
                            },
                            timeout=15,
                        )

                        if response.status_code == 201:

                            st.success(
                                "Account created successfully! "
                                "You can now log in."
                            )

                        else:

                            try:
                                detail = response.json().get(
                                    "detail",
                                    "Registration failed.",
                                )

                            except ValueError:
                                detail = "Registration failed."

                            st.error(detail)

                    except requests.exceptions.RequestException:

                        st.error("Cannot connect to the backend.")


# =========================================================
# 6. ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    show_header(
        "Admin Dashboard 🏥",
        "Manage doctors, create accounts, and assign appointment slots.",
    )

    show_logout()

    doctors = api_request(
        "GET",
        "/admin/doctors",
    )

    if doctors is None:
        doctors = []

    total_doctors = len(doctors)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Doctors", total_doctors)
    col2.metric("Admin Account", "Active")
    col3.metric("System", "Operational")

    st.divider()

    create_tab, doctors_tab, slots_tab = st.tabs(
        [
            "➕ Create Doctor",
            "👨‍⚕️ Manage Doctors",
            "📅 Assign Slots",
        ]
    )

    # CREATE DOCTOR

    with create_tab:

        st.subheader("Create a doctor account")

        with st.form("create_doctor_form"):

            doctor_name = st.text_input("Doctor full name")

            doctor_email = st.text_input("Doctor email")

            doctor_password = st.text_input(
                "Temporary password",
                type="password",
            )

            create_button = st.form_submit_button(
                "Create Doctor Account",
                use_container_width=True,
            )

        if create_button:

            if not doctor_name.strip() or not doctor_email.strip():

                st.warning("Name and email are required.")

            elif len(doctor_password) < 8:

                st.warning(
                    "Password must contain at least 8 characters."
                )

            else:

                result = api_request(
                    "POST",
                    "/admin/doctors",
                    json={
                        "full_name": doctor_name.strip(),
                        "email": doctor_email.strip().lower(),
                        "password": doctor_password,
                    },
                )

                if result is not None:

                    st.success(
                        f"Doctor account created: "
                        f"{result.get('full_name')}"
                    )

                    st.rerun()

    # VIEW DOCTORS

    with doctors_tab:

        st.subheader("Registered doctors")

        if doctors:

            doctor_df = pd.DataFrame(doctors)

            st.dataframe(
                doctor_df,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download Doctor List",
                doctor_df.to_csv(index=False),
                file_name="mediflow_doctors.csv",
                mime="text/csv",
            )

        else:

            st.info("No doctors have been registered yet.")

        if st.button("Refresh Doctor List"):

            st.rerun()

    # ASSIGN SLOTS

    with slots_tab:

        st.subheader("Assign an appointment slot")

        if not doctors:

            st.warning(
                "Create a doctor account before assigning slots."
            )

        else:

            doctor_options = {
                (
                    f"{doctor['full_name']} "
                    f"(ID: {doctor['id']})"
                ): doctor["id"]
                for doctor in doctors
            }

            selected_doctor = st.selectbox(
                "Select doctor",
                options=list(doctor_options.keys()),
            )

            selected_doctor_id = doctor_options[selected_doctor]

            st.write(
                "Select the slot date and time in Indian Standard Time."
            )

            slot_date = st.date_input(
                "Slot date",
                value=date.today() + timedelta(days=1),
                key="admin_slot_date",
            )

            col1, col2 = st.columns(2)

            with col1:

                start_time = st.time_input(
                    "Start time",
                    value=time(10, 0),
                    key="admin_start_time",
                )

            with col2:

                end_time = st.time_input(
                    "End time",
                    value=time(10, 30),
                    key="admin_end_time",
                )

            if st.button(
                "Assign Slot",
                use_container_width=True,
            ):

                if end_time <= start_time:

                    st.error(
                        "End time must be later than start time."
                    )

                else:

                    result = api_request(
                        "POST",
                        f"/admin/doctors/{selected_doctor_id}/slots",
                        json={
                            "start_time": make_datetime(
                                slot_date,
                                start_time,
                            ),
                            "end_time": make_datetime(
                                slot_date,
                                end_time,
                            ),
                        },
                    )

                    if result is not None:

                        st.success(
                            f"Slot assigned successfully to "
                            f"{result.get('doctor_name')}."
                        )


# =========================================================
# 7. DOCTOR DASHBOARD
# =========================================================

def doctor_dashboard():

    show_header(
        "Doctor Dashboard 👨‍⚕️",
        "Manage your availability and patient appointments.",
    )

    show_logout()

    slots = api_request(
        "GET",
        "/slots/my-slots",
    )

    appointments = api_request(
        "GET",
        "/appointments/doctor-appointments",
    )

    if slots is None:
        slots = []

    if appointments is None:
        appointments = []

    total_slots = len(slots)
    total_appointments = len(appointments)

    booked = sum(
        1 for appointment in appointments
        if appointment.get("status") == "booked"
    )

    completed = sum(
        1 for appointment in appointments
        if appointment.get("status") == "completed"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("My Slots", total_slots)
    col2.metric("Total Appointments", total_appointments)
    col3.metric("Booked", booked)
    col4.metric("Completed", completed)

    st.divider()

    slot_tab, appointment_tab, analytics_tab = st.tabs(
        [
            "📅 Manage Slots",
            "👥 Patient Appointments",
            "📊 Analytics",
        ]
    )

    # MANAGE SLOTS

    with slot_tab:

        st.subheader("Create your availability")

        with st.form("doctor_create_slot"):

            selected_date = st.date_input(
                "Date",
                value=date.today() + timedelta(days=1),
            )

            col1, col2 = st.columns(2)

            with col1:

                start_time = st.time_input(
                    "Start time",
                    value=time(10, 0),
                )

            with col2:

                end_time = st.time_input(
                    "End time",
                    value=time(10, 30),
                )

            create_slot_button = st.form_submit_button(
                "Create Slot",
                use_container_width=True,
            )

        if create_slot_button:

            if end_time <= start_time:

                st.error(
                    "End time must be later than start time."
                )

            else:

                result = api_request(
                    "POST",
                    "/slots/",
                    json={
                        "start_time": make_datetime(
                            selected_date,
                            start_time,
                        ),
                        "end_time": make_datetime(
                            selected_date,
                            end_time,
                        ),
                    },
                )

                if result is not None:

                    st.success("Your slot has been created.")

                    st.rerun()

        st.divider()

        st.subheader("My created slots")

        if slots:

            for slot in slots:

                start = display_datetime(
                    slot.get("start_time")
                )

                end = display_datetime(
                    slot.get("end_time")
                )

                with st.container(border=True):

                    col1, col2 = st.columns([4, 1])

                    with col1:

                        st.write(f"**Slot #{slot['id']}**")
                        st.write(f"Start: {start}")
                        st.write(f"End: {end}")

                    with col2:

                        if st.button(
                            "Delete",
                            key=f"delete_slot_{slot['id']}",
                        ):

                            result = api_request(
                                "DELETE",
                                f"/slots/{slot['id']}",
                            )

                            if result is not None:

                                st.success("Slot deleted.")

                                st.rerun()

        else:

            st.info(
                "You have not created any slots yet."
            )

    # PATIENT APPOINTMENTS

    with appointment_tab:

        st.subheader("Patient appointments")

        if appointments:

            for appointment in appointments:

                patient = appointment.get("patient") or {}
                slot = appointment.get("slot") or {}

                with st.expander(
                    f"Appointment #{appointment['id']} | "
                    f"{appointment.get('status', '').title()}"
                ):

                    st.write(
                        f"**Patient:** "
                        f"{patient.get('full_name', 'Unknown')}"
                    )

                    st.write(
                        f"**Appointment ID:** "
                        f"{appointment['id']}"
                    )

                    st.write(
                        f"**Date:** "
                        f"{display_datetime(slot.get('start_time'))}"
                    )

                    st.write(
                        f"**End time:** "
                        f"{display_datetime(slot.get('end_time'))}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{appointment.get('status', 'Unknown').title()}"
                    )

                    if appointment.get("status") == "booked":

                        if st.button(
                            "Mark as Completed",
                            key=f"complete_{appointment['id']}",
                        ):

                            result = api_request(
                                "PATCH",
                                f"/appointments/{appointment['id']}/complete",
                            )

                            if result is not None:

                                st.success(
                                    "Appointment completed."
                                )

                                st.rerun()

        else:

            st.info(
                "You do not have any patient appointments yet."
            )

    # DOCTOR ANALYTICS

    with analytics_tab:

        st.subheader("Appointment analytics")

        if appointments:

            show_appointment_chart(appointments)

            appointment_df = pd.DataFrame([
                {
                    "Appointment ID": item.get("id"),
                    "Patient": (
                        item.get("patient") or {}
                    ).get("full_name", "Unknown"),
                    "Status": item.get("status"),
                    "Date": display_datetime(
                        (item.get("slot") or {}).get("start_time")
                    ),
                }
                for item in appointments
            ])

            fig = px.bar(
                appointment_df,
                x="Status",
                color="Status",
                title="Appointments by Status",
                text="Appointment ID",
                template="plotly_dark",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:

            st.info(
                "Analytics will appear when patients book appointments."
            )


# =========================================================
# 8. PATIENT DASHBOARD
# =========================================================

def patient_dashboard():

    show_header(
        "Patient Dashboard 🩺",
        "Find available doctors and manage your appointments.",
    )

    show_logout()

    appointments = api_request(
        "GET",
        "/appointments/my-appointments",
    )

    available_slots = api_request(
        "GET",
        "/slots/",
    )

    if appointments is None:
        appointments = []

    if available_slots is None:
        available_slots = []

    total_appointments = len(appointments)

    booked = sum(
        1 for appointment in appointments
        if appointment.get("status") == "booked"
    )

    completed = sum(
        1 for appointment in appointments
        if appointment.get("status") == "completed"
    )

    cancelled = sum(
        1 for appointment in appointments
        if appointment.get("status") == "cancelled"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Appointments", total_appointments)
    col2.metric("Active Bookings", booked)
    col3.metric("Completed", completed)
    col4.metric("Cancelled", cancelled)

    st.divider()

    booking_tab, appointments_tab, analytics_tab = st.tabs(
        [
            "🔍 Find & Book Slots",
            "📋 My Appointments",
            "📊 Analytics",
        ]
    )

    # FIND AND BOOK SLOTS

    with booking_tab:

        st.subheader("Available appointment slots")

        if available_slots:

            slot_options = {
                (
                    f"Slot #{slot['id']} | "
                    f"Doctor ID: {slot['doctor_id']} | "
                    f"{display_datetime(slot['start_time'])} - "
                    f"{display_datetime(slot['end_time'])}"
                ): slot["id"]
                for slot in available_slots
            }

            selected_slot_label = st.selectbox(
                "Choose an appointment slot",
                options=list(slot_options.keys()),
            )

            selected_slot_id = slot_options[
                selected_slot_label
            ]

            if st.button(
                "Book Appointment",
                use_container_width=True,
            ):

                result = api_request(
                    "POST",
                    "/appointments/",
                    json={
                        "slot_id": selected_slot_id,
                    },
                )

                if result is not None:

                    st.success(
                        "Appointment booked successfully!"
                    )

                    st.rerun()

            st.divider()

            st.subheader("Other available slots")

            slot_df = pd.DataFrame([
                {
                    "Slot ID": slot["id"],
                    "Doctor ID": slot["doctor_id"],
                    "Start Time (IST)": display_datetime(
                        slot["start_time"]
                    ),
                    "End Time (IST)": display_datetime(
                        slot["end_time"]
                    ),
                }
                for slot in available_slots
            ])

            st.dataframe(
                slot_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No available slots at the moment. "
                "Please check again later."
            )

    # MY APPOINTMENTS

    with appointments_tab:

        st.subheader("Your appointment history")

        if appointments:

            for appointment in appointments:

                slot = appointment.get("slot") or {}
                doctor = slot.get("doctor") or {}

                status_value = appointment.get(
                    "status",
                    "unknown",
                )

                with st.expander(
                    f"Appointment #{appointment['id']} | "
                    f"{status_value.title()}"
                ):

                    st.write(
                        f"**Doctor:** "
                        f"{doctor.get('full_name', 'Unknown')}"
                    )

                    st.write(
                        f"**Appointment ID:** "
                        f"{appointment['id']}"
                    )

                    st.write(
                        f"**Start:** "
                        f"{display_datetime(slot.get('start_time'))}"
                    )

                    st.write(
                        f"**End:** "
                        f"{display_datetime(slot.get('end_time'))}"
                    )

                    st.write(
                        f"**Status:** {status_value.title()}"
                    )

                    if status_value == "booked":

                        col1, col2 = st.columns(2)

                        with col1:

                            if st.button(
                                "Cancel Appointment",
                                key=f"cancel_{appointment['id']}",
                                use_container_width=True,
                            ):

                                result = api_request(
                                    "PATCH",
                                    f"/appointments/{appointment['id']}/cancel",
                                )

                                if result is not None:

                                    st.success(
                                        "Appointment cancelled."
                                    )

                                    st.rerun()

                        with col2:

                            other_slots = [
                                item for item in available_slots
                                if item["id"] != slot.get("id")
                            ]

                            if other_slots:

                                slot_map = {
                                    (
                                        f"Slot #{item['id']} | "
                                        f"Doctor ID: {item['doctor_id']} | "
                                        f"{display_datetime(item['start_time'])}"
                                    ): item["id"]
                                    for item in other_slots
                                }

                                new_slot_label = st.selectbox(
                                    "Choose a new slot",
                                    options=list(slot_map.keys()),
                                    key=f"reschedule_select_{appointment['id']}",
                                )

                                if st.button(
                                    "Reschedule",
                                    key=f"reschedule_{appointment['id']}",
                                    use_container_width=True,
                                ):

                                    result = api_request(
                                        "PATCH",
                                        f"/appointments/{appointment['id']}/reschedule",
                                        params={
                                            "new_slot_id": slot_map[
                                                new_slot_label
                                            ]
                                        },
                                    )

                                    if result is not None:

                                        st.success(
                                            "Appointment rescheduled."
                                        )

                                        st.rerun()

                            else:

                                st.caption(
                                    "No alternative slots available."
                                )

        else:

            st.info(
                "You have not booked any appointments yet."
            )

    # PATIENT ANALYTICS

    with analytics_tab:

        st.subheader("Your appointment analytics")

        if appointments:

            show_appointment_chart(appointments)

            appointment_df = pd.DataFrame([
                {
                    "Appointment ID": item.get("id"),
                    "Status": item.get("status"),
                }
                for item in appointments
            ])

            fig = px.bar(
                appointment_df,
                x="Appointment ID",
                color="Status",
                title="Your Appointment History",
                barmode="group",
                template="plotly_dark",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:

            st.info(
                "Book your first appointment to see your analytics."
            )


# =========================================================
# 9. MAIN APPLICATION
# =========================================================

def main():

    if (
        not st.session_state.token
        or not st.session_state.user
    ):

        login_page()

        return

    role = st.session_state.user.get("role")

    if role == "admin":

        admin_dashboard()

    elif role == "doctor":

        doctor_dashboard()

    elif role == "patient":

        patient_dashboard()

    else:

        st.error(
            "Your account has an unrecognized role."
        )

        logout()


if __name__ == "__main__":
    main()
