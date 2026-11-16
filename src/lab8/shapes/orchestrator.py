"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.

Implementation notes (team TV3)
-------------------------------
Boundary between code and model:

* The orchestrator (this code) owns every decision that moves money: routing,
  the quote (from the investigator's DB order view via `compute_compensation`),
  and the single call to the host gate `durability.issue_refund`.
* Investigators get a typed `handoff.v1` built from an allowlist. They only hold
  read tools; `make_handoff` refuses any write tool and `dispatch(worker=True)`
  refuses anything outside READONLY_TOOLS.
* MockLLM is used for two calls only: `plan` (routing note) and `draft` (reply
  text). Neither prompt contains ticket text, and neither output is read back
  into a decision.
* Ticket text is user data. It is never parsed for delay, order id or clause, and
  never written to the trace.

What the trace records (allowlist): claim presence flags, the sanitized handoff,
the investigator's allowlisted order view, refund-history totals, the quote, the
host outcome (ok / reason / conflict / committed amount) and the final decision.
What it never records: ticket text, claim row, raw order row, parent_secret,
raw_headers, phone, address, item name, internal note, exception messages.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "orchestrator"

# Read-only tools handed to the investigator. Deliberately NOT get_claim_view:
# its result carries the ticket text, which must not travel into the trace.
INVESTIGATOR_TOOLS = ["lookup_order", "lookup_refund_history", "compute_compensation"]
INVESTIGATOR_TASK = "quote_from_order_row"

# Allowlisted keys copied from tool payloads into the trace.
_HISTORY_KEYS = ("visible", "reason", "refund_count", "refunded_vnd")
_QUOTE_KEYS = ("amount_vnd", "reason", "clause_ids", "parts")


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal), "error_reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    try:
        return _orchestrate(conn, claim_id, seed=seed, crash_at=crash_at, budget=budget, trace=trace, done=done)
    except InjectedCrash:
        # Fault-lab crash: flush the trace so the run is auditable, then let it propagate (T12).
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    except Exception as exc:  # noqa: BLE001 — run_claim must not raise; message may hold data, log type only
        return done("failed", 0, f"internal_error:{type(exc).__name__}")


def _orchestrate(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
    budget: Budget,
    trace: Trace,
    done,
) -> RunResult:
    # 1. Orchestrator reads the claim through the allowlisted view (no parent_secret, no headers).
    view = get_claim_view(conn, claim_id)
    budget.add_tool(tool_cost())
    trace.add("claim", {"found": bool(view.get("found")), "has_order_id": bool(view.get("order_id"))})
    if not view.get("found"):
        return done("failed", 0, "unknown_claim")

    if not view.get("order_id"):
        # Do not mine an order id from the ticket. Ask the customer instead.
        complete(budget, seed=seed, purpose="draft", prompt="status=needs_info")
        return done("needs_info", 0, "missing_order_id")

    # 2. Typed, allowlisted handoff. facts stay empty: the orchestrator has no verified
    #    order facts yet, and ticket claims are not facts.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task=INVESTIGATOR_TASK,
        facts={},
        allowed_tools=list(INVESTIGATOR_TOOLS),
    )
    # Sorted so the trace is byte-identical across runs (ALLOWED_FIELDS is a set).
    trace.add("handoff", safe_dump(dict(sorted(handoff.items()))))
    complete(budget, seed=seed, purpose="plan", prompt=f"task={INVESTIGATOR_TASK};tools={','.join(INVESTIGATOR_TOOLS)}")

    # 3. Read-only investigators. principal_id scopes order visibility.
    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=view["principal_id"])
    tools: dict[str, Any] = investigated.get("tools") or {}
    order_view = tools.get("lookup_order") or {}
    history = tools.get("lookup_refund_history") or {}
    trace.add(
        "investigator",
        {
            "lookup_order": safe_dump(order_view),  # allowlisted by lab8.tools.ORDER_FIELDS
            "refund_history": {key: history[key] for key in _HISTORY_KEYS if key in history},
        },
    )

    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="status=escalated")
        return done("escalated", 0, order_view.get("reason") or "order_not_visible")

    # 4. Quote comes from code (compute_compensation over the DB order row), never from the model.
    quote_payload = tools.get("compute_compensation")
    if not isinstance(quote_payload, dict) or "amount_vnd" not in quote_payload:
        return done("failed", 0, "missing_quote")
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", {key: quote_payload[key] for key in _QUOTE_KEYS if key in quote_payload})

    if proposal <= 0:
        # Nothing to pay: no host call, so no policy_denied audit is expected.
        complete(budget, seed=seed, purpose="draft", prompt="status=denied")
        return done("denied", 0, quote_payload.get("reason") or "no_entitlement")

    # 5. Single writer: the host gate checks approval, per-order cap and idempotency.
    #    Pass the FULL quote; the host subtracts what earlier claims already received.
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    effect = outcome.get("effect") or {}
    trace.add(
        "host",
        {
            "ok": bool(outcome.get("ok")),
            "reason": outcome.get("reason"),
            "conflict": bool(outcome.get("conflict")),
            "committed_vnd": effect.get("amount_vnd"),
        },
    )

    if outcome.get("ok"):
        status, reason = "resolved", None
    elif outcome.get("conflict"):
        status, reason = "failed", outcome.get("reason")
    else:
        status, reason = "denied", outcome.get("reason")
    complete(budget, seed=seed, purpose="draft", prompt=f"status={status}")
    # proposal_amount is the full quote even when the host capped or denied it.
    return done(status, proposal, reason)
