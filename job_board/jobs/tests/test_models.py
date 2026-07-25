from django.test import TestCase
from django.db import IntegrityError, transaction

from datetime import timedelta
from django.utils import timezone

from jobs.models import Users, Companies, Employers, JobOffers

class UsersModelTest(TestCase):
    def setUp(self):
        self.user = Users.objects.create_user(email="email@example.com", phone_number="+48123456789", password="password", role="Candidate")

    def test_user_is_created(self):
        self.assertEqual(Users.objects.filter(email=self.user.email).count(), 1)

    def test_string_representation(self):
        self.assertEqual(str(self.user), "email@example.com")

    def test_default_values(self):
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_timestamps_are_created(self):
        self.assertIsNotNone(self.user.created_at)
        self.assertIsNotNone(self.user.updated_at)

    def test_wrong_password_is_rejected(self):
        self.assertFalse(self.user.check_password("wrong_password"))

    def test_email_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            Users.objects.create_user(email="email@example.com", password="new_password", role="Candidate")

    def test_phone_number_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            Users.objects.create_user(email="new_email@example.com", phone_number="+48123456789", password="password", role="Candidate")

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, "password")
        self.assertTrue(self.user.check_password("password"))

    def test_create_superuser(self):
        admin = Users.objects.create_superuser(email="admin@example.com", password="admin-password")

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.role, "Admin")
        self.assertTrue(admin.check_password("admin-password"))

class JobOffersModelTest(TestCase):
    def setUp(self):
        self.company = Companies.objects.create(name="company_name")

        self.user = Users.objects.create_user(email="email@example.com", phone_number="+48123456789", password="password", role="Candidate")
        self.employer = Employers.objects.create(user_id=self.user.id, company_id=self.company.id)

        self.valid_payload = {"employer_id" : self.employer.id, "company_id" : self.company.id, "title" : "New Offer", "location" : "Warszawa", 
                    "salary_min" : 1000, "salary_max" : 10000, "employment_type" : "Full-time", "experience_level" : "Junior", 
                    "contract_type" : "B2b", "work_mode" : "Hybrid", "status" : "Active", "expires_at" : timezone.now() + timedelta(days=7)}

        self.offer = JobOffers.objects.create(**self.valid_payload)

    def test_offer_is_created(self):
        self.assertEqual(JobOffers.objects.count(), 1)

    def test_offer_cannot_have_salary_min_greater_than_salary_max(self):
        payload = self.valid_payload.copy()
        payload["salary_min"] = 100000
        payload["salary_max"] = 10000

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobOffers.objects.create(**payload)

        self.assertEqual(JobOffers.objects.count(), 1)

    def test_offer_cannot_have_negative_salary_min(self):
        payload = self.valid_payload.copy()
        payload["salary_min"] = -1

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobOffers.objects.create(**payload)

        self.assertEqual(JobOffers.objects.count(), 1)

    def test_offer_cannot_have_invalid_employment_type(self):
        payload = self.valid_payload.copy()
        payload["employment_type"] = "Unknown"

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobOffers.objects.create(**payload)

    def test_deleting_employer_deletes_offer(self):
        employer_id = self.employer.id
        offer_id = self.offer.id
        self.employer.delete()

        self.assertFalse(Employers.objects.filter(id=employer_id).exists())
        self.assertFalse(JobOffers.objects.filter(id=offer_id).exists())

    def test_deleting_company_deletes_offer(self):
        offer_id = self.offer.id

        self.company.delete()

        self.assertFalse(JobOffers.objects.filter(id=offer_id).exists())
        