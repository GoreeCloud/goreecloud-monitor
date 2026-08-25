from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "everkeep.adoption.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_everkeep_manifest_is_fail_closed_and_read_only() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == 1
    assert manifest["project"] == "GoreeCloud Monitor"
    assert manifest["repository"] == "GoreeCloud/goreecloud-monitor"
    assert manifest["role"] == "producer"
    assert manifest["read_only"] is True
    assert manifest["fail_closed"] is True
    assert manifest["status_schema"] == "contracts/continuity.status.schema.json"


def test_everkeep_dimensions_match_existing_recovery_evidence() -> None:
    assert set(_manifest()["dimensions"]) == {
        "backup_coverage",
        "restore_capability",
        "recovery_freshness",
        "migration",
        "dependency_recovery",
        "documentation",
        "provenance",
    }


def test_everkeep_authoritative_sources_exist() -> None:
    for relative_path in _manifest()["authoritative_sources"]:
        assert (ROOT / relative_path).is_file(), relative_path


def test_everkeep_manifest_does_not_claim_ready() -> None:
    text = MANIFEST.read_text(encoding="utf-8").lower()
    assert '"ready": true' not in text
    assert "target-native database restore" in text
    assert "live rollback" in text
    assert "exact-revision acceptance" in text
