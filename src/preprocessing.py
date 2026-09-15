import numpy as np
import pandas as pd

def aggregate_duplicate_timestamps(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    x = df.copy()
    x["date_time"] = pd.to_datetime(x["date_time"], errors="coerce")
    x = x.dropna(subset=["date_time", "traffic_volume"])
    x = x.drop_duplicates()
    # Holiday labels occur sparsely; propagate true holidays to all observations on that calendar date.
    none_tokens = {"None", "none", "NaN", "nan", ""}
    x["date_only"] = x.date_time.dt.date
    holiday_dates = set(x.loc[~x.holiday.fillna("None").astype(str).isin(none_tokens), "date_only"])
    holiday_name_by_date = x.loc[x.date_only.isin(holiday_dates) & ~x.holiday.fillna("None").astype(str).isin(none_tokens)].groupby("date_only").holiday.first()
    x["holiday_normalized"] = x.date_only.map(holiday_name_by_date).fillna("None")
    def mode_first(s):
        m=s.dropna().mode(); return m.iloc[0] if len(m) else "Unknown"
    rows=[]; inconsistent=0
    for ts,g in x.groupby("date_time", sort=True):
        if g.traffic_volume.nunique()>1: inconsistent += 1
        rows.append({"date_time":ts, "holiday":mode_first(g.holiday_normalized), "temp":g.temp.median(),
                     "rain_1h":g.rain_1h.max(), "snow_1h":g.snow_1h.max(), "clouds_all":g.clouds_all.mean(),
                     "weather_main":mode_first(g.weather_main), "weather_description":mode_first(g.weather_description),
                     "traffic_volume":g.traffic_volume.median()})
    out=pd.DataFrame(rows).sort_values("date_time").reset_index(drop=True)
    # Zero Kelvin is physically invalid. Replace only these audited values using time-aware interpolation.
    zero_count=int((out.temp==0).sum())
    out.loc[out.temp==0,"temp"]=np.nan
    out["temp"]=out.temp.interpolate(limit_direction="both")
    # The source contains one impossible sensor/data-entry value (9831.3 mm/h).
    # Preserve credible extreme rain and replace only values above 100 mm/h.
    invalid_rain=int((out.rain_1h>100).sum())
    out.loc[out.rain_1h>100,"rain_1h"]=np.nan
    out["rain_1h"]=out.rain_1h.interpolate(method="linear",limit_direction="both").clip(lower=0)
    stats={"rows_after_exact_dedup":int(len(x)),"rows_after_timestamp_aggregation":int(len(out)),
           "inconsistent_groups_seen":inconsistent,"zero_temp_replaced":zero_count,
           "invalid_rain_replaced":invalid_rain,"rain_validity_threshold_mm":100.0}
    return out, stats
