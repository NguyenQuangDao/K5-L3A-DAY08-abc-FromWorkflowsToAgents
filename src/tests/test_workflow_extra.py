"""Additional unit and branch tests for Shape A (workflow)."""

from __future__ import annotations

import time

from lab8.db import connect, init_store
from lab8.durability import committed_audit_count, get_refund
from lab8.metrics import check_trace, trial_pass
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def test_workflow_ignores_ticket_delay_at_seed_55(public_db):
    started_at = time.time()
    result = run_claim("C-002", seed=55, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-002"]["expected"], conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason


def test_workflow_unknown_claim_fails_safely_with_valid_trace(public_db):
    started_at = time.time()
    result = run_claim("C-999", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.error_reason == "unknown_claim"
    assert result.run_id == "R-workflow-C-999-s11"
    ok, reason = check_trace(result.as_dict(), started_at=started_at)
    assert ok, reason


def test_workflow_broken_approval_and_wrong_claim_approval_are_denied(tmp_path):
    store = tmp_path / "approval-branches.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    # C-007 has an expired approval -> quote > 0, denied with policy_denied audit.
    expired = run_claim("C-007", seed=11, store_path=str(store))
    assert expired.status == "denied"
    assert expired.proposal_amount == 35000
    assert expired.refund_effects == []

    # Claim pointing to an approval issued for another claim (A-001 belongs to C-001).
    conn = connect(store)
    try:
        conn.execute(
            """
            INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
            VALUES ('C-MISMATCH', 'P-100', 'O-808', 'delay 4 days', 'CANARY_SECRET_PARENT_MISMATCH', '{}', 'A-001')
            """
        )
        conn.commit()
    finally:
        conn.close()

    mismatch = run_claim("C-MISMATCH", seed=11, store_path=str(store))
    assert mismatch.status == "denied"
    assert mismatch.proposal_amount == 35000
    assert mismatch.error_reason == "approval_claim_mismatch"
    assert mismatch.refund_effects == []
    conn = connect(store)
    try:
        assert get_refund(conn, "C-MISMATCH") is None
        audits = conn.execute(
            "SELECT event_type FROM audit_events WHERE claim_id = 'C-MISMATCH'"
        ).fetchall()
        assert any(row["event_type"] == "policy_denied" for row in audits)
    finally:
        conn.close()


def test_workflow_already_refunded_and_topup_branches(public_db):
    # C-013: order O-505 already refunded 35,000 -> denied, proposal stays full quote.
    c13 = run_claim("C-013", seed=11, store_path=str(public_db))
    assert c13.status == "denied"
    assert c13.proposal_amount == 35000
    assert c13.error_reason == "order_already_refunded"
    assert c13.refund_effects == []

    # C-014: order O-515 already refunded 30,000, damage entitlement 150,000 -> pays 120,000 delta.
    c14 = run_claim("C-014", seed=11, store_path=str(public_db))
    assert c14.status == "resolved"
    assert c14.proposal_amount == 150000
    assert len(c14.refund_effects) == 1
    assert int(c14.refund_effects[0]["amount_vnd"]) == 120000
    assert c14.committed_audit_count == 1


def test_workflow_amount_conflict_returns_failed_and_preserves_ledger(public_db):
    conn = connect(public_db)
    try:
        conn.execute(
            """
            INSERT INTO refund_ledger (claim_id, order_id, idempotency_key, amount_vnd, status)
            VALUES ('C-001', 'O-107', 'refund:C-001', 10000, 'committed')
            """
        )
        conn.commit()
    finally:
        conn.close()

    res = run_claim("C-001", seed=11, store_path=str(public_db))
    assert res.status == "failed"
    assert res.proposal_amount == 35000
    assert res.error_reason == "amount_conflict"
    conn = connect(public_db)
    try:
        effect = get_refund(conn, "C-001")
        assert effect is not None
        assert int(effect["amount_vnd"]) == 10000
        assert committed_audit_count(conn, "C-001") == 0
    finally:
        conn.close()

