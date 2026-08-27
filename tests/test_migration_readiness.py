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

    def test_ready_to_begin_migration_but_not_cutover(self):
        self.assertEqual(
            self.contract["schema"], "goreecloud-monitor-migration-readiness/v1"
        )
        readiness = self.contract["readiness"]
        self.assertTrue(readiness["source_ready"])
        self.assertTrue(readiness["migration_ready"])
        self.assertFalse(readiness["production_cutover_authorized"])
        self.assertFalse(readiness["stable_eligible"])
        self.assertEqual(
            self.contract["authority"]["current_production_monitoring"], "Uptime Kuma"
        )

    def test_all_required_source_evidence_exists(self):
        for relative_path in self.contract["required_source_evidence"]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((self.base / relative_path).is_file())

    def test_live_pre_cutover_gates_remain_explicit(self):
        gates = set(self.contract["pre_cutover_live_gates"])
        self.assertIn("fresh-sanitized-uptime-kuma-configuration-reconciliation", gates)
        self.assertIn("repeated-parallel-runtime-comparison", gates)
        self.assertIn("live-ping-icmp-and-resolver-specific-dns-validation", gates)
        self.assertIn("notify-producer-runtime-credential-and-delivery-acceptance", gates)
        self.assertIn("live-rollback-exercise", gates)
        self.assertIn("explicit-production-cutover-approval", gates)
