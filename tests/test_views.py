from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from monitoring.models import CheckResult, Incident, Monitor


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
        self.assertContains(response, "GoreeCloud Monitor")
        self.assertContains(response, "goreecloud-monitor.svg")
        self.assertContains(response, "glaze.accessibility.css")
        self.assertContains(response, "wardveil.css")
        self.assertContains(response, "Protected by Wardveil")
        self.assertContains(response, "data-appearance-toggle")

    def test_authenticated_pages_receive_wardveil_browser_headers(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response["Content-Security-Policy"].split("; ")[0], "default-src 'self'")
        self.assertIn("camera=()", response["Permissions-Policy"])
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow, noarchive, nosnippet")
        self.assertEqual(response["Cache-Control"], "no-store, max-age=0, private")

    def test_non_staff_cannot_create_monitor(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-create"))
        self.assertEqual(response.status_code, 403)

    def test_push_endpoint_records_heartbeat_and_minimizes_response(self):
        monitor = Monitor.objects.create(name="push", kind=Monitor.Kind.PUSH, interval_seconds=60)
        url = reverse("monitoring:push-heartbeat", kwargs={"token": str(monitor.heartbeat_token)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)
        self.assertNotIn("monitor", response.json())
        self.assertIn("received_at", response.json())
        monitor.refresh_from_db()
        self.assertIsNotNone(monitor.last_heartbeat_at)

    def test_push_head_is_rejected_without_mutating_heartbeat(self):
        monitor = Monitor.objects.create(name="push-head", kind=Monitor.Kind.PUSH, interval_seconds=60)
        url = reverse("monitoring:push-heartbeat", kwargs={"token": str(monitor.heartbeat_token)})
        response = self.client.head(url)
        self.assertEqual(response.status_code, 405)
        monitor.refresh_from_db()
        self.assertIsNone(monitor.last_heartbeat_at)

    def test_manager_api_requires_bearer_token(self):
        response = self.client.get(reverse("monitoring:manager-summary"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Bearer realm="GoreeCloud Monitor"')

    @override_settings(MANAGER_API_TOKEN="expected-token")
    def test_manager_api_accepts_bearer_token(self):
        response = self.client.get(
            reverse("monitoring:manager-summary"),
            HTTP_AUTHORIZATION="Bearer expected-token",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("monitors", response.json())

    def test_non_staff_monitor_detail_hides_push_token_and_diagnostics(self):
        monitor = Monitor.objects.create(name="private monitor", kind=Monitor.Kind.PUSH, interval_seconds=60)
        CheckResult.objects.create(
            monitor=monitor,
            status=CheckResult.Status.DOWN,
            message="database.internal.example:5432 connection refused",
            latency_ms=10,
        )
        Incident.objects.create(
            monitor=monitor,
            opened_at=timezone.now(),
            reason="sensitive.internal.example failed",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-detail", kwargs={"pk": monitor.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, str(monitor.heartbeat_token))
        self.assertNotContains(response, "database.internal.example")
        self.assertNotContains(response, "sensitive.internal.example")
        self.assertContains(response, "Detailed diagnostics are available to staff only")

    def test_staff_monitor_detail_can_access_push_credential(self):
        monitor = Monitor.objects.create(name="staff monitor", kind=Monitor.Kind.PUSH, interval_seconds=60)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", kwargs={"pk": monitor.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(monitor.heartbeat_token))
        self.assertContains(response, "Rotate heartbeat token")

    def test_staff_can_rotate_push_token(self):
        monitor = Monitor.objects.create(name="rotate", kind=Monitor.Kind.PUSH, interval_seconds=60)
        original_token = monitor.heartbeat_token
        self.client.force_login(self.staff)
        response = self.client.post(reverse("monitoring:monitor-rotate-token", kwargs={"pk": monitor.pk}))
        self.assertEqual(response.status_code, 302)
        monitor.refresh_from_db()
        self.assertNotEqual(monitor.heartbeat_token, original_token)

    def test_settings_requires_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 403)

    @override_settings(NTFY_BASE_URL="https://notify.example.test", NTFY_TOPIC="test", NTFY_TOKEN="secret")
    def test_settings_reports_complete_ntfy_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enabled")
        self.assertNotContains(response, "secret")

    @override_settings(NTFY_BASE_URL="https://notify.example.test", NTFY_TOPIC="test", NTFY_TOKEN="")
    def test_settings_does_not_claim_partial_ntfy_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incomplete")

    def test_notifications_reports_posture_without_exposing_token(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GoreeCloud Notify")
        self.assertNotContains(response, "NTFY_TOKEN")

    def test_incident_history_requires_login_and_supports_status_filter(self):
        monitor = Monitor.objects.create(name="web", kind=Monitor.Kind.HTTP, target="https://example.com")
        Incident.objects.create(monitor=monitor, opened_at=timezone.now(), reason="down")
        Incident.objects.create(
            monitor=monitor,
            opened_at=timezone.now() - timedelta(hours=1),
            recovered_at=timezone.now(),
            reason="recovered",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:incident-list"), {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "down")
        self.assertNotContains(response, "recovered")

    def test_monitor_list_filters_by_name_state_and_kind(self):
        Monitor.objects.create(name="API", kind=Monitor.Kind.HTTP, target="https://api.example.com")
        Monitor.objects.create(name="DB", kind=Monitor.Kind.TCP, target="db.example.com", port=5432)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-list"), {"q": "API", "kind": "HTTP"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API")
        self.assertNotContains(response, "DB")

    def test_security_posture_is_staff_only_and_secret_free(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:security"))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:security"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wardveil Security by GoreeCloud")
        self.assertNotContains(response, "DJANGO_SECRET_KEY")

    def test_health_responses_are_minimized(self):
        response = self.client.get(reverse("monitoring:health-live"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
