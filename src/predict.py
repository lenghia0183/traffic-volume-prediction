import json
from pathlib import Path
import joblib, pandas as pd
from .config import ARTIFACT_DIR

def build_model_row(payload):
    dt=pd.to_datetime(payload["date_time"]); temp=float(payload["temp_c"])+273.15
    import numpy as np
    return pd.DataFrame([{"temp":temp,"rain_1h":float(payload.get("rain_1h",0)),"snow_1h":float(payload.get("snow_1h",0)),
      "clouds_all":float(payload["clouds_all"]),"weather_main":payload["weather_main"],"year":dt.year,"month":dt.month,"day_of_week":dt.dayofweek,
      "hour":dt.hour,"is_weekend":int(dt.dayofweek>=5),"is_holiday":int(bool(payload.get("is_holiday",False))),
      "hour_sin":np.sin(2*np.pi*dt.hour/24),"hour_cos":np.cos(2*np.pi*dt.hour/24),"dow_sin":np.sin(2*np.pi*dt.dayofweek/7),"dow_cos":np.cos(2*np.pi*dt.dayofweek/7),
      "month_sin":np.sin(2*np.pi*(dt.month-1)/12),"month_cos":np.cos(2*np.pi*(dt.month-1)/12)}])

def predict(payload):
    model=joblib.load(ARTIFACT_DIR/"traffic_rf_pipeline.joblib")
    return max(0,round(float(model.predict(build_model_row(payload))[0])))

