# Dự đoán lưu lượng giao thông I-94

Dự án phân tích dữ liệu và dự đoán `traffic_volume` bằng Random Forest Regression trên bộ Metro Interstate Traffic Volume (UCI ID 492).

## Cài đặt và chạy

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_all.py
```

Pipeline tự tải/cache CSV vào `data/raw/`, audit và tổng hợp timestamp trùng, sinh EDA, huấn luyện/tối ưu mô hình, lưu artifacts và tạo `reports/final_report.docx`.

## Chạy demo

```powershell
.venv\Scripts\python app.py
```

Mở `http://127.0.0.1:5000`. API gồm `GET /health`, `GET /api/model-info`, `POST /api/predict`.

Lưu ý: dữ liệu chỉ mô tả luồng xe hướng tây trên I-94 tại trạm ATR 301 giữa Minneapolis và St. Paul, không đại diện cho toàn bộ giao thông đô thị.
