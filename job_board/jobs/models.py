from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db.models.functions import Now
from django.db.models import F, Q

class UserRole(models.TextChoices):
    CANDIDATE = "Candidate", "Candidate"
    EMPLOYER = "Employer", "Employer"
    ADMIN = "Admin", "Admin"


class ExperienceLevel(models.TextChoices):
    INTERN = "Intern", "Intern"
    ENTRY_LEVEL = "Entry level", "Entry level"
    JUNIOR = "Junior", "Junior"
    MID_LEVEL = "Mid level", "Mid level"
    SENIOR = "Senior", "Senior"
    LEAD = "Lead", "Lead"
    EXPERT = "Expert", "Expert"


class EmploymentType(models.TextChoices):
    FULL_TIME = "Full-time", "Full-time"
    PART_TIME = "Part-time", "Part-time"
    CONTRACT = "Contract", "Contract"
    TEMPORARY = "Temporary", "Temporary"
    INTERNSHIP = "Internship", "Internship"
    SEASONAL = "Seasonal", "Seasonal"
    VOLUNTEER = "Volunteer", "Volunteer"


class ContractType(models.TextChoices):
    B2B = "B2b", "B2b"
    EMPLOYMENT_CONTRACT = "Employment contract", "Employment contract"
    CONTRACT_OF_MANDATE = "Contract of mandate", "Contract of mandate"
    CONTRACT_FOR_SPECIFIC_WORK = "Contract for specific work", "Contract for specific work"


class WorkMode(models.TextChoices):
    REMOTE = "Remote", "Remote"
    HYBRID = "Hybrid", "Hybrid"
    ONSITE = "Onsite", "Onsite"


class JobOfferStatus(models.TextChoices):
    DRAFT = "Draft", "Draft"
    ACTIVE = "Active", "Active"
    CLOSED = "Closed", "Closed"
    EXPIRED = "Expired", "Expired"


class ApplicationStatus(models.TextChoices):
    SENT = "Sent", "Sent"
    REVIEWED = "Reviewed", "Reviewed"
    REJECTED = "Rejected", "Rejected"
    ACCEPTED = "Accepted", "Accepted"

class Applications(models.Model):
    pk = models.CompositePrimaryKey('job_offer', 'candidate', 'cv')
    job_offer = models.ForeignKey('JobOffers', on_delete=models.CASCADE, db_column="job_offer_id")
    candidate = models.ForeignKey('Candidates', on_delete=models.CASCADE, db_column="candidate_id")
    cv = models.ForeignKey('Cvs', on_delete=models.CASCADE, db_column="cv_id")
    status = models.CharField(choices=ApplicationStatus.choices)
    created_at = models.DateTimeField(editable=False, db_default=Now())
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'applications'
        constraints = [models.CheckConstraint(condition=Q(status__in=ApplicationStatus.values), name="applications_status_check")]


class Candidates(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    experience_level = models.CharField(blank=True, null=True, choices=ExperienceLevel.choices)

    class Meta:
        db_table = 'candidates'
        constraints  = [models.CheckConstraint(condition=(Q(experience_level__isnull=True) | Q(experience_level__in=ExperienceLevel.values)), name="candidates_experience_level_check")]


class Companies(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    size = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(editable=False, db_default=Now())

    class Meta:
        db_table = 'companies'

    def __str__(self):
        return f"{self.name}"


class Cvs(models.Model):
    id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(Candidates, on_delete=models.CASCADE, db_column="candidate_id", blank=True, null=True, related_name="cvs")
    file_url = models.FileField(max_length=500, upload_to="cvs/", validators=[FileExtensionValidator(allowed_extensions=["pdf"])])
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(editable=False, db_default=Now())

    class Meta:
        db_table = 'cvs'


class Employers(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, db_column="company_id", blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'employers'


class JobOffers(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, db_column="company_id", blank=True, null=True)
    employer = models.ForeignKey(Employers, on_delete=models.CASCADE, db_column="employer_id", blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255)
    salary_min = models.IntegerField()
    salary_max = models.IntegerField()
    employment_type = models.CharField(choices=EmploymentType.choices)
    experience_level = models.CharField(choices=ExperienceLevel.choices)
    contract_type = models.CharField(choices=ContractType.choices)
    work_mode = models.CharField(choices=WorkMode.choices)
    status = models.CharField(choices=JobOfferStatus.choices)
    created_at = models.DateTimeField(editable=False, db_default=Now())
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'job_offers'
        constraints = [
            models.CheckConstraint(
                condition=Q(employment_type__in=EmploymentType.values),
                name="job_offers_employment_type_check"
            ),
            models.CheckConstraint(
                condition=Q(experience_level__in=ExperienceLevel.values),
                name="job_offers_experience_level_check"
            ),
            models.CheckConstraint(
                condition=Q(contract_type__in=ContractType.values),
                name="job_offers_contract_type_check"
            ),
            models.CheckConstraint(
                condition=Q(work_mode__in=WorkMode.values),
                name="job_offers_work_mode_check"
            ),
            models.CheckConstraint(
                condition=Q(status__in=JobOfferStatus.values),
                name="job_offers_status_check"
            ),
            models.CheckConstraint(
                condition=Q(salary_min__gte=0),
                name="salary_min_pos"
            ),
            models.CheckConstraint(
                condition=Q(salary_max__gte=F("salary_min")),
                name="salary_max_pos"
            ),
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("created_at")),
                name="expires_after_creation"
            ),
        ]


class SavedJobs(models.Model):
    pk = models.CompositePrimaryKey('candidate', 'job_offer')
    candidate = models.ForeignKey(Candidates, on_delete=models.CASCADE, db_column="candidate_id")
    job_offer = models.ForeignKey(JobOffers, on_delete=models.CASCADE, db_column="job_offer_id")
    created_at = models.DateTimeField(editable=False, db_default=Now())

    class Meta:
        db_table = 'saved_jobs'

class UsersManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "Admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)

class Users(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)

    email = models.EmailField(unique=True, max_length=255)
    phone_number = models.CharField(unique=True, max_length=20, null=True, blank=True)

    role = models.CharField(max_length=15, choices=UserRole.choices)

    is_active = models.BooleanField(default=True, db_default=True)
    is_staff = models.BooleanField(default=False, db_default=False)

    created_at = models.DateTimeField(editable=False, db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UsersManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        constraints = [models.CheckConstraint(condition=Q(role__in=UserRole.values), name="users_role_check")]

    def __str__(self):
        return self.email