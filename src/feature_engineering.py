import numpy as np
import pandas as pd

def engineer_features(df: pd.DataFrame, include_description: bool=False) -> tuple[pd.DataFrame, list[str], list[str]]:
    x=df.copy(); dt=pd.to_datetime(x.pop("date_time"))
    x["year"]=dt.dt.year; x["month"]=dt.dt.month; x["day_of_week"]=dt.dt.dayofweek; x["hour"]=dt.dt.hour
    x["is_weekend"]=(dt.dt.dayofweek>=5).astype(int); x["is_holiday"]=(x["holiday"].astype(str).str.lower()!="none").astype(int)
    x["hour_sin"]=np.sin(2*np.pi*x.hour/24); x["hour_cos"]=np.cos(2*np.pi*x.hour/24)
    x["dow_sin"]=np.sin(2*np.pi*x.day_of_week/7); x["dow_cos"]=np.cos(2*np.pi*x.day_of_week/7)
    x["month_sin"]=np.sin(2*np.pi*(x.month-1)/12); x["month_cos"]=np.cos(2*np.pi*(x.month-1)/12)
    drop=["holiday"] + ([] if include_description else ["weather_description"])
    x=x.drop(columns=drop)
    categorical=[c for c in ["weather_main","weather_description"] if c in x]
    numeric=[c for c in x.columns if c not in categorical+['traffic_volume']]
    return x, numeric, categorical

