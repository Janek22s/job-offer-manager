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
python job_board/management_cli.py
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

5. Create a PostgreSQL database:
```bash 
psql -U postgres -c "CREATE DATABASE job_offer_manager;"
```
You can also create the database using pgAdmin.

6. Create a .env file in the repository root directory:
```bash
DJANGO_SECRET_KEY=replace_with_a_random_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=job_offer_manager
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgresql_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```
Replace the PostgreSQL username and password with your local database credentials.

7. Apply database migrations:
```bash
python job_board/manage.py migrate
```

8. Load the additional PostgreSQL indexes and triggers:
```bash
psql -U postgres -d job_offer_manager -f db_files/indexes.sql
psql -U postgres -d job_offer_manager -f db_files/triggers.sql
```

9. Optionally generate demo data for local development:
```bash
python job_board/manage.py seed_demo
```
To recreate the demo data:
```bash
python job_board/manage.py seed_demo --reset
```
All generated demo accounts use Demo123!ChangeMe as their default password.

10. Create an administrator account:
```bash
python job_board/manage.py createsuperuser
```

11. Start the development server:
```bash
python job_board/manage.py runserver
```
The application will be available at:
```bash
http://127.0.0.1:8000/
```

## Running Tests

Run the test suite from the repository root directory:
```bash
python job_board/manage.py test
```

## PostgreSQL Database Initialization
Django migrations create the application's database tables. After running the migrations, load the additional PostgreSQL indexes and triggers:

python job_board/manage.py migrate
```bash
psql -U postgres -d job_offer_manager -f db_files/indexes.sql
psql -U postgres -d job_offer_manager -f db_files/triggers.sql
```

Replace postgres and job_offer_manager with the values configured in your .env file when using different database credentials.

Do not run db_files/schema.sql after Django migrations. The file contains a standalone SQL representation of the database schema and would attempt to create tables that already exist.

## Demo Data

The project includes a Django management command that generates sample data for local development and testing.

The command creates:

4 companies
5 candidate accounts
4 employer accounts
1 administrator account
5 candidate profiles and CV records
4 employer profiles
10 job offers
Sample saved offers
Sample job applications with different statuses

To generate the demo data, run the following command from the repository root:
```bash
python job_board/manage.py seed_demo
```
All generated demo users use the following default password:
```bash
Demo123!ChangeMe
```
A different password can be assigned using the --password option:
```bash
python job_board/manage.py seed_demo --password "YourDemoPassword123!"
```
To delete previously generated demo records and recreate them, use:
```bash
python job_board/manage.py seed_demo --reset
```
The command uses the Django ORM and set_password(), so user passwords are securely hashed using Django's configured password hasher before being stored in PostgreSQL.

The generated CV records contain example file paths, but the command does not create physical PDF files. To test CV downloads, corresponding PDF files must be added manually to the configured media directory.

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