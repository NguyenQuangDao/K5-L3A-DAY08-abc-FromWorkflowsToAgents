"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Execute a refund claim deterministically via fixed workflow steps."""
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("workflow_nodraft", claim_id, seed)
    trace = Trace(run_id)

    def _done(status: str, proposal_amount: int, error_reason: str | None = None) -> RunResult:
        return finish(
            conn,
            shape="workflow_nodraft",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    view = get_claim_view(conn, claim_id)
    budget.add_tool(tool_cost())
    if not view.get("found"):
        trace.add("claim", {"found": False, "claim_id": claim_id, "reason": "unknown_claim"})
        return _done("failed", 0, "unknown_claim")

    order_id = view.get("order_id")
    trace.add("claim", {"found": True, "claim_id": claim_id, "has_order_id": bool(order_id)})
    if not order_id:
        trace.add("decision", {"status": "needs_info", "reason": "missing_order_id"})
        return _done("needs_info", 0, "missing_order_id")

    ov = lookup_order(conn, order_id, view["principal_id"])
    budget.add_tool(tool_cost())
    trace.add("lookup_order", safe_dump(ov))
    if not ov.get("visible"):
        reason = ov.get("reason")
        trace.add("decision", {"status": "escalated", "reason": reason})
        return _done("escalated", 0, reason)

    q = compute_compensation(conn, ov["order"])
    budget.add_tool(tool_cost())
    trace.add("quote", safe_dump(q))
    amount = int(q["amount_vnd"])

    if amount <= 0:
        reason = q.get("reason")
        trace.add("decision", {"status": "denied", "proposal_amount": 0, "reason": reason})
        return _done("denied", 0, reason)

    try:
        outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add(
        "host",
        {
            "ok": bool(outcome.get("ok")),
            "reason": outcome.get("reason"),
            "conflict": bool(outcome.get("conflict")),
        },
    )

    if outcome.get("ok"):
        return _done("resolved", amount, None)
    if outcome.get("conflict"):
        return _done("failed", amount, outcome.get("reason"))
    return _done("denied", amount, outcome.get("reason"))
