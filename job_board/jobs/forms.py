from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from .models import Users, Companies, Cvs
from django.utils import timezone


class RegisterForm(forms.Form):
    email = forms.EmailField(label="users_email", required=True)
    phone_number = forms.CharField(label="users_phone", max_length=20)
    role = forms.ChoiceField(label="choose_your_role", choices=[("Employer", "Employer"), ("Candidate", "Candidate")])
    company = forms.ModelChoiceField(queryset=Companies.objects.all(), required=False)

    password1 = forms.CharField(label="password1", widget=forms.PasswordInput)
    password2 = forms.CharField(label="password2", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"]

        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("Email")
        
        return email

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        company = cleaned_data.get("company")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if role == "Employer" and company is None:
            self.add_error(
                "company",
                "Wybór firmy jest wymagany dla pracodawcy.",
            )
        
        if role == "Candidate":
            cleaned_data["company"] = None

        if password1 and password2 and password1 != password2:
            self.add_error(
                "password2",
                "Podane hasła nie są takie same.",
            )
        
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField(label="users_email", required=True)
    password = forms.CharField(label="password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")

        if email and not Users.objects.filter(email=email).exists():
            raise forms.ValidationError("Invalid email or password")

        return cleaned_data
    
class CandidateForm(forms.Form):
    # email = forms.EmailField(label="updated_email", required=False)
    phone_number = forms.CharField(label="updated_phone", required=False)
    first_name = forms.CharField(label="updated_first_name", required=False)
    last_name = forms.CharField(label="updated_last_name", required=False)
    bio = forms.CharField(label="updated_bio", required=False)
    experience_level = forms.ChoiceField(label="choose_your_role", choices= [
        ("Intern", "Intern"), 
        ("Entry level", "Entry level"),
        ("Junior", "Junior"), 
        ("Mid level", "Mid level"), 
        ("Senior", "Senior"), 
        ("Lead", "Lead"), 
        ("Expert", "Expert"),
        ], required=False) 
    
class EmployerForm(forms.Form):
    phone_number = forms.CharField(label="updated_phone", required=False)
    first_name = forms.CharField(label="updated_first_name", required=False)
    last_name = forms.CharField(label="updated_last_name", required=False)
    position = forms.CharField(label="updated_position", required=False)

class EditForm(forms.Form):
    EMPLOYMENT_TYPE_CHOICES = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Contract", "Contract"),
        ("Temporary", "Temporary"),
        ("Internship", "Internship"),
        ("Seasonal", "Seasonal"),
        ("Volunteer", "Volunteer"),
    ]

    WORK_MODE_CHOICES = [
        ("Remote", "Remote"),
        ("Hybrid", "Hybrid"),
        ("Onsite", "Onsite"),
    ]

    CONTRACT_TYPE_CHOICES = [
        ("B2b", "B2b"),
        ("Employment contract", "Employment contract"),
        ("Contract of mandate", "Contract of mandate"),
        ("Contract for specific work", "Contract for specific work"),
    ]

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Active", "Active"),
        ("Closed", "Closed"),
        ("Expired", "Expired"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("Intern", "Intern"),
        ("Entry level", "Entry level"),
        ("Junior", "Junior"),
        ("Mid level", "Mid level"),
        ("Senior", "Senior"),
        ("Lead", "Lead"),
        ("Expert", "Expert"),
    ]

    title = forms.CharField(
        label="title",
        required=False,
        max_length=255,
    )

    description = forms.CharField(
        label="description",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    requirements = forms.CharField(
        label="requirements",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    responsibilities = forms.CharField(
        label="responsibilities",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    employment_type = forms.ChoiceField(
        label="employment_type",
        choices=EMPLOYMENT_TYPE_CHOICES,
        required=False,
    )

    work_mode = forms.ChoiceField(
        label="Work mode",
        choices=WORK_MODE_CHOICES,
        required=False,
    )

    contract_type = forms.ChoiceField(
        label="Contract type",
        choices=CONTRACT_TYPE_CHOICES,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        choices=STATUS_CHOICES,
        required=False,
    )

    experience_level = forms.ChoiceField(
        label="Experience level",
        choices=EXPERIENCE_LEVEL_CHOICES,
        required=False,
    )

    salary_min = forms.DecimalField(
        label="Minimum salary",
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    salary_max = forms.DecimalField(
        label="Maximum salary",
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    def clean(self):
        cleaned_data = super().clean()

        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            self.add_error(
                "salary_max",
                "Maximum salary cannot be lower than minimum salary.",
            )

        return cleaned_data
    
class ApplicationForm(forms.ModelForm):
    message = forms.CharField(label="messagem", required=False, widget=forms.Textarea)
    
    class Meta:
        model = Cvs
        fields = ["file_url"]
        labels = {"file_url": "CV"}

class NewOfferForm(forms.Form):
    EMPLOYMENT_TYPE_CHOICES = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Contract", "Contract"),
        ("Temporary", "Temporary"),
        ("Internship", "Internship"),
        ("Seasonal", "Seasonal"),
        ("Volunteer", "Volunteer"),
    ]

    WORK_MODE_CHOICES = [
        ("Remote", "Remote"),
        ("Hybrid", "Hybrid"),
        ("Onsite", "Onsite"),
    ]

    CONTRACT_TYPE_CHOICES = [
        ("B2b", "B2b"),
        ("Employment contract", "Employment contract"),
        ("Contract of mandate", "Contract of mandate"),
        ("Contract for specific work", "Contract for specific work"),
    ]

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Active", "Active"),
        ("Closed", "Closed"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("Intern", "Intern"),
        ("Entry level", "Entry level"),
        ("Junior", "Junior"),
        ("Mid level", "Mid level"),
        ("Senior", "Senior"),
        ("Lead", "Lead"),
        ("Expert", "Expert"),
    ]

    title = forms.CharField(
        label="title",
        required=True,
        max_length=255,
    )

    description = forms.CharField(
        label="description",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    requirements = forms.CharField(
        label="requirements",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    responsibilities = forms.CharField(
        label="responsibilities",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    location = forms.CharField(
        label="location",
        required=True,
        max_length=255
    )

    employment_type = forms.ChoiceField(
        label="employment_type",
        choices=EMPLOYMENT_TYPE_CHOICES,
        required=True,
    )

    work_mode = forms.ChoiceField(
        label="Work mode",
        choices=WORK_MODE_CHOICES,
        required=True,
    )

    contract_type = forms.ChoiceField(
        label="Contract type",
        choices=CONTRACT_TYPE_CHOICES,
        required=True,
    )

    status = forms.ChoiceField(
        label="Status",
        choices=STATUS_CHOICES,
        required=True,
    )

    experience_level = forms.ChoiceField(
        label="Experience level",
        choices=EXPERIENCE_LEVEL_CHOICES,
        required=True,
    )

    salary_min = forms.DecimalField(
        label="Minimum salary",
        required=True,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    salary_max = forms.DecimalField(
        label="Maximum salary",
        required=True,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )

    expiration_date = forms.DateField(
        label="expiration_date",
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()

        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        expiration_date = self.cleaned_data.get("expiration_date")

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            self.add_error(
                "salary_max",
                "Maximum salary cannot be lower than minimum salary.",
            )
        
        if expiration_date and expiration_date < timezone.localdate():
            self.add_error(
                "expiration_date",
                "Expiration date cannot be earlier than today."
            )

        return cleaned_data

class ChangeStatusForm(forms.Form):
    status = forms.ChoiceField(label="status", choices=[("Reviewed", "Reviewed"), ("Rejected", "Rejected"), ("Accepted", "Accepted")])