from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from monitoring.models import Monitor


class ViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="strong-password")
        self.staff = get_user_model().objects.create_user(username="staff", password="strong-password", is_staff=True)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_create_monitor(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-create"))
        self.assertEqual(response.status_code, 403)

    def test_push_endpoint_records_heartbeat(self):
        monitor = Monitor.objects.create(name="job", kind=Monitor.Kind.PUSH, interval_seconds=60)
        response = self.client.post(reverse("monitoring:push-heartbeat", args=[monitor.heartbeat_token]))
        self.assertEqual(response.status_code, 200)
        monitor.refresh_from_db()
        self.assertIsNotNone(monitor.last_heartbeat_at)

    def test_settings_requires_login(self):
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_rotate_push_token(self):
        monitor = Monitor.objects.create(name="rotate", kind=Monitor.Kind.PUSH, interval_seconds=60)
        old_token = monitor.heartbeat_token
        self.client.force_login(self.staff)
        response = self.client.post(reverse("monitoring:monitor-rotate-token", args=[monitor.pk]))
        self.assertEqual(response.status_code, 302)
        monitor.refresh_from_db()
        self.assertNotEqual(monitor.heartbeat_token, old_token)

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_api_requires_bearer_token(self):
        response = self.client.get(reverse("monitoring:manager-summary"))
        self.assertEqual(response.status_code, 401)
        response = self.client.get(reverse("monitoring:manager-summary"), HTTP_AUTHORIZATION="Bearer manager-secret")
        self.assertEqual(response.status_code, 200)
