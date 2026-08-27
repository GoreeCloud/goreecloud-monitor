from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "glaze-ui-1.4-gates.json"


def _ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_glaze_1_4_ledger_covers_all_required_gates() -> None:
    ledger = _ledger()
    assert ledger["schema_version"] == 1
    assert ledger["application"] == "goreecloud-monitor"
    assert ledger["target_release"] == "1.4.0"
    assert ledger["canonical_repository"] == "GoreeCloud/glaze-ui"
    assert ledger["canonical_revision"] == "7574138c8f754b69657f8b386d3ecd3e16fad53a"
    assert len(ledger["gates"]) == 21
    assert list(ledger["gates"])[0] == "01_identity"
    assert list(ledger["gates"])[-1] == "21_stability_and_lifecycle"


def test_glaze_1_4_ledger_is_fail_closed() -> None:
    ledger = _ledger()
    assert ledger["conformance_claim"] is False
    assert ledger["stable_eligible"] is False
    assert ledger["gates"]["20_visual_acceptance"]["status"] == "pending"
    assert ledger["gates"]["21_stability_and_lifecycle"]["status"] == "pending"
    assert "20_visual_acceptance" in ledger["blocking_gates"]
    assert "21_stability_and_lifecycle" in ledger["blocking_gates"]


def test_glaze_1_4_source_evidence_paths_exist() -> None:
    for gate in _ledger()["gates"].values():
        for relative_path in gate.get("evidence", []):
            assert (ROOT / relative_path).exists(), relative_path


def test_manual_acceptance_is_not_silently_substituted_by_source_evidence() -> None:
    ledger = _ledger()
    statuses = {key: value["status"] for key, value in ledger["gates"].items()}
    assert "manual-acceptance-required" in statuses["08_accessibility"]
    assert "manual-acceptance-required" in statuses["10_form_factor_fidelity"]
    assert "manual-acceptance-required" in statuses["11_mobile_fidelity"]
    assert "manual-acceptance-required" in statuses["12_tablet_fidelity"]
    assert "manual-acceptance-required" in statuses["13_desktop_fidelity"]
    assert statuses["20_visual_acceptance"] == "pending"
    assert "does not constitute Glaze UI 1.4 conformance" in ledger["acceptance_boundary"]
