# IQPlus - Online IQ Test Platform

A Django-based web application for administering and taking IQ tests. The platform provides separate interfaces for administrators and students with features for test management, question banking, and result tracking.

## Features

- **Admin Dashboard**: Create and manage tests and questions
- **Question Bank**: Maintain a centralized repository of test questions
- **Student Dashboard**: View available tests and attempt them
- **Test Management**: Track student attempts and results
- **Result Analysis**: Detailed performance metrics for each test attempt
- **User Authentication**: Secure login system for both admins and students

## Project Structure

```
iqplus/
├── my_iq_test/              # Main Django project settings
│   ├── settings.py          # Project configuration
│   ├── urls.py              # URL routing
│   ├── asgi.py              # ASGI config
│   └── wsgi.py              # WSGI config
│
├── myapp/                   # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View logic
│   ├── admin.py             # Admin configuration
│   ├── tests.py             # Unit tests
│   └── migrations/          # Database migrations
│
├── templates/               # HTML templates
│   ├── admin/               # Admin interface templates
│   └── student/             # Student interface templates
│
├── db.sqlite3               # SQLite database
├── manage.py                # Django management script
└── README.md                # This file
```

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. **Clone the repository** (if applicable)
   ```bash
   git clone <repository-url>
   cd iqplus
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install django
   ```

5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

## Running the Server

Start the Django development server:

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Access Points

- **Admin Login**: Navigate to the admin login page to manage tests and questions
- **Student Login**: Students can register and log in to view and attempt tests
- **Admin Dashboard**: View, create, and manage tests
- **Question Bank**: Add and manage IQ test questions
- **Student Dashboard**: Browse available tests and track results

## Database Models

The application includes the following main models:

- **Student**: Student user information and authentication
- **Admin**: Admin user information and authentication
- **School**: School information linked to admins
- **Test**: Test information and configuration
- **Question**: IQ test questions and options
- **StudentTest**: Linking students to tests they can attempt
- **Attempt**: Tracking student test attempts and results

## Creating a Superuser (Django Admin)

To access Django's built-in admin panel:

```bash
python manage.py createsuperuser
```

Then visit `http://127.0.0.1:8000/admin/` with your credentials.

## Making Migrations

After modifying models, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing

Run the test suite:

```bash
python manage.py test
```

## Project Links

- **Admin**: http://127.0.0.1:8000/admin/
- **Student**: http://127.0.0.1:8000/student/
- **Home**: http://127.0.0.1:8000/

## Development Notes

- This is a development server. For production, use a production WSGI/ASGI server
- The database is SQLite (suitable for development; use PostgreSQL for production)
- Static files need to be collected before deployment (`python manage.py collectstatic`)

## Troubleshooting

**Django module not found**
- Ensure virtual environment is activated
- Verify Django is installed: `pip list`

**Database errors**
- Run migrations: `python manage.py migrate`
- Check database file permissions

**Server won't start**
- Check if port 8000 is already in use
- Run on a different port: `python manage.py runserver 8080`

## License

This project is proprietary.

## Support

For issues or questions, contact the development team.
