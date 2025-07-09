from typing import Any
from crystallize.core.datasource import DataSource
from crystallize.core.context import FrozenContext

class SimpleDataSource(DataSource):
    def __init__(self, data: Any):
        self.data = data

    def fetch(self, ctx: FrozenContext) -> Any:
        return self.data
