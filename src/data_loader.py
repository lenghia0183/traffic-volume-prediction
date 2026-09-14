from pathlib import Path
import pandas as pd
from .config import RAW_DIR, ensure_dirs

EXPECTED = ["holiday", "temp", "rain_1h", "snow_1h", "clouds_all", "weather_main", "weather_description", "date_time", "traffic_volume"]

def load_dataset() -> tuple[pd.DataFrame, Path]:
    ensure_dirs()
    candidates = list(RAW_DIR.glob("*.csv"))
    for path in candidates:
        df = pd.read_csv(path)
        if set(EXPECTED).issubset(df.columns):
            return df[EXPECTED].copy(), path
    try:
        from ucimlrepo import fetch_ucirepo
        ds = fetch_ucirepo(id=492)
        df = pd.concat([ds.data.features, ds.data.targets], axis=1)
        df = df.loc[:, ~df.columns.duplicated()]
        if not set(EXPECTED).issubset(df.columns):
            raise ValueError(f"UCI response missing columns: {set(EXPECTED)-set(df.columns)}")
        path = RAW_DIR / "Metro_Interstate_Traffic_Volume.csv"
        df[EXPECTED].to_csv(path, index=False)
        return df[EXPECTED].copy(), path
    except Exception as first_error:
        import io, zipfile, requests
        url = "https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            csv_name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
            df = pd.read_csv(archive.open(csv_name))
        path = RAW_DIR / "Metro_Interstate_Traffic_Volume.csv"
        df[EXPECTED].to_csv(path, index=False)
        return df[EXPECTED].copy(), path

