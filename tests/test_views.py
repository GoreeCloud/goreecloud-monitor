from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from monitoring.models import CheckResult, Incident, JobEvent, Monitor, hash_heartbeat_token, heartbeat_token_is_digest


class ViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="strong-password")
        self.staff = get_user_model().objects.create_user(username="staff", password="strong-password", is_staff=True)

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("monitoring:dashboard")).status_code, 302)

    def test_authenticated_dashboard_preserves_canonical_identity_and_glaze_shell(self):
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

    def test_authenticated_pages_receive_wardveil_browser_headers_and_request_id(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertEqual(response["Content-Security-Policy"].split("; ")[0], "default-src 'self'")
        self.assertIn("camera=()", response["Permissions-Policy"])
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow, noarchive, nosnippet")
        self.assertEqual(response["Cache-Control"], "no-store, max-age=0, private")
        self.assertEqual(len(response["X-Request-ID"]), 32)

    def test_non_staff_cannot_create_monitor(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("monitoring:monitor-create")).status_code, 403)

    def test_push_endpoint_requires_bearer_and_records_minimized_heartbeat(self):
        monitor = Monitor.objects.create(name="private-job-name", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = monitor.issue_heartbeat_token()
        unauthorized = self.client.post(reverse("monitoring:push-heartbeat"))
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized["WWW-Authenticate"], "Bearer")
        response = self.client.post(reverse("monitoring:push-heartbeat"), HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(response.status_code, 200)
        monitor.refresh_from_db()
        self.assertIsNotNone(monitor.last_heartbeat_at)
        self.assertNotContains(response, "private-job-name")
        self.assertEqual(set(response.json()), {"ok", "received_at"})


    def test_job_signal_endpoint_requires_bearer_and_records_correlated_run(self):
        monitor = Monitor.objects.create(
            name="backup-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_grace_seconds=300,
        )
        raw = monitor.issue_heartbeat_token()
        unauthorized = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "start"},
            content_type="application/json",
        )
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized["WWW-Authenticate"], "Bearer")

        started = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "start"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(started.status_code, 200)
        run_id = started.json()["run_id"]
        self.assertTrue(run_id)

        completed = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "run_id": run_id, "message": "backup complete"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(completed.status_code, 200)
        success = JobEvent.objects.get(monitor=monitor, event_type=JobEvent.EventType.SUCCESS)
        self.assertEqual(success.run_id, run_id)
        self.assertIsNotNone(success.duration_ms)
        self.assertGreaterEqual(success.duration_ms, 0)

    def test_job_signal_endpoint_records_explicit_failure(self):
        monitor = Monitor.objects.create(name="failed-backup", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "fail", "run_id": "nightly-1", "exit_code": 23},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 200)
        event = JobEvent.objects.get(monitor=monitor)
        self.assertEqual(event.event_type, JobEvent.EventType.FAILURE)
        self.assertEqual(event.exit_code, 23)

    def test_job_success_rejects_nonzero_exit_code(self):
        monitor = Monitor.objects.create(name="contradictory-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "run_id": "run-1", "exit_code": 1},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(JobEvent.objects.filter(monitor=monitor).exists())

    def test_job_signal_rejects_unbounded_or_unknown_payload_fields(self):
        monitor = Monitor.objects.create(name="bounded-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "unexpected": "value"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 400)

    def test_job_signal_rejects_non_string_metadata(self):
        monitor = Monitor.objects.create(name="typed-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "run_id": {"unexpected": "object"}},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(JobEvent.objects.filter(monitor=monitor).exists())

    def test_job_start_rejects_exit_code(self):
        monitor = Monitor.objects.create(name="start-exit-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "start", "exit_code": 0},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(JobEvent.objects.filter(monitor=monitor).exists())

    def test_job_signal_idempotent_replay_returns_existing_event(self):
        monitor = Monitor.objects.create(name="idempotent-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        event_id = str(uuid4())
        payload = {"event": "start", "event_id": event_id, "message": "starting"}

        first = self.client.post(
            reverse("monitoring:job-signal"),
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        second = self.client.post(
            reverse("monitoring:job-signal"),
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(first.json()["replayed"])
        self.assertTrue(second.json()["replayed"])
        self.assertEqual(first.json()["run_id"], second.json()["run_id"])
        self.assertEqual(first.json()["event_id"], event_id)
        self.assertEqual(JobEvent.objects.filter(monitor=monitor).count(), 1)

    def test_job_success_replay_treats_omitted_and_zero_exit_code_as_equivalent(self):
        monitor = Monitor.objects.create(name="success-replay-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        event_id = str(uuid4())
        first = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "event_id": event_id},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        replay = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "event_id": event_id, "exit_code": 0},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["replayed"])
        self.assertEqual(JobEvent.objects.filter(monitor=monitor).count(), 1)

    def test_job_signal_conflicting_idempotency_replay_is_rejected(self):
        monitor = Monitor.objects.create(name="conflicting-replay-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        event_id = str(uuid4())
        first = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "event_id": event_id, "message": "done"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        conflict = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "failure", "event_id": event_id, "exit_code": 2, "message": "failed"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(JobEvent.objects.filter(monitor=monitor).count(), 1)

    def test_job_signal_rejects_invalid_event_id(self):
        monitor = Monitor.objects.create(name="invalid-event-id-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "event_id": "not-a-uuid"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(JobEvent.objects.filter(monitor=monitor).exists())

    @override_settings(MONITOR_JOB_SIGNAL_MAX_PER_MINUTE=2)
    def test_job_signal_rate_limit_returns_429_and_retry_after(self):
        monitor = Monitor.objects.create(name="rate-limited-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        for index in range(2):
            response = self.client.post(
                reverse("monitoring:job-signal"),
                data={"event": "log", "event_id": str(uuid4()), "message": f"log {index}"},
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {raw}",
            )
            self.assertEqual(response.status_code, 200)

        limited = self.client.post(
            reverse("monitoring:job-signal"),
            data={"event": "success", "event_id": str(uuid4())},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(limited.status_code, 429)
        self.assertGreaterEqual(int(limited["Retry-After"]), 1)
        self.assertEqual(JobEvent.objects.filter(monitor=monitor).count(), 2)

    @override_settings(MONITOR_JOB_SIGNAL_MAX_PER_MINUTE=1)
    def test_idempotent_replay_bypasses_rate_limit_without_new_event(self):
        monitor = Monitor.objects.create(name="replay-at-limit-job", kind=Monitor.Kind.JOB, interval_seconds=3600)
        raw = monitor.issue_heartbeat_token()
        event_id = str(uuid4())
        payload = {"event": "success", "event_id": event_id}
        first = self.client.post(
            reverse("monitoring:job-signal"),
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        replay = self.client.post(
            reverse("monitoring:job-signal"),
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {raw}",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["replayed"])
        self.assertEqual(JobEvent.objects.filter(monitor=monitor).count(), 1)

    def test_staff_job_detail_exposes_signal_contract_not_verifier(self):
        monitor = Monitor.objects.create(name="job-detail", kind=Monitor.Kind.JOB, interval_seconds=3600)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/api/v1/jobs/signal/")
        self.assertContains(response, "Scheduled job signals")
        self.assertNotContains(response, monitor.heartbeat_token)

    def test_job_recovery_requires_staff_and_job_monitor(self):
        job = Monitor.objects.create(
            name="recovery-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        push = Monitor.objects.create(
            name="not-a-job",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
        )
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse("monitoring:job-recovery", args=[job.pk])).status_code,
            403,
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:job-recovery", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scheduled job recovery")
        self.assertContains(response, "Versioned export")
        self.assertNotContains(response, job.heartbeat_token)
        self.assertEqual(
            self.client.get(reverse("monitoring:job-recovery", args=[push.pk])).status_code,
            404,
        )

    @override_settings(MONITOR_JOB_EVENT_RETENTION_DAYS=90)
    def test_job_recovery_shows_state_preserving_anchors(self):
        job = Monitor.objects.create(
            name="anchor-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_max_runtime_seconds=600,
        )
        terminal = JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.SUCCESS,
            run_id="completed-run",
        )
        start = JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.START,
            run_id="active-run",
            received_at=terminal.received_at + timedelta(seconds=1),
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:job-recovery", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["latest_terminal"].pk, terminal.pk)
        self.assertEqual(response.context["unmatched_start"].pk, start.pk)
        self.assertEqual(response.context["retention_days"], 90)
        self.assertEqual(response.context["evaluation"].phase, "STARTED")
        self.assertContains(response, "Started")
        self.assertContains(response, "active-run")
        self.assertNotContains(response, job.heartbeat_token)

    def test_job_history_export_is_staff_only_versioned_and_secret_free(self):
        job = Monitor.objects.create(
            name="export-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_grace_seconds=120,
        )
        raw = job.issue_heartbeat_token()
        event = JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.FAILURE,
            event_id=str(uuid4()),
            run_id="run-42",
            exit_code=7,
            message="bounded diagnostic",
        )

        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse("monitoring:job-history-export", args=[job.pk])).status_code,
            403,
        )

        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:job-history-export", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schema"], "goreecloud-monitor-job-events-v1")
        self.assertEqual(payload["monitor"]["id"], job.pk)
        self.assertEqual(payload["events"][0]["id"], event.pk)
        self.assertEqual(payload["events"][0]["message"], "bounded diagnostic")
        self.assertEqual(payload["evaluation"]["phase"], "FAILED")
        self.assertIn("attachment;", response["Content-Disposition"])
        rendered = response.content.decode("utf-8")
        self.assertNotIn(raw, rendered)
        job.refresh_from_db()
        self.assertNotIn(job.heartbeat_token, rendered)
        self.assertNotIn("heartbeat_token", rendered)

    def test_oncalendar_job_detail_and_export_preserve_native_schedule(self):
        job = Monitor.objects.create(
            name="oncalendar-view-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.ONCALENDAR,
            job_cron_expression="*-*-* 03:00:00",
            job_timezone="America/Chicago",
        )
        self.client.force_login(self.staff)

        detail = self.client.get(reverse("monitoring:monitor-detail", args=[job.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "OnCalendar")
        self.assertContains(detail, "*-*-* 03:00:00")

        exported = self.client.get(reverse("monitoring:job-history-export", args=[job.pk]))
        self.assertEqual(exported.status_code, 200)
        payload = exported.json()
        self.assertEqual(payload["monitor"]["schedule_mode"], "ONCAL")
        self.assertEqual(payload["monitor"]["schedule_expression"], "*-*-* 03:00:00")
        self.assertIsNone(payload["monitor"]["cron_expression"])
        self.assertEqual(payload["monitor"]["oncalendar_expression"], "*-*-* 03:00:00")
        self.assertEqual(payload["monitor"]["timezone"], "America/Chicago")

    def test_job_history_export_paginates_with_stable_before_id_cursor(self):
        job = Monitor.objects.create(
            name="paged-export-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        events = [
            JobEvent.objects.create(
                monitor=job,
                event_type=JobEvent.EventType.LOG,
                message=f"event-{index}",
            )
            for index in range(3)
        ]
        self.client.force_login(self.staff)

        first = self.client.get(
            reverse("monitoring:job-history-export", args=[job.pk]),
            {"limit": "2"},
        )
        self.assertEqual(first.status_code, 200)
        first_payload = first.json()
        self.assertTrue(first_payload["page"]["has_more"])
        self.assertEqual(first_payload["page"]["returned"], 2)
        self.assertEqual(
            [row["id"] for row in first_payload["events"]],
            [events[2].pk, events[1].pk],
        )

        second = self.client.get(
            reverse("monitoring:job-history-export", args=[job.pk]),
            {
                "limit": "2",
                "before_id": str(first_payload["page"]["next_before_id"]),
            },
        )
        self.assertEqual(second.status_code, 200)
        second_payload = second.json()
        self.assertFalse(second_payload["page"]["has_more"])
        self.assertEqual(
            [row["id"] for row in second_payload["events"]],
            [events[0].pk],
        )
        self.assertFalse(
            set(row["id"] for row in first_payload["events"])
            & set(row["id"] for row in second_payload["events"])
        )

    def test_job_history_export_rejects_invalid_pagination(self):
        job = Monitor.objects.create(
            name="invalid-export-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        self.client.force_login(self.staff)
        endpoint = reverse("monitoring:job-history-export", args=[job.pk])
        self.assertEqual(self.client.get(endpoint, {"limit": "0"}).status_code, 400)
        self.assertEqual(self.client.get(endpoint, {"limit": "5001"}).status_code, 400)
        self.assertEqual(self.client.get(endpoint, {"before_id": "nope"}).status_code, 400)

    def test_staff_job_detail_links_recovery_without_exposing_verifier(self):
        job = Monitor.objects.create(
            name="linked-recovery-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("monitoring:job-recovery", args=[job.pk]))
        self.assertContains(response, "Recovery &amp; export")
        self.assertNotContains(response, job.heartbeat_token)

    def test_job_detail_presents_started_phase_without_changing_monitor_state(self):
        job = Monitor.objects.create(
            name="started-detail-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_max_runtime_seconds=600,
            state=Monitor.State.UP,
        )
        JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.START,
            run_id="active-detail-run",
            received_at=timezone.now() - timedelta(seconds=30),
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["job_evaluation"].phase, "STARTED")
        self.assertContains(response, "Lifecycle: Started")
        self.assertEqual(job.state, Monitor.State.UP)

    def test_job_detail_presents_late_phase_for_runtime_overrun(self):
        job = Monitor.objects.create(
            name="late-detail-job",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_max_runtime_seconds=10,
        )
        JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.START,
            run_id="late-run",
            received_at=timezone.now() - timedelta(seconds=30),
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["job_evaluation"].phase, "LATE")
        self.assertContains(response, "Lifecycle: Late")

    def test_secure_push_endpoint_rejects_get_without_mutating(self):
        monitor = Monitor.objects.create(name="post-only", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = monitor.issue_heartbeat_token()
        response = self.client.get(reverse("monitoring:push-heartbeat"), HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(response.status_code, 405)
        monitor.refresh_from_db()
        self.assertIsNone(monitor.last_heartbeat_at)

    def test_legacy_path_heartbeat_is_hidden_by_default(self):
        monitor = Monitor.objects.create(name="legacy-off", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = monitor.issue_heartbeat_token()
        response = self.client.post(reverse("monitoring:push-heartbeat-legacy", args=[raw]))
        self.assertEqual(response.status_code, 404)
        monitor.refresh_from_db()
        self.assertIsNone(monitor.last_heartbeat_at)

    @override_settings(MONITOR_ALLOW_LEGACY_PATH_HEARTBEATS=True)
    def test_legacy_plaintext_credential_is_upgraded_after_accepted_use(self):
        monitor = Monitor.objects.create(name="legacy-upgrade", kind=Monitor.Kind.PUSH, interval_seconds=60)
        raw = "legacy-token-value-for-upgrade"
        Monitor.objects.filter(pk=monitor.pk).update(heartbeat_token=raw)
        response = self.client.post(reverse("monitoring:push-heartbeat-legacy", args=[raw]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Deprecation"], "true")
        monitor.refresh_from_db()
        self.assertEqual(monitor.heartbeat_token, hash_heartbeat_token(raw))
        self.assertTrue(heartbeat_token_is_digest(monitor.heartbeat_token))

    def test_non_staff_monitor_detail_hides_diagnostics_and_credential_verifier(self):
        monitor = Monitor.objects.create(name="restricted-push", kind=Monitor.Kind.PUSH, interval_seconds=60, last_message="internal diagnostic secret-ish detail")
        CheckResult.objects.create(monitor=monitor, success=False, observed_state=Monitor.State.DOWN, message="backend.internal.example refused connection")
        Incident.objects.create(monitor=monitor, failure_reason="private failure detail")
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, monitor.heartbeat_token)
        self.assertNotContains(response, "internal diagnostic secret-ish detail")
        self.assertNotContains(response, "backend.internal.example")
        self.assertNotContains(response, "private failure detail")
        self.assertContains(response, "Credential protected")

    def test_staff_monitor_detail_does_not_expose_persisted_verifier(self):
        monitor = Monitor.objects.create(name="staff-push", kind=Monitor.Kind.PUSH, interval_seconds=60)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:monitor-detail", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, monitor.heartbeat_token)
        self.assertContains(response, "/api/v1/heartbeat/")
        self.assertContains(response, "Non-recoverable credential")

    @override_settings(
        MONITOR_CHECK_RETENTION_DAYS=30,
        MONITOR_JOB_EVENT_RETENTION_DAYS=90,
    )
    def test_settings_reports_bounded_history_retention(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["retention_days"], 30)
        self.assertEqual(response.context["job_event_retention_days"], 90)
        self.assertContains(response, "Job event retention")
        self.assertContains(response, "90 days")

    def test_settings_requires_staff(self):
        self.assertEqual(self.client.get(reverse("monitoring:settings")).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("monitoring:settings")).status_code, 403)

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="",
    )
    def test_settings_does_not_claim_partial_notify_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertFalse(response.context["notify_enabled"])

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="producer-token",
    )
    def test_settings_reports_complete_notify_configuration(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:settings"))
        self.assertTrue(response.context["notify_enabled"])
        self.assertEqual(response.context["glaze_version"], "1.5.1")
        self.assertContains(response, "1.5.1")

    @override_settings(
        MONITOR_ALLOWED_NETWORKS=["10.20.30.0/24", "fd00:1234::/64"],
        MANAGER_API_TOKEN="manager-secret",
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="publisher-secret",
    )
    def test_security_posture_is_staff_only_and_secret_free(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("monitoring:security")).status_code, 403)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("monitoring:security"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wardveil Security by GoreeCloud")
        self.assertContains(response, "Protected by Wardveil")
        self.assertContains(response, "Legacy path heartbeat credentials disabled")
        self.assertNotContains(response, "10.20.30.0/24")
        self.assertNotContains(response, "manager-secret")
        self.assertNotContains(response, "publisher-secret")

    @override_settings(
        MONITOR_NOTIFY_ENABLED=True,
        GOREECLOUD_NOTIFY_BASE_URL="https://notify.example.test",
        GOREECLOUD_NOTIFY_TOKEN="super-secret-publisher-token",
    )
    def test_notifications_reports_notify_posture_without_exposing_token(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:notifications"))
        self.assertTrue(response.context["notify_enabled"])
        self.assertNotContains(response, "super-secret-publisher-token")
        self.assertContains(response, "Operational events, not delivery receipts")
        self.assertNotContains(response, "ntfy migration path")

    def test_incident_history_requires_login_and_supports_status_filter(self):
        monitor = Monitor.objects.create(name="service-a", kind=Monitor.Kind.HTTPS, target="https://example.com")
        active = Incident.objects.create(monitor=monitor, failure_reason="down")
        Incident.objects.create(monitor=monitor, failure_reason="old", ended_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.client.get(reverse("monitoring:incident-list")).status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:incident-list"), {"status": "active"})
        self.assertEqual(list(response.context["incidents"]), [active])

    def test_monitor_list_filters_by_name_state_and_kind(self):
        Monitor.objects.create(name="Alpha HTTPS", kind=Monitor.Kind.HTTPS, target="https://example.com", state=Monitor.State.UP)
        Monitor.objects.create(name="Beta TCP", kind=Monitor.Kind.TCP, target="example.com", port=443, state=Monitor.State.DOWN)
        self.client.force_login(self.user)
        response = self.client.get(reverse("monitoring:monitor-list"), {"q": "Alpha", "state": "UP", "kind": "HTTPS"})
        self.assertEqual([monitor.name for monitor in response.context["monitors"]], ["Alpha HTTPS"])

    def test_staff_rotation_shows_raw_once_and_persists_only_verifier(self):
        monitor = Monitor.objects.create(name="rotate", kind=Monitor.Kind.PUSH, interval_seconds=60)
        old_verifier = monitor.heartbeat_token
        self.client.force_login(self.staff)
        response = self.client.post(reverse("monitoring:monitor-rotate-token", args=[monitor.pk]))
        self.assertEqual(response.status_code, 200)
        monitor.refresh_from_db()
        self.assertNotEqual(monitor.heartbeat_token, old_verifier)
        self.assertNotContains(response, monitor.heartbeat_token)
        self.assertContains(response, "shown once")

    def test_health_responses_are_minimized(self):
        self.assertEqual(self.client.get(reverse("monitoring:health-live")).json(), {"ok": True})
        self.assertEqual(self.client.get(reverse("monitoring:health-ready")).json(), {"ok": True})

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_api_requires_bearer_token(self):
        response = self.client.get(reverse("monitoring:manager-summary"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")
        self.assertEqual(self.client.get(reverse("monitoring:manager-summary"), HTTP_AUTHORIZATION="Bearer manager-secret").status_code, 200)

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_jobs_api_is_read_only_bounded_and_job_only(self):
        first = Monitor.objects.create(
            name="manager-job-a",
            kind=Monitor.Kind.JOB,
            interval_seconds=3600,
            job_schedule_mode=Monitor.JobScheduleMode.CRON,
            job_cron_expression="0 3 * * *",
            job_timezone="UTC",
        )
        second = Monitor.objects.create(
            name="manager-job-b",
            kind=Monitor.Kind.JOB,
            interval_seconds=7200,
        )
        Monitor.objects.create(
            name="not-a-job",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
        )

        endpoint = reverse("monitoring:manager-jobs")
        unauthorized = self.client.get(endpoint)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized["WWW-Authenticate"], "Bearer")
        self.assertEqual(self.client.post(endpoint, HTTP_AUTHORIZATION="Bearer manager-secret").status_code, 405)

        page = self.client.get(
            endpoint,
            {"limit": "1"},
            HTTP_AUTHORIZATION="Bearer manager-secret",
        )
        self.assertEqual(page.status_code, 200)
        payload = page.json()
        self.assertEqual(payload["schema"], "goreecloud-monitor-manager-jobs-v1")
        self.assertEqual(payload["page"]["returned"], 1)
        self.assertTrue(payload["page"]["has_more"])
        self.assertEqual(payload["jobs"][0]["id"], first.pk)
        self.assertNotIn("heartbeat_token", page.content.decode("utf-8"))
        self.assertNotIn("not-a-job", page.content.decode("utf-8"))

        next_page = self.client.get(
            endpoint,
            {"limit": "10", "after_id": str(payload["page"]["next_after_id"])},
            HTTP_AUTHORIZATION="Bearer manager-secret",
        )
        self.assertEqual([row["id"] for row in next_page.json()["jobs"]], [second.pk])
        self.assertEqual(
            self.client.get(endpoint, {"limit": "101"}, HTTP_AUTHORIZATION="Bearer manager-secret").status_code,
            400,
        )

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_job_detail_exposes_sanitized_signal_metadata_only(self):
        job = Monitor.objects.create(
            name="manager-job-detail",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.ONCALENDAR,
            job_cron_expression="*-*-* 03:00:00",
            job_timezone="America/Chicago",
        )
        raw = job.issue_heartbeat_token()
        event = JobEvent.objects.create(
            monitor=job,
            event_type=JobEvent.EventType.FAILURE,
            event_id=str(uuid4()),
            run_id="private-run-id",
            exit_code=9,
            duration_ms=1234,
            message="private operator diagnostic",
        )
        Incident.objects.create(monitor=job, failure_reason="private failure reason")

        endpoint = reverse("monitoring:manager-job-detail", args=[job.pk])
        response = self.client.get(endpoint, HTTP_AUTHORIZATION="Bearer manager-secret")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schema"], "goreecloud-monitor-manager-job-v1")
        self.assertEqual(payload["job"]["id"], job.pk)
        self.assertEqual(payload["job"]["schedule"]["mode"], "ONCAL")
        self.assertEqual(payload["job"]["schedule"]["expression"], "*-*-* 03:00:00")
        self.assertEqual(payload["recent_events"][0]["event_type"], "FAILURE")
        self.assertEqual(payload["recent_events"][0]["exit_code"], 9)
        self.assertEqual(payload["recent_events"][0]["duration_ms"], 1234)
        rendered = response.content.decode("utf-8")
        self.assertNotIn(raw, rendered)
        job.refresh_from_db()
        self.assertNotIn(job.heartbeat_token, rendered)
        self.assertNotIn(event.event_id, rendered)
        self.assertNotIn("private-run-id", rendered)
        self.assertNotIn("private operator diagnostic", rendered)
        self.assertNotIn("private failure reason", rendered)
        self.assertEqual(self.client.post(endpoint, HTTP_AUTHORIZATION="Bearer manager-secret").status_code, 405)
        self.assertEqual(
            self.client.get(endpoint, {"event_limit": "101"}, HTTP_AUTHORIZATION="Bearer manager-secret").status_code,
            400,
        )

    @override_settings(MANAGER_API_TOKEN="manager-secret")
    def test_manager_job_detail_rejects_non_job_monitor(self):
        monitor = Monitor.objects.create(
            name="manager-push",
            kind=Monitor.Kind.PUSH,
            interval_seconds=60,
        )
        response = self.client.get(
            reverse("monitoring:manager-job-detail", args=[monitor.pk]),
            HTTP_AUTHORIZATION="Bearer manager-secret",
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_unknown_page_uses_glaze_error_surface_without_path_disclosure(self):
        response = self.client.get("/definitely-not-a-monitor-page/?secret=query-value")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, "Protected by Wardveil", status_code=404)
        self.assertContains(response, "goreecloud-monitor-icon.svg", status_code=404)
        self.assertNotContains(response, "query-value", status_code=404)
        self.assertEqual(len(response["X-Request-ID"]), 32)
