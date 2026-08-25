from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EverkeepAcceptanceTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.policy = json.loads((cls.base / "docs/everkeep.acceptance.json").read_text(encoding="utf-8"))
        cls.adoption = json.loads((cls.base / "docs/everkeep.adoption.json").read_text(encoding="utf-8"))

    def test_policy_covers_every_declared_dimension(self):
        self.assertEqual(self.policy["application"], "goreecloud-monitor")
        self.assertEqual(self.policy["producer"], "GoreeCloud/goreecloud-monitor")
        self.assertEqual(set(self.adoption["dimensions"]), set(self.policy["required_ready_evidence"]))

    def test_fail_closed_states_are_explicit(self):
        failure = self.policy["failure_behavior"]
        self.assertEqual(failure["producer_unavailable"], "unknown")
        self.assertEqual(failure["malformed_evidence"], "unknown")
        self.assertEqual(failure["missing_required_evidence"], "unknown")
        self.assertEqual(failure["failed_restore_validation"], "degraded")
        self.assertIn("never be more favorable", failure["summary_rule"])

    def test_freshness_cannot_silently_pass(self):
        freshness = self.policy["freshness"]
        self.assertTrue(freshness["required_for_ready"])
        self.assertIn("fresh_until", freshness["rule"])
        self.assertIn("unknown", freshness["rule"])

    def test_backup_and_restore_are_distinct_evidence(self):
        ready = self.policy["required_ready_evidence"]
        self.assertIn("artifact integrity was verified", ready["backup_coverage"])
        self.assertIn("restore was tested", ready["restore_capability"])
        self.assertIn("restored application state was verified", ready["restore_capability"])

    def test_sensitive_recovery_material_is_forbidden(self):
        forbidden = set(self.policy["sensitive_evidence"]["forbidden"])
        self.assertTrue({"passwords", "tokens", "recovery codes", "private keys", "secret values"} <= forbidden)

    def test_source_policy_does_not_claim_everkeep_acceptance(self):
        acceptance = self.policy["acceptance"]
        self.assertFalse(acceptance["everkeep_integrated"])
        self.assertFalse(acceptance["everkeep_ready"])
        self.assertTrue(acceptance["target_runtime_acceptance_required"])
        self.assertTrue(acceptance["exact_revision_acceptance_required"])
