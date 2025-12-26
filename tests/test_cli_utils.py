from cli.utils import generate_xml_summary
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    ExperimentMetrics,
    HypothesisResult,
    TreatmentMetrics,
)


def test_generate_xml_summary_escapes_quotes_and_apostrophes() -> None:
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({'score"dev\'': [1]}),
        treatments={
            'treat"name\'': TreatmentMetrics({'score"dev\'': [2]}),
        },
        hypotheses=[
            HypothesisResult(
                name='hyp"one\'',
                results={'treat"name\'': {"p_value": '0.1"'}},
                ranking={"best": 'treat"name\''},
            )
        ],
    )
    artifacts = {'artifact"name\'': {'treat"name\'': 'path"file\''}}
    xml = generate_xml_summary(Result(metrics=metrics, artifacts=artifacts))
    assert '<Metric name="score&quot;dev&apos;">' in xml
    assert 'condition="treat&quot;name&apos;"' in xml
    assert '<Hypothesis name="hyp&quot;one&apos;">' in xml
    assert "&quot;" in xml and "&apos;" in xml
    assert "<Path" in xml and "&quot;" in xml
