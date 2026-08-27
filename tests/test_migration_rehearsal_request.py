import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class MigrationRehearsalRequestTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.request = json.loads(
            (cls.base / "docs/migration-rehearsal-request.json").read_text(encoding="utf-8")
        )

    def test_request_is_bound_to_reviewed_migration_ready_base(self):
        self.assertEqual(
            self.request["schema"],
            "goreecloud-monitor-migration-rehearsal-request/v1",
        )
        self.assertEqual(
            self.request["reviewed_base_revision"],
            "7d21cc24a97f2ad92c728b6854570cfb0e521d64",
        )
        self.assertEqual(self.request["requested_mode"], "isolated-parallel-acceptance")

    def test_rehearsal_request_cannot_authorize_cutover_or_retirement(self):
        authority = self.request["authority"]
        authorizations = self.request["authorizations"]
        self.assertEqual(authority["current_production_monitoring"], "Uptime Kuma")
        self.assertTrue(authority["uptime_kuma_must_remain_active"])
        self.assertTrue(authorizations["rehearsal_preparation"])
        self.assertTrue(authorizations["sanitized_evidence_collection"])
        self.assertTrue(authorizations["isolated_candidate_validation"])
        self.assertFalse(authorizations["production_cutover"])
        self.assertFalse(authorizations["uptime_kuma_retirement"])
        self.assertFalse(authorizations["monitoring_source_identity_reuse"])

    def test_required_live_acceptance_evidence_stays_explicit(self):
        evidence = set(self.request["required_session_evidence"])
        for required in {
            "exact-candidate-git-revision",
            "fresh-sanitized-uptime-kuma-configuration-reconciliation",
            "target-postgresql-recovery-point-and-isolated-restore",
            "notify-producer-runtime-delivery",
            "repeated-parallel-runtime-comparison",
            "controlled-down-recovered-tls-maintenance-notification-scenarios",
            "live-ping-icmp-and-resolver-specific-dns-validation",
            "live-rollback-exercise",
        }:
            with self.subTest(required=required):
                self.assertIn(required, evidence)
