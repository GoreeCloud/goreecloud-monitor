from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUiConformanceTests(SimpleTestCase):
    """Fail closed when Monitor drifts away from the source-controlled Glaze UI 1.0 contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.css = (cls.base / "static/monitoring/css/glaze.css").read_text()
        cls.accessibility = (cls.base / "static/monitoring/css/glaze.accessibility.css").read_text()
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text()
        cls.script = (cls.base / "static/monitoring/js/glaze.js").read_text()
        cls.admin_shell = (cls.base / "templates/admin/base_site.html").read_text()
        cls.admin_css = (cls.base / "static/monitoring/css/glaze-admin.css").read_text()

    def test_semantic_tokens_and_surface_hierarchy_are_present(self):
        for token in (
            "--glaze-canvas",
            "--glaze-surface",
            "--glaze-surface-strong",
            "--glaze-accent",
            "--glaze-target-min: 44px",
            "--glaze-motion-instant: 90ms",
            "--glaze-motion-fast: 160ms",
            "--glaze-motion-standard: 220ms",
            "--glaze-motion-emphasized: 320ms",
        ):
            self.assertIn(token, self.css)
        for surface in ("glaze-surface-solid", "glaze-surface-raised", "glaze-surface", "glaze-overlay"):
            self.assertIn(surface, self.css)

    def test_glaze_adaptive_ranges_and_compact_navigation_are_present(self):
        self.assertIn("max-width: 599px", self.css)
        self.assertIn("max-width: 1023px", self.css)
        self.assertIn("min-width: 1440px", self.css)
        self.assertIn("mobile-nav", self.css)
        self.assertIn("Primary mobile navigation", self.shell)

    def test_accessibility_resilience_contract_is_present(self):
        for rule in (
            "prefers-reduced-transparency",
            "prefers-reduced-motion",
            "prefers-contrast: more",
            "forced-colors: active",
            "backdrop-filter",
            "glaze-sr-only",
        ):
            self.assertIn(rule, self.accessibility)
        self.assertIn("focus-visible", self.css)
        self.assertIn("Skip to main content", self.shell)
        self.assertIn("prefers-reduced-transparency", self.admin_css)
        self.assertIn("forced-colors: active", self.admin_css)
        self.assertIn("focus-visible", self.admin_css)

    def test_product_identity_and_local_assets_are_present(self):
        self.assertIn("monitor-mark.svg", self.shell)
        self.assertNotIn("brand-mark\" aria-hidden=\"true\">G", self.shell)
        self.assertNotIn("@import url", self.css)
        self.assertNotIn("https://", self.css)
        self.assertNotIn("http://", self.css)
        self.assertIn("monitor-mark.svg", self.admin_shell)
        self.assertIn("glaze-admin.css", self.admin_shell)
        self.assertIn("--glaze-canvas", self.admin_css)
        self.assertNotIn("https://", self.admin_css)
        self.assertNotIn("http://", self.admin_css)

    def test_appearance_preference_is_fail_soft_and_local_only(self):
        self.assertIn("goreecloud-monitor-appearance", self.script)
        self.assertIn("localStorage", self.script)
        self.assertIn("catch", self.script)
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)
