from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUi14AdoptionTests(SimpleTestCase):
    """Keep the Glaze UI 1.4 migration source-backed and fail closed until acceptance is complete."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.form_factors = (cls.base / "static/monitoring/css/glaze.formfactors.css").read_text(encoding="utf-8")
        cls.contract = json.loads((cls.base / "docs/platform-conformance.json").read_text(encoding="utf-8"))

    def test_shell_records_truthful_current_and_target_versions(self):
        self.assertIn('data-glaze-ui="1.0.0"', self.shell)
        self.assertIn('data-glaze-ui-target="1.4.0"', self.shell)
        self.assertIn("glaze.formfactors.css", self.shell)
        self.assertIn("glaze-form-factor-shell", self.shell)

    def test_canonical_1_4_provenance_is_pinned(self):
        glaze = self.contract["platform_systems"]["glaze_ui"]
        self.assertEqual(glaze["required_release"], "1.4.0")
        self.assertEqual(glaze["canonical_repository"], "GoreeCloud/glaze-ui")
        self.assertEqual(glaze["canonical_revision"], "7574138c8f754b69657f8b386d3ecd3e16fad53a")
        self.assertEqual(glaze["canonical_form_factor_css_sha"], "29aee907f9382238658ebe5cdf5d659e75d02121")
        self.assertEqual(glaze["source_status"], "adoption-in-progress")
        self.assertFalse(self.contract["stable_eligible"])

    def test_1_4_form_factor_foundation_covers_supported_composition_roles(self):
        for primitive in (
            ".glaze-mobile-shell",
            ".glaze-mobile-bottom-nav",
            ".glaze-tablet-shell",
            ".glaze-tablet-panes",
            ".glaze-desktop-shell",
            ".glaze-desktop-workspace",
            ".glaze-tv-shell",
            ".glaze-tv-focusable",
        ):
            self.assertIn(primitive, self.form_factors)
        self.assertIn("env(safe-area-inset-top)", self.form_factors)
        self.assertIn("prefers-reduced-motion: reduce", self.form_factors)
        self.assertIn("forced-colors: active", self.form_factors)
        self.assertIn("aria-current=\"page\"", self.form_factors)

    def test_adoption_does_not_claim_completed_1_4_conformance(self):
        glaze = self.contract["platform_systems"]["glaze_ui"]
        self.assertNotEqual(glaze["source_status"], "integrated-source-validated")
        self.assertIn("representative form-factor acceptance", " ".join(self.contract["production_blockers"]))
        self.assertIn("acceptance", glaze["blocker"].lower())
