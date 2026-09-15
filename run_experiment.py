import json, platform, sys
from pathlib import Path
import joblib
import pandas as pd
import sklearn
from src.config import ensure_dirs, ARTIFACT_DIR, PROCESSED_DIR, FIGURE_DIR, TABLE_DIR
from src.data_loader import load_dataset
from src.data_audit import audit_dataset
from src.preprocessing import aggregate_duplicate_timestamps
from src.feature_engineering import engineer_features
from src.eda import create_eda
from src.train import train_baselines
from src.tuning import tune_random_forest
from src.evaluation import evaluate_final

def clean_params(d): return {k.replace("model__",""):v for k,v in d.items()}

def main():
    ensure_dirs(); raw,path=load_dataset(); audit=audit_dataset(raw)
    clean,clean_stats=aggregate_duplicate_timestamps(raw); clean.to_csv(PROCESSED_DIR/"traffic_clean.csv",index=False)
    eda=create_eda(clean)
    X,numeric,categorical=engineer_features(clean,include_description=False); y=X.pop("traffic_volume")
    split,baselines,fitted=train_baselines(X,y,numeric,categorical); Xtr,Xte,ytr,yte=split
    search,space=tune_random_forest(Xtr,ytr,numeric,categorical)
    final=search.best_estimator_; train_metrics,test_metrics,fi,perm,error=evaluate_final(final,Xtr,Xte,ytr,yte,clean.date_time)
    joblib.dump(final,ARTIFACT_DIR/"traffic_rf_pipeline.joblib")
    model_check=joblib.load(ARTIFACT_DIR/"traffic_rf_pipeline.joblib"); sample_prediction=float(model_check.predict(Xte.iloc[[0]])[0])
    comparison=[]
    for name,r in baselines.items():
        comparison.append({"model":name,"train_mae":r["train"]["mae"],"test_mae":r["test"]["mae"],"train_rmse":r["train"]["rmse"],"test_rmse":r["test"]["rmse"],"train_r2":r["train"]["r2"],"test_r2":r["test"]["r2"]})
    comparison.append({"model":"Random Forest Tuned","train_mae":train_metrics["mae"],"test_mae":test_metrics["mae"],"train_rmse":train_metrics["rmse"],"test_rmse":test_metrics["rmse"],"train_r2":train_metrics["r2"],"test_r2":test_metrics["r2"]})
    pd.DataFrame(comparison).to_csv(TABLE_DIR/"model_comparison.csv",index=False)
    report={"dataset":{**audit,"source_file":str(path),"processed_rows":int(len(clean))},"quality":{**clean_stats},
      "split":{"train_rows":len(Xtr),"test_rows":len(Xte),"train_start":str(clean.date_time.iloc[0]),"train_end":str(clean.date_time.iloc[len(Xtr)-1]),"test_start":str(clean.date_time.iloc[len(Xtr)]),"test_end":str(clean.date_time.iloc[-1])},
      "features":{"numeric":numeric,"categorical":categorical,"all":list(X.columns)},"models":{"comparison":comparison},
      "tuning":{"search_space":space,"best_parameters":clean_params(search.best_params_),"best_cv_mae":float(-search.best_score_),"cv":"TimeSeriesSplit(n_splits=5)","candidates":24},
      "final_model":{"train":train_metrics,"test":test_metrics,"model_path":"artifacts/traffic_rf_pipeline.joblib","reload_prediction":sample_prediction},
      "feature_importance":fi,"permutation_importance":perm,"error_analysis":error,"eda":eda,
      "environment":{"python":platform.python_version(),"pandas":pd.__version__,"scikit_learn":sklearn.__version__,"platform":platform.platform()},
      "figures":sorted(str(p.relative_to(Path.cwd())) for p in FIGURE_DIR.glob("*.png")),"tables":sorted(str(p.relative_to(Path.cwd())) for p in TABLE_DIR.glob("*"))}
    schema={"features":report["features"],"constraints":{"temp_c":{"min":-50.0,"max":50.0},"rain_1h":{"min":0.0,"max":float(clean.rain_1h.max())},"snow_1h":{"min":0.0,"max":float(clean.snow_1h.max())},"clouds_all":{"min":0.0,"max":100.0}},"date_range":{"min":str(clean.date_time.min()),"max":str(clean.date_time.max())}}
    for name,obj in [("metrics.json",report["final_model"]),("best_params.json",report["tuning"]),("experiment_results.json",report["models"]),("input_schema.json",schema),("category_values.json",{"weather_main":sorted(clean.weather_main.unique().tolist())})]:
        (ARTIFACT_DIR/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    (ARTIFACT_DIR/"report_data.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(json.dumps({"raw_rows":len(raw),"processed_rows":len(clean),"test_metrics":test_metrics,"best_params":clean_params(search.best_params_)},ensure_ascii=False,indent=2))
    return report

if __name__=="__main__": main()
