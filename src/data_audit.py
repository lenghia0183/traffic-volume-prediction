import json
import numpy as np
import pandas as pd
from .config import TABLE_DIR

def audit_dataset(df: pd.DataFrame) -> dict:
    data = df.copy()
    data["holiday"] = data["holiday"].fillna("None")
    data["date_time"] = pd.to_datetime(data["date_time"], errors="coerce")
    data.head(10).to_csv(TABLE_DIR / "dataset_head.csv", index=False)
    pd.DataFrame({"column": data.columns, "dtype": data.dtypes.astype(str)}).to_csv(TABLE_DIR / "data_types.csv", index=False)
    numeric = data.select_dtypes(include=np.number).describe().T.reset_index(names="column")
    numeric.to_csv(TABLE_DIR / "data_profile.csv", index=False)
    missing = data.isna().sum().rename("missing_count").reset_index(name="missing_count").rename(columns={"index":"column"})
    missing.to_csv(TABLE_DIR / "missing_values.csv", index=False)
    groups = data.groupby("date_time", dropna=False).agg(
        row_count=("traffic_volume", "size"), traffic_volume_nunique=("traffic_volume", "nunique"),
        weather_main_nunique=("weather_main", "nunique"), weather_description_nunique=("weather_description", "nunique")
    ).reset_index()
    dup_ts = groups[groups.row_count > 1].copy()
    dup_ts.to_csv(TABLE_DIR / "timestamp_duplicates.csv", index=False)
    gaps = pd.Series(sorted(data.date_time.dropna().unique())).diff().dropna()
    gap_table = pd.DataFrame({"gap": gaps.astype(str), "hours": gaps.dt.total_seconds()/3600})
    gap_table[gap_table.hours > 1].to_csv(TABLE_DIR / "time_gaps.csv", index=False)
    category_rows = []
    for col in ["holiday", "weather_main", "weather_description"]:
        for value, count in data[col].fillna("<MISSING>").value_counts().items():
            category_rows.append({"column": col, "value": value, "count": int(count)})
    pd.DataFrame(category_rows).to_csv(TABLE_DIR / "category_summary.csv", index=False)
    exact = int(data.duplicated().sum())
    anomaly = int((data.temp < 200).sum())
    zero_temp = int((data.temp == 0).sum())
    inconsistent = int((dup_ts.traffic_volume_nunique > 1).sum())
    summary = {
        "raw_rows": int(len(data)), "columns": int(data.shape[1]), "column_names": list(data.columns),
        "date_start": data.date_time.min().isoformat(), "date_end": data.date_time.max().isoformat(),
        "missing": {k:int(v) for k,v in data.isna().sum().items()}, "exact_duplicates": exact,
        "unique_timestamps": int(data.date_time.nunique()), "duplicate_timestamp_groups": int(len(dup_ts)),
        "duplicate_timestamp_extra_rows": int(len(data)-data.date_time.nunique()),
        "inconsistent_traffic_timestamp_groups": inconsistent,
        "time_gaps_over_1h": int((gaps.dt.total_seconds()/3600 > 1).sum()),
        "max_gap_hours": float((gaps.dt.total_seconds()/3600).max()),
        "temp_min": float(data.temp.min()), "temp_max": float(data.temp.max()),
        "temp_mean": float(data.temp.mean()), "temp_median": float(data.temp.median()),
        "temp_below_200": anomaly, "temp_equal_zero": zero_temp,
        "holiday_values": sorted(map(str, data.holiday.dropna().unique())),
    }
    pd.DataFrame([{"metric":k,"value":json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v} for k,v in summary.items()]).to_csv(TABLE_DIR / "duplicate_analysis.csv", index=False)
    return summary
