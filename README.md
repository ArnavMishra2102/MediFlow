# MediFlow 🏥
### Healthcare Appointment Management System

MediFlow is a role-based healthcare appointment management system developed using Python, FastAPI, Streamlit, and PostgreSQL. It simplifies appointment scheduling and management by connecting administrators, doctors, and patients through an integrated platform.

## 🚀 Features

### 👨‍💼 Admin
- Secure admin authentication.
- Create and manage doctor accounts.
- View registered doctors.
- Assign appointment slots to doctors.

### 🩺 Doctor
- Secure doctor login.
- Create and manage availability slots.
- View scheduled patient appointments.
- Mark appointments as completed.

### 🧑‍⚕️ Patient
- Patient registration and login.
- Browse available doctor slots.
- Book appointments.
- Cancel appointments.
- Reschedule appointments.
- View appointment history.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend REST API |
| Streamlit | Interactive frontend |
| PostgreSQL | Relational database |
| SQLAlchemy | ORM and database operations |
| Pydantic | Data validation |
| JWT | Authentication |
| Argon2 | Password hashing |
| Plotly | Interactive charts and analytics |
| Pandas | Data processing |
| Uvicorn | ASGI server |

## 🏗️ System Architecture

The application follows a three-layer architecture:

1. **Frontend:** Streamlit provides role-specific dashboards and user interactions.
2. **Backend:** FastAPI handles authentication, business logic, and API requests.
3. **Database:** PostgreSQL stores user accounts, doctor availability, and appointment records.

Streamlit communicates with FastAPI through HTTP requests, while FastAPI interacts with PostgreSQL using SQLAlchemy.

## 🔐 Security and Database Features

- JWT-based authentication.
- Role-based access control.
- Argon2 password hashing.
- Pydantic request validation.
- Foreign key relationships.
- Database transactions.
- Row-level locking for appointment booking.
- Unique database constraint for active slot bookings.
- Timezone-aware appointment scheduling.

## 📁 Project Structure

```text
MediFlow/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── database.py
│   │   └── main.py
│   │
│   └── create_admin.py
│
├── frontend/
│   └── app.py
│
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/MediFlow.git
cd MediFlow
```

### 2. Create and activate the virtual environment

```bash
uv sync
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Configure PostgreSQL

- Install PostgreSQL.
- Create a database named `mediflow`.
- Configure your database connection and required application secrets in a local `.env` file.
- Never commit your `.env` file or expose database credentials.

### 4. Start the FastAPI backend

```bash
uv run uvicorn backend.app.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 5. Start the Streamlit frontend

Open another terminal:

```bash
uv run streamlit run frontend/app.py
```

Frontend URL:

`http://localhost:8501`

## 📊 Dashboard and Analytics

MediFlow includes interactive dashboard components using Plotly to present appointment statistics and visual analytics.

## 🔮 Future Enhancements

- Email-based password recovery with OTP verification.
- Automated appointment reminders.
- Online deployment.
- Automated backend and frontend testing.
- Enhanced doctor and patient analytics.

## 👨‍💻 Author

**YOUR NAME**

GitHub: [YOUR_GITHUB_PROFILE](https://github.com/YOUR_USERNAME)

---

*Built with Python, FastAPI, Streamlit, and PostgreSQL.*
