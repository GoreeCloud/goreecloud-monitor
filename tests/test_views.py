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
        self.assertContains(response, "goreecloud-monitor-icon.svg")
        self.assertContains(response, "site.webmanifest")
        self.assertNotContains(response, "monitor-mark.svg")
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
        monitor = Monitor.objects.create(name="private-job-name", kind=Monitor.Kind.PUSH, interval_seconds=60)
        response = self.client.post(reverse("monitoring:push-heartbeat", args=[monitor.heartbeat_token]))
        self.assertEqual(response.status_code, 200)
        monitor.refresh_from_db()
        self.assertIsNotNone(monitor.last_heartbeat_at)
        self.assertNotContains(response, "private-job-name")
        self.assertEqual(set(response.json()), {"ok", "received_at"})

    def test_push_head_is_rejected_without_mutating_heartbeat(self):
        monitor = Monitor.objects.create(name="head-must-not-write", kind=Monitor.Kind.PUSH, interval_seconds=60)
        response = self.client.head(reverse("monitoring:push-heartbeat", args=[monitor.heartbeat_token]))
        self.assertEqual(response.status_code, 405)
        monitor.refresh_from_db()
        self.assertIsNone(monitor.last_heartbeat_at)

    def test_non_staff_monitor_detail_hides_push_token_and_diagnostics(self):
        monitor = Monitor.objects.create(
            name="restricted-push",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
            last_message="internal diagnostic secret-ish detail",
        )
        CheckResult.objects.create(
            monitor=monitor,
            success=False,
            observed_state=Monitor.State.DOWN,
            message="backend.internal.example refused connection",
        )
        Incident.objects.create(monitor=monitor, failure_reason="private failure detail")
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, monitor.heartbeat_token)
        self.assertNotContains(response, "internal diagnostic secret-ish detail")
        self.assertNotContains(response, "backend.internal.example")
        self.assertNotContains(response, "private failure detail")
        self.assertContains(response, "Credential protected")

    def test_staff_monitor_detail_can_access_push_credential(self):
        monitor = Monitor.objects.create(name="staff-push", kind=Monitor.Kind.PUSH, interval_seconds=60)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, monitor.heartbeat_token)

    def test_settings_requires_staff(self):
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 403)

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="")
    def test_settings_does_not_claim_partial_ntfy_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["ntfy_enabled"])

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    def test_settings_reports_complete_ntfy_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["ntfy_enabled"])
        self.assertEqual(response.context["glaze_version"], "1.0.0")

    @override_settings(
        MONITOR_ALLOWED_NETWORKS=["10.20.30.0/24", "fd00:1234::/64"],
        MANAGER_API_TOKEN="manager-secret",
        NTFY_BASE_URL="http://ntfy:80",
        NTFY_TOPIC="goreecloud-uptime",
        NTFY_TOKEN="publisher-secret",
    )
    def test_security_posture_is_staff_only_and_secret_free(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:security"))
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:security"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wardveil Security by GoreeCloud")
        self.assertContains(response, "Protected by Wardveil")
        self.assertContains(response, "2")
        self.assertNotContains(response, "10.20.30.0/24")
        self.assertNotContains(response, "fd00:1234::/64")
        self.assertNotContains(response, "manager-secret")
        self.assertNotContains(response, "publisher-secret")

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="super-secret-publisher-token")
    def test_notifications_reports_posture_without_exposing_token(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["ntfy_enabled"])
        self.assertNotContains(response, "super-secret-publisher-token")
        self.assertContains(response, "Operational events, not delivery receipts")

    def test_incident_history_requires_login_and_supports_status_filter(self):
        monitor = Monitor.objects.create(name="service-a", kind=Monitor.Kind.HTTPS, target="https://example.com")
        active = Incident.objects.create(monitor=monitor, failure_reason="down")
        Incident.objects.create(monitor=monitor, failure_reason="old", ended_at=timezone.now() - timedelta(minutes=1))
        response = self.client.get(reverse("monitoring:incident-list"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:incident-list"), {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["incidents"]), [active])

    def test_monitor_list_filters_by_name_state_and_kind(self):
        Monitor.objects.create(name="Alpha HTTPS", kind=Monitor.Kind.HTTPS, target="https://example.com", state=Monitor.State.UP)
        Monitor.objects.create(name="Beta TCP", kind=Monitor.Kind.TCP, target="example.com", port=443, state=Monitor.State.DOWN)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-list"), {"q": "Alpha", "state": "UP", "kind": "HTTPS"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([monitor.name for monitor in response.context["monitors"]], ["Alpha HTTPS"])

    def test_staff_can_rotate_push_token(self):
        monitor = Monitor.objects.create(name="rotate", kind=Monitor.Kind.PUSH, interval_seconds=60)
        old_token = monitor.heartbeat_token
        self.client.force_login(self.staff)
        response = self.client.post(reverse("monitoring:monitor-rotate-token", args=[monitor.pk]))
        self.assertEqual(response.status_code, 302)
        monitor.refresh_from_db()
        self.assertNotEqual(monitor.heartbeat_token, old_token)

    def test_health_responses_are_minimized(self):
        live = self.client.get(reverse("monitoring:health-live"))
        ready = self.client.get(reverse("monitoring:health-ready"))
        self.assertEqual(live.json(), {"ok": True})
        self.assertEqual(ready.json(), {"ok": True})

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_api_requires_bearer_token(self):
        response = self.client.get(reverse("monitoring:manager-summary"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")
        response = self.client.get(reverse("monitoring:manager-summary"), HTTP_AUTHORIZATION="Bearer manager-secret")
        self.assertEqual(response.status_code, 200)
