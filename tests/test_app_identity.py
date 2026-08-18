import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class AppIdentityContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = Path(settings.BASE_DIR)
        cls.canonical_path = cls.root / "assets/app-icon/goreecloud-monitor.svg"
        cls.web_path = cls.root / "static/monitoring/img/goreecloud-monitor.svg"
        cls.identity_manifest = json.loads((cls.root / "assets/app-icon/manifest.json").read_text(encoding="utf-8"))

    def test_canonical_icon_is_text_free_local_scalable_artwork(self):
        source = self.canonical_path.read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 1024 1024"', source)
        self.assertNotIn("<text", source.lower())
        self.assertNotIn("href=", source.lower())
        self.assertIn("#73d9a2", source)
        self.assertIn("monitor-gradient", source)

    def test_web_icon_is_byte_identical_to_canonical_source(self):
        canonical = self.canonical_path.read_bytes()
        self.assertEqual(canonical, self.web_path.read_bytes())
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), self.identity_manifest["canonical_sha256"])

    def test_web_manifest_uses_canonical_monitor_identity(self):
        manifest = json.loads((self.root / "static/monitoring/manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "GoreeCloud Monitor")
        self.assertEqual(manifest["icons"][0]["src"], "/static/monitoring/img/goreecloud-monitor.svg")
        self.assertEqual(manifest["icons"][0]["sizes"], "any")
        self.assertIn("maskable", manifest["icons"][0]["purpose"])

    def test_native_clients_share_identity_and_canonical_origin(self):
        config = json.loads((self.root / "clients/goreecloud-monitor/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        rust = (self.root / "clients/goreecloud-monitor/src-tauri/src/lib.rs").read_text(encoding="utf-8")
        workflow = (self.root / ".github/workflows/native-clients.yml").read_text(encoding="utf-8")
        self.assertEqual(config["productName"], "GoreeCloud Monitor")
        self.assertEqual(config["identifier"], "com.goreecloud.monitor")
        self.assertFalse(config["app"]["withGlobalTauri"])
        self.assertIn('const APP_URL: &str = "https://monitor.goreecloud.com";', rust)
        self.assertIn("NewWindowResponse::Deny", rust)
        self.assertIn("port_or_known_default() == Some(443)", rust)
        self.assertIn("assets/app-icon/goreecloud-monitor.svg", workflow)
        self.assertIn("appimage,deb", workflow)
        self.assertIn("android build --debug --apk --target aarch64", workflow)

    def test_identity_manifest_declares_web_linux_and_android_consumers(self):
        self.assertEqual(self.identity_manifest["canonical_source"], "assets/app-icon/goreecloud-monitor.svg")
        self.assertEqual(self.identity_manifest["web"]["source"], "static/monitoring/img/goreecloud-monitor.svg")
        platforms = self.identity_manifest["native_generation"]["platforms"]
        self.assertIn("Linux AppImage", platforms)
        self.assertIn("Android APK", platforms)
