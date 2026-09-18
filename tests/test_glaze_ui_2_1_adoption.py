from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class HistoricalGlazeUi21RecordTests(SimpleTestCase):
    """Prevent superseded Monitor 2.1 material from regaining current authority."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.shell = (cls.base / "templates/monitoring/base.html").read_text(encoding="utf-8")
        cls.ledger = json.loads(
            (cls.base / "docs/glaze-ui-2.1-adoption.json").read_text(encoding="utf-8")
        )

    def test_2_1_record_is_historical_and_superseded(self):
        self.assertEqual(
            self.ledger["adoption_status"],
            "historical-invalid-current-authority-superseded",
        )
        self.assertEqual(
            self.ledger["superseded_by"],
            "docs/glaze-ui-v1.5.1-adoption.json",
        )
        self.assertFalse(self.ledger["conformance_claim"])
        self.assertFalse(self.ledger["stable_eligible"])

    def test_active_shell_does_not_load_or_claim_2_1(self):
        self.assertNotIn("glaze.2.1.css", self.shell)
        self.assertNotIn('data-glaze-ui="2.1.0"', self.shell)
        self.assertNotIn('data-glaze-ui-target="2.1.0"', self.shell)
        self.assertIn("glaze.1.5.1.css", self.shell)
        self.assertIn('data-glaze-ui="1.5.1"', self.shell)
