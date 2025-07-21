class CrystallizeError(Exception):
    """Base class for all Crystallize errors."""


class MissingMetricError(CrystallizeError):
    """Raised when a required metric is missing from the pipeline's output."""

    def __init__(self, metric: str) -> None:
        super().__init__(f"Required metric '{metric}' missing from pipeline output.")


class PipelineExecutionError(CrystallizeError):
    """Raised when a pipeline step fails unexpectedly."""

    def __init__(self, step_name: str, original_exception: Exception) -> None:
        super().__init__(f"Step '{step_name}' failed: {str(original_exception)}")
        self.original_exception = original_exception
