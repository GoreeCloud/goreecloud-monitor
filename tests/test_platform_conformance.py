from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "platform-conformance.json"
EXPECTED_SYSTEMS = {
    "manager",
    "privacy_shield",
    "wardveil_security",
    "everkeep",
    "glaze_ui",
    "goreecloud_mesh",
    "goreecloud_identity",
    "goreecloud_policy",
    "goreecloud_observability",
}
EXPECTED_IDENTITIES = {
    "manager": "GoreeCloud Manager",
    "privacy_shield": "GoreeCloud Privacy Shield",
    "wardveil_security": "Wardveil Security by GoreeCloud",
    "everkeep": "Everkeep",
    "glaze_ui": "Glaze UI",
    "goreecloud_mesh": "GoreeCloud Mesh",
    "goreecloud_identity": "GoreeCloud Identity",
    "goreecloud_policy": "GoreeCloud Policy",
    "goreecloud_observability": "GoreeCloud Observability",
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
        for relative_path in system.get("evidence", []):
            assert (ROOT / relative_path).is_file(), relative_path


def test_unfinished_platform_work_cannot_be_presented_as_stable() -> None:
    contract = _contract()
    systems = contract["platform_systems"]
    glaze = systems["glaze_ui"]
    assert glaze["required_version"] == "1.5"
    assert glaze["required_release"] == "1.5.1"
    assert glaze["canonical_repository"] == "GoreeCloud/goreecloud-glaze-ui"
    assert glaze["canonical_revision"] == "5b59d0e36950d737dba35b58ae58058684e0831b"
    assert glaze["source_status"] == "v1.5.1-source-adoption-candidate-acceptance-required"
    assert systems["wardveil_security"]["source_status"] == "integrated-source-validated-adoption-contract"
    wardveil = json.loads((ROOT / "docs" / "wardveil.adoption.json").read_text(encoding="utf-8"))
    assert wardveil["fail_closed"] is True
    assert wardveil["unknown_when_evidence_missing"] is True
    assert wardveil["acceptance"]["target_runtime_acceptance_required"] is True
    assert wardveil["acceptance"]["production_approved"] is False
    assert systems["privacy_shield"]["source_status"] == "draft-adapter-source-candidate"
    assert systems["everkeep"]["source_status"] == "draft-acceptance-policy-candidate"
    assert systems["manager"]["source_status"] == "applicable-blocked"
    assert systems["goreecloud_mesh"]["source_status"] == "applicable-blocked"
    assert systems["goreecloud_identity"]["source_status"] == "applicable-blocked"
    assert systems["goreecloud_policy"]["source_status"] == "applicable-blocked"
    assert systems["goreecloud_observability"]["source_status"] == "applicable-blocked"
    everkeep = json.loads((ROOT / "docs" / "everkeep.adoption.json").read_text(encoding="utf-8"))
    assert everkeep["fail_closed"] is True
    assert everkeep["read_only"] is True
    assert contract["production_blockers"]
    assert contract["stable_eligible"] is False
