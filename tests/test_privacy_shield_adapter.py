from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class PrivacyShieldAdapterTests(SimpleTestCase):
    """Validate only the Privacy Shield capabilities Monitor can currently prove in source."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.adapter = json.loads((cls.base / "docs/privacy-shield.adapter.json").read_text(encoding="utf-8"))
        cls.audit = (cls.base / "src/monitoring/audit.py").read_text(encoding="utf-8")
        cls.middleware = (cls.base / "src/monitoring/middleware.py").read_text(encoding="utf-8")
        cls.portability = (cls.base / "tests/test_portability.py").read_text(encoding="utf-8")
        cls.pruning = (cls.base / "src/monitoring/management/commands/prunemonitorhistory.py").read_text(encoding="utf-8")

    def test_adapter_identity_and_runtime_authority_are_explicit(self):
        adapter = self.adapter["adapter"]
        self.assertEqual(self.adapter["schema_version"], 1)
        self.assertEqual(adapter["id"], "monitor-application-privacy")
        self.assertEqual(adapter["product"], "GoreeCloud Monitor")
        self.assertEqual(adapter["runtime_authority"], "GoreeCloud/goreecloud-monitor")
        self.assertEqual(adapter["contract_version"], 1)

    def test_capability_claims_are_intentionally_narrow(self):
        self.assertEqual(
            set(self.adapter["capabilities"]),
            {"telemetry-minimization", "data-minimization", "retention-controls", "portable-export"},
        )
        for unsupported in (
            "content-blocking",
            "tracking-resistance",
            "url-cleaning",
            "dns-privacy",
            "network-privacy",
            "deletion-controls",
            "privacy-status",
            "user-visible-exceptions",
        ):
            self.assertNotIn(unsupported, self.adapter["capabilities"])

    def test_privacy_boundary_is_local_first_and_status_safe(self):
        privacy = self.adapter["privacy"]
        self.assertTrue(privacy["local_first"])
        self.assertFalse(privacy["raw_private_activity_exported_for_status"])
        self.assertFalse(privacy["remote_tracker_learning"])
        self.assertFalse(privacy["remote_tracker_telemetry"])

    def test_runtime_acceptance_remains_fail_closed(self):
        acceptance = self.adapter["acceptance"]
        self.assertTrue(acceptance["runtime_acceptance_required"])
        self.assertFalse(acceptance["production_approved"])

    def test_claimed_capabilities_have_source_evidence(self):
        self.assertIn("record_security_event", self.audit)
        self.assertIn("correlation", self.middleware.lower())
        self.assertIn("export", self.portability.lower())
        self.assertIn("retention", self.pruning.lower())
