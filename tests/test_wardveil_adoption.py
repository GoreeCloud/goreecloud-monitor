from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "wardveil.adoption.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_wardveil_adoption_identity_and_fail_closed_state() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == 1
    assert manifest["project"] == "GoreeCloud Monitor"
    assert manifest["repository"] == "GoreeCloud/goreecloud-monitor"
    assert manifest["identity"] == "Wardveil Security by GoreeCloud"
    assert manifest["presentation_claim"] == "Protected by Wardveil"
    assert manifest["source_status"] == "integrated-source-validated-adoption-contract"
    assert manifest["fail_closed"] is True
    assert manifest["unknown_when_evidence_missing"] is True


def test_wardveil_controls_have_explicit_scope_authority_and_real_evidence() -> None:
    controls = _manifest()["authoritative_controls"]
    assert controls
    for control in controls:
        assert control["scope"]
        assert control["producer"]
        assert (ROOT / control["evidence"]).is_file(), control["evidence"]


def test_wardveil_does_not_claim_external_control_authority() -> None:
    excluded = set(_manifest()["excluded_authority"])
    assert {"firewall", "vpn", "backup", "external-vulnerability-management"} <= excluded


def test_wardveil_target_acceptance_remains_fail_closed() -> None:
    acceptance = _manifest()["acceptance"]
    assert acceptance["exact_revision_ci_required"] is True
    assert acceptance["target_runtime_acceptance_required"] is True
    assert acceptance["production_approved"] is False


def test_wardveil_document_preserves_identity_and_authority_boundary() -> None:
    text = (ROOT / "docs" / "wardveil-security.md").read_text(encoding="utf-8")
    assert "Wardveil Security by GoreeCloud" in text
    assert "Protected by Wardveil" in text
    assert "does **not** replace" in text
    assert "Uptime Kuma remains authoritative" in text
