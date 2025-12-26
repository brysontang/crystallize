from __future__ import annotations

import math
import os
import textwrap

import pytest

from crystallize.agentic.schema import Spec
from crystallize.agentic.steps import (
    bounded_synthesis,
    execute_capsule,
    generate_spec,
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


def test_demo_spec_first_bounded_synthesis_happy_path(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(
        claim={"id": "demo1", "text": "happy path claim", "acceptance": {}}
    )
    claim_payload, claim_metadata = claim_step(3, frozen_ctx)
    assert claim_metadata["claim_id"] == "demo1"

    spec_step = generate_spec(
        spec=Spec(
            allowed_imports=["math"],
            resources={"time_s": 2, "mem_mb": 64},
        )
    )
    spec_payload, spec_metadata = spec_step(claim_payload, frozen_ctx)
    assert '"allowed_imports": ["math"]' in spec_metadata["spec_json"]

    synthesis_step = bounded_synthesis(
        code=textwrap.dedent(
            """
            import math

            def fit_and_eval(data):
                return {"rmse": float(math.sqrt(data))}
            """
        )
    )
    synthesis_payload, synthesis_metadata = synthesis_step(spec_payload, frozen_ctx)
    assert "code_sha" in synthesis_metadata
    generated_code = frozen_ctx.get("generated_code")
    assert isinstance(generated_code, str) and "import math" in generated_code

    execution_step = execute_capsule()
    execution_payload, execution_metadata = execution_step(
        synthesis_payload, frozen_ctx
    )
    claim_obj, spec_obj, metrics = execution_payload
    assert claim_obj.id == "demo1"
    assert spec_obj.resources == {"time_s": 2, "mem_mb": 64}
    expected_rmse = math.sqrt(3.0)
    assert metrics["rmse"] == pytest.approx(expected_rmse, rel=1e-6)
    assert execution_metadata["rmse"] == pytest.approx(expected_rmse, rel=1e-6)
    capsule_output = frozen_ctx.get("capsule_output")
    assert capsule_output["rmse"] == pytest.approx(expected_rmse, rel=1e-6)

