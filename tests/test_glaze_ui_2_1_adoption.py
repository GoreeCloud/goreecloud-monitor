from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUi21AdoptionTests(SimpleTestCase):
    """Keep the Glaze UI 2.1 adoption exact, source-backed, and fail closed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.css = (cls.base / "static/monitoring/css/glaze.2.1.css").read_text(encoding="utf-8")
        cls.accessibility = (cls.base / "static/monitoring/css/glaze.accessibility.css").read_text(encoding="utf-8")
        cls.form_factors = (cls.base / "static/monitoring/css/glaze.formfactors.css").read_text(encoding="utf-8")
        cls.ledger = json.loads((cls.base / "docs/glaze-ui-2.1-adoption.json").read_text(encoding="utf-8"))
        cls.platform = json.loads((cls.base / "docs/platform-conformance.json").read_text(encoding="utf-8"))

    def test_shell_targets_2_1_as_an_adoption_candidate(self):
        self.assertIn("glaze.2.1.css", self.shell)
        self.assertIn('data-glaze-ui="2.1.0"', self.shell)
        self.assertIn('data-glaze-ui-target="2.1.0"', self.shell)
        self.assertIn('data-glaze-ui-status="adoption-candidate"', self.shell)

    def test_exact_stable_release_anchor_is_pinned(self):
        self.assertEqual(self.ledger["target_release"], "2.1.0")
        self.assertEqual(self.ledger["canonical_repository"], "GoreeCloud/goreecloud-glaze-ui")
        self.assertEqual(self.ledger["canonical_release_tag"], "v2.1.0")
        self.assertEqual(self.ledger["canonical_revision"], "c49113eb8b93c267613fdf1bbca1f814495acad7")
        self.assertEqual(self.ledger["adoption_status"], "adoption-candidate")
        self.assertFalse(self.ledger["conformance_claim"])
        self.assertFalse(self.ledger["stable_eligible"])

    def test_2_1_material_target_and_density_contract_is_present(self):
        for token in (
            '--glaze-ui-version: "2.1.0"',
            "--glaze-target-min: 48px",
            "--glaze-target-touch-assistance: 56px",
            "--glaze-target-far-view: 56px",
            "--glaze-material-canvas",
            "--glaze-material-surface",
            "--glaze-material-soft-glaze",
            "--glaze-material-glaze",
            "--glaze-material-deep-glaze",
            "--glaze-material-live-glaze",
            "--glaze-material-clarity: balanced",
            "--glaze-density-effective: standard",
        ):
            self.assertIn(token, self.css)

    def test_accessibility_resolution_hooks_are_explicit(self):
        for rule in (
            'data-glaze-large-text="true"',
            'data-glaze-touch-assistance="true"',
            "prefers-reduced-transparency: reduce",
            "prefers-contrast: more",
            "forced-colors: active",
        ):
            self.assertIn(rule, self.css)
        self.assertIn("prefers-reduced-motion: reduce", self.accessibility)
        self.assertIn("--glaze-tv-target-min: 56px", self.form_factors)

    def test_platform_authorities_are_not_replaced_by_glaze(self):
        authorities = self.ledger["platform_authority"]
        self.assertEqual(authorities["security"], "Wardveil Security")
        self.assertEqual(authorities["privacy"], "Privacy Shield")
        self.assertEqual(authorities["continuity"], "Everkeep")
        self.assertEqual(authorities["identity"], "GoreeCloud Identity")
        self.assertEqual(authorities["coordination"], "GoreeCloud Mesh")

    def test_production_readiness_remains_fail_closed(self):
        self.assertFalse(self.platform["stable_eligible"])
        self.assertIn("15_rendered_visual_excellence", self.ledger["blocking_gates"])
        self.assertIn("16_browser_os_accessibility", self.ledger["blocking_gates"])
        self.assertIn("18_central_consumer_registry", self.ledger["blocking_gates"])
