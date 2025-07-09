import hashlib
import pickle
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".cache")


def compute_hash(obj: Any) -> str:
    """Compute sha256 hash of object's string representation."""
    return hashlib.sha256(str(obj).encode()).hexdigest()


def cache_path(step_hash: str, input_hash: str) -> Path:
    dir_path = CACHE_DIR / step_hash
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / f"{input_hash}.pkl"


def load_cache(step_hash: str, input_hash: str) -> Any:
    path = cache_path(step_hash, input_hash)
    if path.exists():
        with path.open("rb") as f:
            return pickle.load(f)
    raise FileNotFoundError


def store_cache(step_hash: str, input_hash: str, data: Any) -> None:
    path = cache_path(step_hash, input_hash)
    with path.open("wb") as f:
        pickle.dump(data, f)
