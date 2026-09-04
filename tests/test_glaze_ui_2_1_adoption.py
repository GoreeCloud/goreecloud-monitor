from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUi21HistoricalEvidenceTests(SimpleTestCase):
    """Keep the former 2.1 adoption record as history, never active authority."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.ledger = json.loads((cls.base / "docs/glaze-ui-2.1-adoption.json").read_text(encoding="utf-8"))
        cls.css = (cls.base / "static/monitoring/css/glaze.2.1.css").read_text(encoding="utf-8")

    def test_historical_2_1_record_remains_exact(self):
        self.assertEqual(self.ledger["target_release"], "2.1.0")
        self.assertEqual(self.ledger["canonical_revision"], "c49113eb8b93c267613fdf1bbca1f814495acad7")
        self.assertFalse(self.ledger["conformance_claim"])
        self.assertFalse(self.ledger["stable_eligible"])
        self.assertIn('--glaze-ui-version: "2.1.0"', self.css)

    def test_historical_2_1_layer_is_not_active_in_current_shell(self):
        self.assertNotIn("glaze.2.1.css", self.shell)
        self.assertNotIn('data-glaze-ui="2.1.0"', self.shell)
        self.assertIn("glaze.1.1.css", self.shell)
        self.assertIn('data-glaze-ui="1.1.0"', self.shell)
