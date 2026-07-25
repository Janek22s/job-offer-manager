from django.contrib.auth import SESSION_KEY
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta
from django.utils import timezone

from jobs.models import Users, Candidates, Employers, Companies, JobOffers


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.password = "password"

        self.user = Users(email="email@example.com", phone_number="+48123456789", role="Candidate", is_active=True)

        self.user.set_password(self.password)
        self.user.save()

        self.login_url = reverse("api:login_view")

    def test_user_can_log_in_with_valid_data(self):
        payload = {"email" : self.user.email, "password" : self.password}

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.data["message"], "User logged in successfully.")
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(response.data["user"]["phone_number"], self.user.phone_number)
        self.assertEqual(response.data["user"]["role"], self.user.role)

        self.assertNotIn("password", response.data["user"])

        self.assertIn(SESSION_KEY, self.client.session)
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

    def test_user_cannot_log_in_with_invalid_password(self):
        payload = {"email": self.user.email, "password": "wrong_password"}

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(str(response.data["non_field_errors"][0]), "Invalid email or password.")

        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_log_in_with_unknown_email(self):
        payload = {"email" : "unknown_email@example.com", "password" : self.password}

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(str(response.data["non_field_errors"][0]), "Invalid email or password.")

        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()

        payload = {"email" : self.user.email, "password" : self.password}

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_log_in_without_password(self):
        payload = {"email" : self.user.email}

        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_log_in_without_email(self):
            payload = {"password" : self.password}
    
            response = self.client.post(self.login_url, payload, format="json")
    
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("email", response.data)
            self.assertNotIn(SESSION_KEY, self.client.session)

class RegistrationAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('api:register_view')
        self.valid_payload = {"email" : "new_user@example.com", "phone_number" : "+48123456789", "password" : "password", "password_confirm" : "password", 
                              "role" : "Candidate"}

    def test_user_can_register_with_valid_credentials(self):
        self.assertFalse(Users.objects.filter(email=self.valid_payload["email"]).exists())
        self.assertFalse(Users.objects.filter(phone_number=self.valid_payload["phone_number"]).exists())

        response = self.client.post(self.register_url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Users.objects.filter(email=self.valid_payload["email"]).exists())
        self.assertTrue(Users.objects.filter(phone_number=self.valid_payload["phone_number"]).exists())

        user = Users.objects.get(email=self.valid_payload["email"])

        self.assertEqual(response.data["message"], "User registered successfully.")
        self.assertEqual(response.data["user"]["email"], user.email)
        self.assertEqual(response.data["user"]["phone_number"], user.phone_number)
        self.assertEqual(response.data["user"]["role"], user.role)

        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_without_password_confirmation(self):
        payload = self.valid_payload.copy()
        del payload["password_confirm"]

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Users.objects.filter(email=payload["email"]).exists())
        self.assertFalse(Users.objects.filter(phone_number=payload["phone_number"]).exists())

        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_with_invalid_password_confirmation(self):
        payload = self.valid_payload.copy()
        payload["password_confirm"] = "invalid_password"

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Users.objects.filter(email=payload["email"]).exists())
        self.assertFalse(Users.objects.filter(phone_number=payload["phone_number"]).exists())

        self.assertIn("password_confirm", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_with_invalid_role(self):
        payload = self.valid_payload.copy()
        payload["role"] = "invalid_role"

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(Users.objects.filter(email=payload["email"]).exists())
        self.assertFalse(Users.objects.filter(phone_number=payload["phone_number"]).exists())

        self.assertIn("role", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_with_existing_email(self):
        Users.objects.create_user(email="email@example.com", phone_number="+48987654321", password="password", role="Candidate", is_active=True)

        payload = self.valid_payload.copy()
        payload["email"] = "email@example.com"

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.assertFalse(Users.objects.filter(phone_number=payload["phone_number"]).exists())
        self.assertEqual(Users.objects.count(), 1)

        self.assertIn("email", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_with_existing_phone_number(self):
        Users.objects.create_user(email="new_email@example.com", phone_number="+48987654321", password="password", role="Candidate", is_active=True)

        payload = self.valid_payload.copy()
        payload["phone_number"] = "+48987654321"

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.assertFalse(Users.objects.filter(email=payload["email"]).exists())
        self.assertEqual(Users.objects.count(), 1)

        self.assertIn("phone_number", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_user_cannot_register_with_existing_email_using_different_letter_case(self):
        Users.objects.create_user(email="email@example.com", phone_number="+48987654321", password="password", role="Candidate", is_active=True)
    
        payload = self.valid_payload.copy()
        payload["email"] = "EmaiL@exAmple.com"

        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.assertFalse(Users.objects.filter(phone_number=payload["phone_number"]).exists())
        self.assertEqual(Users.objects.count(), 1)

        self.assertIn("email", response.data)
        self.assertNotIn(SESSION_KEY, self.client.session)
    
class UserProfileAPITests(APITestCase):
    def setUp(self):
        self.user = Users.objects.create_user(email="email@example.com", phone_number="+48123456789", password="password",
                    role="Candidate", is_active=True)

        self.profile_url = reverse("api:user_profile")

    def test_authenticated_user_can_get_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["phone_number"], self.user.phone_number)
        self.assertEqual(response.data["role"], self.user.role)

        self.assertNotIn("password", response.data)

    def test_unauthenticated_user_cannot_get_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_update_profile(self):
        self.client.force_authenticate(user=self.user)

        payload = {"phone_number" : "+48987654321"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["phone_number"], payload["phone_number"])

        self.user.refresh_from_db()

        self.assertEqual(self.user.phone_number, payload["phone_number"])
        self.assertEqual(self.user.email, "email@example.com")

    def test_user_cannot_update_profile_with_invalid_data(self):
        self.client.force_authenticate(user=self.user)

        payload = {"email": "invalid-email"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("email", response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "email@example.com")

    def test_user_cannot_update_profile_with_existing_email(self):
        self.client.force_authenticate(user=self.user)
        new_user = Users.objects.create_user(email="new_email@example.com", phone_number="+48918273645", password="password", 
                                role="Candidate", is_active=True)

        payload = {"email" : "new_email@example.com"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("email", response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "email@example.com")
        self.assertEqual(new_user.email, "new_email@example.com")

    def test_patch_updates_only_provided_fields(self):
        self.client.force_authenticate(user=self.user)

        original_email = self.user.email
        original_role = self.user.role

        payload = {"phone_number": "+48987654321"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.user.refresh_from_db()

        self.assertEqual(self.user.phone_number, payload["phone_number"])

        self.assertEqual(self.user.email, original_email)
        self.assertEqual(self.user.role, original_role)

    def test_authenticated_user_can_delete_profile(self):
        self.client.force_authenticate(user=self.user)

        user_id = self.user.id

        response = self.client.delete(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)
        self.assertFalse(Users.objects.filter(id=user_id).exists())

    def test_unauthenticated_user_cannot_delete_profile(self):
        user_id = self.user.id

        response = self.client.delete(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Users.objects.filter(id=user_id).exists())

class CandidateProfileAPITests(APITestCase):
    def setUp(self):
        self.user = Users.objects.create_user(email="email@example.com", phone_number="+48123456789", password="password", role="Candidate", is_active=True)
        self.candidate = Candidates.objects.create(user_id=self.user.id)

        self.profile_url = reverse("api:candidate_profile")

    def test_authenticated_candidate_can_get_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.data["user"], self.candidate.user_id)
        self.assertNotIn("password", response.data)

    def test_unauthenticated_candidate_cannot_get_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_authenticated_candidate_can_update_profile(self):
        self.client.force_authenticate(user=self.user)

        payload = {"first_name" : "Jan"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.first_name, payload["first_name"])

    def test_unauthenticated_candidate_cannot_update_profile(self):
        payload = {"first_name" : "Jan"}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_candidate_cannot_update_user_id(self):
        self.client.force_authenticate(user=self.user)

        original_user = self.candidate.user
        new_user = Users.objects.create_user(email="new_email@example.com", phone_number="+48975312468", password="password", role="Candidate", is_active=True)

        payload = {"user" : new_user.id}

        response = self.client.patch(self.profile_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.user, original_user)

    def test_candidate_without_profile_receives_404(self):
        user = Users.objects.create_user(email="new_email@example.com", phone_number="+48975312468", password="password", role="Candidate", is_active=True)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class OfferCreateAPITests(APITestCase):
    def setUp(self):
        self.company = Companies.objects.create(name="example")

        self.user = Users.objects.create_user(email="email@example.com", phone_number="+48123456789", password="password", role="Employer", is_active=True)
        self.employer = Employers.objects.create(user_id=self.user.id, company_id=self.company.id)

        self.url = reverse("api:offer_create")

    def test_offer_can_be_created_with_valid_data(self):
        self.client.force_authenticate(user=self.user)

        payload = {"employer" : self.employer.id, "company" : self.company.id, "title" : "New Offer", "location" : "Warszawa", 
                   "salary_min" : 1000, "salary_max" : 10000, "employment_type" : "Full-time", "experience_level" : "Junior", "contract_type" : "B2b",
                   "work_mode" : "Hybrid", "status" : "Active", "expires_at" : timezone.now() + timedelta(days=7)}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)    
        self.assertEqual(response.data["employer"], self.employer.id)
        self.assertEqual(response.data["company"], self.company.id)

        self.assertTrue(JobOffers.objects.filter(company=self.company, employer=self.employer).exists())

    def test_offer_cannot_be_created_with_invalid_data(self):
        self.client.force_authenticate(user=self.user)

        # example : salary_min > salary_max
        payload = {"employer" : self.employer.id, "company" : self.company.id, "title" : "New Offer", "salary_min" : 1000000, "salary_max" : 10000, 
                    "employment_type" : "Full-time", "experience_level" : "Junior", "contract_type" : "B2b", "work_mode" : "Hybrid", 
                    "expires_at" : timezone.now() + timedelta(days=7)}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertFalse(JobOffers.objects.filter(company=self.company, employer=self.employer).exists())

    def test_offer_cannot_be_created_with_invalid_employer(self):
        self.client.force_authenticate(user=self.user)

        new_company = Companies.objects.create(name="new_example")

        new_user = Users.objects.create_user(email="new_email@example.com", phone_number="+48123789456", password="password", role="Employer", is_active=True)
        new_employer = Employers.objects.create(user_id=new_user.id, company_id=new_company.id)

        payload = {"employer" : new_employer.id, "company" : self.company.id, "title" : "New Offer", "salary_min" : 1000, "salary_max" : 10000, 
                    "employment_type" : "Full-time", "experience_level" : "Junior", "contract_type" : "B2b", "work_mode" : "Hybrid", 
                    "expires_at" : timezone.now() + timedelta(days=7)}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertFalse(JobOffers.objects.filter(company=self.company, employer=self.employer).exists())

    def test_unauthenticated_user_cannot_create_offer(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)