from functools import lru_cache
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MILITARY_DATA_PATH = REPO_ROOT / "military_data.json"


class MilitaryDataError(RuntimeError):
    """Raised when required military data cannot be loaded."""


@lru_cache(maxsize=4)
def load_military_data(path=None):
    """Load the military pay, BAH, and ZIP/MHA reference data."""
    data_path = Path(path) if path is not None else DEFAULT_MILITARY_DATA_PATH

    if not data_path.exists():
        raise MilitaryDataError(f"Military data file not found: {data_path}")

    try:
        with data_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise MilitaryDataError(f"Military data file is not valid JSON: {data_path}") from exc

    required_sections = ("base_pay", "zip_to_mha", "bah_rates")
    missing = [section for section in required_sections if section not in data]
    if missing:
        raise MilitaryDataError(f"Military data file missing required sections: {', '.join(missing)}")

    return data
