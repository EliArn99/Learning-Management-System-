Learning Management System (LMS) 🎓
A modern, feature-rich educational platform built with Django that empowers universities and educational institutions with a complete digital learning ecosystem.

https://img.shields.io/badge/Demo-Coming_Soon-blue
https://img.shields.io/badge/Python-3.10%252B-green
https://img.shields.io/badge/Django-4.x-darkgreen
https://img.shields.io/badge/PostgreSQL-Supported-blue
https://img.shields.io/badge/License-MIT-yellow
https://img.shields.io/badge/Docker-Ready-blue

✨ Overview
The Learning Management System (LMS) is a comprehensive Django-powered platform designed to support the complete academic lifecycle. Built with scalability and security in mind, it provides role-based workflows for students and teachers, administrative controls, and a seamless learning experience.

📋 Table of Contents
🌟 Key Features

🛠️ Tech Stack

📁 Project Structure

🚀 Quick Start

🐳 Docker Deployment (Recommended)

💻 Local Development

🎯 Usage Guide

🔐 Administrative Workflow

⚙️ Configuration

🌐 Production Deployment

🗺️ Roadmap

🤝 Contributing

📄 License

📞 Contact

🌟 Key Features
👥 User Management & Security
Dual Role System: Student & Teacher profiles with distinct permissions

Admin Approval Workflow: All new accounts require administrative approval

Secure Authentication: Django's robust authentication system with custom extensions

📚 Course Management
Course Creation: Teachers can design and manage comprehensive courses

Smart Enrollment: Supports both free and paid enrollment models

Content Organization: Modular course structure with progressive access

📝 Assignments & Assessment
Assignment Creation: Teachers can create assignments with due dates and instructions

Digital Submissions: Secure file upload system with anti-tampering measures

Grading System: Efficient grading interface with feedback capabilities

🧠 Quizzes & Exams
Flexible Quizzes: Support for multiple question types including Open Text

Time Management: Enforced time limits and attempt tracking

Randomization: Question randomization for fair assessment

💬 Communication
Internal Messaging: Secure messaging system between users

Notification Ready: Architecture prepared for email/in-app notifications

Bulk Operations: Efficient message management with bulk actions

📊 Dashboards
Teacher Dashboard: Course analytics, student progress, and grading overview

Student Dashboard: Course access, upcoming deadlines, and progress tracking

Real-time Stats: Dynamic statistics and performance metrics

🛠️ Tech Stack
Component	Technology
Backend Framework	Django 4.x
Database	PostgreSQL (recommended)
Frontend	HTML5, CSS3, JavaScript
Containerization	Docker & Docker Compose
Environment	Python 3.10+
Version Control	Git
📁 Project Structure
text
Learning-Management-System/
├── users/           # Authentication, profiles, approval system
├── courses/         # Course creation, modules, enrollments
├── assignments/     # Assignments, submissions, grading
├── quizz/          # Quizzes, questions, attempts, results
├── messaging/      # Internal messaging system
├── dashboards/     # Role-specific dashboards
├── static/         # CSS, JavaScript, images
├── templates/      # HTML templates
└── manage.py       # Django management script
🚀 Quick Start
Prerequisites
Python 3.10+ or Docker

PostgreSQL (for local setup)

Git

🐳 Docker Deployment (Recommended)
bash
# 1. Clone the repository
git clone https://github.com/EliArn99/Learning-Management-System-.git
cd Learning-Management-System-

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your settings

# 3. Start the application
docker-compose up --build -d

# 4. Apply database migrations
docker-compose exec web python manage.py migrate

# 5. Create a superuser
docker-compose exec web python manage.py createsuperuser

# 6. Access the application
# App:      http://localhost:8000
# Admin:    http://localhost:8000/admin
💻 Local Development
bash
# 1. Clone and navigate
git clone https://github.com/EliArn99/Learning-Management-System-.git
cd Learning-Management-System-

# 2. Set up virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database settings

# 5. Set up database and run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 6. Access at http://localhost:8000
🎯 Usage Guide
For Administrators
Access Admin Panel at /admin/

Approve New Users via the approval interface

Monitor System through comprehensive admin controls

For Teachers
Register as a teacher at /register/teacher/

Await Approval from administrators

Create Courses and manage content

Create Assignments & Quizzes for students

Grade Submissions and provide feedback

Access Analytics through the teacher dashboard

For Students
Register as a student at /register/student/

Await Approval from administrators

Browse & Enroll in available courses

Complete Assignments and submit work

Take Quizzes within specified timeframes

Track Progress through the student dashboard

🔐 Administrative Workflow





⚙️ Configuration
Environment Variables (.env)
bash
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration
DB_NAME=lms_database
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-specific-password
DEFAULT_FROM_EMAIL=noreply@lms.example.com
🌐 Production Deployment
Critical Security Steps
Disable Debug Mode

python
DEBUG = False
Configure Security Settings

python
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
CSRF_TRUSTED_ORIGINS = ['https://your-domain.com']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
Use Environment Variables for all secrets

Enable Proper Logging

Set Up HTTPS with a valid SSL certificate

Performance Considerations
Configure database connection pooling

Implement caching with Redis/Memcached

Use a CDN for static files

Set up monitoring (Sentry, Prometheus)

🗺️ Roadmap
🎯 Short Term (Next Release)
Pagination for inbox and submission lists

Email notifications for grades and deadlines

Course catalog with search and filters

🔮 Medium Term
Discussion forums per course

Enhanced quiz analytics for teachers

Mobile-responsive improvements

🚀 Long Term
REST API for mobile applications

Live video class integration

Advanced payment gateway integration

Gamification features (badges, leaderboards)

CI/CD pipeline with GitHub Actions

🤝 Contributing
We welcome contributions! Here's how you can help:

Fork the Repository

Create a Feature Branch

bash
git checkout -b feature/amazing-feature
Commit Your Changes

bash
git commit -m 'feat: add amazing feature'
Push to Your Branch

bash
git push origin feature/amazing-feature
Open a Pull Request

Contribution Guidelines
Follow existing code style and conventions

Write clear commit messages

Add tests for new features

Update documentation as needed

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

text
MIT License

Copyright (c) 2024 Eli Arnautska

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
📞 Contact & Support
Eli Arnautska
📧 Email: eli_arnaytska@abv.bg
🐙 GitHub: @EliArn99
📂 Repository: Learning-Management-System
