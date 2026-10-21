from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academics.models import Course, Department, Institution, Semester, Subject

User = get_user_model()


class UniversalSearchViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin-search@example.com", password="test-password-123",
            first_name="Search", last_name="Admin", role=User.Roles.ADMIN,
        )

    def test_search_requires_login(self):
        response = self.client.get(reverse("dashboard:search"), {"q": "math"})
        self.assertEqual(response.status_code, 302)

    def test_short_query_returns_empty_results(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:search"), {"q": "a"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_admin_search_returns_matching_student(self):
        student_user = User.objects.create_user(
            email="student-search@example.com", password="test-password-123",
            first_name="Mira", last_name="Patel", role=User.Roles.STUDENT,
        )
        from apps.students.models import Student
        Student.objects.create(user=student_user, student_id="STU-SEARCH-01")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:search"), {"q": "Mira"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["title"] == "Mira Patel" for item in response.json()["results"]))
