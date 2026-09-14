import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .config import FIGURE_DIR, TABLE_DIR, RANDOM_STATE

def calc(y,p): return {"mae":float(mean_absolute_error(y,p)),"rmse":float(mean_squared_error(y,p)**0.5),"r2":float(r2_score(y,p))}
def _save(name): plt.tight_layout(); plt.savefig(FIGURE_DIR/name,dpi=180,bbox_inches="tight"); plt.close()

def evaluate_final(model,Xtr,Xte,ytr,yte,timestamps):
    ptr=model.predict(Xtr); pte=model.predict(Xte); train=calc(ytr,ptr); test=calc(yte,pte)
    err=pd.DataFrame({"date_time":timestamps.iloc[len(Xtr):].values,"actual":yte.values,"predicted":pte})
    err["residual"]=err.actual-err.predicted; err["absolute_error"]=err.residual.abs(); err["hour"]=pd.to_datetime(err.date_time).dt.hour
    err.to_csv(TABLE_DIR/"test_predictions.csv",index=False)
    plt.figure(figsize=(6,5)); sns.scatterplot(data=err,x="actual",y="predicted",alpha=.25,s=14); lim=[0,max(err.actual.max(),err.predicted.max())]; plt.plot(lim,lim,"r--"); plt.title("Giá trị thực tế và dự đoán"); _save("09_actual_vs_predicted.png")
    plt.figure(figsize=(8,4)); sns.histplot(err.residual,bins=45,kde=True,color="#7c3aed"); plt.axvline(0,color="black",ls="--"); plt.title("Phân phối phần dư"); _save("10_residual_distribution.png")
    tail=err.tail(500); plt.figure(figsize=(10,4)); plt.plot(tail.date_time,tail.actual,label="Thực tế",lw=1); plt.plot(tail.date_time,tail.predicted,label="Dự đoán",lw=1); plt.legend(); plt.title("Dự đoán theo thời gian - 500 quan sát cuối"); _save("11_prediction_timeseries.png")
    by_hour=err.groupby("hour").absolute_error.mean(); by_hour.to_csv(TABLE_DIR/"mae_by_hour.csv"); plt.figure(figsize=(8,4)); by_hour.plot(kind="bar",color="#dc2626"); plt.title("MAE theo giờ"); _save("12_mae_by_hour.png")
    weather=Xte["weather_main"].reset_index(drop=True); by_weather=pd.DataFrame({"weather_main":weather,"ae":err.absolute_error}).groupby("weather_main").agg(mae=("ae","mean"),count=("ae","size")).sort_values("mae",ascending=False)
    by_weather.to_csv(TABLE_DIR/"mae_by_weather.csv"); plt.figure(figsize=(8,5)); sns.barplot(data=by_weather.reset_index(),y="weather_main",x="mae",color="#f59e0b"); plt.title("MAE theo nhóm thời tiết"); _save("13_mae_by_weather.png")
    sample_n=min(2500,len(Xte)); ix=np.linspace(0,len(Xte)-1,sample_n,dtype=int)
    perm=permutation_importance(model,Xte.iloc[ix],yte.iloc[ix],n_repeats=3,random_state=RANDOM_STATE,scoring="neg_mean_absolute_error",n_jobs=-1)
    perm_df=pd.DataFrame({"feature":Xte.columns,"importance":perm.importances_mean,"std":perm.importances_std}).sort_values("importance",ascending=False)
    perm_df.to_csv(TABLE_DIR/"permutation_importance.csv",index=False)
    top=perm_df.head(10).sort_values("importance"); plt.figure(figsize=(8,5)); plt.barh(top.feature,top.importance,color="#0f766e"); plt.title("Permutation Importance - Top 10"); _save("14_permutation_importance.png")
    transformed=model.named_steps["preprocessor"].get_feature_names_out(); raw_imp=model.named_steps["model"].feature_importances_
    fi=pd.DataFrame({"feature":transformed,"importance":raw_imp}).sort_values("importance",ascending=False); fi.to_csv(TABLE_DIR/"random_forest_feature_importance.csv",index=False)
    top2=fi.head(15).sort_values("importance"); plt.figure(figsize=(8,6)); plt.barh(top2.feature.str.replace("num__","",regex=False).str.replace("cat__","",regex=False),top2.importance,color="#2563eb"); plt.title("Random Forest Feature Importance - Top 15"); _save("15_rf_feature_importance.png")
    error_summary={"mean_residual":float(err.residual.mean()),"median_absolute_error":float(err.absolute_error.median()),"worst_mae_hour":int(by_hour.idxmax()),"worst_mae_hour_value":float(by_hour.max()),"worst_mae_weather":str(by_weather.index[0]),"worst_mae_weather_value":float(by_weather.mae.iloc[0])}
    return train,test,fi.head(10).to_dict("records"),perm_df.head(10).to_dict("records"),error_summary

