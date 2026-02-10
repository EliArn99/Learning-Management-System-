# Learning Management System (LMS) 🎓

A Django-powered Learning Management System built for a university-style workflow: role-based access (Student/Teacher), administrative approval, paid enrollments, assignments, quizzes, internal messaging, and dashboards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4%2B-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)

---

## Table of Contents
- [About](#about)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Option A: Docker (Recommended)](#option-a-docker-recommended)
  - [Option B: Local Setup (venv)](#option-b-local-setup-venv)
- [Usage](#usage)
- [Administrative Approval Flow](#administrative-approval-flow)
- [Environment Variables](#environment-variables)
- [Production Notes](#production-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## About

**Learning Management System (LMS)** is a full-stack Django project designed to support an academic lifecycle:
- Students enroll in courses (with paid access support)
- Teachers create/manage course content, assignments, and quizzes
- Students submit work and take quizzes
- Teachers grade submissions and track progress
- Users communicate via internal messaging
- An **admin approval workflow** ensures controlled access for newly registered accounts

---

## Key Features

### ✅ Authentication & Roles
- Custom user roles: **Student** / **Teacher**
- Profile pages with role-specific data
- Access control checks enforced on the server side

### ✅ Administrative Approval System
- New accounts start with `is_approved=False`
- Unapproved users are redirected to an “Approval Pending” page
- Admin approves students/teachers via Django Admin

### ✅ Course & Enrollment
- Teachers create courses
- Students can access course content only if enrolled and (optionally) **paid**
- Enrollment logic includes payment flags (`is_paid`, `transaction_id`)

### ✅ Assignments & Grading
- Teachers create assignments (due dates validated)
- Students upload submissions (tamper-proof forms)
- Teachers grade submissions with feedback
- Teacher submissions overview with filters (graded/pending)

### ✅ Quizzes
- Quizzes tied to courses with availability window
- Student access is restricted by enrollment + active quiz window
- Attempts track:
  - `start_time`
  - selected randomized questions
  - stable time limit enforcement
- Supports question types including **Open Text (OT)**

### ✅ Messaging
- Inbox/sent views
- Bulk “mark as read” for performance
- Allowed recipients controlled via form validation
- Admin actions for read/unread & soft delete/restore

### ✅ Dashboards
- **Teacher dashboard**: courses, unique paid students, submissions stats, recent submissions, unread messages
- **Student dashboard**: paid courses, upcoming assignments/quizzes, quiz completion progress, unread messages

---

## Tech Stack
- **Backend:** Python, Django
- **Database:** PostgreSQL (recommended)
- **Frontend:** HTML, CSS, JavaScript
- **Other:** Docker / docker-compose (optional but recommended)

---

## Project Structure

High-level apps:
- `users/` – authentication, roles, profiles, approval flow
- `courses/` – courses, modules, enrollments (paid access flags)
- `assignments/` – assignments, submissions, grading
- `quizz/` – quizzes, questions/answers, attempts, results
- `messaging/` – internal messaging
- `dashboards/` – teacher/student dashboards + static pages

---

## Getting Started

### Prerequisites
- Python 3.10+ (or your project’s version)
- PostgreSQL (recommended)
- Git
- Docker (optional, recommended)

---

## Option A: Docker (Recommended)

1) **Clone repository**
```bash
git clone https://github.com/EliArn99/Learning-Management-System-.git
cd Learning-Management-System-
---

**Create .env**
Create a .env file in the project root (see example below).

**Build & run**
docker-compose up --build -d


Run migrations

docker-compose exec web python manage.py migrate


Create admin user

docker-compose exec web python manage.py createsuperuser


Open

App: http://127.0.0.1:8000/

Admin: http://127.0.0.1:8000/admin/

Option B: Local Setup (venv)

Clone repository

git clone https://github.com/EliArn99/Learning-Management-System-.git
cd Learning-Management-System-


Create and activate venv

python -m venv venv


Windows:

.\venv\Scripts\activate


macOS/Linux:

source venv/bin/activate


Install dependencies

pip install -r requirements.txt


Set environment variables
Create .env (example below) or export variables in your shell.

Migrate + run

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver


Open: http://127.0.0.1:8000/

Usage
Registration

Student registration: /register/student/

Teacher registration: /register/teacher/

After registration, users can log in but remain restricted until approved.

Admin

Login to /admin/

Approve profiles:

StudentProfile.is_approved = True

TeacherProfile.is_approved = True

Teacher (Approved)

Create/manage courses

Create assignments and grade submissions

Create quizzes and manage questions/answers

View teacher dashboard

Student (Approved)

Access paid/enrolled courses

Submit assignments

Take quizzes

View student dashboard

Administrative Approval Flow

User registers (Student/Teacher) → profile created with is_approved=False

User can log in but is redirected to Approval Pending

Admin approves the profile via Django Admin

User gets full access on next login

Environment Variables

Example .env:

SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=lms_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=no-reply@lms.local

Production Notes

Before deploying:

Set DEBUG=False

Configure ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS

Use secure cookies + HTTPS:

SESSION_COOKIE_SECURE=True

CSRF_COOKIE_SECURE=True

Store secrets in environment variables (never commit .env)

Add proper logging (avoid logging sensitive payloads)

Add tests (especially for permissions/enrollment/payment gating)

Add monitoring (Sentry/Prometheus optional)

Roadmap

 Add pagination to inbox/sent and submissions lists

 Add notifications (email + in-app) for grades/quizzes/assignments

 Add course catalog search & filters

 Add discussion threads per course/module

 Improve quiz reporting/analytics for teachers

 Add CI (lint + tests) via GitHub Actions

 Harden payment flow with webhook verification (if payments are enabled)

Contributing

Fork the repo

Create branch:

git checkout -b feature/your-feature


Commit using conventional messages (feat:, fix:, refactor:)

Push and open PR

License

MIT License. See LICENSE.

Contact

Eli Arnautska
Email: eli_arnaytska@abv.bg

Repository: https://github.com/EliArn99/Learning-Management-System-


