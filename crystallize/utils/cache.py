import hashlib
import os
import pickle
from pathlib import Path
from typing import Any

try:
    import fcntl
except Exception:  # pragma: no cover - non-posix fallback
    fcntl = None

CACHE_DIR = Path(os.getenv("CRYSTALLIZE_CACHE_DIR", ".cache"))


def compute_hash(obj: Any) -> str:
    """Compute sha256 hash of object's pickle representation."""

    return hashlib.sha256(pickle.dumps(obj)).hexdigest()


def cache_path(step_hash: str, input_hash: str) -> Path:
    dir_path = CACHE_DIR / step_hash
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / f"{input_hash}.pkl"


def load_cache(step_hash: str, input_hash: str) -> Any:
    path = cache_path(step_hash, input_hash)
    if not path.exists():
        raise FileNotFoundError
    try:
        with path.open("rb") as f:
            return pickle.load(f)
    except Exception as exc:  # pragma: no cover - corrupted cache
        raise IOError(f"Failed to load cache from {path}") from exc


def store_cache(step_hash: str, input_hash: str, data: Any) -> None:
    path = cache_path(step_hash, input_hash)
    lock_path = path.with_suffix(path.suffix + ".lock")
    try:
        if fcntl is not None:
            with lock_path.open("w") as lock_f:
                fcntl.flock(lock_f, fcntl.LOCK_EX)
                if not path.exists():
                    with path.open("wb") as f:
                        pickle.dump(data, f)
        else:
            if not path.exists():
                with path.open("wb") as f:
                    pickle.dump(data, f)
    except Exception as exc:  # pragma: no cover - disk issues
        raise IOError(f"Failed to store cache at {path}") from exc
