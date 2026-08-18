from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from monitoring.models import CheckResult, Incident, Monitor, hash_heartbeat_token, heartbeat_token_is_digest


class ViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="strong-password")
        self.staff = get_user_model().objects.create_user(username="staff", password="strong-password", is_staff=True)

    def test_dashboard_requires_login(self): self.assertEqual(self.client.get(reverse("monitoring:dashboard")).status_code, 302)

    def test_authenticated_dashboard(self):
        self.client.force_login(self.user); response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response.status_code, 200); self.assertContains(response, "GoreeCloud Monitor"); self.assertContains(response, "monitor-mark.svg"); self.assertContains(response, "glaze.accessibility.css"); self.assertContains(response, "wardveil.css"); self.assertContains(response, "Protected by Wardveil"); self.assertContains(response, "data-appearance-toggle")

    def test_authenticated_pages_receive_wardveil_browser_headers_and_request_id(self):
        self.client.force_login(self.user); response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response["Content-Security-Policy"].split("; ")[0], "default-src 'self'"); self.assertIn("camera=()", response["Permissions-Policy"]); self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin"); self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow,noarchive,nosnippet".replace(",no", ", no")); self.assertEqual(response["Cache-Control"], "no-store, max-age=0, private"); self.assertEqual(len(response["X-Request-ID"]), 32)

    def test_non_staff_cannot_create_monitor(self):
        self.client.force_login(self.user); self.assertEqual(self.client.get(reverse("monitoring:monitor-create")).status_code, 403)

    def test_push_endpoint_requires_bearer_and_records_minimized_heartbeat(self):
        monitor = Monitor.objects.create(name="private-job-name", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = monitor.issue_heartbeat_token()
        unauthorized = self.client.post(reverse("monitoring:push-heartbeat"))
        self.assertEqual(unauthorized.status_code, 401); self.assertEqual(unauthorized["WWW-Authenticate"], "Bearer")
        response = self.client.post(reverse("monitoring:push-heartbeat"), HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(response.status_code, 200); monitor.refresh_from_db(); self.assertIsNotNone(monitor.last_heartbeat_at); self.assertNotContains(response, "private-job-name"); self.assertEqual(set(response.json()), {"ok", "received_at"})

    def test_secure_push_endpoint_rejects_get_without_mutating(self):
        monitor = Monitor.objects.create(name="post-only", kind=Monitor.Kind.PUSH, interval_seconds=60); raw = monitor.issue_heartbeat_token()
        response = self.client.get(reverse("monitoring:push-heartbeat"), HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(response.status_code, 405); monitor.refresh_from_db(); self.assertIsNone(monitor.last_heartbeat_at)

    def test_legacy_path_heartbeat_is_hidden_by_default(self):
        monitor = Monitor.objects.create(name="legacy-off", kind=Monitor.Kind.PUSH, interval_seconds=60); raw = monitor.issue_heartbeat_token()
        response = self.client.post(reverse("monitoring:push-heartbeat-legacy", args=[raw]))
        self.assertEqual(response.status_code, 404); monitor.refresh_from_db(); self.assertIsNone(monitor.last_heartbeat_at)

    @override_settings(MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS=True)
    def test_legacy_plaintext_credential_is_upgraded_after_accepted_use(self):
        monitor = Monitor.objects.create(name="legacy-upgrade", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = "legacy-token-value-for-upgrade"
        Monitor.objects.filter(pk=monitor.pk).update(heartbeat_token=raw)
        response = self.client.post(reverse("monitoring:push-heartbeat-legacy", args=[raw]))
        self.assertEqual(response.status_code, 200); self.assertEqual(response["Deprecation"], "true")
        monitor.refresh_from_db(); self.assertEqual(monitor.heartbeat_token, hash_heartbeat_token(raw)); self.assertTrue(heartbeat_token_is_digest(monitor.heartbeat_token))

    def test_non_staff_monitor_detail_hides_diagnostics_and_credential_verifier(self):
        monitor = Monitor.objects.create(name="restricted-push", kind=Monitor.Kind.PUSH, interval_seconds=60, last_message="internal diagnostic secret-ish detail")
        CheckResult.objects.create(monitor=monitor, success=False, observed_state=Monitor.State.DOWN, message="backend.internal.example refused connection")
        Incident.objects.create(monitor=monitor, failure_reason="private failure detail")
        self.client.force_login(self.user); response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200); self.assertNotContains(response, monitor.heartbeat_token); self.assertNotContains(response, "internal diagnostic secret-ish detail"); self.assertNotContains(response, "backend.internal.example"); self.assertNotContains(response, "private failure detail"); self.assertContains(response, "Credential protected")

    def test_staff_monitor_detail_does_not_expose_persisted_verifier(self):
        monitor = Monitor.objects.create(name="staff-push", kind=Monitor.Kind.PUSH, interval_seconds=60)
        self.client.force_login(self.staff); response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200); self.assertNotContains(response, monitor.heartbeat_token); self.assertContains(response, "/api/v1/heartbeat/"); self.assertContains(response, "Non-recoverable credential")

    def test_settings_requires_staff(self):
        self.assertEqual(self.client.get(reverse("monitoring:settings")).status_code, 302); self.client.force_login(self.user); self.assertEqual(self.client.get(reverse("monitoring:settings")).status_code, 403)

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="")
    def test_settings_does_not_claim_partial_ntfy_configuration(self):
        self.client.force_login(self.staff); response = self.client.get(reverse("monitoring:settings")); self.assertFalse(response.context["ntfy_enabled"])

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="write-only-token")
    def test_settings_reports_complete_ntfy_configuration(self):
        self.client.force_login(self.staff); response = self.client.get(reverse("monitoring:settings")); self.assertTrue(response.context["ntfy_enabled"]); self.assertEqual(response.context["glaze_version"], "1.0.0")

    @override_settings(MONITOR_ALLOWED_NETWORKS=["10.20.30.0/24", "fd00:1234::/64"], MANAGER_API_TOKEN="manager-secret", NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="publisher-secret")
    def test_security_posture_is_staff_only_and_secret_free(self):
        self.client.force_login(self.user); self.assertEqual(self.client.get(reverse("monitoring:security")).status_code, 403)
        self.client.force_login(self.staff); response = self.client.get(reverse("monitoring:security")); self.assertEqual(response.status_code, 200); self.assertContains(response, "Wardveil Security by GoreeCloud"); self.assertContains(response, "Protected by Wardveil"); self.assertContains(response, "Legacy path heartbeat credentials disabled"); self.assertNotContains(response, "10.20.30.0/24"); self.assertNotContains(response, "manager-secret"); self.assertNotContains(response, "publisher-secret")

    @override_settings(NTFY_BASE_URL="http://ntfy:80", NTFY_TOPIC="goreecloud-uptime", NTFY_TOKEN="super-secret-publisher-token")
    def test_notifications_reports_posture_without_exposing_token(self):
        self.client.force_login(self.user); response = self.client.get(reverse("monitoring:notifications")); self.assertTrue(response.context["ntfy_enabled"]); self.assertNotContains(response, "super-secret-publisher-token"); self.assertContains(response, "Operational events, not delivery receipts")

    def test_incident_history_requires_login_and_supports_status_filter(self):
        monitor = Monitor.objects.create(name="service-a", kind=Monitor.Kind.HTTPS, target="https://example.com"); active = Incident.objects.create(monitor=monitor, failure_reason="down"); Incident.objects.create(monitor=monitor, failure_reason="old", ended_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.get(reverse("monitoring:incident-list")).status_code, 302); self.client.force_login(self.user); response = self.client.get(reverse("monitoring:incident-list"), {"status": "active"}); self.assertEqual(list(response.context["incidents"]), [active])

    def test_monitor_list_filters_by_name_state_and_kind(self):
        Monitor.objects.create(name="Alpha HTTPS", kind=Monitor.Kind.HTTPS, target="https://example.com", state=Monitor.State.UP); Monitor.objects.create(name="Beta TCP", kind=Monitor.Kind.TCP, target="example.com", port=443, state=Monitor.State.DOWN)
        self.client.force_login(self.user); response = self.client.get(reverse("monitoring:monitor-list"), {"q": "Alpha", "state": "UP", "kind": "HTTPS"}); self.assertEqual([monitor.name for monitor in response.context["monitors"]], ["Alpha HTTPS"])

    def test_staff_rotation_shows_raw_once_and_persists_only_verifier(self):
        monitor = Monitor.objects.create(name="rotate", kind=Monitor.Kind.PUSH, interval_seconds=60); old_verifier = monitor.heartbeat_token
        self.client.force_login(self.staff); response = self.client.post(reverse("monitoring:monitor-rotate-token", args=[monitor.pk])); self.assertEqual(response.status_code, 200); monitor.refresh_from_db(); self.assertNotEqual(monitor.heartbeat_token, old_verifier); self.assertNotContains(response, monitor.heartbeat_token); self.assertContains(response, "shown once")

    def test_health_responses_are_minimized(self):
        self.assertEqual(self.client.get(reverse("monitoring:health-live")).json(), {"ok": True}); self.assertEqual(self.client.get(reverse("monitoring:health-ready")).json(), {"ok": True})

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_api_requires_bearer_token(self):
        response = self.client.get(reverse("monitoring:manager-summary")); self.assertEqual(response.status_code, 401); self.assertEqual(response["WWW-Authenticate"], "Bearer"); self.assertEqual(self.client.get(reverse("monitoring:manager-summary"), HTTP_AUTHORIZATION="Bearer manager-secret").status_code, 200)

    @override_settings(DEBUG=False)
    def test_unknown_page_uses_glaze_error_surface_without_path_disclosure(self):
        response = self.client.get("/definitely-not-a-monitor-page/?secret=query-value")
        self.assertEqual(response.status_code, 404); self.assertContains(response, "Page not found", status_code=404); self.assertContains(response, "Protected by Wardveil", status_code=404); self.assertNotContains(response, "query-value", status_code=404); self.assertEqual(len(response["X-Request-ID"]), 32)
