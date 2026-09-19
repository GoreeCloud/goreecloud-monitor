from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUi151AdoptionTests(SimpleTestCase):
    """Enforce Monitor's current Glaze UI 1.5.1 source-adoption boundary."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.css = (cls.base / "static/monitoring/css/glaze.1.5.1.css").read_text(encoding="utf-8")
        cls.script = (cls.base / "static/monitoring/js/glaze.js").read_text(encoding="utf-8")
        cls.accessibility = (
            cls.base / "static/monitoring/css/glaze.accessibility.css"
        ).read_text(encoding="utf-8")
        cls.form_factors = (
            cls.base / "static/monitoring/css/glaze.formfactors.css"
        ).read_text(encoding="utf-8")
        cls.ledger = json.loads(
            (cls.base / "docs/glaze-ui-v1.5.1-adoption.json").read_text(encoding="utf-8")
        )
        cls.platform = json.loads(
            (cls.base / "docs/platform-conformance.json").read_text(encoding="utf-8")
        )

    def test_exact_current_stable_identity_is_pinned(self):
        self.assertEqual(self.ledger["required_target_release"], "1.5.1")
        self.assertEqual(self.ledger["current_source_mapping_release"], "1.5.1")
        self.assertEqual(
            self.ledger["canonical_repository"],
            "GoreeCloud/goreecloud-glaze-ui",
        )
        self.assertEqual(
            self.ledger["reviewed_implementation_anchor"],
            "ee1032a0822ab8e103f8afe48e5c1859fde65cc9",
        )
        self.assertEqual(
            self.ledger["source_qualification_anchor"],
            "5b59d0e36950d737dba35b58ae58058684e0831b",
        )
        self.assertEqual(self.ledger["adoption_status"], "source-adoption-candidate")
        self.assertFalse(self.ledger["conformance_claim"])
        self.assertFalse(self.ledger["production_eligible"])

    def test_active_shell_targets_1_5_1_with_presentation_only_authority(self):
        self.assertIn("glaze.1.5.1.css", self.shell)
        self.assertIn('data-glaze-ui="1.5.1"', self.shell)
        self.assertIn('data-glaze-ui-target="1.5.1"', self.shell)
        self.assertIn('data-glaze-ui-status="source-adoption-candidate"', self.shell)
        self.assertIn('data-glaze-authority="presentation-only"', self.shell)

    def test_material_target_density_and_accessibility_source_is_present(self):
        for token in (
            '--glaze-ui-version: "1.5.1"',
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

        for rule in (
            "prefers-reduced-transparency: reduce",
            "prefers-contrast: more",
            "forced-colors: active",
        ):
            self.assertIn(rule, self.css)
        self.assertIn("prefers-reduced-motion: reduce", self.accessibility)
        self.assertIn("--glaze-tv-target-min: 56px", self.form_factors)

    def test_browser_resolver_is_local_presentation_only(self):
        for marker in (
            'root.dataset.glazeUi = "1.5.1"',
            'root.dataset.glazeAuthority = "presentation-only"',
            "prefers-reduced-motion: reduce",
            "prefers-reduced-transparency: reduce",
            "prefers-contrast: more",
            "forced-colors: active",
        ):
            self.assertIn(marker, self.script)
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)

    def test_current_glaze_gate_remains_fail_closed(self):
        self.assertFalse(self.platform["stable_eligible"])
        self.assertTrue(self.ledger["blockers"])
        for gate in (
            "representative-browser-os-accessibility",
            "application-performance-budget",
            "governed-consumer-registry-acceptance",
            "exact-revision-production-approval",
        ):
            self.assertIn(gate, self.ledger["required_acceptance"])
