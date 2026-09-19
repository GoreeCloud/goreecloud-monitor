import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class MigrationReadinessContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.contract = json.loads(
            (cls.base / "docs/migration-readiness.json").read_text(encoding="utf-8")
        )

    def test_source_ready_for_replacement_activation_but_not_production(self):
        self.assertEqual(
            self.contract["schema"], "goreecloud-monitor-migration-readiness/v1"
        )
        readiness = self.contract["readiness"]
        self.assertTrue(readiness["source_ready"])
        self.assertTrue(readiness["migration_ready"])
        self.assertFalse(readiness["production_cutover_authorized"])
        self.assertFalse(readiness["stable_eligible"])
        self.assertEqual(
            self.contract["authority"]["current_production_monitoring"],
            "None; Uptime Kuma retired 2026-09-18 and GoreeCloud Monitor remains pending production acceptance",
        )
        self.assertEqual(
            self.contract["authority"]["migration_mode"],
            "post-retirement-replacement-activation",
        )
        self.assertFalse(
            self.contract["authority"]["retirement_requires_explicit_approval"]
        )

    def test_all_required_source_evidence_exists(self):
        for relative_path in self.contract["required_source_evidence"]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((self.base / relative_path).is_file())

    def test_live_replacement_activation_gates_remain_explicit(self):
        gates = set(self.contract["pre_cutover_live_gates"])
        self.assertIn("preserved-uptime-kuma-evidence-reconciliation", gates)
        self.assertIn("representative-live-monitor-validation-against-preserved-requirements", gates)
        self.assertIn("live-ping-icmp-and-resolver-specific-dns-validation", gates)
        self.assertIn("notify-producer-runtime-credential-and-delivery-acceptance", gates)
        self.assertIn("notify-durable-outbox-restart-replay-and-retention-acceptance", gates)
        self.assertIn("monitor-rollback-and-recovery-exercise", gates)
        self.assertIn("explicit-production-activation-approval", gates)
