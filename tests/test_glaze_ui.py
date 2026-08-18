import json
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
        cls.wardveil = (cls.base / "static/monitoring/css/wardveil.css").read_text()
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text()
        cls.security = (cls.base / "templates/monitoring/security.html").read_text()
        cls.script = (cls.base / "static/monitoring/js/glaze.js").read_text()
        cls.admin_shell = (cls.base / "templates/admin/base_site.html").read_text()
        cls.admin_css = (cls.base / "static/monitoring/css/glaze-admin.css").read_text()
        cls.canonical_icon = (cls.base / "assets/identity/goreecloud-monitor-icon.svg").read_text()
        cls.web_icon = (cls.base / "static/monitoring/img/goreecloud-monitor-icon.svg").read_text()
        cls.appimage_icon = (cls.base / "packaging/appimage/goreecloud-monitor.svg").read_text()
        cls.web_manifest = json.loads((cls.base / "static/monitoring/site.webmanifest").read_text())
        cls.android_foreground = (cls.base / "packaging/android/res/drawable/goreecloud_monitor_icon_foreground.xml").read_text()
        cls.android_monochrome = (cls.base / "packaging/android/res/drawable/goreecloud_monitor_icon_monochrome.xml").read_text()

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
        self.assertIn("viewer-nav", self.wardveil)
        self.assertIn("staff-nav", self.wardveil)

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
        self.assertIn("prefers-reduced-transparency", self.wardveil)
        self.assertIn("forced-colors: active", self.wardveil)
        self.assertIn("prefers-reduced-transparency", self.admin_css)
        self.assertIn("forced-colors: active", self.admin_css)
        self.assertIn("focus-visible", self.admin_css)

    def test_product_identity_and_local_assets_are_present(self):
        self.assertIn("goreecloud-monitor-icon.svg", self.shell)
        self.assertIn("site.webmanifest", self.shell)
        self.assertNotIn("monitor-mark.svg", self.shell)
        self.assertNotIn("brand-mark\" aria-hidden=\"true\">G", self.shell)
        self.assertNotIn("@import url", self.css)
        self.assertNotIn("https://", self.css)
        self.assertNotIn("http://", self.css)
        self.assertNotIn("https://", self.wardveil)
        self.assertNotIn("http://", self.wardveil)
        self.assertIn("goreecloud-monitor-icon.svg", self.admin_shell)
        self.assertIn("glaze-admin.css", self.admin_shell)
        self.assertIn("--glaze-canvas", self.admin_css)
        self.assertNotIn("https://", self.admin_css)
        self.assertNotIn("http://", self.admin_css)

    def test_cross_platform_icon_identity_is_complete_and_consistent(self):
        identity_path = "M102 282h67l31-87 56 174 41-113h56l36-42h33"
        self.assertEqual(self.canonical_icon, self.web_icon)
        self.assertIn(identity_path, self.canonical_icon)
        self.assertIn(identity_path, self.appimage_icon)
        self.assertIn("M102,282 L169,282 L200,195 L256,369 L297,256 L353,256 L389,214 L422,214", self.android_foreground)
        self.assertIn("M102,282 L169,282 L200,195 L256,369 L297,256 L353,256 L389,214 L422,214", self.android_monochrome)
        self.assertEqual(self.web_manifest["name"], "GoreeCloud Monitor")
        manifest_sizes = {icon["sizes"] for icon in self.web_manifest["icons"]}
        self.assertEqual(manifest_sizes, {"192x192", "512x512"})
        self.assertTrue(any("maskable" in icon["purpose"] for icon in self.web_manifest["icons"]))
        for size in (16, 32, 48, 192, 512):
            variant = self.base / f"static/monitoring/img/goreecloud-monitor-icon-{size}.svg"
            self.assertTrue(variant.exists())
            text = variant.read_text()
            self.assertIn(f'width="{size}"', text)
            self.assertIn(f'height="{size}"', text)
            self.assertIn(identity_path, text)
        self.assertTrue((self.base / "packaging/android/res/mipmap-anydpi-v26/ic_launcher.xml").exists())
        self.assertTrue((self.base / "packaging/android/res/mipmap-anydpi-v26/ic_launcher_round.xml").exists())

    def test_wardveil_is_a_glaze_consumer_not_a_replacement_design_system(self):
        self.assertIn("wardveil.css", self.shell)
        self.assertIn("Protected by Wardveil", self.shell)
        # The canonical full identity is supplied by the security view and is separately
        # asserted on the rendered response. Keep the template bound to that single source
        # rather than duplicating the identity string in presentation markup.
        self.assertIn("{{ wardveil_identity }}", self.security)
        self.assertIn("var(--glaze-", self.wardveil)
        self.assertNotIn("Wardveil Security Center", self.security)
        self.assertNotIn("--wardveil-color", self.wardveil)
        self.assertIn("Protected by Wardveil", self.admin_shell)

    def test_appearance_preference_is_fail_soft_and_local_only(self):
        self.assertIn("goreecloud-monitor-appearance", self.script)
        self.assertIn("localStorage", self.script)
        self.assertIn("catch", self.script)
        self.assertNotIn("fetch(", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)
