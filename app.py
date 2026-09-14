from flask import Flask, jsonify, render_template, request
from src.predict import predict
from src.config import ARTIFACT_DIR
import json

app=Flask(__name__)
@app.get("/")
def home():
    cats=json.loads((ARTIFACT_DIR/"category_values.json").read_text(encoding="utf-8"))
    return render_template("index.html",weather_values=cats["weather_main"])
@app.post("/api/predict")
def api_predict():
    try:
        payload=request.get_json(force=True)
        required=["date_time","temp_c","clouds_all","weather_main"]
        missing=[x for x in required if x not in payload]
        if missing: return jsonify({"error":"Thiếu trường: "+", ".join(missing)}),400
        return jsonify({"prediction":predict(payload),"unit":"vehicles/hour"})
    except Exception as exc: return jsonify({"error":str(exc)}),400
@app.get("/api/model-info")
def model_info():
    data=json.loads((ARTIFACT_DIR/"report_data.json").read_text(encoding="utf-8"))
    return jsonify({"algorithm":"RandomForestRegressor","metrics":data["final_model"]["test"],"date_range":[data["dataset"]["date_start"],data["dataset"]["date_end"]]})
@app.get("/health")
def health(): return jsonify({"status":"ok","model_exists":(ARTIFACT_DIR/"traffic_rf_pipeline.joblib").exists()})
if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)

