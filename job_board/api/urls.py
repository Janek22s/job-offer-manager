from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('auth/register/', views.register_view, name="register_view"),
    path('auth/login/', views.login_view, name="login_view"),
    path('auth/logout/', views.logout_view, name="logout_view"),
    path('users/me/', views.user_profile, name="user_profile"),
    path('admin/users/', views.user_list, name="user_list"),
    path('admin/users/<int:user_id>/', views.user_profile_admin, name="user_profile_admin"),
    path('candidates/me/', views.candidate_profile, name="candidate_profile"),
    path('candidates/<int:candidate_id>/', views.candidate_view, name="candidate_view"),
    path('employers/me/', views.employer_profile, name="employer_profile"),
    path('employers/<int:employer_id>/', views.employer_view, name="employer_view"),
    path('companies/', views.company_list, name="company_list"),
    path('companies/<int:company_id>/', views.company_view, name="company_view"),
    path('companies/patch/<int:company_id>/', views.company_view_patch, name="company_view_patch"),
    path('admin/companies/delete/<int:company_id>/', views.company_view_delete, name="company_view_delete"),    
    path('admin/companies/post/', views.company_view_create, name="company_view_create"),
    path('companies/<int:company_id>/job_offers/', views.company_job_offers, name="company_job_offers"),
    path('companies/<int:company_id>/employers/', views.company_employers, name="company_employers"),
    path('job-offers/', views.offer_list, name="offer_list"),
    path('job-offers/<int:offer_id>/', views.offer_view, name="offer_view"),
    path('job-offers/<int:offer_id>/edit/', views.offer_edit, name="offer_edit"),
    path('job-offers/create/', views.offer_create, name="offer_create"),
    path('admin/job-offers/create/<int:company_id>/<int:employer_id>/', views.admin_offer_create, name="admin_offer_create"),
    path('employers/me/job-offers/', views.employer_offers, name="employer_offers"),
    path('candidates/me/applications/', views.candidate_applications, name="candidate_applications"),
    path('candidates/me/applications/create/<int:offer_id>/', views.application_create, name="application_create"),
    path('employers/me/applications/', views.employer_applications, name="employer_applications"),
    path('employers/me/applications/<int:offer_id>/<int:candidate_id>/<int:cv_id>/status/', views.application_change_status, name="application_change_status"),
    path('candidates/me/cvs/', views.cv_create, name="cv_create")
]