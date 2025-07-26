from crystallize import verifier


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True}
