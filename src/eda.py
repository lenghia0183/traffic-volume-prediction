import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from .config import FIGURE_DIR, TABLE_DIR

def _save(name):
    plt.tight_layout(); plt.savefig(FIGURE_DIR/name, dpi=180, bbox_inches="tight"); plt.close()

def create_eda(df: pd.DataFrame) -> dict:
    sns.set_theme(style="whitegrid"); x=df.copy(); x["date_time"]=pd.to_datetime(x.date_time)
    x["hour"]=x.date_time.dt.hour; x["dow"]=x.date_time.dt.day_name(); x["month"]=x.date_time.dt.month
    plt.figure(figsize=(8,4)); sns.histplot(x.traffic_volume,bins=40,kde=True,color="#2563eb"); plt.title("Phân phối lưu lượng giao thông"); plt.xlabel("Phương tiện/giờ"); _save("01_traffic_distribution.png")
    hourly=x.groupby("hour").traffic_volume.mean(); plt.figure(figsize=(8,4)); hourly.plot(marker="o",color="#2563eb"); plt.title("Lưu lượng trung bình theo giờ"); plt.ylabel("Phương tiện/giờ"); _save("02_hourly_pattern.png")
    order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    daily=x.groupby("dow").traffic_volume.mean().reindex(order); plt.figure(figsize=(8,4)); daily.plot(kind="bar",color="#0f766e"); plt.title("Lưu lượng trung bình theo thứ"); plt.ylabel("Phương tiện/giờ"); _save("03_weekday_pattern.png")
    monthly=x.groupby("month").traffic_volume.mean(); plt.figure(figsize=(8,4)); monthly.plot(marker="o",color="#7c3aed"); plt.title("Lưu lượng trung bình theo tháng"); plt.ylabel("Phương tiện/giờ"); _save("04_monthly_pattern.png")
    weather=x.groupby("weather_main").traffic_volume.agg(["mean","count"]).sort_values("mean"); weather.to_csv(TABLE_DIR/"traffic_by_weather.csv")
    plt.figure(figsize=(8,5)); sns.barplot(data=weather.reset_index(),y="weather_main",x="mean",color="#f59e0b"); plt.title("Lưu lượng trung bình theo thời tiết"); _save("05_weather_pattern.png")
    plt.figure(figsize=(8,4)); sns.scatterplot(data=x.sample(min(6000,len(x)),random_state=42),x="temp",y="traffic_volume",alpha=.25,s=12); plt.title("Nhiệt độ và lưu lượng"); _save("06_temp_vs_traffic.png")
    pivot=x.pivot_table(index=x.date_time.dt.dayofweek,columns="hour",values="traffic_volume",aggfunc="mean")
    plt.figure(figsize=(10,4)); sns.heatmap(pivot,cmap="YlGnBu"); plt.title("Heatmap lưu lượng theo thứ và giờ"); plt.ylabel("Thứ (0=Thứ Hai)"); _save("07_hour_week_heatmap.png")
    plt.figure(figsize=(9,4)); x.set_index("date_time").traffic_volume.resample("30D").mean().plot(color="#dc2626"); plt.title("Xu hướng lưu lượng trung bình 30 ngày"); plt.ylabel("Phương tiện/giờ"); _save("08_time_trend.png")
    findings={"mean_traffic":float(x.traffic_volume.mean()),"median_traffic":float(x.traffic_volume.median()),
              "peak_mean_hour":int(hourly.idxmax()),"peak_mean_hour_value":float(hourly.max()),
              "lowest_mean_hour":int(hourly.idxmin()),"highest_mean_weather":str(weather['mean'].idxmax())}
    (TABLE_DIR/"eda_findings.json").write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding="utf-8")
    return findings

