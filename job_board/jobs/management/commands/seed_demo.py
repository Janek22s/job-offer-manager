from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ...models import (
    ApplicationStatus,
    Applications,
    Candidates,
    Companies,
    ContractType,
    Cvs,
    Employers,
    EmploymentType,
    ExperienceLevel,
    JobOffers,
    JobOfferStatus,
    SavedJobs,
    UserRole,
    Users,
    WorkMode,
)


DEMO_EMAIL_DOMAIN = "@jobs-demo.test"
DEFAULT_PASSWORD = "Demo123!ChangeMe"


class Command(BaseCommand):
    help = "Creates deterministic demo users, companies, CVs, job offers and applications."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Deletes records created by this command before recreating them.",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help="Password assigned to all demo users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        if options["reset"]:
            self._delete_demo_data()

        companies = self._seed_companies()
        users = self._seed_users(password)
        candidates = self._seed_candidates(users)
        cvs = self._seed_cvs(candidates)
        employers = self._seed_employers(users, companies)
        offers = self._seed_job_offers(companies, employers)
        self._seed_saved_jobs(candidates, offers)
        self._seed_applications(candidates, cvs, offers)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data created: "
                f"{len(companies)} companies, "
                f"{len(users)} users, "
                f"{len(candidates)} candidates, "
                f"{len(employers)} employers, "
                f"{len(offers)} job offers."
            )
        )
        self.stdout.write("")
        self.stdout.write("Demo password:")
        self.stdout.write(f"  {password}")
        self.stdout.write("")
        self.stdout.write("Demo accounts:")
        for email in users:
            self.stdout.write(f"  {email}")

    def _delete_demo_data(self):
        # Deleting companies cascades to their employers, offers,
        # applications and saved jobs. Deleting users cascades to profiles.
        Companies.objects.filter(name__startswith="[DEMO]").delete()
        Users.objects.filter(email__endswith=DEMO_EMAIL_DOMAIN).delete()
        self.stdout.write("Previous demo records deleted.")

    def _seed_companies(self):
        rows = [
            {
                "key": "byteforge",
                "name": "[DEMO] ByteForge",
                "description": "Software house building web platforms and internal business systems.",
                "website": "https://byteforge.example",
                "industry": "Software development",
                "location": "Warszawa",
                "size": "51-200",
            },
            {
                "key": "cloudnest",
                "name": "[DEMO] CloudNest",
                "description": "Cloud infrastructure, observability and platform engineering company.",
                "website": "https://cloudnest.example",
                "industry": "Cloud computing",
                "location": "Kraków",
                "size": "11-50",
            },
            {
                "key": "finpilot",
                "name": "[DEMO] FinPilot",
                "description": "Fintech company developing analytics and risk-management products.",
                "website": "https://finpilot.example",
                "industry": "Fintech",
                "location": "Wrocław",
                "size": "201-500",
            },
            {
                "key": "healthsoft",
                "name": "[DEMO] HealthSoft",
                "description": "Digital health products for clinics, doctors and patients.",
                "website": "https://healthsoft.example",
                "industry": "HealthTech",
                "location": "Poznań",
                "size": "51-200",
            },
        ]

        result = {}
        for row in rows:
            key = row.pop("key")
            company, _ = Companies.objects.update_or_create(
                name=row["name"],
                defaults=row,
            )
            result[key] = company
        return result

    def _seed_users(self, password):
        now = timezone.now()
        rows = [
            {
                "email": "anna.kowalska@jobs-demo.test",
                "phone_number": "+48500100001",
                "role": UserRole.CANDIDATE,
            },
            {
                "email": "piotr.nowak@jobs-demo.test",
                "phone_number": "+48500100002",
                "role": UserRole.CANDIDATE,
            },
            {
                "email": "maria.wisniewska@jobs-demo.test",
                "phone_number": "+48500100003",
                "role": UserRole.CANDIDATE,
            },
            {
                "email": "tomasz.wojcik@jobs-demo.test",
                "phone_number": "+48500100004",
                "role": UserRole.CANDIDATE,
            },
            {
                "email": "zofia.kaminska@jobs-demo.test",
                "phone_number": "+48500100005",
                "role": UserRole.CANDIDATE,
            },
            {
                "email": "rekruter.byteforge@jobs-demo.test",
                "phone_number": "+48500200001",
                "role": UserRole.EMPLOYER,
            },
            {
                "email": "rekruter.cloudnest@jobs-demo.test",
                "phone_number": "+48500200002",
                "role": UserRole.EMPLOYER,
            },
            {
                "email": "rekruter.finpilot@jobs-demo.test",
                "phone_number": "+48500200003",
                "role": UserRole.EMPLOYER,
            },
            {
                "email": "rekruter.healthsoft@jobs-demo.test",
                "phone_number": "+48500200004",
                "role": UserRole.EMPLOYER,
            },
            {
                "email": "admin@jobs-demo.test",
                "phone_number": "+48500999999",
                "role": UserRole.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        result = {}
        for row in rows:
            email = row["email"]
            role = row["role"]
            is_admin = role == UserRole.ADMIN

            user, _ = Users.objects.update_or_create(
                email=email,
                defaults={
                    "phone_number": row["phone_number"],
                    "role": role,
                    "is_active": True,
                    "is_staff": row.get("is_staff", is_admin),
                    "is_superuser": row.get("is_superuser", is_admin),
                    "updated_at": now,
                },
            )

            # update_or_create() does not hash a plain-text password.
            user.set_password(password)
            user.save(update_fields=["password"])

            result[email] = user

        return result

    def _seed_candidates(self, users):
        rows = [
            {
                "email": "anna.kowalska@jobs-demo.test",
                "first_name": "Anna",
                "last_name": "Kowalska",
                "bio": "Python developer interested in backend systems and REST APIs.",
                "experience_level": ExperienceLevel.JUNIOR,
            },
            {
                "email": "piotr.nowak@jobs-demo.test",
                "first_name": "Piotr",
                "last_name": "Nowak",
                "bio": "DevOps engineer working with Linux, Docker, Kubernetes and CI/CD.",
                "experience_level": ExperienceLevel.MID_LEVEL,
            },
            {
                "email": "maria.wisniewska@jobs-demo.test",
                "first_name": "Maria",
                "last_name": "Wiśniewska",
                "bio": "Data analyst using SQL, Python and BI tools.",
                "experience_level": ExperienceLevel.MID_LEVEL,
            },
            {
                "email": "tomasz.wojcik@jobs-demo.test",
                "first_name": "Tomasz",
                "last_name": "Wójcik",
                "bio": "Frontend developer focused on React and TypeScript.",
                "experience_level": ExperienceLevel.JUNIOR,
            },
            {
                "email": "zofia.kaminska@jobs-demo.test",
                "first_name": "Zofia",
                "last_name": "Kamińska",
                "bio": "Computer science student looking for a first commercial internship.",
                "experience_level": ExperienceLevel.INTERN,
            },
        ]

        result = {}
        for row in rows:
            email = row.pop("email")
            candidate, _ = Candidates.objects.update_or_create(
                user=users[email],
                defaults=row,
            )
            result[email] = candidate
        return result

    def _seed_cvs(self, candidates):
        rows = [
            ("anna.kowalska@jobs-demo.test", "anna-kowalska-cv.pdf"),
            ("piotr.nowak@jobs-demo.test", "piotr-nowak-cv.pdf"),
            ("maria.wisniewska@jobs-demo.test", "maria-wisniewska-cv.pdf"),
            ("tomasz.wojcik@jobs-demo.test", "tomasz-wojcik-cv.pdf"),
            ("zofia.kaminska@jobs-demo.test", "zofia-kaminska-cv.pdf"),
        ]

        result = {}
        for email, filename in rows:
            cv, _ = Cvs.objects.update_or_create(
                candidate=candidates[email],
                file_name=filename,
                defaults={"file_url": f"cvs/demo/{filename}"},
            )
            result[email] = cv
        return result

    def _seed_employers(self, users, companies):
        rows = [
            {
                "email": "rekruter.byteforge@jobs-demo.test",
                "company": "byteforge",
                "first_name": "Karolina",
                "last_name": "Mazur",
                "position": "IT Recruiter",
            },
            {
                "email": "rekruter.cloudnest@jobs-demo.test",
                "company": "cloudnest",
                "first_name": "Michał",
                "last_name": "Lewandowski",
                "position": "Talent Acquisition Specialist",
            },
            {
                "email": "rekruter.finpilot@jobs-demo.test",
                "company": "finpilot",
                "first_name": "Alicja",
                "last_name": "Dąbrowska",
                "position": "HR Business Partner",
            },
            {
                "email": "rekruter.healthsoft@jobs-demo.test",
                "company": "healthsoft",
                "first_name": "Jakub",
                "last_name": "Zieliński",
                "position": "Technical Recruiter",
            },
        ]

        result = {}
        for row in rows:
            email = row.pop("email")
            company_key = row.pop("company")
            employer, _ = Employers.objects.update_or_create(
                user=users[email],
                defaults={
                    **row,
                    "company": companies[company_key],
                },
            )
            result[email] = employer
        return result

    def _seed_job_offers(self, companies, employers):
        now = timezone.now()
        rows = [
            {
                "key": "django",
                "company": "byteforge",
                "employer": "rekruter.byteforge@jobs-demo.test",
                "title": "Backend Developer Python/Django",
                "description": "Development of APIs and backend services for business platforms.",
                "requirements": "Python, Django, PostgreSQL, REST, Git.",
                "responsibilities": "Implementing features, code reviews, tests and database design.",
                "location": "Warszawa",
                "salary_min": 16000,
                "salary_max": 23000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.MID_LEVEL,
                "contract_type": ContractType.B2B,
                "work_mode": WorkMode.HYBRID,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=45),
            },
            {
                "key": "junior-python",
                "company": "byteforge",
                "employer": "rekruter.byteforge@jobs-demo.test",
                "title": "Junior Python Developer",
                "description": "Backend development under the guidance of senior developers.",
                "requirements": "Python basics, SQL, Git and willingness to learn Django.",
                "responsibilities": "Bug fixing, writing tests and implementing smaller features.",
                "location": "Warszawa",
                "salary_min": 8000,
                "salary_max": 12000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.JUNIOR,
                "contract_type": ContractType.EMPLOYMENT_CONTRACT,
                "work_mode": WorkMode.HYBRID,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=30),
            },
            {
                "key": "react",
                "company": "byteforge",
                "employer": "rekruter.byteforge@jobs-demo.test",
                "title": "Frontend Developer React",
                "description": "Building modern web interfaces for SaaS products.",
                "requirements": "React, TypeScript, HTML, CSS and REST APIs.",
                "responsibilities": "UI implementation, tests and cooperation with designers.",
                "location": "Polska",
                "salary_min": 15000,
                "salary_max": 22000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.MID_LEVEL,
                "contract_type": ContractType.B2B,
                "work_mode": WorkMode.REMOTE,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=38),
            },
            {
                "key": "internship",
                "company": "byteforge",
                "employer": "rekruter.byteforge@jobs-demo.test",
                "title": "Python Developer Internship",
                "description": "Paid internship in a backend development team.",
                "requirements": "Basic Python, object-oriented programming and Git.",
                "responsibilities": "Learning the codebase, fixing simple issues and writing tests.",
                "location": "Warszawa",
                "salary_min": 4500,
                "salary_max": 6000,
                "employment_type": EmploymentType.INTERNSHIP,
                "experience_level": ExperienceLevel.INTERN,
                "contract_type": ContractType.CONTRACT_OF_MANDATE,
                "work_mode": WorkMode.ONSITE,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=60),
            },
            {
                "key": "devops",
                "company": "cloudnest",
                "employer": "rekruter.cloudnest@jobs-demo.test",
                "title": "Senior DevOps Engineer",
                "description": "Designing and maintaining cloud platforms and deployment pipelines.",
                "requirements": "Kubernetes, Terraform, AWS or Azure, Linux and CI/CD.",
                "responsibilities": "Platform automation, observability and incident support.",
                "location": "Polska",
                "salary_min": 22000,
                "salary_max": 30000,
                "employment_type": EmploymentType.CONTRACT,
                "experience_level": ExperienceLevel.SENIOR,
                "contract_type": ContractType.B2B,
                "work_mode": WorkMode.REMOTE,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=50),
            },
            {
                "key": "cloud-support",
                "company": "cloudnest",
                "employer": "rekruter.cloudnest@jobs-demo.test",
                "title": "Cloud Support Engineer",
                "description": "Supporting customers using managed cloud environments.",
                "requirements": "Linux basics, networking, English and troubleshooting skills.",
                "responsibilities": "Handling tickets, diagnosing incidents and documenting solutions.",
                "location": "Kraków",
                "salary_min": 8000,
                "salary_max": 11000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.ENTRY_LEVEL,
                "contract_type": ContractType.EMPLOYMENT_CONTRACT,
                "work_mode": WorkMode.ONSITE,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=25),
            },
            {
                "key": "data-analyst",
                "company": "finpilot",
                "employer": "rekruter.finpilot@jobs-demo.test",
                "title": "Data Analyst",
                "description": "Analysis of financial and product data for business teams.",
                "requirements": "SQL, Python, Excel and a BI tool.",
                "responsibilities": "Dashboards, ad-hoc analyses and data-quality monitoring.",
                "location": "Wrocław",
                "salary_min": 13000,
                "salary_max": 18000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.MID_LEVEL,
                "contract_type": ContractType.EMPLOYMENT_CONTRACT,
                "work_mode": WorkMode.HYBRID,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=42),
            },
            {
                "key": "ml-engineer",
                "company": "finpilot",
                "employer": "rekruter.finpilot@jobs-demo.test",
                "title": "Machine Learning Engineer",
                "description": "Developing machine-learning services for fraud and risk detection.",
                "requirements": "Python, scikit-learn or PyTorch, SQL and Docker.",
                "responsibilities": "Model training, deployment and production monitoring.",
                "location": "Polska",
                "salary_min": 24000,
                "salary_max": 33000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.SENIOR,
                "contract_type": ContractType.B2B,
                "work_mode": WorkMode.REMOTE,
                "status": JobOfferStatus.DRAFT,
                "expires_at": now + timedelta(days=90),
            },
            {
                "key": "qa",
                "company": "healthsoft",
                "employer": "rekruter.healthsoft@jobs-demo.test",
                "title": "QA Automation Engineer",
                "description": "Automated testing of web applications used by medical staff.",
                "requirements": "Python or Java, Selenium or Playwright, API testing and CI.",
                "responsibilities": "Test automation, regression suites and quality reporting.",
                "location": "Poznań",
                "salary_min": 14000,
                "salary_max": 20000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.MID_LEVEL,
                "contract_type": ContractType.EMPLOYMENT_CONTRACT,
                "work_mode": WorkMode.HYBRID,
                "status": JobOfferStatus.ACTIVE,
                "expires_at": now + timedelta(days=35),
            },
            {
                "key": "ux",
                "company": "healthsoft",
                "employer": "rekruter.healthsoft@jobs-demo.test",
                "title": "Junior UX/UI Designer",
                "description": "Designing accessible interfaces for healthcare products.",
                "requirements": "Figma, portfolio, UX basics and communication skills.",
                "responsibilities": "Wireframes, prototypes, design-system maintenance and user research.",
                "location": "Poznań",
                "salary_min": 9000,
                "salary_max": 14000,
                "employment_type": EmploymentType.FULL_TIME,
                "experience_level": ExperienceLevel.JUNIOR,
                "contract_type": ContractType.EMPLOYMENT_CONTRACT,
                "work_mode": WorkMode.HYBRID,
                "status": JobOfferStatus.CLOSED,
                "expires_at": now + timedelta(days=10),
            },
        ]

        result = {}
        for row in rows:
            key = row.pop("key")
            company = companies[row.pop("company")]
            employer = employers[row.pop("employer")]

            offer = JobOffers.objects.filter(
                company=company,
                title=row["title"],
            ).first()

            if offer is None:
                offer = JobOffers.objects.create(
                    company=company,
                    employer=employer,
                    **row,
                )
            else:
                offer.employer = employer
                for field, value in row.items():
                    setattr(offer, field, value)
                offer.save()

            result[key] = offer

        return result

    def _seed_saved_jobs(self, candidates, offers):
        rows = [
            ("anna.kowalska@jobs-demo.test", "django"),
            ("anna.kowalska@jobs-demo.test", "junior-python"),
            ("piotr.nowak@jobs-demo.test", "devops"),
            ("piotr.nowak@jobs-demo.test", "cloud-support"),
            ("maria.wisniewska@jobs-demo.test", "data-analyst"),
            ("tomasz.wojcik@jobs-demo.test", "react"),
            ("zofia.kaminska@jobs-demo.test", "internship"),
        ]

        for candidate_email, offer_key in rows:
            SavedJobs.objects.get_or_create(
                candidate=candidates[candidate_email],
                job_offer=offers[offer_key],
            )

    def _seed_applications(self, candidates, cvs, offers):
        rows = [
            (
                "anna.kowalska@jobs-demo.test",
                "junior-python",
                ApplicationStatus.REVIEWED,
            ),
            (
                "anna.kowalska@jobs-demo.test",
                "django",
                ApplicationStatus.SENT,
            ),
            (
                "piotr.nowak@jobs-demo.test",
                "devops",
                ApplicationStatus.ACCEPTED,
            ),
            (
                "maria.wisniewska@jobs-demo.test",
                "data-analyst",
                ApplicationStatus.REVIEWED,
            ),
            (
                "tomasz.wojcik@jobs-demo.test",
                "react",
                ApplicationStatus.REJECTED,
            ),
            (
                "zofia.kaminska@jobs-demo.test",
                "internship",
                ApplicationStatus.SENT,
            ),
        ]

        for candidate_email, offer_key, status in rows:
            application, created = Applications.objects.get_or_create(
                job_offer=offers[offer_key],
                candidate=candidates[candidate_email],
                cv=cvs[candidate_email],
                defaults={"status": status},
            )

            if not created and application.status != status:
                application.status = status
                application.updated_at = timezone.now()
                application.save(update_fields=["status", "updated_at"])