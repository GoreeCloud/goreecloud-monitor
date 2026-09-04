from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUiV11AdoptionTests(SimpleTestCase):
    """Keep the V1.1 source mapping exact, non-semantic, and fail closed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.css = (cls.base / "static/monitoring/css/glaze.1.1.css").read_text(encoding="utf-8")
        cls.script = (cls.base / "static/monitoring/js/glaze.js").read_text(encoding="utf-8")
        cls.accessibility = (cls.base / "static/monitoring/css/glaze.accessibility.css").read_text(encoding="utf-8")
        cls.form_factors = (cls.base / "static/monitoring/css/glaze.formfactors.css").read_text(encoding="utf-8")
        cls.ledger = json.loads((cls.base / "docs/glaze-ui-v1.1-adoption.json").read_text(encoding="utf-8"))
        cls.platform = json.loads((cls.base / "docs/platform-conformance.json").read_text(encoding="utf-8"))

    def test_shell_activates_v1_1_only(self):
        self.assertIn('data-glaze-version="1.1"', self.shell)
        self.assertIn("glaze.1.1.css", self.shell)
        self.assertNotIn("glaze.2.1.css", self.shell)
        self.assertIn('data-glaze-ui="1.1.0"', self.shell)
        self.assertIn('data-glaze-ui-target="1.1.0"', self.shell)
        self.assertIn('data-glaze-ui-status="adoption-candidate"', self.shell)

    def test_exact_stable_release_anchor_is_pinned(self):
        self.assertEqual(self.ledger["target_release"], "1.1.0")
        self.assertEqual(self.ledger["canonical_repository"], "GoreeCloud/goreecloud-glaze-ui")
        self.assertEqual(self.ledger["canonical_release_tag"], "v1.1.0")
        self.assertEqual(self.ledger["canonical_revision"], "15cc76d2bcd4065552dc31c77145b63f34d9e7b2")
        self.assertEqual(self.ledger["adoption_status"], "adoption-candidate")
        self.assertFalse(self.ledger["conformance_claim"])
        self.assertFalse(self.ledger["stable_eligible"])

    def test_v1_1_optical_geometry_and_target_contract_is_present(self):
        for token in (
            '--glaze-ui-version: "1.1.0"',
            "--glaze-optical-radius-micro: 8px",
            "--glaze-optical-radius-control: 16px",
            "--glaze-optical-radius-container: 24px",
            "--glaze-optical-radius-hero: 32px",
            "--glaze-optical-radius-capsule: 999px",
            "--glaze-target-min: 48px",
            "--glaze-target-touch-assistance: 56px",
            "--glaze-target-far-view: 56px",
        ):
            self.assertIn(token, self.css)

    def test_deep_dark_is_explicit_browser_local_appearance(self):
        self.assertEqual(self.ledger["appearance"]["modes"], ["system", "light", "dark", "deep-dark"])
        self.assertEqual(self.ledger["appearance"]["persistence"], "browser-local-only")
        self.assertFalse(self.ledger["appearance"]["server_account_sync"])
        self.assertIn('data-glz-appearance="deep-dark"', self.css)
        self.assertIn('const values = ["system", "light", "dark", "deep-dark"]', self.script)
        self.assertIn("localStorage", self.script)
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)

    def test_atmosphere_is_static_and_not_operational_state_authority(self):
        atmosphere = self.ledger["atmosphere"]
        self.assertFalse(atmosphere["semantic_authority"])
        self.assertFalse(atmosphere["environmental_color_memory"])
        self.assertFalse(atmosphere["remote_derivation"])
        self.assertFalse(atmosphere["sample_persistence"])
        self.assertFalse(atmosphere["content_sampling"])
        self.assertFalse(atmosphere["operational_state_sampling"])
        self.assertFalse(atmosphere["security_privacy_identity_sampling"])
        self.assertIn("--glaze-atmosphere-deep-teal: #0f6b6f", self.css)
        self.assertIn("--glaze-atmosphere-soft-amber: #d9a35f", self.css)
        for forbidden_selector in ('.metric[data-state=', ".status-dot.up", ".status-dot.down", ".status-dot.degraded"):
            self.assertNotIn(forbidden_selector, self.css)

    def test_accessibility_resolution_hooks_remain_explicit(self):
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
