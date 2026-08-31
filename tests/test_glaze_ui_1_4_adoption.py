from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class GlazeUi14HistoricalEvidenceTests(SimpleTestCase):
    """Preserve 1.4 evidence as migration history without treating it as current."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = Path(settings.BASE_DIR)
        cls.historical = json.loads((cls.base / "docs/glaze-ui-1.4-gates.json").read_text(encoding="utf-8"))
        cls.current = json.loads((cls.base / "docs/glaze-ui-2.1-adoption.json").read_text(encoding="utf-8"))
        cls.platform = json.loads((cls.base / "docs/platform-conformance.json").read_text(encoding="utf-8"))

    def test_1_4_evidence_is_retained_for_migration_and_audit(self):
        self.assertEqual(self.historical["target_release"], "1.4.0")
        self.assertEqual(self.historical["canonical_revision"], "7574138c8f754b69657f8b386d3ecd3e16fad53a")
        self.assertFalse(self.historical["conformance_claim"])
        self.assertFalse(self.historical["stable_eligible"])

    def test_1_4_is_not_the_current_consumer_target(self):
        glaze = self.platform["platform_systems"]["glaze_ui"]
        self.assertEqual(glaze["required_release"], "2.1.0")
        self.assertEqual(self.current["target_release"], "2.1.0")
        self.assertEqual(self.current["adoption_status"], "adoption-candidate")
        self.assertNotEqual(glaze["required_release"], self.historical["target_release"])
        self.assertFalse(self.platform["stable_eligible"])
