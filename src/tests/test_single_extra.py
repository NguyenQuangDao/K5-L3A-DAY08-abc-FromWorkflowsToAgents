"""Focused tests for the single-agent shape owned by TV2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.runtime import ToolRejected, dispatch
from lab8.schemas import Budget, make_run_id
from lab8.shapes.single import run_claim


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_single_uses_order_data_when_ticket_overstates_delay(public_db, seed):
    """C-002's ticket says five days, but the authoritative order says two."""
    result = run_claim("C-002", seed=seed, store_path=str(public_db))

    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


def test_single_counts_react_calls_and_writes_bounded_safe_trace(public_db):
    result = run_claim("C-001", seed=11, store_path=str(public_db))

    trace_path = Path(result.trace_path)
    assert trace_path.is_file()
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id == make_run_id("single", "C-001", 11)
    assert isinstance(trace["events"], list)
    assert trace["steps"] == len(trace["events"])
    assert len(trace["events"]) <= 8
    assert 1 <= result.model_calls <= 8

    # Trace the process, not the user supplied ticket or private claim context.
    serialized = json.dumps(trace, ensure_ascii=False)
    assert "CANARY_SECRET_" not in serialized
    assert "parent_secret" not in serialized
    assert "raw_headers" not in serialized


def test_single_agent_cannot_dispatch_refund_write(public_db):
    conn = connect(public_db)
    try:
        with pytest.raises(ToolRejected):
            dispatch(
                conn,
                Budget(),
                "issue_refund",
                {"claim_id": "C-001", "proposed_vnd": 35_000},
                worker=False,
            )
    finally:
        conn.close()


def test_single_unknown_claim_returns_failed_with_trace(public_db):
    result = run_claim("C-999", seed=11, store_path=str(public_db))

    assert result.status == "failed"
    assert result.proposal_amount == 0
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert trace["events"]
