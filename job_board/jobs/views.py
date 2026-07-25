from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models.functions import Now

from .forms import RegisterForm, LoginForm, CandidateForm, EmployerForm, EditForm, ApplicationForm, NewOfferForm, ChangeStatusForm

from .models import Users, JobOffers, Candidates, Employers, Companies, Cvs, Applications, SavedJobs

def home(request):
    job_offers = JobOffers.objects.all()

    title = request.GET.get("title") or None
    company = request.GET.get("company") or None
    employment_type = request.GET.get("employment_type") or None
    experience_level = request.GET.get("experience_level") or None
    contract_type = request.GET.get("contract_type") or None
    work_mode = request.GET.get("work_mode") or None

    if title:
        job_offers = job_offers.filter(title=title)
    if company:
        job_offers = job_offers.filter(company__name=company)
    if employment_type:
        job_offers = job_offers.filter(employment_type=employment_type)
    if experience_level:
        job_offers = job_offers.filter(experience_level=experience_level)
    if contract_type:
        job_offers = job_offers.filter(contract_type=contract_type)
    if work_mode:
        job_offers = job_offers.filter(work_mode=work_mode)

    paginator = Paginator(job_offers, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    saved_offers_ids = None
    user = None

    if request.user.is_authenticated:
        user = request.user
        if user.role == "Candidate":
            candidate = Candidates.objects.get(user_id=user.id)
            saved_offers_ids = SavedJobs.objects.filter(candidate_id=candidate.id).values_list('job_offer_id', flat=True)
 
    return render(request, 'offers/home.html', {'user' : user, 'job_offers' : job_offers, 'page_obj' : page_obj, 'saved_offers_ids' : saved_offers_ids})

def offer_detail(request, offer_id):
    user = request.user
    offer = JobOffers.objects.get(id=offer_id)

    if not request.user.is_authenticated:
        return render(request, 'offers/offer_detail.html', {'offer' : offer})

    employer, candidate = None, None
    if user.role == 'Employer':
        employer = Employers.objects.get(user_id=user.id)
        return render(request, 'offers/offer_detail.html', {'offer' : offer, 'user' : user, 'employer' : employer})

    if user.role == 'Candidate':
        candidate = Candidates.objects.get(user_id=user.id)
        applications = Applications.objects.filter(job_offer_id=offer_id, candidate_id=candidate.id).order_by("-updated_at")
        return render(request, 'offers/offer_detail.html', {'offer' : offer, 'user' : user, 'applications' : applications})

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            role = form.cleaned_data["role"]
            password = form.cleaned_data["password1"]
            company = form.cleaned_data["company"]

            user = Users.objects.create_user(email=email, phone_number=phone_number, role=role, password=password)

            if role == 'Candidate':
                Candidates.objects.create(user_id=user.id)

            if role == 'Employer':
                Employers.objects.create(user_id=user.id, company_id=company.id)

            login(request, user)
            return redirect('offers:home')
        
    else:
        form = RegisterForm()

    companies = Companies.objects.all()
        
    return render(request, 'users/register.html', {'form' : form, 'companies' : companies})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=email, password=password)

            if user:
                login(request, user)
                return redirect('offers:home')
            
            else:
                form.add_error(None, "Invalid email or password")

    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form' : form})

@require_POST
def logout_view(request):
    logout(request)
    return redirect('offers:home')

# user = request.user

@login_required
def application_view(request, offer_id):
    user = request.user
    candidate = Candidates.objects.get(user_id=user.id)
    offer = JobOffers.objects.get(id=offer_id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            cv = form.save()
            cv.candidate_id = candidate.id
            cv.file_name = request.FILES['file_url'].name

            cv.save()

            message = form.cleaned_data.get("message")

            earliest_application = Applications.objects.filter(job_offer_id=offer_id, candidate_id=candidate.id).first()

            if earliest_application:
                Applications.objects.create(job_offer_id=offer_id, candidate_id=candidate.id, cv_id=cv.id, status='Sent', created_at=earliest_application.created_at, updated_at=Now())
            else:
                Applications.objects.create(job_offer_id=offer_id, candidate_id=candidate.id, cv_id=cv.id, status='Sent', created_at=Now(), updated_at=Now())

            return redirect('offers:offer_detail', offer_id)
        
    else:
        form = ApplicationForm()

    return render(request, 'offers/application.html', {'user' : user, 'candidate' : candidate, 'offer' : offer, 'form' : form})

@login_required
def candidate_profile_view(request):
    user = request.user

    candidate = Candidates.objects.filter(user_id=user.id).first()

    return render(request, 'candidate/candidate_profile.html', {'user' : user, 'candidate' : candidate})

@login_required
def candidate_profile_update_view(request):
    user = request.user

    candidate = Candidates.objects.filter(user_id=user.id).first()

    if request.method == "POST":
        form = CandidateForm(request.POST)

        if form.is_valid():

            # user.email = form.cleaned_data.get("email") or ""
            user.phone_number = form.cleaned_data.get("phone_number") or None
            candidate.first_name = form.cleaned_data.get("first_name") or None
            candidate.last_name = form.cleaned_data.get("last_name") or None
            candidate.bio = form.cleaned_data.get("bio") or None
            candidate.experience_level = form.cleaned_data.get("experience_level") or None

            user.save()
            candidate.save()

            return redirect('offers:candidate_profile')

        else:
            form.add_error(None, "Invalid data")

    else:
        form = CandidateForm()

    return render(request, 'candidate/candidate_profile_update.html', {'user' : user, 'candidate' : candidate, 'form' : form})

@login_required
def employer_profile_view(request):
    user = request.user

    employer = Employers.objects.filter(user_id=user.id).first()
    company = Companies.objects.filter(id=employer.company_id).first()

    return render(request, 'employer/employer_profile.html', {'user' : user, 'employer' : employer, 'company' : company})

@login_required
def employer_profile_update_view(request):
    user = request.user

    employer = Employers.objects.filter(user_id=user.id).first()

    if request.method == "POST":
        form = EmployerForm(request.POST)

        if form.is_valid():

            # user.email = form.cleaned_data.get("email") or ""
            user.phone_number = form.cleaned_data.get("phone_number") or None
            employer.first_name = form.cleaned_data.get("first_name") or None
            employer.last_name = form.cleaned_data.get("last_name") or None
            employer.position = form.cleaned_data.get("position") or None

            user.save()
            employer.save()

            return redirect('offers:employer_profile')

        else:
            form.add_error(None, "Invalid data")

    else:
        form = EmployerForm()

    companies = Companies.objects.all()

    return render(request, 'employer/employer_profile_update.html', {'user' : user, 'employer' : employer, 'form' : form, 'companies' : companies})

@login_required
def offer_edition_view(request, offer_id):
    offer = JobOffers.objects.get(id=offer_id)

    if request.method == "POST":
        form = EditForm(request.POST)

        if form.is_valid():
            offer.title = form.cleaned_data.get("title") or None
            offer.description = form.cleaned_data.get("description") or None
            offer.requirements = form.cleaned_data.get("requirements") or None
            offer.responsibilities = form.cleaned_data.get("responsibilities") or None
            offer.employment_type = form.cleaned_data.get("employment_type") or None
            offer.work_mode = form.cleaned_data.get("work_mode")
            offer.contract_type = form.cleaned_data.get("contract_type") or None
            offer.status = form.cleaned_data.get("status") or None
            offer.experience_level = form.cleaned_data.get("experience_level") or None
            offer.salary_min = form.cleaned_data.get("salary_min") or None
            offer.salary_max = form.cleaned_data.get("salary_max") or None

            offer.save()
            return redirect('offers:offer_detail', offer_id=offer_id)
        
    else:
        form = EditForm()

    return render(request, 'offers/offer_edition.html', {'form' : form, 'offer' : offer})

@login_required
def create_offer_view(request):
    user = request.user
    employer = Employers.objects.get(user_id=user.id)

    if request.method == "POST":
        form = NewOfferForm(request.POST)

        if form.is_valid():
            title = form.cleaned_data.get("title")
            description = form.cleaned_data.get("description") or None
            requirements = form.cleaned_data.get("requirements") or None
            responsibilities = form.cleaned_data.get("responsibilities") or None
            location = form.cleaned_data.get("location") 
            employment_type = form.cleaned_data.get("employment_type") 
            work_mode = form.cleaned_data.get("work_mode")
            contract_type = form.cleaned_data.get("contract_type") 
            status = form.cleaned_data.get("status") 
            experience_level = form.cleaned_data.get("experience_level") 
            salary_min = form.cleaned_data.get("salary_min") 
            salary_max = form.cleaned_data.get("salary_max")
            expiration_date = form.cleaned_data.get("expiration_date")

            JobOffers.objects.create(
                company_id=employer.company_id,
                employer_id=employer.id,
                title=title,
                description=description,
                requirements=requirements,
                responsibilities=responsibilities,
                location=location,
                employment_type=employment_type,
                work_mode=work_mode,
                contract_type=contract_type,
                status=status,
                experience_level=experience_level,
                salary_min=salary_min,
                salary_max=salary_max,
                expires_at=expiration_date
            )

            return redirect('offers:home')
    else:
        form = NewOfferForm()

    return render(request, 'offers/create_offer.html', {'employer' : employer, 'form' : form})

@login_required
def save_offer(request, offer_id):
    user = request.user
    candidate = Candidates.objects.get(user_id=user.id)
    offer = JobOffers.objects.get(id=offer_id)

    SavedJobs.objects.create(candidate_id=candidate.id, job_offer_id=offer.id)

    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def delete_form_saved(request, offer_id):
    user = request.user
    candidate = Candidates.objects.get(user_id=user.id)
    offer = JobOffers.objects.get(id=offer_id)

    SavedJobs.objects.get(candidate_id=candidate.id, job_offer_id=offer.id).delete()

    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def saved_offers_view(request):
    user = request.user
    candidate = Candidates.objects.get(user_id=user.id)
    saved_offers = SavedJobs.objects.filter(candidate_id=candidate.id)

    saved_offers_ids = None

    if request.user.is_authenticated:
        user = request.user
        if user.role == "Candidate":
            candidate = Candidates.objects.get(user_id=user.id)
            saved_offers_ids = SavedJobs.objects.filter(candidate_id=candidate.id).values_list('job_offer_id', flat=True)

    return render(request, 'candidate/saved_offers.html', {'user' : user, 'saved_offers' : saved_offers, "saved_offers_ids" : saved_offers_ids})

@login_required
@require_POST
def delete_offer(request, offer_id):
    JobOffers.objects.get(id=offer_id).delete()
    return redirect('offers:home')

@login_required
@require_POST
def delete_account(request):
    user = request.user

    logout(request)

    candidate = Candidates.objects.filter(user_id=user.id).first()
    employer = Employers.objects.filter(user_id=user.id).first()

    if candidate:
        for cv in candidate.cvs.all():
            if cv.file_url:
                cv.file_url.delete(save=False)

        user.delete()

    elif employer:
        user.is_active = False
        user.save()

        JobOffers.objects.filter(employer_id=employer.id, status="Active",).update(status="Closed")

    return redirect('offers:home')

@login_required
def employer_applications_view(request):
    user = request.user
    employer = Employers.objects.get(user=user)
    
    applications = Applications.objects.filter(
        job_offer__employer=employer
    ).order_by(
        'candidate', 
        'job_offer', 
        '-created_at'
    ).distinct(
        'candidate', 
        'job_offer'
    )

    if request.method == "POST":
        form = ChangeStatusForm(request.POST)

        job_offer_id = request.POST.get("job_offer_id")
        candidate_id = request.POST.get("candidate_id")
        cv_id = request.POST.get("cv_id")

        application = Applications.objects.get(job_offer_id=job_offer_id, candidate_id=candidate_id, cv_id=cv_id)

        if form.is_valid():
            new_status = form.cleaned_data["status"]

            application.status = new_status
            application.save()

        return redirect(request.META.get("HTTP_REFERER", "/"))

    else:
        form = ChangeStatusForm()
    
    
    return render(request, 'employer/applications_for_offers.html', {'applications': applications, 'form' : form})