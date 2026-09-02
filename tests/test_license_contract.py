"""Repository licensing contract tests for GoreeCloud Monitor."""

from __future__ import annotations

import tomllib
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]


class LicenseContractTests(TestCase):
    def test_repository_license_is_agpl_v3_only(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("SPDX-License-Identifier: AGPL-3.0-only", license_text)
        self.assertIn("version 3 only", license_text)
        self.assertIn("https://www.gnu.org/licenses/agpl-3.0.txt", license_text)
        self.assertNotIn("MIT License", license_text)

    def test_package_metadata_matches_repository_license(self):
        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)["project"]

        self.assertEqual(project["license"]["text"], "AGPL-3.0-only")

    def test_readme_and_notice_record_current_and_prior_license_boundaries(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        notice = (ROOT / "LICENSE-NOTICE.md").read_text(encoding="utf-8")

        self.assertIn("AGPL-3.0-only", readme)
        self.assertIn("LICENSE-NOTICE.md", readme)
        self.assertNotIn("MIT. See `LICENSE`.", readme)
        self.assertIn("already distributed under the MIT License", notice)
        self.assertIn("retain the MIT permissions previously granted", notice)
        self.assertIn("Uptime Kuma", notice)
        self.assertIn("third-party materials retain their applicable licenses", notice)
