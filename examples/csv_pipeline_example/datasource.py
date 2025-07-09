import csv
import random
from pathlib import Path
from typing import List

from crystallize.core.datasource import DataSource
from crystallize.core.context import FrozenContext


class CSVDataSource(DataSource):
    def __init__(self, default_path: str, ctx_key: str = "csv_path") -> None:
        self.default_path = Path(default_path)
        self.ctx_key = ctx_key

    def fetch(self, ctx: FrozenContext) -> List[List[float]]:
        path = Path(ctx.as_dict().get(self.ctx_key, self.default_path))
        with path.open() as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
            sampled_rows = random.sample(all_rows, min(4, len(all_rows)))

            data = [
                [
                    float(row[field]) + random.uniform(-0.05, 0.05)  # add slight noise
                    for field in reader.fieldnames
                ]
                for row in sampled_rows
            ]
        return data


def set_csv_path(ctx: FrozenContext, path: str, ctx_key: str = "csv_path") -> None:
    """Helper to update the CSV path in a context."""
    ctx[ctx_key] = path
