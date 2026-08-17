from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_uptime_kuma_runtime_evidence.py"


def load_collector():
    spec = importlib.util.spec_from_file_location("uptime_kuma_runtime_evidence_collector", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load runtime evidence collector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UptimeKumaRuntimeEvidenceTests(SimpleTestCase):
    def test_runtime_helper_passes_token_only_on_stdin(self):
        module = load_collector()
        payload = {
            "ok": True,
            "data": [
                {
                    "id": 2,
                    "name": "Web",
                    "type": "http",
                    "active": True,
                    "heartbeat": {"status": 1, "ping": 15.5},
                }
            ],
        }
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
            document = module._collect_raw_runtime("uptime-kuma", "reusable-secret-token")

        self.assertEqual(document, payload)
        command = run.call_args.args[0]
        kwargs = run.call_args.kwargs
        self.assertNotIn("reusable-secret-token", " ".join(command))
        self.assertEqual(kwargs["input"], "reusable-secret-token\n")
        self.assertEqual(command[:6], ["docker", "exec", "-i", "-w", "/app", "uptime-kuma"])
        self.assertNotIn("reusable-secret-token", json.dumps(kwargs.get("env", {})))

    def test_protected_token_file_rejects_group_or_other_permissions(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            os.chmod(root, 0o700)
            path = root / "auth.txt"
            path.write_text("secret-token\n", encoding="utf-8")
            os.chmod(path, 0o640)
            with self.assertRaises(ValueError):
                module._load_protected_token(path)

            os.chmod(path, 0o600)
            self.assertEqual(module._load_protected_token(path), "secret-token")

    def test_protected_token_file_rejects_nonprivate_parent_directory(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "auth.txt"
            path.write_text("secret-token\n", encoding="utf-8")
            os.chmod(path, 0o600)
            os.chmod(root, 0o750)
            with self.assertRaises(ValueError):
                module._load_protected_token(path)

            os.chmod(root, 0o700)
            self.assertEqual(module._load_protected_token(path), "secret-token")

    def test_active_monitor_without_heartbeat_fails_closed(self):
        module = load_collector()
        with self.assertRaises(ValueError):
            module._validate_runtime_completeness(
                {
                    "data": [
                        {
                            "id": 2,
                            "name": "Web",
                            "type": "http",
                            "active": True,
                            "heartbeat": None,
                        }
                    ]
                }
            )

    def test_complete_runtime_snapshot_accepts_inactive_without_history(self):
        module = load_collector()
        summary = module._validate_runtime_completeness(
            {
                "data": [
                    {
                        "id": 2,
                        "name": "Web",
                        "type": "http",
                        "active": True,
                        "heartbeat": {"status": 1, "ping": 12.0},
                    },
                    {
                        "id": 3,
                        "name": "Paused",
                        "type": "http",
                        "active": False,
                        "heartbeat": None,
                    },
                ]
            }
        )
        self.assertEqual(
            summary,
            {"monitors": 2, "active_monitors": 1, "monitors_with_heartbeat": 1},
        )

    def test_invalid_heartbeat_status_is_rejected(self):
        module = load_collector()
        with self.assertRaises(ValueError):
            module._validate_runtime_completeness(
                {
                    "data": [
                        {
                            "id": 2,
                            "name": "Web",
                            "type": "http",
                            "active": True,
                            "heartbeat": {"status": 9, "ping": 12.0},
                        }
                    ]
                }
            )

    def test_boolean_ping_is_rejected(self):
        module = load_collector()
        with self.assertRaises(ValueError):
            module._validate_runtime_completeness(
                {
                    "data": [
                        {
                            "id": 2,
                            "name": "Web",
                            "type": "http",
                            "active": True,
                            "heartbeat": {"status": 1, "ping": True},
                        }
                    ]
                }
            )
