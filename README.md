# Learning Management System (LMS) 📚

A comprehensive Django-powered Learning Management System for universities. It streamlines course enrollment, assignments, grading, and communication. All new accounts require **administrator approval** before gaining full access.

---

## 🚀 Features

* **Custom User Roles**: Students, Teachers, Admins
* **Admin Approval Flow**: Accounts pending until approved
* **Course Management**: Create, enroll, and organize courses
* **Assignments & Grading**
* **Quizzes**: Participate in upcoming quizzes
* **Messaging**: Internal communication system
* **Dashboards**: Personalized views for students and teachers
* **Responsive Design**

---

## 🛠️ Built With

* Python 3.9+
* Django
* PostgreSQL
* HTML5, CSS3, JavaScript, Bootstrap
* Docker (optional)

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/EliArn99/Learning-Management-System-.git
cd Learning-Management-System-
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

* **Windows**: `venv\Scripts\activate`
* **Linux/Mac**: `source venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database

Create a PostgreSQL database, then add credentials in a `.env` file:

```env
SECRET_KEY=your_secret_key
DEBUG=True
DB_NAME=academicflow_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the server

```bash
python manage.py runserver
```

Access the app at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🐳 Run with Docker (optional)

```bash
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## 👥 User Roles

### Students

* Register at `/register/student/`
* View dashboard, enroll in courses, submit assignments & quizzes

### Teachers

* Register at `/register/teacher/`
* Create/manage courses, assignments, and quizzes

### Admins

* Approve user accounts
* Manage all courses, users, and content from the Django admin panel

---

## 🔒 Approval Flow

1. User registers (Student/Teacher)
2. Status: **Pending Approval**
3. Admin sets `is_approved=True` in Django admin
4. User gains full access

---

## 📸 Screenshots (to add)

* Login Page
* Student Dashboard
* Teacher Dashboard
* Admin Panel

---

## 📌 Roadmap

* Course catalog with search
* Enhanced quiz module
* Discussion forums
* Email notifications
* Analytics for teachers

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/xyz`)
3. Commit changes (`git commit -m 'feat: add xyz'`)
4. Push branch (`git push origin feature/xyz`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License.

---

## 📬 Contact

**Author:** Eli Arnautska
📧 Email: [eli_arnaytska@abv.bg](mailto:eli_arnaytska@abv.bg)
🔗 Project: [Learning-Management-System](https://github.com/EliArn99/Learning-Management-System-)

---

## 🙏 Acknowledgments

* Django 💚
* PostgreSQL 🐘
* Docker 🐳
* Shields.io 🛡️
* Font Awesome ✨
