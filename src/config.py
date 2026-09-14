from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACT_DIR = ROOT / "artifacts"
REPORT_DIR = ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
TABLE_DIR = REPORT_DIR / "tables"
DEMO_FIGURE_DIR = FIGURE_DIR / "demo"
RANDOM_STATE = 42
TEST_FRACTION = 0.20
TARGET = "traffic_volume"

def ensure_dirs():
    for path in [RAW_DIR, PROCESSED_DIR, ARTIFACT_DIR, FIGURE_DIR, TABLE_DIR, DEMO_FIGURE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

