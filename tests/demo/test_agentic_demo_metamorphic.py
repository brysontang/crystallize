from __future__ import annotations

import os
import textwrap

import pytest

from crystallize.agentic.schema import Spec
from crystallize.agentic.steps import (
    bounded_synthesis,
    execute_capsule,
    generate_spec,
    run_metamorphic_tests,
    specify_claim,
)
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext

pytestmark = [
    pytest.mark.demo,
    pytest.mark.skipif(
        os.getenv("RUN_DEMOS") != "1", reason="Demo tests are opt-in (RUN_DEMOS=1)."
    ),
]


@pytest.fixture()
def frozen_ctx() -> FrozenContext:
    return FrozenContext({CONDITION_KEY: BASELINE_CONDITION, REPLICATE_KEY: 0})


def test_demo_metamorphic_invariance(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(
        claim={"id": "demo2", "text": "sum stays stable when rows permute", "acceptance": {}}
    )
    claim_payload, _ = claim_step([1, 2, 3], frozen_ctx)

    spec_step = generate_spec(
        spec=Spec(
            allowed_imports=[],
            resources={"time_s": 2, "mem_mb": 64},
            properties=[
                {
                    "name": "perm_invariance",
                    "metamorphic": "permute_rows",
                    "metric": "total",
                }
            ],
        )
    )
    spec_payload, _ = spec_step(claim_payload, frozen_ctx)

    synthesis_step = bounded_synthesis(
        code=textwrap.dedent(
            """
            def fit_and_eval(data):
                return {"total": sum(data)}
            """
        )
    )
    synthesis_payload, _ = synthesis_step(spec_payload, frozen_ctx)

    execution_step = execute_capsule()
    execution_payload, execution_metadata = execution_step(
        synthesis_payload, frozen_ctx
    )
    metrics = execution_payload[2]
    assert metrics["total"] == 6
    assert execution_metadata["total"] == 6

    metamorphic_step = run_metamorphic_tests()
    (_, _, baseline_metrics), metamorphic_metadata = metamorphic_step(
        execution_payload, frozen_ctx
    )
    assert baseline_metrics["total"] == 6
    assert metamorphic_metadata["perm_invariance_pass"] is True

    stored = frozen_ctx.get("metamorphic_perm_invariance_result")
    assert stored["transform"] == "permute_rows"
    assert stored["passed"] is True
    assert stored["metrics"]["total"] == 6

