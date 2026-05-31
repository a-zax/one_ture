from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "vector_store"
ENV_FILE = PROJECT_ROOT / ".env"

if load_dotenv:
    load_dotenv(ENV_FILE)

DEFAULT_FACTSHEET_CANDIDATES = [
    DATA_DIR / "HDFC MF Factsheet -  June 2024.pdf",
    Path(r"C:\Users\Aryan Shukla.000\Downloads\HDFC MF Factsheet -  June 2024.pdf"),
]


def get_factsheet_path() -> Path | None:
    candidates = list(DEFAULT_FACTSHEET_CANDIDATES)
    configured_path = os.getenv("FACTSHEET_PATH")
    if configured_path:
        candidates.insert(0, Path(configured_path))

    for path in candidates:
        if path.exists():
            return path
    return None
