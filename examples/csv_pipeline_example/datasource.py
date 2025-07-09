import csv
from pathlib import Path
from typing import List

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource


class CSVDataSource(DataSource):
    """Simple CSV reader returning numerical rows."""

    def __init__(self, default_path: str, ctx_key: str = "csv_path") -> None:
        self.default_path = Path(default_path)
        self.ctx_key = ctx_key

    def fetch(self, ctx: FrozenContext) -> List[List[float]]:
        path = Path(ctx.as_dict().get(self.ctx_key, self.default_path))
        with path.open() as f:
            reader = csv.DictReader(f)
            data = [
                [float(row[field]) for field in reader.fieldnames]  # type: ignore[arg-type]
                for row in reader
            ]
        return data
