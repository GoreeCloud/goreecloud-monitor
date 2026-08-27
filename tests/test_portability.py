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
        self.assertEqual(document["version"], 1)
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

    def test_import_refuses_non_empty_target(self):
        Monitor.objects.create(name="existing", kind=Monitor.Kind.PUSH, interval_seconds=60)
        document = {"schema": "goreecloud-monitor", "version": 1, "monitors": [], "maintenance_windows": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "export.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("importmonitors", str(path), stdout=StringIO())
