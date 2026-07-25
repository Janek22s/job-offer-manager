# Job Offer Manager

Job Offer Manager is a Django-based recruitment platform that connects candidates with employers. It allows users to publish and browse job offers, submit applications, upload CVs, manage recruitment statuses, and perform administrative operations through both a web interface and a command-line tool.

# About the Project

Job Offer Manager is a web application designed to support the recruitment process for candidates, employers, and administrators.

Candidates can browse job offers, save selected listings, upload their CVs, submit applications, and track their application status. Employers can publish and manage job offers, review submitted applications, and update candidates’ recruitment statuses. Administrators can manage users, companies, job offers, and other system data through a dedicated management interface.

The project was built with Python, Django, Django REST Framework, and PostgreSQL. It includes a REST API, role-based access control, custom database constraints, indexes, and PostgreSQL triggers used to maintain data consistency.

An additional command-line management tool was created to perform administrative operations, generate statistics, and manage data directly from the terminal.

The main goal of the project was to develop a complete recruitment platform while improving practical skills in backend development, relational database design, authentication, authorization, API development, automated testing, and SQL.

## Features

### Candidate
- Creating an account
- Browsing job offers
- Uploading a CV
- Applying for jobs
- Saving offers
- Updating profile

### Employer
- Creating and updating job offers
- Managing applications
- Updating application statuses
- Updating profile

### Administrator
- Managing users
- Managing companies
- Viewing statistics

## Technologies Used
- Python
- Django
- Django REST Framework
- PostgreSQL
- HTML
- CSS
- Git and GitHub

## Management CLI

The project includes an interactive command-line management console with role-based permissions. It allows administrators and employers to manage users, companies, job offers and applications, view system statistics, inspect registered members, and display available API endpoints directly from the terminal.

Run the console with:
```bash
python management_cli.py
```

## Installation
1. Clone the repository
```bash
git clone https://github.com/Janek22s/job-offer-manager.git
cd job-offer-manager
```

2. Create a virtual environment
```bash
python -m venv .venv
```

3. Activate the environment
Windows:
```bash
.venv\Scripts\activate
```
Linux/macOS:
```bash
source .venv/bin/activate
```

4. Install the required dependencies:
```bash 
pip install -r requirements.txt
```

5. Create a PostgreSQL database for the application, including triggers, indexes, and sample data as described in the PostgreSQL Database Initialization section.

6. Create a .env file based on .env.example and configure the required environment variables.

7. Apply database migrations:
```bash
python manage.py migrate
```

8. Create an administrator account:
```bash
python manage.py createsuperuser
```

9. Start the development server:
```bash
python manage.py runserver
```
The application will be available at:
```bash
http://127.0.0.1:8000/
```

## Running Tests

Run the test suite with:

```bash
python manage.py test
```

## PostgreSQL Database Initialization

After applying the Django migrations, load the additional PostgreSQL configuration files located in the db_files directory.

These files create the required database indexes and triggers and optionally insert sample data.

Run the SQL files in the following order:

```bash
psql -U <database_user> -d <database_name> -f db_files/indexes.sql
psql -U <database_user> -d <database_name> -f db_files/triggers.sql
psql -U <database_user> -d <database_name> -f db_files/sample_data.sql
```

Replace <database_user> and <database_name> with the values configured in your .env file.

The sample data file is optional and should only be loaded if you want to populate the application with demonstration data.

The complete database setup order is:

```bash
python manage.py migrate
psql -U <database_user> -d <database_name> -f db_files/indexes.sql
psql -U <database_user> -d <database_name> -f db_files/triggers.sql
psql -U <database_user> -d <database_name> -f db_files/sample_data.sql
```

## REST API

The project provides a REST API built with Django REST Framework.

### Base URL
http://127.0.0.1:8000/api/

### Authentication

Protected endpoints require authentication. Depending on the configured authentication method, the client must provide a valid session.

### API Endpoints
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| **POST** | `api/auth/register/` | Registers a new user account. | Public |
| **POST** | `api/auth/login/` | Authenticates a user and starts a session. | Public |
| **POST** | `api/auth/logout/` | Logs out the authenticated user and ends the current session. | User |
| **GET** / **PATCH** / **DELETE** | `api/users/me/` | Displays / patches / deletes user data. | Users |
| **GET** | `api/admin/users/` | Displays data for all users. | Admin |
| **GET** / **PATCH** / **DELETE** | `api/admin/users/{user_id}/` | Displays / patches / deletes user data. | Admin |
| **GET** / **PATCH** | `api/candidates/me/` | Displays / patches candidate data. | Candidate |
| **GET** | `api/candidates/{candidate_id}/` | Displays candidate data. | User |
| **GET** / **PATCH** | `api/employers/me/` | Displays / patches employer data. | Employer |
| **GET** | `api/employers/{employer_id}/` | Displays employer data. | User |
| **GET** | `api/companies/` | Displays data for all companies. | User |
| **GET** | `api/companies/{company_id}/` | Displays company data. | User |
| **PATCH** | `api/companies/patch/{company_id}/` | Patches company data. | Employer, Admin |
| **DELETE** | `api/admin/companies/delete/{company_id}/` | Deletes company. | Admin |
| **POST** | `api/admin/companies/post/` | Creates new company. | Admin |
| **GET** | `api/companies/{company_id}/job_offers/` | Displays the company's job offers. | User |
| **GET** | `api/companies/{company_id}/employers/` | Displays the company's employers. | User |
| **GET** | `api/job-offers/` | Displays all job offers data. | User |
| **GET** | `api/job-offers/{offer_id}/` | Displays offer's data. | User |
| **PATCH** / **DELETE** | `api/job-offers/{offer_id}/edit/` | Patches / deletes offer's data. | Employer |
| **POST** | `api/job-offers/create/` | Creates a new job offer. | Employer |
| **POST** | `api/admin/job-offers/create/{company_id}/{employer_id}/` | Creates a new job offer. | Admin |
| **GET** | `api/employers/me/job-offers/` | Displays job offers created by the employer. | Employer |
| **GET** | `api/candidates/me/applications/` | Displays candidate's applications. | Candidate |
| **POST** | `api/candidates/me/applications/create/{offer_id}/` | Creates candidate's applications. | Candidate |
| **GET** | `api/employers/me/applications/` | Displays applications sent to employer's offers. | Employer |
| **PATCH** | `api/employers/me/applications/{offer_id}/{candidate_id}/{cv_id}/status/` | Changes status of candidate's application. | Employer |
| **GET** / **POST** | `api/candidates/me/cvs/` | Displays / uploads a PDF CV for the candidate. | Candidate |

## Future Improvements
1. Docker configuration
2. Improved test coverage
3. Email notifications

## Author
Jan Piwowarczyk