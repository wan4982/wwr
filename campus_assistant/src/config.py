from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "campus_data.csv"
VECTOR_DIR = BASE_DIR / "vector_db"

SCHOOL_TERM_START = "2026-02-24"
DEFAULT_TOP_K = 3
