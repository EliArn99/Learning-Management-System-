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
