from crystallize.utils.exceptions import MissingMetricError, PipelineExecutionError


def test_missing_metric_error_message():
    err = MissingMetricError("acc")
    assert "acc" in str(err)


def test_pipeline_execution_error_message():
    original = ValueError("boom")
    err = PipelineExecutionError("MyStep", original)
    assert "MyStep" in str(err)
    assert "boom" in str(err)
    assert err.original_exception is original
