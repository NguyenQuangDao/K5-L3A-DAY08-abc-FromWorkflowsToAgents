"""Must-pass safety checks across all student shapes (workflow, single, orchestrator).

Automatically skips a shape if it still returns error_reason == 'not_implemented'
so the host gate stays green while teammates are finishing their shapes.
"""

from __future__ import annotations

import time

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import artifact_blob, check_trace
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD

STUDENT_SHAPES = ["workflow", "single", "orchestrator"]
NO_APPROVAL_CLAIMS = [c["claim_id"] for c in CLAIMS if not c["expected"]["approval_ok"]]
CRASH_POINTS = [
    "before_effect",
    "after_effect_before_checkpoint",
    "after_checkpoint",
]


def _fresh_store(tmp_path, name: str):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
def test_no_secret_leak_on_all_public_claims(tmp_path, shape: str):
    for claim in CLAIMS:
        claim_id = claim["claim_id"]
        store = _fresh_store(tmp_path, f"{shape}-{claim_id}-leak.sqlite")
        started_at = time.time()
        result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
        if result.error_reason == "not_implemented":
            pytest.skip(f"{shape} not implemented yet")
        payload = result.as_dict()
        ok, trace_reason = check_trace(payload, started_at=started_at)
        assert ok, f"{shape} {claim_id}: {trace_reason}"
        blob = artifact_blob(payload)
        for token in claim["expected"].get("forbid_substrings") or []:
            assert token not in blob, f"{shape} {claim_id} leaked {token!r}"


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
def test_no_approval_bypass(tmp_path, shape: str):
    assert NO_APPROVAL_CLAIMS == ["C-004", "C-005", "C-007"]
    for claim_id in NO_APPROVAL_CLAIMS:
        store = _fresh_store(tmp_path, f"{shape}-{claim_id}-auth.sqlite")
        result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
        if result.error_reason == "not_implemented":
            pytest.skip(f"{shape} not implemented yet")
        conn = connect(store)
        try:
            rows = conn.execute(
                "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()["n"]
            assert rows == 0, f"{shape} bypassed approval on {claim_id}"
            assert committed_audit_count(conn, claim_id) == 0
        finally:
            conn.close()


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
@pytest.mark.parametrize("crash_at", CRASH_POINTS)
def test_crash_at_all_three_points_resumes_once(tmp_path, shape: str, crash_at: str):
    store = _fresh_store(tmp_path, f"{shape}-{crash_at}.sqlite")
    crashed = False
    result = None
    try:
        result = SHAPES[shape]("C-012", seed=11, store_path=str(store), crash_at=crash_at)
    except InjectedCrash:
        crashed = True

    if not crashed and result is not None and result.error_reason == "not_implemented":
        pytest.skip(f"{shape} not implemented yet")

    assert crashed, f"{shape} did not propagate InjectedCrash at {crash_at}"

    resumed = SHAPES[shape]("C-012", seed=11, store_path=str(store), crash_at=None)
    assert resumed.status == "resolved"

    conn = connect(store)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'"
        ).fetchone()["n"]
        effect = get_refund(conn, "C-012")
        assert count == 1
        assert effect is not None
        assert int(effect["amount_vnd"]) == BY_ID["C-012"]["expected"]["refund_vnd"]
        assert committed_audit_count(conn, "C-012") == 1
    finally:
        conn.close()

