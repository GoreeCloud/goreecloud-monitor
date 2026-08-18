from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]


class AppIdentityTests(TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "packaging" / "app-identity.json").read_text(encoding="utf-8"))

    def test_canonical_monitor_mark_matches_recorded_digest(self):
        artwork = ROOT / self.contract["canonical_artwork"]["path"]
        self.assertEqual(hashlib.sha256(artwork.read_bytes()).hexdigest(), self.contract["canonical_artwork"]["sha256"])
        self.assertFalse(self.contract["canonical_artwork"]["artwork_changed_by_this_contract"])

    def test_web_surfaces_share_canonical_identity(self):
        shell = (ROOT / "templates" / "monitoring" / "base.html").read_text(encoding="utf-8")
        admin = (ROOT / "templates" / "admin" / "base_site.html").read_text(encoding="utf-8")
        login = (ROOT / "templates" / "registration" / "login.html").read_text(encoding="utf-8")
        self.assertIn("monitor-mark.svg", shell); self.assertIn("monitor-mark.svg", admin); self.assertIn("monitor-mark.svg", login)
        self.assertIn("manifest.webmanifest", shell)
        manifest = json.loads((ROOT / "static" / "monitoring" / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "GoreeCloud Monitor")
        self.assertTrue(any(icon["src"].endswith("/monitor-mark.svg") and icon["type"] == "image/svg+xml" for icon in manifest["icons"]))

    def test_nonexistent_client_packages_are_explicitly_blocked_not_mocked(self):
        self.assertEqual(self.contract["surfaces"]["linux_appimage"]["status"], "blocked-no-client-package")
        self.assertEqual(self.contract["surfaces"]["android_apk"]["status"], "blocked-no-client-package")
        self.assertEqual(self.contract["surfaces"]["linux_appimage"]["canonical_source"], self.contract["canonical_artwork"]["path"])
        self.assertEqual(self.contract["surfaces"]["android_apk"]["canonical_source"], self.contract["canonical_artwork"]["path"])

    def test_identity_assets_have_no_remote_dependency(self):
        manifest = (ROOT / "static" / "monitoring" / "manifest.webmanifest").read_text(encoding="utf-8")
        contract = (ROOT / "packaging" / "app-identity.json").read_text(encoding="utf-8")
        self.assertNotIn("https://", manifest); self.assertNotIn("http://", manifest); self.assertNotIn("https://", contract); self.assertNotIn("http://", contract)
