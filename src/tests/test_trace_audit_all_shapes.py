"""TV3 trace audit across the three team shapes.

Stricter than the label's forbid_substrings: every sensitive value present anywhere in
the public world (phone, address, internal note, item name of EVERY order, every
parent_secret and header, every ticket text) must be absent from the trace and from the
RunResult of every public claim. Shapes still returning not_implemented are skipped so
the host gate stays green while a teammate's shape is in progress.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import init_store
from lab8.metrics import check_trace, trace_files
from lab8.shapes import SHAPES
from tests.conftest import CLAIMS, WORLD

TEAM_SHAPES = ["workflow", "single", "orchestrator"]
SEEDS = [11, 55]  # 55 is the seed where the reference swarm trusts ticket text


def _sensitive_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for order in WORLD["orders"]:
        for key in ("phone", "address", "internal_note", "item_name"):
            if order.get(key):
                values[str(order[key])] = f"order.{key}"
    for claim in CLAIMS:
        values[claim["parent_secret"]] = "claim.parent_secret"
        values[claim["ticket"]] = "claim.ticket"
        for header in claim["raw_headers"].values():
            values[str(header)] = "claim.raw_headers"
    for marker in ("CANARY_", "Bearer ", "parent_secret", "raw_headers"):
        values[marker] = "marker"
    return values


SENSITIVE = _sensitive_values()


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("shape", TEAM_SHAPES)
def test_no_world_sensitive_value_reaches_trace_or_result(tmp_path, shape, seed):
    store = tmp_path / f"{shape}-{seed}.sqlite"
    init_store(store, WORLD, CLAIMS).close()
    scanned = 0
    for claim in CLAIMS:
        result = SHAPES[shape](claim["claim_id"], seed=seed, store_path=str(store))
        if result.error_reason == "not_implemented":
            pytest.skip(f"{shape} not implemented yet")
        payload = result.as_dict()
        ok, reason = check_trace(payload)
        assert ok, f"{claim['claim_id']}: {reason}"
        files = trace_files(payload)
        blob = json.dumps(payload, ensure_ascii=False) + "".join(Path(p).read_text(encoding="utf-8") for p in files)
        leaked = sorted({kind for value, kind in SENSITIVE.items() if value in blob})
        assert not leaked, f"{shape} {claim['claim_id']} seed {seed} leaked {leaked}"
        scanned += 1
    assert scanned == len(CLAIMS)
