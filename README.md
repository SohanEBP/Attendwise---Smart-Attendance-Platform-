# AttendWise – Smart Attendance Management System

A production-ready, full-stack attendance management web application built with Django, Bootstrap 5, SQLite, and Chart.js.

---

## Features

### Admin
- Dashboard with real-time stats, charts, and low-attendance alerts
- Full CRUD for students, teachers, subjects, classes, and departments
- Attendance reports with filters (class, subject, date range, student name)
- Export reports as CSV or PDF (requires `reportlab`)

### Teacher
- Dashboard with subject-wise attendance statistics and 7-day chart
- Mark attendance for any class and subject with bulk present/absent toggle
- View and filter own attendance records

### Student
- Personal dashboard with overall and subject-wise attendance percentage
- Low-attendance warning when below 75%
- Filter attendance by subject and date
- Download personal attendance report as CSV

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Backend     | Django 4.2              |
| Database    | SQLite                  |
| Frontend    | Bootstrap 5 + Chart.js  |
| Forms       | django-crispy-forms     |
| PDF Export  | reportlab               |
| Language    | Python 3.10+            |

---

## Installation

### 1. Clone / Extract the project

```bash
# If you cloned from GitHub:
git clone <your-repo-url>
cd attendwise

# Or just extract the zip and cd into the folder
cd attendwise
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. (Optional) Load demo data

This creates sample admin, teachers, students, classes, subjects, and 30 days of attendance records.

```bash
python manage.py create_demo_data
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser at: **http://127.0.0.1:8000**

---

## Demo Credentials

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Admin   | admin     | admin123     |
| Teacher | teacher1  | Teacher@123  |
| Student | student1  | Student@123  |

---

## Project Structure

```
attendwise/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3              (created after migrate)
├── attendwise/             # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── attendance/             # Main app
│   ├── models.py           # DB models (User, Student, Teacher, Subject, Attendance…)
│   ├── views.py            # All view logic
│   ├── urls.py             # URL routing
│   ├── forms.py            # Django forms
│   ├── decorators.py       # Role-based access decorators
│   └── management/
│       └── commands/
│           └── create_demo_data.py
├── templates/
│   ├── base.html           # Dashboard base layout (sidebar + topbar)
│   ├── base_public.html    # Public pages base (navbar + footer)
│   ├── home.html
│   ├── about.html
│   ├── contact.html
│   ├── auth/               # login, register, forgot_password
│   ├── admin_panel/        # Admin dashboard and CRUD templates
│   ├── teacher/            # Teacher dashboard, mark attendance
│   └── student/            # Student dashboard, attendance view
├── static/
│   ├── css/main.css        # All custom styles
│   └── js/main.js          # Sidebar toggle, AJAX, animations
└── media/                  # Uploaded files (profile pictures etc.)
```

---

## Key URLs

| URL                    | Description                     |
|------------------------|---------------------------------|
| `/`                    | Home page                       |
| `/login/`              | Login                           |
| `/register/`           | Register                        |
| `/dashboard/`          | Auto-redirects by role          |
| `/admin-dashboard/`    | Admin dashboard                 |
| `/admin/students/`     | Manage students                 |
| `/admin/teachers/`     | Manage teachers                 |
| `/admin/subjects/`     | Manage subjects                 |
| `/admin/classes/`      | Manage classes                  |
| `/admin/reports/`      | Attendance reports              |
| `/teacher-dashboard/`  | Teacher dashboard               |
| `/teacher/mark-attendance/` | Mark attendance            |
| `/student-dashboard/`  | Student dashboard               |
| `/admin/`              | Django admin panel              |

---

## Future Improvements

- QR code attendance marking
- Email notifications for low attendance
- Dark mode toggle
- REST API with JWT authentication (Django REST Framework)
- Docker support
- Parent portal to view student attendance
- Push notifications

---

## Screenshots

### Login Page
![Login](screenshots/login.png)

### Admin Dashboard
![Dashboard](screenshots/dashboard.png)

### Attendance Reports
![Reports](screenshots/reports.png)

## 👨‍💻 Author

### Sohan Saha
Computer Science Engineering (IoT & Cybersecurity)
Heritage Institute of Technology


## License

MIT — Free to use for personal, academic, and portfolio projects.
