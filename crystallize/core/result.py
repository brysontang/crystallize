from typing import Dict, Any, Optional

class Result:
    def __init__(
        self, 
        metrics: Dict[str, Any], 
        artifacts: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Exception]] = None,
        provenance: Optional[Dict[str, Any]] = None
    ):
        self.metrics = metrics
        self.artifacts = artifacts or {}
        self.errors = errors or {}
        self.provenance = provenance or {}

    def get_metrics(self, key: str) -> Any:
        return self.metrics.get(key)

    def get_artifact(self, name: str) -> Any:
        return self.artifacts.get(name)
