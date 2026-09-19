from __future__ import annotations

import json
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from monitoring.models import MaintenanceWindow, Monitor


class PortableMonitorDefinitionTests(TestCase):
    def test_export_import_round_trip_excludes_heartbeat_token(self):
        monitor = Monitor.objects.create(
            name="homepage",
            kind=Monitor.Kind.HTTPS,
            target="https://example.com/health",
            interval_seconds=60,
            timeout_seconds=10,
            expected_status_code=200,
        )
        original_token = monitor.heartbeat_token
        window = MaintenanceWindow.objects.create(
            name="upgrade",
            starts_at=timezone.now() + timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        window.monitors.add(monitor)

        out = StringIO()
        call_command("exportmonitors", stdout=out)
        document = json.loads(out.getvalue())
        self.assertEqual(document["schema"], "goreecloud-monitor")
        self.assertEqual(document["version"], 2)
        self.assertNotIn("heartbeat_token", document["monitors"][0])
        self.assertNotIn("state", document["monitors"][0])

        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "monitor-export.json"
            export_path.write_text(json.dumps(document), encoding="utf-8")
            MaintenanceWindow.objects.all().delete()
            Monitor.objects.all().delete()
            call_command("importmonitors", str(export_path), stdout=StringIO())

        restored = Monitor.objects.get(name="homepage")
        self.assertEqual(restored.target, "https://example.com/health")
        self.assertNotEqual(restored.heartbeat_token, original_token)
        restored_window = MaintenanceWindow.objects.get(name="upgrade")
        self.assertEqual(list(restored_window.monitors.values_list("name", flat=True)), ["homepage"])

    def test_oncalendar_job_export_import_round_trip_preserves_schedule(self):
        monitor = Monitor.objects.create(
            name="nightly-oncalendar",
            kind=Monitor.Kind.JOB,
            interval_seconds=60,
            job_schedule_mode=Monitor.JobScheduleMode.ONCALENDAR,
            job_cron_expression="*-*-* 03:00:00\n*-*-* 15:00:00",
            job_timezone="America/Chicago",
            job_grace_seconds=600,
            job_max_runtime_seconds=7200,
        )
        original_token = monitor.heartbeat_token

        out = StringIO()
        call_command("exportmonitors", stdout=out)
        document = json.loads(out.getvalue())
        exported = document["monitors"][0]
        self.assertEqual(document["version"], 2)
        self.assertEqual(exported["job_schedule_mode"], "ONCAL")
        self.assertEqual(exported["job_cron_expression"], "*-*-* 03:00:00\n*-*-* 15:00:00")
        self.assertEqual(exported["job_timezone"], "America/Chicago")

        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "monitor-export-v2.json"
            export_path.write_text(json.dumps(document), encoding="utf-8")
            Monitor.objects.all().delete()
            call_command("importmonitors", str(export_path), stdout=StringIO())

        restored = Monitor.objects.get(name="nightly-oncalendar")
        self.assertEqual(restored.job_schedule_mode, Monitor.JobScheduleMode.ONCALENDAR)
        self.assertEqual(restored.job_cron_expression, "*-*-* 03:00:00\n*-*-* 15:00:00")
        self.assertEqual(restored.job_timezone, "America/Chicago")
        self.assertEqual(restored.job_grace_seconds, 600)
        self.assertEqual(restored.job_max_runtime_seconds, 7200)
        self.assertNotEqual(restored.heartbeat_token, original_token)

    def test_v1_scheduled_job_import_is_rejected_as_incomplete(self):
        document = {
            "schema": "goreecloud-monitor",
            "version": 1,
            "monitors": [{
                "name": "legacy-job",
                "kind": "JOB",
                "target": "",
                "port": None,
                "enabled": True,
                "interval_seconds": 3600,
                "timeout_seconds": 10,
                "failure_threshold": 2,
                "recovery_threshold": 1,
                "http_method": "GET",
                "expected_status_code": 200,
                "follow_redirects": True,
                "expected_body_text": "",
                "expected_json_path": "",
                "expected_json_value": "",
                "tls_warning_days": 14,
                "dns_record_type": "A",
                "expected_dns_answer": "",
                "heartbeat_grace_seconds": 60,
            }],
            "maintenance_windows": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy-v1-job.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("importmonitors", str(path), stdout=StringIO())

    def test_import_refuses_non_empty_target(self):
        Monitor.objects.create(name="existing", kind=Monitor.Kind.PUSH, interval_seconds=60)
        document = {"schema": "goreecloud-monitor", "version": 1, "monitors": [], "maintenance_windows": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "export.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("importmonitors", str(path), stdout=StringIO())
