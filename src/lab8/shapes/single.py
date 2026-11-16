"""Shape B: one bounded ReAct agent; the host remains the only refund writer."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Investigate with read tools, then let the host validate and commit the quote."""
    shape = "single"
    budget = Budget()
    trace = Trace(make_run_id(shape, claim_id, seed))
    conn = connect(store_path)
    try:
        # Read a small, explicit claim view. Do not put the ticket in the agent's
        # observation: ticket text is untrusted input and is not needed to quote.
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("claim_lookup", {"found": claim.get("found", False), "claim_id": claim_id})

        if not claim.get("found"):
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="unknown_claim",
            )
        if not claim.get("order_id"):
            trace.add("decision", {"status": "needs_info"})
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="needs_info",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="missing_order_id",
            )

        # The ReAct loop replaces its observation with the latest tool result on
        # each turn, so keep the minimal identifiers and intermediate order in
        # this closure instead of relying on the previous observation being kept.
        observation = {
            "claim": {
                "claim_id": claim_id,
                "order_id": claim["order_id"],
                "principal_id": claim["principal_id"],
            }
        }
        state: dict[str, dict] = {}

        def decide(seen: dict) -> dict:
            # Count each agent turn in the simulated budget. Prompts contain no
            # ticket, raw claim row, or order details.
            complete(
                budget,
                seed=seed,
                purpose="think",
                prompt=f"claim={claim_id}; previous_tool={seen.get('last_tool', 'start')}",
            )

            last_tool = seen.get("last_tool")
            if last_tool == "lookup_order":
                result = seen.get("last_result") or {}
                if not result.get("visible"):
                    action = {
                        "final": {
                            "status": "escalated",
                            "reason": result.get("reason", "not_found"),
                        }
                    }
                else:
                    state["order"] = result["order"]
                    action = {
                        "tool": "compute_compensation",
                        "args": {"order": state["order"]},
                    }
            elif last_tool == "compute_compensation":
                action = {"final": {"quote": seen.get("last_result") or {}}}
            elif last_tool is None:
                safe_claim = seen.get("claim") or {}
                action = {
                    "tool": "lookup_order",
                    "args": {
                        "order_id": safe_claim.get("order_id"),
                        "principal_id": safe_claim.get("principal_id"),
                    },
                }
            else:
                action = {
                    "final": {
                        "status": "failed",
                        "reason": "unexpected_tool_result",
                    }
                }

            # Record only the selected action, never its arguments or tool output.
            trace.add(
                "agent_step",
                {
                    "step": budget.model_calls,
                    "selected_tool": action.get("tool"),
                    "final": "final" in action,
                },
            )
            return action

        loop = run_react(
            conn,
            budget,
            observation=observation,
            decide=decide,
            max_steps=8,
        )
        final = loop.get("final") or {}
        trace.add(
            "react_summary",
            {
                "stopped": loop.get("stopped"),
                "model_calls": budget.model_calls,
                "tool_calls": budget.tool_calls,
            },
        )

        if loop.get("stopped") == "step_cap":
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="step_cap",
            )

        if final.get("status") == "escalated":
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="escalated",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=final.get("reason"),
            )
        if final.get("status") == "failed":
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=final.get("reason", "react_failed"),
            )

        quote = final.get("quote") or {}
        if "amount_vnd" not in quote:
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="missing_quote",
            )

        amount = int(quote["amount_vnd"])
        trace.add("quote", quote)
        if amount <= 0:
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status="denied",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=quote.get("reason"),
            )

        # Send the full entitlement quote. The host applies approval, idempotency,
        # and the per-order cap in its transaction. Let injected crashes propagate.
        try:
            outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise

        trace.add(
            "host_result",
            {"ok": outcome["ok"], "reason": outcome["reason"]},
        )
        if not outcome["ok"]:
            status = "failed" if outcome["conflict"] else "denied"
            return finish(
                conn,
                shape=shape,
                claim_id=claim_id,
                seed=seed,
                status=status,
                proposal_amount=amount,
                budget=budget,
                trace=trace,
                error_reason=outcome["reason"],
            )

        return finish(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=amount,
            budget=budget,
            trace=trace,
        )
    finally:
        conn.close()
