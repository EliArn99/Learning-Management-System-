# AcademicFlow: A Comprehensive Django LMS 👋

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
Elevating Education: Seamless Course Management for Modern Universities.

AcademicFlow is a robust, Django-powered Learning Management System (LMS) designed to streamline the entire academic lifecycle within a university environment. It provides a secure, intuitive platform for students and teachers to manage course enrollment, assignments, grading, and communication, all while featuring an essential administrative verification process for user accounts before full access is granted.

---

## Table of Contents

* [About The Project](#about-the-project)
* [Features](#features)
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
* [Usage](#usage)
* [Administrative Approval Flow](#administrative-approval-flow)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
* [Acknowledgments](#acknowledgments)

---

## About The Project

AcademicFlow was developed to simplify the complex administrative and pedagogical tasks inherent in university education. By offering distinct user roles and a critical pre-approval mechanism, it ensures a controlled and secure learning environment. The platform aims to enhance communication, centralize learning resources, and provide clear tracking of academic progress for all stakeholders.

### Built With

* [![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
* [![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
* [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
* HTML5, CSS3, JavaScript
* Bootstrap (or other frontend framework if used)

---

## Features

AcademicFlow provides a rich set of features tailored for university academic management:

* **Custom User Roles & Profiles**:
    * **Students**: Dedicated profiles including `age`, auto-generated `faculty_number` (e.g., F-00001), and `achievements` tracking.
    * **Teachers**: Profiles featuring `education` background and `years of experience`.
    * **Dynamic Profile Management**: Users can view and update their personal profiles.
* **Administrator Approval System**: All new student and teacher registrations are set to `is_approved=False` by default, requiring explicit administrator verification for full platform access. Users see a dedicated "Approval Pending" page until approved.
* **Course Management**: (Elaborate: e.g., create, enroll, view course details, manage sections.)
* **Content Delivery**: (Elaborate: e.g., upload and organize various learning materials like documents, videos, presentations.)
* **Assignment & Grading**: (Elaborate: e.g., instructors can create and distribute assignments; students can submit work; a system for recording and viewing grades.)
* **Quiz Integration**: Students can view and participate in upcoming quizzes assigned to their enrolled courses.
* **Internal Messaging**: (Elaborate: e.g., secure communication channels between students, teachers, and admins.)
* **Secure Authentication**: Robust user login and logout functionalities.
* **Responsive Design**: (If applicable) Ensures optimal viewing experience across different devices.

---

## Getting Started

To get a local copy of AcademicFlow up and running for development or testing, follow these steps.

### Prerequisites

Ensure you have the following software installed on your system:

* **Python 3.9+** (or your specific Python version)
* **pip** (Python package installer, usually comes with Python)
* **PostgreSQL** (or your chosen database system)
* **Git**

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/EliArn99/Learning-Management-System-.git](https://github.com/EliArn99/Learning-Management-System-.git)
    ```
2.  **Navigate to the Project Directory**
    ```bash
    cd Learning-Management-System-
    ```
3.  **Create a Python Virtual Environment (Highly Recommended)**
    ```bash
    python -m venv venv
    ```
4.  **Activate the Virtual Environment**
    * **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```
5.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Make sure you have a `requirements.txt` file generated via `pip freeze > requirements.txt`.*
6.  **Configure Database (PostgreSQL Example)**
    * Create a new PostgreSQL database (e.g., `academicflow_db`).
    * **Create a `.env` file** in the root of your project directory based on a provided `.env.example` (or configure your `settings.py` directly). This file should contain sensitive credentials:
        ```
        # .env (Example content)
        SECRET_KEY='your_super_secret_django_key'
        DEBUG=True

        # Database Configuration
        DB_NAME='academicflow_db'
        DB_USER='your_db_username'
        DB_PASSWORD='your_db_password'
        DB_HOST='localhost'
        DB_PORT='5432'

        # Email Settings (for internal messaging, etc.)
        EMAIL_HOST='smtp.yourprovider.com'
        EMAIL_PORT='587'
        EMAIL_USE_TLS=True
        EMAIL_HOST_USER='your_email@example.com'
        EMAIL_HOST_PASSWORD='your_email_password'
        ```
7.  **Apply Database Migrations**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
8.  **Create an Administrator Superuser**
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create an admin username, email, and password. This account will be able to approve new users.
9.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```
    The application should now be accessible in your web browser at `http://127.0.0.1:8000/`.

---

## Usage

AcademicFlow supports distinct workflows for different user roles:

* **Registration**: New users (students or teachers) can register via the `/register/student/` or `/register/teacher/` routes. Upon successful registration, they are automatically logged in but redirected to a dedicated "Approval Pending" page (`/approval-pending/`).
* **Login**: Access the login page at `/login/`. If an account is pending approval, the user will be redirected to the "Approval Pending" page after login.
* **As an Administrator**:
    * Log in with your superuser credentials.
    * Access the Django admin panel (typically at `http://127.0.0.1:8000/admin/`).
    * From the admin panel, you can manage `CustomUser` accounts, and approve `StudentProfile` and `TeacherProfile` instances by setting their `is_approved` field to `True`.
    * Manage courses, assignments, and other core LMS entities.
* **As a Teacher (Approved)**:
    * Once approved by an administrator, teachers can log in and access their dashboard (e.g., `/dashboards/teacher/`).
    * Create new courses, upload educational content, design assignments and quizzes, and grade student submissions.
    * Manage their own `TeacherProfile`.
* **As a Student (Approved)**:
    * After approval, students can log in and view their dashboard (e.g., `/dashboards/student/`).
    * Enroll in available courses, access lecture materials, submit assignments, take quizzes, and track their academic progress.
    * View upcoming quizzes.
    * Manage their `StudentProfile`.
* **Profile Management**: All approved users can view and edit their respective profiles (e.g., `/profile/` and `/profile/edit/`).

---

## Administrative Approval Flow

A core feature of AcademicFlow is the mandatory administrative approval for all new user accounts.

1.  **User Registration**: A new Student or Teacher signs up. Their `CustomUser` account is created, and a corresponding `StudentProfile` or `TeacherProfile` is linked, with `is_approved` set to `False`.
2.  **Pending Status**: The newly registered user can log in but is immediately redirected to an `approval_pending_view` page, indicating that their account is awaiting administrator review. They cannot access main dashboard functionalities until approved.
3.  **Administrator Action**: An administrator must log into the Django admin interface, navigate to the `Student Profiles` or `Teacher Profiles` section, find the pending user's profile, and manually set `is_approved` to `True`.
4.  **Full Access**: Once approved, the next time the user logs in, they will be redirected to their respective dashboard (e.g., `student_dashboard` or `teacher_dashboard`) and gain full access to the platform's features.

---

## Roadmap

This project is under active development. Here are some planned features and improvements:

* [ ] Implement a comprehensive **course catalog** with search and filtering capabilities.
* [ ] Develop an **in-platform messaging system** for direct communication between students and teachers.
* [ ] Enhance the **quiz module** with various question types, time limits, and automatic grading.
* [ ] Introduce **course discussion forums** for collaborative learning.
* [ ] Create a dedicated **admin dashboard** for easier user approval, statistics, and system management.
* [ ] Implement **email notifications** for new assignments, grades, and course announcements.
* [ ] Integrate **analytics and reporting tools** for instructors to track student performance.
* [ ] Containerize the application using **Docker** for simplified deployment.

See the [open issues](https://github.com/EliArn99/Learning-Management-System-/issues) for a full list of proposed features and known issues.

---

## Contributing

We welcome contributions to AcademicFlow! If you have suggestions or want to contribute code, please follow these steps:

1.  **Fork** the repository.
2.  **Create a new branch** for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  **Commit your changes** (`git commit -m 'feat: Add a new amazing feature'`).
4.  **Push your branch** (`git push origin feature/your-feature-name`).
5.  **Open a Pull Request** against the `main` branch.
    * Please ensure your code adheres to a clean, readable style and includes relevant tests if applicable.

For reporting bugs or suggesting enhancements, please open an issue in the [Issues section](https://github.com/EliArn99/Learning-Management-System-/issues).

---

## License

Distributed under the MIT License. See the `LICENSE` file for more information.

---

## Contact

Eli Arnaytska - eli_arnaytska@abv.bg
Project Link: [https://github.com/EliArn99/Learning-Management-System-](https://github.com/EliArn99/Learning-Management-System-)

---

## Acknowledgments

* [Django Project](https://www.djangoproject.com/)
* [PostgreSQL](https://www.postgresql.org/)
* [Shields.io](https://shields.io/) (for badges)
* [Font Awesome](https://fontawesome.com/) (for icons)
