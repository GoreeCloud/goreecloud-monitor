from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "platform-conformance.json"
EXPECTED_SYSTEMS = {"glaze_ui", "wardveil_security", "privacy_shield", "everkeep"}
EXPECTED_IDENTITIES = {
    "glaze_ui": "Glaze UI",
    "wardveil_security": "Wardveil Security by GoreeCloud",
    "privacy_shield": "GoreeCloud Privacy Shield",
    "everkeep": "Everkeep",
}


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_platform_contract_covers_all_mandatory_systems() -> None:
    contract = _contract()
    assert contract["schema_version"] == 1
    assert contract["application"] == "goreecloud-monitor"
    assert set(contract["platform_systems"]) == EXPECTED_SYSTEMS
    assert contract["stable_eligible"] is False


def test_platform_identities_are_canonical() -> None:
    systems = _contract()["platform_systems"]
    for key, identity in EXPECTED_IDENTITIES.items():
        assert systems[key]["identity"] == identity


def test_conformance_evidence_paths_are_real_repository_files() -> None:
    systems = _contract()["platform_systems"]
    for system in systems.values():
        evidence = system["evidence"]
        assert evidence
        for relative_path in evidence:
            assert (ROOT / relative_path).is_file(), relative_path


def test_unfinished_platform_work_cannot_be_presented_as_stable() -> None:
    contract = _contract()
    systems = contract["platform_systems"]
    assert systems["glaze_ui"]["required_version"] == "1.4"
    assert systems["glaze_ui"]["source_status"] == "upgrade-required"
    assert systems["privacy_shield"]["source_status"].endswith("contract-pending")
    assert systems["everkeep"]["source_status"].endswith("contract-pending")
    assert contract["production_blockers"]
    assert contract["stable_eligible"] is False
