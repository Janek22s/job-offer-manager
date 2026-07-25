import os
import psycopg
import django
import time
from textwrap import wrap
from psycopg import sql, Error
from tabulate import tabulate
from datetime import date, datetime
from getpass import getpass

DB_NAME = ''        # database name
DB_PASSWORD = ''    # database password
PORT_NUMBER = 5432

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection, transaction, IntegrityError, DatabaseError
from django.contrib.auth.hashers import make_password

Users = get_user_model()

def connect():
    return psycopg.connect(
        host="localhost",
        dbname=DB_NAME,
        user="postgres",
        password=DB_PASSWORD,
        port=PORT_NUMBER
    )

def clear():
    os.system("cls" if os.name == "nt" else "clear")

class OfferNotFoundError(Exception):
    pass

class CompanyNotFoundError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class ApplicationNotFoundError(Exception):
    pass

class App:
    APP_ROLES = ['Viewer', 'Employer', 'Admin']
    
    ACTIONS = {
        "Viewer": {
            "offers.view",
            "applications.view",
            "stats.view",
            "api.view",
            "members.view",
        },
        "Employer": {
            "offers.view",
            "offers.add",
            "offers.change",
            "offers.delete",
            "applications.view",
            "applications.change_status",
            "stats.view",
            "members.view",
        },
        "Admin": {
            "users.view",
            "users.add",
            "users.change",
            "users.delete",

            "companies.view",
            "companies.add",
            "companies.change",
            "companies.delete",

            "offers.view",
            "offers.add",
            "offers.change",
            "offers.delete",

            "applications.view",
            "applications.change_status",

            "stats.view",
            "api.view",
            "members.view",
        }
    }

    def __init__(self):
        self.role = None
        self.company_id = None
        self.employer_id = None
        self.conn = connect()

    def set_role(self, role):
        if role not in self.APP_ROLES:
            raise ValueError("Invalid application role.")

        self.role = role

    def set_company(self, company_id):
        if self.role != "Employer":
            raise ValueError("A company can be assigned only to an employer.")

        self.validate_company(company_id)
        self.company_id = int(company_id)

    def has_permission(self, action):
        if self.role is None:
            return False

        return action in self.ACTIONS[self.role]

    def validate_offer(self, offer_id):
        if not offer_id.isdigit():
            raise ValueError("Offer id must be a number.")

        query = """SELECT 1 FROM job_offers o WHERE o.id = %s"""
        
        with self.conn.cursor() as cur:
            cur.execute(query, (offer_id,))
            offer = cur.fetchone()

            if offer is None:
                raise OfferNotFoundError("Offer was not found.")

    def validate_company(self, company_id):
        if not company_id.isdigit():
            raise ValueError("Company id must be a digit.")

        query = """SELECT 1 FROM companies c WHERE c.id = %s"""
        
        with self.conn.cursor() as cur:
            cur.execute(query, (company_id,))
            company = cur.fetchone()

            if company is None:
                raise CompanyNotFoundError("Company was not found.")

    def validate_employer(self, employer_id):
        if not employer_id.isdigit():
            raise ValueError("Employer id must be a digit.")

        query = """SELECT company_id FROM employers e WHERE e.id = %s"""
        
        with self.conn.cursor() as cur:
            cur.execute(query, (employer_id,))
            employer = cur.fetchone()

        if employer is None:
            raise ValueError("Employer was not found.")

        if self.role == "Employer" and employer[0] != self.company_id:
            raise ValueError("Employer does not belong to the selected company.")

        if self.role == "Employer" and not self.employer_id:
            self.employer_id = int(employer_id)

class UsersService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query = """
                SELECT u.id, u.email, u.phone_number, u.role, u.is_active, u.is_staff, u.is_superuser, u.last_login
                FROM users u
                """
        with self.conn.cursor() as cur:
            cur.execute(query)
            users = cur.fetchall()

            if not users:
                print("\nNO USERS.\n")
                return

            headers = [
                "ID",
                "Email", 
                "Phone number",
                "Role",
                "Is active",
                "Is staff",
                "Is superuser",
                "Last login"
            ]

            table_rows = []

            for user in users:
                id, email, phone_number, role, is_active, is_staff, is_superuser, last_login = user

                table_rows.append([
                    id,
                    email,
                    phone_number,
                    role,
                    is_active,
                    is_staff,
                    is_superuser,
                    last_login
                ])

            print("\nUSERS\n")
            print(
                tabulate(
                    table_rows,
                    headers=headers,
                    tablefmt="rounded_grid",
                    stralign="left",
                    numalign="right",
                )
            )
    
    def add(self):
        try:
            roles = ['Candidate', 'Employer', 'Admin']

            print("\nCREATE USER")
            print("Provide:")

            email = input("Email: ").strip().lower()
            phone_number = input("Phone number: ").strip()
            role = input(f"Choose role from {', '.join(roles)}: ").strip()
            password1 = getpass("Password: ")
            password2 = getpass("Repeat password: ")

            while role not in roles:
                print(f"Choose role from {', '.join(roles)}")

                role = input("Enter a valid role or 0 if you want to exit: ")
                if role == "0":
                    raise ValueError
                
            company_id = None
            if role == "Employer":
                company_id = input("Enter company id: ")
                self.check_company(company_id)

                company_id = int(company_id)

            with transaction.atomic():
                password = self.validate_password(password1, password2, hash_password=False)

                self.check_email(email)

                phone_number = self.validate_phone_number(phone_number)
                self.check_phone_number(phone_number)

                with connection.cursor() as cur:
                    if role == "Admin":
                        user = Users.objects.create_superuser(
                            email=email,
                            password=password,
                            phone_number=phone_number,
                        )
                    else:
                        user = Users.objects.create_user(
                                email=email,
                                password=password,
                                phone_number=phone_number,
                                role=role,
                            )
                        
                        if role == "Candidate":
                            candidate_query = """
                                            INSERT INTO candidates(user_id)
                                            VALUES(%s) 
                                            """
                            
                            cur.execute(candidate_query, (user.id,))

                        if role == "Employer":
                            employer_query = """
                                            INSERT INTO employers(user_id, company_id)
                                            VALUES(%s, %s) 
                                            """
                            
                            cur.execute(employer_query, (user.id, company_id))

                    self.conn.commit()
                print("\nUSER CREATED\n")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except CompanyNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
        
        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def change(self):
        try:
            with self.conn.cursor() as cur:
                user_id = input("Provide id of user you want to change: ")

                if not user_id.isdigit():
                    raise ValueError("User id must be a number.")
                
                user_query = f"""
                        SELECT *
                        FROM users
                        WHERE id = %s
                        """
                
                cur.execute(user_query, (user_id,))
                user = cur.fetchone()

                if user is None:
                    raise UserNotFoundError(f"User with ID {user_id} was not found.")
                
                columns = ["email", "phone_number", "role", "password", "is_active"]

                print("Choose the column you want to change, from: ")
                print(", ".join(columns))
                col = input()
                if col not in columns:
                    raise ValueError("Invalid column.")

                new_value = input("Provide new data for this column: ")
                    
                if col == "password":
                    repeated_password = input("Repeat password: ")
                    new_value = self.validate_password(new_value, repeated_password)

                if col == "email":
                    new_value = new_value.strip().lower()
                    self.check_email(new_value)
                
                if col == "phone_number":
                    new_value = new_value.strip()
                    new_value = self.validate_phone_number(new_value)
                    self.check_phone_number(new_value)

                if col == "is_active":
                    new_value = self.parse_is_active(new_value)

                if col == "role":
                    new_value = self.check_role(user_id, user[3], new_value)

                update_query = sql.SQL("""
                                UPDATE users
                                SET {} = %s
                                WHERE id = %s
                                """).format(sql.Identifier(col))

                    
                cur.execute(update_query, (new_value, user_id))
                cur.execute("""UPDATE users SET updated_at = %s WHERE id = %s""", (datetime.now(), user_id))

                self.conn.commit()
                print("\nUSER UPDATED")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except UserNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except CompanyNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def delete(self):
        try:
            with self.conn.cursor() as cur:
                user_id = input("Provide id of user you want to delete: ")

                if not user_id.isdigit():
                    raise ValueError("User id must be a number.")
                
                user_query = f"""
                        SELECT *
                        FROM users
                        WHERE id = %s
                        """
                
                cur.execute(user_query, (user_id,))
                user = cur.fetchone()

                if user is None:
                    raise UserNotFoundError(f"User with ID {user_id} was not found.")
                
                query = f"""
                        DELETE FROM users
                        WHERE id = %s
                        """
                
                check = (input(f"Are you sure you want to delete user with ID {user_id}? (Y/n) ") in ("Y", "y", "yes", "Yes", "YES"))

                if check:
                    cur.execute(query, (user_id, ))
                    self.conn.commit()
                    print("\nUSER SUCCESSFULLY REMOVED")

                else:
                    clear()
                    print("\nACTION ABORTED")
                    input("PRESS ENTER TO CONTINUE")
                
        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
                
        except UserNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def check_role(self, user_id, old_role, new_role):
        with self.conn.cursor() as cur:
            roles = ['Candidate', 'Employer', 'Admin']

            while new_role not in roles:
                print(f"Choose role from {', '.join(roles)}")

                new_role = input("Enter a valid role or 0 if you want to exit: ")
                if new_role == "0": raise ValueError

            if old_role == new_role:
                return new_role

            if old_role == 'Candidate':
                delete_query = """DELETE FROM candidates WHERE user_id = %s"""
                cur.execute(delete_query, (user_id,))

            if old_role == "Employer":
                delete_query = """DELETE FROM employers WHERE user_id = %s"""
                cur.execute(delete_query, (user_id,))

            if old_role == "Admin":
                delete_query = """UPDATE users SET is_staff = FALSE, is_superuser = FALSE WHERE id = %s"""
                cur.execute(delete_query, (user_id,))

            if new_role == "Candidate":
                insert_query = """INSERT INTO candidates(user_id) VALUES(%s)"""
                cur.execute(insert_query, (user_id,))

            if new_role == "Employer":
                company_id = input("Enter company id: ")
                self.check_company(company_id)

                insert_query = """INSERT INTO employers(user_id, company_id) VALUES(%s, %s)"""
                cur.execute(insert_query, (user_id, company_id))
            
            if new_role == "Admin":
                insert_query = """UPDATE users SET is_staff = TRUE, is_superuser = TRUE WHERE id = %s"""
                cur.execute(insert_query, (user_id,))

            return new_role

    def check_email(self, email):
        with self.conn.cursor() as cur:
            email_query = """SELECT 1 FROM users WHERE email = %s LIMIT 1"""
        
            cur.execute(email_query, (email,))
            email_exists = cur.fetchone() is not None

            if email_exists:
                raise ValueError("This email already exists.")
            
    def check_phone_number(self, phone_number):
        with self.conn.cursor() as cur:
            phone_number_query = """SELECT 1 FROM users WHERE phone_number = %s LIMIT 1"""

            cur.execute(phone_number_query, (phone_number,))
            phone_number_exists = cur.fetchone() is not None

            if phone_number_exists:
                raise ValueError("This phone number already exists.")
    
    def check_company(self, company_id):
        if not company_id.isdigit():
            raise ValueError("Company id must be a number.")

        with self.conn.cursor() as cur:
            company_query = """SELECT 1 FROM companies WHERE id = %s"""
            cur.execute(company_query, (company_id,))
            company_exists = cur.fetchone() is not None

            if not company_exists:
                raise CompanyNotFoundError("Company was not found.")
            
    @staticmethod
    def parse_is_active(new_value):
        value = new_value.strip().lower()

        if value in {"false", "f", "no", "n", "0"}:
            return False
        
        if value in {"true", "t", "yes", "y", "1"}:
            return True
        
        raise ValueError("Invalid value. Enter true or false.")
    
    @staticmethod
    def validate_password(password1, password2, *, hash_password=True):
        if not password1:
            raise ValueError("Password cannot be empty.")

        if password1 != password2:
            raise ValueError("Passwords do not match.")

        if hash_password:
            return make_password(password1)

        return password1

    @staticmethod
    def validate_phone_number(phone_number):
        phone_number = (
            phone_number.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if phone_number.startswith("+"):
            digits = phone_number[1:]
        else:
            digits = phone_number

        if not digits or not digits.isdigit():
            raise ValueError("Invalid phone number.")
    
        return phone_number

class OffersService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query = """ 
                SELECT o.id, c.name, o.title, o.location, o.salary_min, o.salary_max, o.employment_type, o.experience_level, o.contract_type, o.work_mode
                FROM job_offers o 
                JOIN companies c 
                ON o.company_id = c.id
                ORDER BY o.created_at DESC
                """

        with self.conn.cursor() as cur:
            cur.execute(query)
            offers = cur.fetchall()

            if not offers:
                print("\nNO JOB OFFERS.\n")
                return

            headers = [
                "ID",
                "Company name", 
                "Position",
                "Location",
                "Salary range",
                "Employment type",
                "Experience level",
                "Contract type",
                "Work mode"
            ]

            table_rows = []

            for offer in offers:
                id, company_name, title, location, salary_min, salary_max, employment_type, experience_level, contract_type, work_mode = offer

                salary_range = self.format_salary(salary_min, salary_max)
                table_rows.append([
                    id,
                    company_name or "-",
                    title or "-",
                    location or "-",
                    salary_range,
                    employment_type or "-",
                    experience_level or "-",
                    contract_type or "-",
                    work_mode or "-",
                ])

            print("\nJOB OFFERS\n")
            print(
                tabulate(
                    table_rows,
                    headers=headers,
                    tablefmt="rounded_grid",
                    stralign="left",
                    numalign="right",
                )
            )

    def add(self, company_id, employer_id):
        try:
            with self.conn.cursor() as cur:
                employment_type_choices = ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Seasonal', 'Volunteer']
                experience_level_choices = ['Intern', 'Entry level', 'Junior', 'Mid level', 'Senior', 'Lead', 'Expert']
                contract_type_choices = ['B2b', 'Employment contract', 'Contract of mandate', 'Contract for specific work']
                work_mode_choices = ['Remote', 'Hybrid', 'Onsite']

                print("\nCREATE OFFER")
                print("Provide:")
                title = input("Title: ")
                description = input("Description: ") or None
                requirements = input("Requirements: ") or None
                responsibilities = input("Responsibilities: ") or None
                location = input("Location: ")
                salary_min = input("Minimum salary: ")
                salary_max = input("Maximum salary: ")
                employment_type = input(f"Choose employment type from {', '.join(employment_type_choices)}: ")
                experience_level = input(f"Choose experience level from {', '.join(experience_level_choices)}: ")
                contract_type = input(f"Choose contract type from {', '.join(contract_type_choices)}: ")
                work_mode = input(f"Choose work mode from {', '.join(work_mode_choices)}: ")
                expires_at = input("Expiration date (YYYY-MM-DD format): ")

                while not title:
                    title = input("Enter a valid title or 0 if you want to exit.")
                    if title == "0":
                        raise ValueError
                    
                while not location:
                    location = input("Enter a valid location or 0 if you want to exit: ")
                    if location == "0":
                        raise ValueError
                
                while not salary_min.isdigit():
                    salary_min = input("Enter a valid minimum salary or 0 if you want to exit: ")
                    if salary_min == "0":
                        raise ValueError
                    
                while not salary_max.isdigit():
                    salary_max = input("Enter a valid maximum salary or 0 if you want to exit: ")
                    if salary_max == "0":
                        raise ValueError
                    
                salary_min = int(salary_min)
                salary_max = int(salary_max)
                
                if salary_min > salary_max:
                    raise ValueError("Minimum salary cannot be greater than maximum salary.")
                    
                while not self.check_employment_type(employment_type):
                    print(f"Employment type must be chosen from {', '.join(employment_type_choices)}")
                    employment_type = input("Enter a valid employment type or 0 if you want to exit: ")
                    if employment_type == "0":
                        raise ValueError
                    
                while not self.check_experience_level(experience_level):
                    print(f"Experience level must be chosen from {', '.join(experience_level_choices)}")
                    experience_level = input("Enter a valid experience level or 0 if you want to exit: ")
                    if experience_level == "0":
                        raise ValueError
                    
                while not self.check_contract_type(contract_type):
                    print(f"Contract type must be chosen from {', '.join(contract_type_choices)}")
                    contract_type = input("Enter a valid contract type or 0 if you want to exit: ")
                    if contract_type == "0":
                        raise ValueError
                    
                while not self.check_work_mode(work_mode):
                    print(f"Work mode must be chosen from {', '.join(work_mode_choices)}")
                    work_mode = input("Enter a valid work mode or 0 if you want to exit: ")
                    if work_mode == "0":
                        raise ValueError
                
                expires_at = date.fromisoformat(expires_at)

                if expires_at <= date.today():
                    raise ValueError("Expiration date must be in the future.")
                    
                query = """
                        INSERT INTO job_offers(company_id, employer_id, title, description, requirements, responsibilities, location, salary_min, salary_max, employment_type, experience_level, contract_type, work_mode, status, expires_at)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        """
                
                values = (company_id, employer_id, title, description, requirements, responsibilities, location, salary_min, salary_max, employment_type, experience_level, contract_type, work_mode, "Active", expires_at)
                
                cur.execute(query, values)
                self.conn.commit()

                print("\nOFFER CREATED\n")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
        
        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")
        
    def change(self, offer_id):
        try:
            with self.conn.cursor() as cur:
                
                offer_query = f"""
                        SELECT *
                        FROM job_offers
                        WHERE id = %s
                        """
                
                cur.execute(offer_query, (offer_id,))
                offer = cur.fetchone()

                if offer is None:
                    raise OfferNotFoundError(f"Offer with ID {offer_id} was not found.")
                
                columns = ["title", "description", "requirements", "responsibilities", "location", "salary_min", "salary_max", "employment_type", "experience_level", "contract_type", "work_mode", "status", "expires_at"]

                print("Choose the column you want to change, from: ")
                print(", ".join(columns))
                col = input()
                if col not in columns:
                    raise ValueError("Invalid column.")

                new_value = input("Provide new data for this column: ")
                    
                if col == "title" and not new_value:
                    raise ValueError("Enter a valid title.")
                if col == "location" and not new_value:
                    raise ValueError("Enter a valid location.")
                
                if col == "employment_type" and not self.check_employment_type(new_value):
                    raise ValueError("Invalid employment type.")
                if col == "experience_level" and not self.check_experience_level(new_value):
                    raise ValueError("Invalid experience level.")
                if col == "contract_type" and not self.check_contract_type(new_value):
                    raise ValueError("Invalid contract type.")
                if col == "work_mode" and not self.check_work_mode(new_value):
                    raise ValueError("Invalid work mode.")
                
                if (col == "salary_max" or col == "salary_min") and not new_value.isdigit():
                    raise ValueError("Salary must be a number.")
                if col == "salary_max" and offer[8] > int(new_value):
                    raise ValueError("Minimum salary cannot be greater than maximum salary.")
                if col == "salary_min" and offer[9] < int(new_value):
                    raise ValueError("Minimum salary cannot be greater than maximum salary.")
                
                if col == "expires_at":
                    new_value = date.fromisoformat(new_value)

                    if new_value <= date.today():
                        raise ValueError("Expiration date must be in the future.")
                
                update_query = sql.SQL("""
                                UPDATE job_offers
                                SET {} = %s
                                WHERE id = %s
                                """).format(sql.Identifier(col))

                cur.execute(update_query, (new_value, offer_id,))
                self.conn.commit()

                print("\nOFFER UPDATED")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except OfferNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def delete(self, offer_id):
        try:
            with self.conn.cursor() as cur:
                
                offer_query = f"""
                        SELECT *
                        FROM job_offers
                        WHERE id = %s
                        """
                
                cur.execute(offer_query, (offer_id,))
                offer = cur.fetchone()

                if offer is None:
                    raise OfferNotFoundError(f"Offer with ID {offer_id} was not found.")
                
                query = f"""
                        DELETE FROM job_offers
                        WHERE id = %s
                        """
                
                check = (input(f"Are you sure you want to delete offer with ID {offer_id}? (Y/n) ") in ("Y", "y", "yes", "Yes", "YES"))

                if check:
                    cur.execute(query, (offer_id, ))
                    self.conn.commit()
                    print("\nOFFER SUCCESSFULLY REMOVED")

                else:
                    clear()
                    print("\nACTION ABORTED")
                    input("PRESS ENTER TO CONTINUE")
                
        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
                
        except OfferNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    @staticmethod
    def format_salary(salary_min, salary_max):
        minimum = f"{salary_min:,.0f}".replace(",", " ")
        maximum = f"{salary_max:,.0f}".replace(",", " ")

        return f"{minimum} - {maximum}"
    
    @staticmethod
    def check_employment_type(value):
        employment_type_choices = {'Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Seasonal', 'Volunteer'}
        return value in employment_type_choices
    @staticmethod
    def check_experience_level(value):
        experience_level_choices = {'Intern', 'Entry level', 'Junior', 'Mid level', 'Senior', 'Lead', 'Expert'}
        return value in experience_level_choices
    
    @staticmethod
    def check_contract_type(value):
        contract_type_choices = {'B2b', 'Employment contract', 'Contract of mandate', 'Contract for specific work'}
        return value in contract_type_choices
    
    @staticmethod
    def check_work_mode(value):
        work_mode_choices = {'Remote', 'Hybrid', 'Onsite'}
        return value in work_mode_choices

class CompaniesService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query = """ 
                SELECT
                    c.id, c.name, c.description, c.website, c.industry, c.location, c.size,
                    COUNT(DISTINCT e.id) AS employees_count,
                    COUNT(DISTINCT o.id) AS job_offers_count
                FROM companies c
                LEFT JOIN employers e
                    ON e.company_id = c.id
                LEFT JOIN job_offers o
                    ON o.company_id = c.id
                GROUP BY c.id;
                """

        with self.conn.cursor() as cur:
            cur.execute(query)
            companies = cur.fetchall()

            if not companies:
                print("\nNO COMPANIES.\n")
                return

            headers = [
                "ID",
                "Company name", 
                "Description",
                "Website",
                "Industry",
                "Location",
                "Size",
                "Employees",
                "Offers"
            ]

            table_rows = []

            for company in companies:
                id, company_name, description, website, industry, location, size, number_of_employers, number_of_offers = company

                table_rows.append([
                    id,
                    company_name or "-",
                    self.wrap_text(description, 25),
                    website or "-",
                    industry or "-",
                    location or "-",
                    size or "-",
                    number_of_employers if number_of_employers is not None else "-",
                    number_of_offers if number_of_offers is not None else "-"
                ])

            print("\nCOMPANIES \n")
            print(
                tabulate(
                    table_rows,
                    headers=headers,
                    tablefmt="rounded_grid",
                    stralign="left",
                    numalign="right",
                )
            )

    def add(self):
        try:
            with self.conn.cursor() as cur:
                print("\nCREATE COMPANY")
                print("Provide:")
                company_name = input("Company name: ")
                description = input("Description: ") or None
                website = input("Website: ") or None
                industry = input("Industry: ") or None
                location = input("Location: ") or None
                size = input("Size: ") or None

                if not company_name:
                    raise ValueError("Invalid company name.")
                
                query = """
                        INSERT INTO companies(name, description, website, industry, location, size)
                        VALUES(%s, %s, %s, %s, %s, %s)
                        """
                
                cur.execute(query, (company_name, description, website, industry, location, size))
                self.conn.commit()

                print("\nCOMPANY CREATED")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
        
        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def change(self):
        try:
            with self.conn.cursor() as cur:
                company_id = input("Provide id of company you want to change: ")

                if not company_id.isdigit():
                    raise ValueError("Company id must be a number.")
                
                company_query = f"""
                        SELECT *
                        FROM companies
                        WHERE id = %s
                        """
                
                cur.execute(company_query, (company_id,))
                company = cur.fetchone()

                if company is None:
                    raise CompanyNotFoundError(f"Company with ID {company_id} was not found.")
                
                columns = ["name", "description", "website", "industry", "location", "size"]

                print("Choose the column you want to change, from: ")
                print(", ".join(columns))
                col = input()
                if col not in columns:
                    raise ValueError("Invalid column.")

                new_value = input("Provide new data for this column: ")
                    
                if col == "name" and not new_value:
                    raise ValueError("Enter a valid company name.")
                
                update_query = sql.SQL("""
                                UPDATE companies
                                SET {} = %s
                                WHERE id = %s
                                """).format(sql.Identifier(col))

                cur.execute(update_query, (new_value, company_id,))
                self.conn.commit()

                print("\nCOMPANY UPDATED")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except CompanyNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    def delete(self):
        try:
            with self.conn.cursor() as cur:
                company_id = input("Provide id of company you want to delete: ")

                if not company_id.isdigit():
                    raise ValueError("Company id must be a number.")
                
                company_query = f"""
                        SELECT *
                        FROM companies
                        WHERE id = %s
                        """
                
                cur.execute(company_query, (company_id,))
                company = cur.fetchone()

                if company is None:
                    raise CompanyNotFoundError(f"Company with ID {company_id} was not found.")
                
                query = f"""
                        DELETE FROM companies
                        WHERE id = %s
                        """
                
                check = (input(f"Are you sure you want to delete the company with ID {company_id}? (Y/n) ") in ("Y", "y", "yes", "Yes", "YES"))

                if check:
                    cur.execute(query, (company_id, ))
                    self.conn.commit()
                    print("\nCOMPANY SUCCESSFULLY REMOVED")

                else:
                    clear()
                    print("\nACTION ABORTED")
                    input("PRESS ENTER TO CONTINUE")
                
        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")
                
        except CompanyNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

    @staticmethod
    def wrap_text(value, width=30):
        if value is None:
            return "-"
        
        return "\n".join(wrap(str(value), width=width)) or "-"
    
class ApplicationsService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query = """ 
                SELECT o.id, o.title, a.candidate_id, c.file_url, a.status, a.updated_at
                FROM job_offers o 
                JOIN applications a 
                    ON o.id = a.job_offer_id
                JOIN cvs c 
                    ON c.id = a.cv_id
                ORDER BY 1, 3, 4
                """

        with self.conn.cursor() as cur:
            cur.execute(query)
            applications = cur.fetchall()

            if not applications:
                print("\nNO APPLICATIONS.\n")
                return

            headers = [
                "Offer ID",
                "Position", 
                "Candidate ID",
                "CV url",
                "Status",
                "Updated at"
            ]

            table_rows = []

            for application in applications:
                offer_id, position, candidate_id, file_url, status, updated_at = application

                table_rows.append([
                    offer_id,
                    position,
                    candidate_id,
                    file_url or "-",
                    status,
                    updated_at
                ])

            print("\nAPPLICATIONS\n")
            print(
                tabulate(
                    table_rows,
                    headers=headers,
                    tablefmt="rounded_grid",
                    stralign="left",
                    numalign="right",
                )
            )

    def change_status(self, job_offer_id, candidate_id, cv_id):
        try:
            with self.conn.cursor() as cur:
                query = """
                        SELECT 1
                        FROM applications a
                        WHERE a.job_offer_id = %s
                        AND a.candidate_id = %s
                        AND a.cv_id = %s
                        """
                
                cur.execute(query, (job_offer_id, candidate_id, cv_id))
                application = cur.fetchone()

                if application is None:
                    raise ApplicationNotFoundError(f"Application with offer ID = {job_offer_id}, candidate ID = {candidate_id}, cv ID = {cv_id} does not exist.")
                
                choices = ['Sent', 'Reviewed', 'Rejected', 'Accepted']
                print(f"Correct statuses: {', '.join(choices)}")
                new_status = input("Enter new application status: ")

                if new_status not in choices:
                    raise ValueError("Invalid new status.")

                update_query =  """
                                UPDATE applications a
                                SET status =  %s, updated_at = %s
                                WHERE a.job_offer_id = %s
                                AND a.candidate_id = %s
                                AND a.cv_id = %s
                                """
                
                cur.execute(update_query, (new_status, datetime.now(), job_offer_id, candidate_id, cv_id))
                self.conn.commit()

                print("\nSTATUS CHANGED")

        except ValueError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except ApplicationNotFoundError as error:
            clear()
            print(error)
            self.conn.rollback()
            input("PRESS ENTER TO CONTINUE")

        except Error as error:
            self.conn.rollback()
            print(f"Database error: {error}")

class StatsService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query1 = """ 
                SELECT 
                    (SELECT COUNT(*) FROM users) AS users_count,
                    (SELECT COUNT(*) FROM candidates) AS candidates_count,
                    (SELECT COUNT(*) FROM employers) AS employers_count,
                    (SELECT COUNT(*) FROM companies) AS companies_count,
                    (SELECT COUNT(*) FROM job_offers) AS offers_count,
                    (SELECT COUNT(*) FROM applications) AS applications_count
                """

        query2 = """
                SELECT c.name, o.title, COUNT(a.*)
                    FROM job_offers o
                    JOIN applications a
                        ON a.job_offer_id = o.id
                    JOIN companies c
                        ON o.company_id = c.id
                    WHERE o.status <> 'Closed'
                    GROUP BY 1, 2
                 """

        query3 = """
                    SELECT
                        experience_level,
                        ROUND(AVG(salary_min), 2) AS average_salary_min,
                        ROUND(AVG(salary_max), 2) AS average_salary_max,
                        COUNT(*) AS offers_count
                    FROM job_offers
                    GROUP BY experience_level
                    ORDER BY average_salary_max DESC;
                 """

        with self.conn.cursor() as cur:
            cur.execute(query1)
            stats1 = cur.fetchone()

            cur.execute(query2)
            stats2 = cur.fetchall()

            cur.execute(query3)
            stats3 = cur.fetchall()

            if stats1 is not None:
                print("Shows the total number of users, candidates, employers, companies, job offers, and applications in the system.")

                headers1 = [
                    "Users",
                    "Candidates", 
                    "Employers",
                    "Companies",
                    "Offers",
                    "Applications"
                ]

                table_rows1 = []

                users_count, candidates_count, employers_count, companies_count, offers_count, applications_count = stats1

                table_rows1.append([
                    users_count,
                    candidates_count,
                    employers_count,
                    companies_count,
                    offers_count,
                    applications_count
                ])

                print(
                    tabulate(
                        table_rows1,
                        headers=headers1,
                        tablefmt="rounded_grid",
                        stralign="left",
                        numalign="right",
                    )
                )

            if stats2:
                print("Shows each company, its non-closed job offers, and the number of applications received for each offer.")

                headers2 = [
                    "Company name",
                    "Job offer title",
                    "Applications count"
                ]

                table_rows2 = []

                for stat in stats2:
                    name, title, count = stat

                    table_rows2.append([
                        name,
                        title,
                        count
                    ])

                print(
                    tabulate(
                        table_rows2,
                        headers=headers2,
                        tablefmt="rounded_grid",
                        stralign="left",
                        numalign="right",
                    )
                )

            if stats3:
                print("Shows the average minimum and maximum salary, together with the number of job offers for each experience level.")

                headers3 = [
                    "Experience level",
                    "Average minimum salary",
                    "Average maximum salary",
                    "Offers count"
                ]

                table_rows3 = []

                for stat in stats3:
                    experience_level, avg_min_salary, avg_max_salary, offers_count = stat

                    table_rows3.append([
                        experience_level,
                        avg_min_salary,
                        avg_max_salary,
                        offers_count
                    ])

                print(
                    tabulate(
                        table_rows3,
                        headers=headers3,
                        tablefmt="rounded_grid",
                        stralign="left",
                        numalign="right",
                    )
                )

class APIService:
    ENDPOINTS = [
        {
            "method": "POST",
            "path": "api/auth/register/",
            "description": "Registers a new user account.",
            "access": "Public"
        },
        {
            "method": "POST",
            "path": "api/auth/login/",
            "description": "Authenticates a user and starts a session.",
            "access": "Public"
        },
        {
            "method": "POST",
            "path": "api/auth/logout/",
            "description": "Logs out the authenticated user and ends the current session.",
            "access": "User"
        },
        {
            "method": "GET, PATCH, DELETE",
            "path": "api/users/me/",
            "description": "Displays / patches / deletes user data.",
            "access": "Users"
        },
        {
            "method": "GET",
            "path": "api/admin/users/",
            "description": "Displays data for all users.",
            "access": "Admin"
        },
        {
            "method": "GET, PATCH, DELETE",
            "path": "api/admin/users/{user_id}/",
            "description": "Displays / patches / deletes user data.",
            "access": "Admin"
        },
        {
            "method": "GET, PATCH",
            "path": "api/candidates/me/",
            "description": "Displays / patches candidate data.",
            "access": "Candidate"
        },
        {
            "method": "GET",
            "path": "api/candidates/{candidate_id}/",
            "description": "Displays candidate data.",
            "access": "User"
        },
        {
            "method": "GET, PATCH",
            "path": "api/employers/me/",
            "description": "Displays / patches employer data.",
            "access": "Employer"
        },
        {
            "method": "GET",
            "path": "api/employers/{employer_id}/",
            "description": "Displays employer data.",
            "access": "User"
        },
        {
            "method": "GET",
            "path": "api/companies/",
            "description": "Displays data for all companies.",
            "access": "User"
        },
        {
            "method": "GET",
            "path": "api/companies/{company_id}/",
            "description": "Displays company data.",
            "access": "User"
        },
        {
            "method": "PATCH",
            "path": "api/companies/patch/{company_id}/",
            "description": "Patches company data.",
            "access": "Employer, Admin"
        },
        {
            "method": "DELETE",
            "path": "api/admin/companies/delete/{company_id}/",
            "description": "Deletes company.",
            "access": "Admin"
        },
        {
            "method": "POST",
            "path": "api/admin/companies/post/",
            "description": "Creates new company.",
            "access": "Admin"
        },
        {
            "method": "GET",
            "path": "api/companies/{company_id}/job_offers/",
            "description": "Displays the company's job offers.",
            "access": "User"
        },
        {
            "method": "GET",
            "path": "api/companies/{company_id}/employers/",
            "description": "Displays the company's employers.",
            "access": "User"
        },
        {
            "method": "GET",
            "path": "api/job-offers/",
            "description": "Displays all job offers data.",
            "access": "User"
        },
        {
            "method": "GET",
            "path": "api/job-offers/{offer_id}/",
            "description": "Displays offer's data.",
            "access": "User"
        },
        {
            "method": "PATCH, DELETE",
            "path": "api/job-offers/{offer_id}/edit/",
            "description": "Patches / deletes offer's data.",
            "access": "Employer"
        },
        {
            "method": "POST",
            "path": "api/job-offers/create/",
            "description": "Creates a new job offer.",
            "access": "Employer"
        },
        {
            "method": "POST",
            "path": "api/admin/job-offers/create/{company_id}/{employer_id}/",
            "description": "Creates a new job offer.",
            "access": "Admin"

        },
        {
            "method": "GET",
            "path": "api/employers/me/job-offers/",
            "description": "Displays job offers created by the employer.",
            "access": "Employer"
        },
        {
            "method": "GET",
            "path": "api/candidates/me/applications/",
            "description": "Displays candidate's applications.",
            "access": "Candidate"
        },
        {
            "method": "POST",
            "path": "api/candidates/me/applications/create/{offer_id}/",
            "description": "Creates candidate's applications.",
            "access": "Candidate"
        },
        {
            "method": "GET",
            "path": "api/employers/me/applications/",
            "description": "Displays applications sent to employer's offers.",
            "access": "Employer"
        },
        {
            "method": "PATCH",
            "path": "api/employers/me/applications/{offer_id}/{candidate_id}/{cv_id}/status/",
            "description": "Changes status of candidate's application.",
            "access": "Employer"
        },
        {
            "method": "GET, POST",
            "path": "api/candidates/me/cvs/",
            "description": "Displays / uploads a PDF CV for the candidate.",
            "access": "Candidate",
        }
    ]
    
    def view(self):
        headers = [
            "Method",
            "Endpoint",
            "Description",
            "Access"
        ]

        table_rows = []

        for endpoint in self.ENDPOINTS:
            table_rows.append([
                endpoint["method"],
                endpoint["path"],
                endpoint["description"],
                endpoint["access"]
            ])

        print("\nAPI ENDPOINTS\n")
        print(
            tabulate(
                table_rows,
                headers=headers,
                tablefmt="rounded_grid",
                stralign="left"
            )
        )

class MembersService:
    def __init__(self):
        self.conn = connect()

    def view(self):
        query = """
                SELECT 
                    u.id as user_id,
                    CASE
                        WHEN u.role = 'Employer' THEN COALESCE(e.first_name, '-')
                        WHEN u.role = 'Candidate' THEN COALESCE(c.first_name, '-')
                        ELSE '-'
                    END AS first_name,
                    CASE
                        WHEN u.role = 'Employer' THEN COALESCE(e.last_name, '-')
                        WHEN u.role = 'Candidate' THEN COALESCE(c.last_name, '-')
                        ELSE '-'
                    END AS last_name,
                    u.role,
                    u.phone_number,
                    co.name,
                    u.created_at
                        FROM users u 
                        LEFT JOIN employers e
                            ON u.id = e.user_id
                        LEFT JOIN candidates c
                            ON u.id = c.user_id
                        LEFT JOIN companies co
                            ON co.id = e.company_id
                        WHERE u.is_active = TRUE
                """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                members = cur.fetchall()

                if not members:
                    print("\nNO MEMBERS.\n")
                    return

                headers = [
                    "User ID",
                    "First name",
                    "Last name",
                    "Role",
                    "Phone number",
                    "Company name",
                    "Joined at"
                ]

                table_rows = []

                for member in members:
                    user_id, first_name, last_name, role, phone_number, company_name, created_at = member

                    table_rows.append([
                        user_id,
                        first_name,
                        last_name,
                        role,
                        phone_number,
                        company_name or "-",
                        created_at,
                        
                    ])

                print("\nMEMBERS\n")
                print(
                    tabulate(
                        table_rows,
                        headers=headers,
                        tablefmt="rounded_grid",
                        stralign="left",
                        numalign="right"
                    )
                )

        except Error as error:
            print(f"Database error: {error}")

def main():
    services = []
    app = None

    try:
        app = App()

        users_service = UsersService()
        companies_service = CompaniesService()
        offers_service = OffersService()
        applications_service = ApplicationsService()
        stats_service = StatsService()
        api_service = APIService()
        members_service = MembersService()

        services = [
            users_service,
            companies_service,
            offers_service,
            applications_service,
            stats_service,
            members_service,
        ]

        print("JOB BOARD MANAGEMENT CONSOLE")
        print("Available roles:", ", ".join(app.APP_ROLES))

        role = input("Choose your role: ").strip()

        try:
            app.set_role(role)

            if app.role == "Employer":
                employer_id = input("Choose employer id: ")
                company_id = input("Choose company id: ")
                app.set_company(company_id)
                app.validate_employer(employer_id)

        except ValueError as error:
            print(error)
            return

        actions = {
            "1": ("users.view", users_service.view),
            "2": ("users.add", users_service.add),
            "3": ("users.change", users_service.change),
            "4": ("users.delete", users_service.delete),

            "5": ("companies.view", companies_service.view),
            "6": ("companies.add", companies_service.add),
            "7": ("companies.change", companies_service.change),
            "8": ("companies.delete", companies_service.delete),

            "9": ("offers.view", offers_service.view),
            "10": ("offers.add", offers_service.add),
            "11": ("offers.change", offers_service.change),
            "12": ("offers.delete", offers_service.delete),

            "13": ("applications.view", applications_service.view),
            "14": ("applications.change_status", applications_service.change_status),

            "15": ("stats.view", stats_service.view),
            "16": ("api.view", api_service.view),
            "17": ("members.view", members_service.view),
        }

        while True:
            print(f"JOB BOARD MANAGEMENT CONSOLE - ROLE: {role} \n")

            for number, (action, _) in actions.items():
                if app.has_permission(action):
                    print(f"{number} - {action}")

            print("0 - Exit")

            choice = input("\nChoose an action: ").strip()

            if choice == "0":
                print("Application closed.")
                break

            selected_action = actions.get(choice)

            if selected_action is None:
                input("Invalid option. Press Enter to continue.")
                continue

            action, function = selected_action
            if not app.has_permission(action):
                input("You do not have permission to perform this action.")
                continue

            try:
                if action == "offers.add":
                    if app.role == "Admin":
                        company_id = input("Enter company id: ")
                        app.validate_company(company_id)
                        company_id = int(company_id)

                        employer_id = input("Enter employer id: ")
                        app.validate_employer(employer_id)
                        employer_id = int(employer_id)

                        with app.conn.cursor() as cur:
                            query = """SELECT company_id FROM employers WHERE id = %s"""
                            cur.execute(query, (employer_id,))

                            employer_company_id = cur.fetchone()

                            if int(employer_company_id[0]) != company_id:
                                raise ValueError("Employer is not assigned to this company.")

                        function(company_id, employer_id)

                    else:
                        function(app.company_id, app.employer_id)

                elif action == "offers.change":
                    offer_id = input("Enter offer id: ")
                    app.validate_offer(offer_id)

                    if app.role == "Employer":
                        with app.conn.cursor() as cur:
                            query = """SELECT employer_id FROM job_offers WHERE id = %s"""
                            cur.execute(query, (offer_id,))
                            row = cur.fetchone()

                            if row is None or row[0] != app.employer_id:
                                raise ValueError("You are not allowed to edit this job offer.")

                    function(offer_id)

                elif action == "offers.delete":
                    offer_id = input("Enter offer id: ")
                    app.validate_offer(offer_id)

                    if app.role == "Employer":
                        with app.conn.cursor() as cur:
                            query = """SELECT employer_id FROM job_offers WHERE id = %s"""
                            cur.execute(query, (offer_id,))
                            row = cur.fetchone()

                            if row is None or row[0] != int(app.employer_id):
                                raise ValueError("You are not allowed to edit this job offer.")

                    function(offer_id)

                elif action == "applications.change_status":
                    with app.conn.cursor() as cur:
                        offer_id = input("Enter offer id: ")
                        app.validate_offer(offer_id)

                        if app.role == "Employer":
                            query = """SELECT employer_id FROM job_offers WHERE id = %s"""
                            cur.execute(query, (offer_id,))
                            row = cur.fetchone()
                            
                            if row is None or row[0] != int(app.employer_id):
                                raise ValueError("You are not allowed to edit this job offer.")

                        candidate_id = input("Enter candidate id: ")
                        cv_id = input("Enter cv id: ")

                        query = """SELECT 1 FROM applications WHERE job_offer_id = %s AND candidate_id = %s AND cv_id = %s"""
                        cur.execute(query, (offer_id, candidate_id, cv_id))

                        if cur.fetchone() is None:
                            raise ApplicationNotFoundError("The specified application does not exist.")

                        function(offer_id, candidate_id, cv_id)

                else:
                    function()

                time.sleep(0.5)

            except ValueError as error:
                print(f"Error: {error}")

            except OfferNotFoundError as error:
                print(f"Error: {error}")

            except CompanyNotFoundError as error:
                print(f"Error: {error}")

            except ApplicationNotFoundError as error:
                print(f"Error: {error}")

            except Exception as error:
                print(f"Unexpected error: {error}")

    finally:
        for service in services:
            connection = getattr(service, "conn", None)

            if connection is not None and not connection.closed:
                connection.close()

        if app is not None and not app.conn.closed:
            app.conn.close()

if __name__ == "__main__":
    main()