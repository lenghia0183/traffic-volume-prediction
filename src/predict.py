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
      "is_rush_hour":int(dt.hour in [6,7,8,9,15,16,17,18]),"day_of_year":dt.dayofyear,
      "hour_sin":np.sin(2*np.pi*dt.hour/24),"hour_cos":np.cos(2*np.pi*dt.hour/24),"dow_sin":np.sin(2*np.pi*dt.dayofweek/7),"dow_cos":np.cos(2*np.pi*dt.dayofweek/7),
      "month_sin":np.sin(2*np.pi*(dt.month-1)/12),"month_cos":np.cos(2*np.pi*(dt.month-1)/12)}])

def predict(payload):
    model=joblib.load(ARTIFACT_DIR/"traffic_rf_pipeline.joblib")
    return max(0,round(float(model.predict(build_model_row(payload))[0])))

def validate_payload(payload):
    schema=json.loads((ARTIFACT_DIR/"input_schema.json").read_text(encoding="utf-8"))
    constraints=schema["constraints"]
    labels={"temp_c":"Nhiệt độ","rain_1h":"Lượng mưa 1 giờ","snow_1h":"Lượng tuyết 1 giờ","clouds_all":"Mây che phủ"}
    for name,rule in constraints.items():
        value=float(payload.get(name,0))
        if not rule["min"] <= value <= rule["max"]:
            raise ValueError(f'{labels[name]} phải nằm trong khoảng {rule["min"]:g}–{rule["max"]:g}. Giá trị {value:g} nằm ngoài miền dữ liệu mô hình.')
    rain=float(payload.get("rain_1h",0)); snow=float(payload.get("snow_1h",0)); weather=str(payload.get("weather_main","")).lower()
    if rain>0 and weather=="clear":
        raise ValueError("Dữ liệu không nhất quán: có mưa nhưng điều kiện thời tiết là Clear. Hãy chọn Rain/Drizzle/Thunderstorm hoặc đặt lượng mưa bằng 0.")
    if snow>0 and weather=="clear":
        raise ValueError("Dữ liệu không nhất quán: có tuyết nhưng điều kiện thời tiết là Clear.")
