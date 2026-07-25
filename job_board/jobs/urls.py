from django.urls import path
from . import views

app_name = 'offers'

urlpatterns = [
    path('', views.home, name='home'),
    path('<int:offer_id>/offer_detail', views.offer_detail, name='offer_detail'),
    path('<int:offer_id>/offer_detail/application/', views.application_view, name='application'),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("candidate_profile/", views.candidate_profile_view, name="candidate_profile"),
    path("employer_profile/", views.employer_profile_view, name="employer_profile"),
    path("candidate_profile_update/", views.candidate_profile_update_view, name="candidate_profile_update"),
    path("employer_profile_update/", views.employer_profile_update_view, name="employer_profile_update"),
    path("<int:offer_id>/offer_detail/edit/", views.offer_edition_view, name="offer_edition"),
    path("create_offer/", views.create_offer_view, name="create_offer"),
    path('<int:offer_id>/save/', views.save_offer, name='save_offer'),
    path('<int:offer_id>/delete_form_saved/', views.delete_form_saved, name='delete_form_saved'),
    path("saved_offers/", views.saved_offers_view, name="saved_offers"),
    path("<int:offer_id>delete_offer/", views.delete_offer, name="delete_offer"),
    path("delete_account/", views.delete_account, name="delete_account"),
    path("employer_applicaitons/", views.employer_applications_view, name="employer_applications")
]