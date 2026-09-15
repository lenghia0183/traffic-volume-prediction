import json, re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from .config import ARTIFACT_DIR, REPORT_DIR, FIGURE_DIR, TABLE_DIR

BLUE="1F4E79"; LIGHT="D9EAF7"; GRAY="F2F2F2"; INK="111827"

def font(run,size=13,bold=False,italic=False,color=INK):
    run.font.name="Times New Roman"; run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"Times New Roman")
    run.font.size=Pt(size); run.bold=bold; run.italic=italic; run.font.color.rgb=RGBColor.from_string(color)

def set_cell_shading(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=tcPr.find(qn("w:shd")) or OxmlElement("w:shd"); shd.set(qn("w:fill"),fill); tcPr.append(shd)

def set_cell_width(cell,dxa):
    tcPr=cell._tc.get_or_add_tcPr(); tcW=tcPr.find(qn("w:tcW")) or OxmlElement("w:tcW"); tcW.set(qn("w:w"),str(dxa)); tcW.set(qn("w:type"),"dxa"); tcPr.append(tcW)

def add_page_number(paragraph):
    paragraph.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=paragraph.add_run(); begin=OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"),"begin"); instr=OxmlElement("w:instrText"); instr.set(qn("xml:space"),"preserve"); instr.text=" PAGE "; end=OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"),"end"); run._r.extend([begin,instr,end]); font(run,10)

def add_toc(doc):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run("MỤC LỤC"),16,True)
    entries=[("DANH MỤC HÌNH ẢNH VÀ BẢNG BIỂU",3,0),("LỜI NÓI ĐẦU",4,0),
      ("CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI",5,0),("1.1. Tổng quan về phân tích dữ liệu",5,1),("1.2. Tổng quan về bài toán dự đoán",5,1),("1.3. Mục tiêu và phạm vi nghiên cứu",5,1),("1.5. Kết luận chương 1",6,1),
      ("CHƯƠNG 2. CÁC PHƯƠNG PHÁP KỸ THUẬT",7,0),("2.1. Phân tích mô tả và tiền xử lý",7,1),("2.2. Feature Engineering",7,1),("2.3. Random Forest Regression",7,1),("2.4. Đánh giá và tối ưu",7,1),("2.6. Kết luận chương 2",8,1),
      ("CHƯƠNG 3. THỰC NGHIỆM VÀ ĐÁNH GIÁ",9,0),("3.1. Dữ liệu thực nghiệm",9,1),("3.2. Quy trình thực nghiệm",9,1),("3.2.2. Audit và tiền xử lý dữ liệu",9,2),("3.2.3. Phân tích mô tả",10,2),("3.2.4. Xây dựng mô hình Random Forest Regression",14,2),("3.3. Đánh giá và thảo luận",23,1),("3.4. Kết luận chương 3",23,1),
      ("CHƯƠNG 4. XÂY DỰNG SẢN PHẨM DEMO",24,0),("4.1. Giới thiệu Flask",24,1),("4.2. Chuẩn bị tài nguyên",24,1),("4.3. Kiến trúc hệ thống",24,1),("4.4. Ưu điểm và hạn chế",25,1),("4.5. Kết luận chương 4",25,1),
      ("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN",26,0),("TÀI LIỆU THAM KHẢO",26,0)]
    for title,page,level in entries:
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Cm(level*.55); p.paragraph_format.space_after=Pt(1); p.paragraph_format.line_spacing=1.0
        tabs=p.paragraph_format.tab_stops; tabs.add_tab_stop(Cm(15.2))
        r=p.add_run(f"{title}\t{page}"); font(r,10.5,bold=(level==0))

def para(doc,text="",bold_lead=None,italic=False,align=WD_ALIGN_PARAGRAPH.JUSTIFY,after=5,first=True):
    p=doc.add_paragraph(); p.alignment=align; p.paragraph_format.space_after=Pt(after); p.paragraph_format.line_spacing=1.35
    if first: p.paragraph_format.first_line_indent=Cm(1)
    if bold_lead and text.startswith(bold_lead): font(p.add_run(bold_lead),13,True); font(p.add_run(text[len(bold_lead):]),13,False,italic)
    else: font(p.add_run(text),13,False,italic)
    return p

def heading(doc,text,level=1):
    p=doc.add_paragraph(style=f"Heading {level}"); p.paragraph_format.keep_with_next=True; p.paragraph_format.space_before=Pt(10 if level>1 else 14); p.paragraph_format.space_after=Pt(6)
    r=p.add_run(text); font(r,16 if level==1 else 14 if level==2 else 13,True,color="000000"); return p

def table(doc,caption,headers,rows,widths=None):
    cp=doc.add_paragraph(); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; cp.paragraph_format.keep_with_next=True; font(cp.add_run(caption),12,True)
    t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False; t.style="Table Grid"
    total=9360; widths=widths or [total//len(headers)]*len(headers); widths[-1]+=total-sum(widths)
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; set_cell_shading(c,LIGHT); set_cell_width(c,widths[i]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run(str(h)),11,True)
    header_props=t.rows[0]._tr.get_or_add_trPr(); header_repeat=OxmlElement("w:tblHeader"); header_repeat.set(qn("w:val"),"true"); header_props.append(header_repeat)
    for row in rows:
        cells=t.add_row().cells
        row_props=t.rows[-1]._tr.get_or_add_trPr(); no_split=OxmlElement("w:cantSplit"); row_props.append(no_split)
        for i,v in enumerate(row):
            set_cell_width(cells[i],widths[i]); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p=cells[i].paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.space_after=Pt(0); font(p.add_run(str(v)),10.5)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return t

def figure(doc,path,caption,width=15.2):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True; p.add_run().add_picture(str(path),width=Cm(width))
    cp=doc.add_paragraph(); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; cp.paragraph_format.keep_with_next=True; font(cp.add_run(caption),12,False,True)

def chapter(doc,title):
    doc.add_page_break(); p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(12); font(p.add_run(title.upper()),17,True,color="000000"); p.style="Heading 1"

def fmt(x,n=3):
    if isinstance(x,int): return f"{x:,}".replace(",",".")
    return f"{x:,.{n}f}".replace(",","X").replace(".",",").replace("X",".")

def configure(doc):
    sec=doc.sections[0]; sec.page_height=Cm(29.7); sec.page_width=Cm(21); sec.top_margin=Cm(2.2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(3); sec.right_margin=Cm(2)
    sec.header_distance=Cm(1); sec.footer_distance=Cm(1)
    styles=doc.styles
    for name,size in [("Normal",13),("Heading 1",17),("Heading 2",14),("Heading 3",13)]:
        s=styles[name]; s.font.name="Times New Roman"; s._element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman"); s.font.size=Pt(size); s.font.color.rgb=RGBColor(0,0,0)
    styles["Normal"].paragraph_format.line_spacing=1.35; styles["Normal"].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    hp=sec.header.paragraphs[0]; hp.alignment=WD_ALIGN_PARAGRAPH.RIGHT; font(hp.add_run("BÁO CÁO BÀI TẬP LỚN - IT6077"),9,False,color="666666")
    add_page_number(sec.footer.paragraphs[0])

def cover(doc):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run("BỘ CÔNG THƯƠNG\n[TRƯỜNG]\n[KHOA]"),14,True)
    doc.add_paragraph(); doc.add_paragraph()
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run("BÁO CÁO BÀI TẬP LỚN\nHỌC PHẦN: IT6077 - PHÂN TÍCH DỮ LIỆU LỚN"),16,True)
    doc.add_paragraph()
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run("ĐỀ TÀI: PHÂN TÍCH DỮ LIỆU VÀ DỰ ĐOÁN LƯU LƯỢNG GIAO THÔNG DỰA TRÊN THỜI GIAN VÀ ĐIỀU KIỆN THỜI TIẾT BẰNG PHƯƠNG PHÁP RANDOM FOREST REGRESSION"),16,True)
    doc.add_paragraph()
    rows=[["Giảng viên hướng dẫn:","[GIẢNG VIÊN HƯỚNG DẪN]"],["Lớp:","[LỚP]"],["Nhóm thực hiện:","[NHÓM]"],["Sinh viên:","[THÀNH VIÊN 1] - [MÃ SINH VIÊN]"]]
    table(doc,"",["Thông tin","Nội dung"],rows,[2600,6760])
    for _ in range(4): doc.add_paragraph()
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run("Hà Nội, tháng 9 năm 2026"),13,True)

def generate_report():
    data=json.loads((ARTIFACT_DIR/"report_data.json").read_text(encoding="utf-8")); d=data["dataset"]; q=data["quality"]; split=data["split"]; final=data["final_model"]; eda=data["eda"]; err=data["error_analysis"]
    feature_meanings={
      "holiday":"Tên ngày lễ của Hoa Kỳ hoặc Minnesota State Fair", "temp":"Nhiệt độ trung bình trong giờ (Kelvin)",
      "rain_1h":"Lượng mưa ghi nhận trong một giờ (mm)", "snow_1h":"Lượng tuyết ghi nhận trong một giờ (mm)",
      "clouds_all":"Tỷ lệ mây che phủ bầu trời (%)", "weather_main":"Nhóm điều kiện thời tiết chính",
      "weather_description":"Mô tả chi tiết trạng thái thời tiết", "date_time":"Thời điểm ghi nhận quan sát",
      "traffic_volume":"Số phương tiện hướng tây đi qua trạm ATR 301 trong một giờ",
      "year":"Năm của thời điểm quan sát", "month":"Tháng của thời điểm quan sát (1-12)",
      "day_of_week":"Thứ trong tuần, từ 0 (Thứ Hai) đến 6 (Chủ nhật)", "hour":"Giờ trong ngày, từ 0 đến 23",
      "is_weekend":"Cờ cuối tuần: 1 nếu Thứ Bảy/Chủ nhật, ngược lại là 0", "is_holiday":"Cờ ngày lễ: 1 nếu thuộc ngày lễ, ngược lại là 0",
      "is_rush_hour":"Cờ giờ cao điểm: 1 nếu thuộc 6–9 giờ hoặc 15–18 giờ, ngược lại là 0", "day_of_year":"Thứ tự ngày trong năm, từ 1 đến 366",
      "hour_sin":"Thành phần sin mã hóa chu kỳ 24 giờ", "hour_cos":"Thành phần cos mã hóa chu kỳ 24 giờ",
      "dow_sin":"Thành phần sin mã hóa chu kỳ 7 ngày", "dow_cos":"Thành phần cos mã hóa chu kỳ 7 ngày",
      "month_sin":"Thành phần sin mã hóa chu kỳ 12 tháng", "month_cos":"Thành phần cos mã hóa chu kỳ 12 tháng",
    }
    doc=Document(); configure(doc); cover(doc); doc.add_page_break(); add_toc(doc)
    doc.add_page_break(); heading(doc,"DANH MỤC HÌNH ẢNH",1)
    for i,p in enumerate(data["figures"],1): para(doc,f"Hình 3.{i}. {Path(p).stem.replace('_',' ')}",first=False)
    heading(doc,"DANH MỤC BẢNG BIỂU",1)
    for i,name in enumerate(["Thuộc tính dữ liệu","Chất lượng dữ liệu","Feature engineering","Chia train/test","Kết quả baseline","Không gian siêu tham số","Kết quả mô hình cuối","Feature Importance","Các API"],1): para(doc,f"Bảng 3.{i}. {name}",first=False)
    heading(doc,"LỜI NÓI ĐẦU",1)
    para(doc,"Sự phát triển của khoa học dữ liệu cho phép khai thác các mẫu có tính chu kỳ và phi tuyến trong dữ liệu giao thông. Trong bài tập lớn này, nhóm xây dựng một quy trình có thể tái lập để phân tích và dự đoán lưu lượng xe theo giờ trên tuyến I-94 hướng tây, tại trạm đo ATR 301 nằm giữa Minneapolis và St. Paul, bang Minnesota.")
    para(doc,"Mục tiêu của báo cáo không phải dự báo toàn bộ giao thông đô thị. Phạm vi kết luận được giới hạn đúng theo trạm đo và giai đoạn dữ liệu. Toàn bộ số liệu thực nghiệm, hình ảnh và bảng đánh giá trong Chương 3 được sinh trực tiếp từ chương trình đã chạy, sau đó được đọc từ hợp đồng dữ liệu artifacts/report_data.json.")

    chapter(doc,"CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI")
    heading(doc,"1.1. Tổng quan về phân tích dữ liệu",2)
    para(doc,"Phân tích dữ liệu là quá trình kiểm tra, làm sạch, biến đổi và mô hình hóa dữ liệu nhằm rút ra thông tin hỗ trợ nhận định. Với dữ liệu giao thông theo thời gian, quy trình phải đồng thời quan tâm đến chất lượng bản ghi, tính lặp của timestamp, khoảng trống thời gian, đặc điểm chu kỳ và nguy cơ rò rỉ thông tin giữa quá khứ với tương lai.")
    heading(doc,"1.1.1. Quy trình phân tích dữ liệu",3)
    para(doc,"Quy trình áp dụng gồm thu thập dữ liệu, audit, tiền xử lý, phân tích khám phá, tạo đặc trưng, chia tập theo thời gian, huấn luyện baseline, tối ưu mô hình, đánh giá sai số, phân tích tầm quan trọng, lưu pipeline và triển khai demo. Mỗi bước tạo ra artifact có thể kiểm tra thay vì nhập kết quả thủ công vào báo cáo.")
    heading(doc,"1.2. Tổng quan về bài toán dự đoán",2)
    para(doc,"Đây là bài toán hồi quy có biến mục tiêu traffic_volume, biểu diễn số phương tiện đi hướng tây qua vị trí đo trong một giờ. Khác với phân loại, đầu ra là đại lượng liên tục; do đó báo cáo sử dụng MAE, RMSE và hệ số xác định R², không sử dụng Accuracy, Precision, Recall, F1-score, ROC hoặc AUC để đánh giá mô hình chính.")
    heading(doc,"1.3. Mục tiêu và phạm vi nghiên cứu",2)
    para(doc,"Nghiên cứu hướng đến ba mục tiêu: mô tả quy luật lưu lượng theo thời gian và thời tiết; xây dựng Random Forest Regressor có khả năng dự đoán trên giai đoạn tương lai; và đóng gói pipeline trong một ứng dụng Flask có kiểm tra đầu vào. Dataset chỉ phản ánh I-94 westbound tại ATR 301, không đại diện cho toàn bộ mạng lưới Minneapolis-St. Paul.")
    heading(doc,"1.4. Ý nghĩa khoa học và thực tiễn",2)
    para(doc,"Về học thuật, đề tài minh họa quy trình hồi quy trên dữ liệu tuần tự, cách kiểm soát leakage và diễn giải sai số. Về thực tiễn, demo cho thấy cách tích hợp mô hình đã huấn luyện vào một giao diện dự đoán. Kết quả không thay thế hệ thống vận hành giao thông và không được diễn giải theo quan hệ nhân quả.")
    heading(doc,"1.5. Kết luận chương 1",2)
    para(doc,"Chương 1 đã xác định đúng bản chất hồi quy, phạm vi trạm đo, mục tiêu và giới hạn sử dụng. Đây là cơ sở để lựa chọn phương pháp kỹ thuật và thiết kế thí nghiệm ở các chương sau.")

    chapter(doc,"CHƯƠNG 2. CÁC PHƯƠNG PHÁP KỸ THUẬT")
    heading(doc,"2.1. Phân tích mô tả và tiền xử lý",2)
    para(doc,"Các thống kê trung tâm, phân tán, tần suất danh mục và đồ thị theo thời gian được sử dụng để kiểm tra phân phối. Timestamp trùng được xem xét theo nhóm: nếu cùng thời điểm có nhiều mô tả thời tiết nhưng traffic_volume nhất quán, các dòng được tổng hợp thành một quan sát giao thông. Nhiệt độ 0 Kelvin được ghi nhận là bất thường vật lý và chỉ được nội suy sau khi đã thống kê.")
    heading(doc,"2.2. Feature Engineering",2)
    para(doc,"Từ date_time, chương trình tạo year, month, day_of_week, day_of_year, hour, is_weekend, is_holiday và is_rush_hour. Các biến chu kỳ hour, day-of-week và month được mã hóa bằng cặp sin/cos để duy trì khoảng cách vòng tròn, ví dụ 23 giờ gần 0 giờ. weather_main được one-hot encoding; weather_description được loại khỏi mô hình chính để giảm độ phân mảnh danh mục và tránh thông tin mô tả dư thừa.")
    heading(doc,"2.3. Random Forest Regression",2)
    para(doc,"Random Forest Regressor kết hợp nhiều cây quyết định được huấn luyện trên các mẫu và tập đặc trưng ngẫu nhiên. Dự đoán cuối là trung bình của các cây, nhờ đó giảm phương sai so với một cây đơn. Mô hình phù hợp với quan hệ phi tuyến và tương tác giữa giờ, ngày trong tuần, thời tiết và lưu lượng mà không đòi hỏi giả định tuyến tính mạnh.")
    heading(doc,"2.4. Đánh giá và tối ưu",2)
    para(doc,"MAE đo độ lệch tuyệt đối trung bình và có đơn vị phương tiện/giờ. RMSE phạt mạnh hơn các lỗi lớn. R² thể hiện phần biến thiên của mục tiêu được giải thích trên tập đánh giá. Việc chia dữ liệu và cross-validation đều theo thứ tự thời gian; TimeSeriesSplit bảo đảm mỗi fold kiểm định nằm sau fold huấn luyện.")
    heading(doc,"2.5. Công cụ",2)
    para(doc,"Python được dùng xuyên suốt với pandas và NumPy cho xử lý dữ liệu, scikit-learn cho pipeline và mô hình, Matplotlib/Seaborn cho trực quan hóa, joblib cho lưu mô hình, Flask cho API và python-docx cho báo cáo. Thiết kế module tách biệt giúp chạy lại và kiểm tra từng giai đoạn.")
    heading(doc,"2.6. Kết luận chương 2",2)
    para(doc,"Các kỹ thuật đã chọn phù hợp với dữ liệu theo giờ và bài toán hồi quy. Chương 3 áp dụng trực tiếp các kỹ thuật này và chỉ báo cáo số liệu thu được từ lần chạy thực tế.")

    chapter(doc,"CHƯƠNG 3. THỰC NGHIỆM VÀ ĐÁNH GIÁ")
    heading(doc,"3.1. Dữ liệu thực nghiệm",2)
    para(doc,f"Dữ liệu gốc có {fmt(d['raw_rows'])} bản ghi và {d['columns']} cột, từ {d['date_start'][:10]} đến {d['date_end'][:10]}. Sau loại dòng trùng hoàn toàn và tổng hợp timestamp, tập xử lý còn {fmt(d['processed_rows'])} quan sát duy nhất theo thời điểm.")
    table(doc,"Bảng 3.1. Thuộc tính của bộ dữ liệu",["Tên biến","Kiểu/đơn vị","Ý nghĩa đầy đủ"],[[name,unit,feature_meanings[name]] for name,unit in [("holiday","Danh mục"),("temp","Kelvin"),("rain_1h","mm"),("snow_1h","mm"),("clouds_all","%"),("weather_main","Danh mục"),("weather_description","Danh mục"),("date_time","Datetime"),("traffic_volume","Xe/giờ")]],[2100,1800,5460])
    heading(doc,"3.2. Quy trình thực nghiệm",2)
    para(doc,"Data Collection → Data Audit → Preprocessing → EDA → Feature Engineering → Chronological Split → Baseline Training → TimeSeriesSplit Tuning → Evaluation → Deployment.",align=WD_ALIGN_PARAGRAPH.CENTER,first=False)
    heading(doc,"3.2.1. Môi trường",3)
    e=data["environment"]; table(doc,"Bảng 3.2. Môi trường thực nghiệm",["Thành phần","Phiên bản"],[["Python",e['python']],["pandas",e['pandas']],["scikit-learn",e['scikit_learn']],["Hệ điều hành",e['platform']]],[3000,6360])
    heading(doc,"3.2.2. Audit và tiền xử lý dữ liệu",3)
    quality_rows=[["Giá trị thiếu",sum(d['missing'].values())],["Dòng trùng hoàn toàn",fmt(d['exact_duplicates'])],["Nhóm timestamp trùng",fmt(d['duplicate_timestamp_groups'])],["Dòng dư do timestamp trùng",fmt(d['duplicate_timestamp_extra_rows'])],["Nhóm có traffic_volume không nhất quán",fmt(d['inconsistent_traffic_timestamp_groups'])],["Nhiệt độ < 200 K",fmt(d['temp_below_200'])],["Nhiệt độ = 0 K",fmt(d['temp_equal_zero'])],["Khoảng trống > 1 giờ",fmt(d['time_gaps_over_1h'])],["Khoảng trống lớn nhất (giờ)",fmt(d['max_gap_hours'],1)]]
    table(doc,"Bảng 3.3. Kết quả kiểm tra chất lượng dữ liệu",["Chỉ tiêu","Kết quả"],quality_rows,[6200,3160])
    para(doc,f"Audit phát hiện {fmt(d['duplicate_timestamp_groups'])} nhóm timestamp lặp. Sau khi loại {fmt(d['exact_duplicates'])} dòng trùng hoàn toàn, hàm aggregate_duplicate_timestamps tổng hợp các mô tả thời tiết cùng giờ bằng median/max/mode theo ý nghĩa biến. Có {fmt(d['temp_equal_zero'])} giá trị 0 K; các giá trị này được thay bằng nội suy theo thời gian sau khi audit. Ngoài ra, một giá trị rain_1h bằng 9.831,3 mm/giờ được xác định là lỗi cảm biến/nhập liệu vì vượt xa ngưỡng audit 100 mm/giờ; chương trình thay đúng {fmt(q['invalid_rain_replaced'])} điểm bất thường bằng nội suy thời gian và giữ lại các mức mưa cực đoan hợp lý. Tập cuối có {fmt(q['rows_after_timestamp_aggregation'])} dòng.")
    heading(doc,"3.2.3. Phân tích mô tả",3)
    figure(doc,FIGURE_DIR/"01_traffic_distribution.png","Hình 3.1. Phân phối lưu lượng giao thông")
    para(doc,f"Lưu lượng trung bình là {fmt(eda['mean_traffic'],1)} phương tiện/giờ và trung vị là {fmt(eda['median_traffic'],1)}. Hình 3.1 cho thấy phân phối rộng, phản ánh sự khác biệt lớn giữa giờ thấp điểm và cao điểm.")
    figure(doc,FIGURE_DIR/"02_hourly_pattern.png","Hình 3.2. Lưu lượng trung bình theo giờ")
    para(doc,f"Giờ có mức trung bình cao nhất trong dữ liệu đã xử lý là {eda['peak_mean_hour']} giờ, đạt khoảng {fmt(eda['peak_mean_hour_value'],1)} phương tiện/giờ. Kết luận này là mô tả mẫu quan sát, không phải quy luật nhân quả.")
    figure(doc,FIGURE_DIR/"03_weekday_pattern.png","Hình 3.3. Lưu lượng trung bình theo thứ")
    para(doc,"Biểu đồ theo thứ cho thấy lưu lượng ngày làm việc và cuối tuần có cấu trúc khác nhau. Điều này ủng hộ việc đưa day_of_week và is_weekend vào tập đặc trưng.")
    figure(doc,FIGURE_DIR/"04_monthly_pattern.png","Hình 3.4. Lưu lượng trung bình theo tháng")
    para(doc,"Mẫu theo tháng biến động nhưng không đủ để kết luận thời tiết gây ra thay đổi lưu lượng. Biến month được giữ cùng mã hóa chu kỳ để mô hình khai thác mùa vụ.")
    figure(doc,FIGURE_DIR/"05_weather_pattern.png","Hình 3.5. Lưu lượng trung bình theo nhóm thời tiết")
    para(doc,f"Nhóm thời tiết có lưu lượng trung bình lớn nhất trong dữ liệu là {eda['highest_mean_weather']}. Số lượng quan sát giữa các nhóm không cân bằng, vì vậy so sánh mô tả này cần được đọc cùng cột count trong bảng traffic_by_weather.csv.")
    figure(doc,FIGURE_DIR/"06_temp_vs_traffic.png","Hình 3.6. Mối quan hệ giữa nhiệt độ và lưu lượng")
    para(doc,"Đám mây điểm cho thấy lưu lượng thay đổi rộng tại cùng một mức nhiệt độ. Nhiệt độ có giá trị dự báo nhưng không đủ để giải thích lưu lượng khi đứng riêng lẻ; mô hình cần kết hợp thêm giờ, thứ và các biến thời tiết khác.")
    figure(doc,FIGURE_DIR/"07_hour_week_heatmap.png","Hình 3.7. Heatmap lưu lượng theo thứ và giờ")
    para(doc,"Heatmap làm rõ tương tác giữa giờ trong ngày và thứ trong tuần; các dải màu khác nhau chứng minh quan hệ không thuần tuyến tính và tạo cơ sở cho mô hình cây tổ hợp.")
    figure(doc,FIGURE_DIR/"08_time_trend.png","Hình 3.8. Xu hướng lưu lượng trung bình theo cửa sổ 30 ngày")
    para(doc,"Chuỗi trung bình 30 ngày cho thấy xu hướng và gián đoạn theo thời gian. Vì dữ liệu có khoảng trống, báo cáo không coi các quan sát là chuỗi giờ liên tục hoàn toàn.")
    heading(doc,"3.2.4. Xây dựng mô hình Random Forest Regression",3)
    heading(doc,"3.2.4.1. Lựa chọn đặc trưng",3)
    feature_rows=[]
    for x in data['features']['numeric']: feature_rows.append([x,feature_meanings.get(x,"Đặc trưng số của mô hình"),"Số","Đầu vào"])
    for x in data['features']['categorical']: feature_rows.append([x,feature_meanings.get(x,"Đặc trưng danh mục"),"Danh mục","Đầu vào; mã hóa one-hot"])
    table(doc,"Bảng 3.4. Danh sách và ý nghĩa các đặc trưng mô hình",["Tên biến","Tên tiếng Việt/Ý nghĩa","Kiểu dữ liệu","Cách sử dụng"],feature_rows,[1900,4560,1300,1600])
    heading(doc,"3.2.4.2. Chia tập dữ liệu",3)
    table(doc,"Bảng 3.5. Chia tập theo thời gian",["Tập","Số quan sát","Bắt đầu","Kết thúc"],[["Train",fmt(split['train_rows']),split['train_start'][:16],split['train_end'][:16]],["Test",fmt(split['test_rows']),split['test_start'][:16],split['test_end'][:16]]],[1500,1800,3030,3030])
    para(doc,"80% quan sát sớm nhất được dùng để huấn luyện và 20% quan sát muộn nhất để kiểm tra. Cách chia chronological split mô phỏng tình huống dự báo tương lai và tránh để thông tin tương lai xuất hiện trong tập huấn luyện.")
    heading(doc,"3.2.4.3. Các mô hình baseline",3)
    rows=[]
    for r in data['models']['comparison']:
        rows.append([r['model'],fmt(r['train_mae'],2),fmt(r['test_mae'],2),fmt(r['train_rmse'],2),fmt(r['test_rmse'],2),fmt(r['test_r2'],4)])
    table(doc,"Bảng 3.6. So sánh các mô hình",["Mô hình","MAE train","MAE test","RMSE train","RMSE test","R² test"],rows,[2200,1400,1400,1500,1500,1360])
    para(doc,"Dummy tạo mốc dự báo theo trung bình; Linear Regression đo mức hiệu quả của quan hệ tuyến tính; Decision Tree thể hiện baseline phi tuyến; Random Forest Default và phiên bản tuned đánh giá lợi ích của tổ hợp cây và tối ưu siêu tham số.")
    para(doc,"Trong Bảng 3.6, MAE là sai số tuyệt đối trung bình; RMSE là căn bậc hai của sai số bình phương trung bình và nhạy hơn với lỗi lớn; R² là tỷ lệ biến thiên của lưu lượng được mô hình giải thích. MAE và RMSE càng thấp càng tốt, còn R² càng gần 1 càng tốt.")
    heading(doc,"3.2.4.4. Tối ưu siêu tham số",3)
    tune=data['tuning']; parameter_meanings={"model__n_estimators":"Số cây quyết định trong rừng","model__max_depth":"Độ sâu tối đa của mỗi cây","model__min_samples_split":"Số mẫu tối thiểu để tách một nút","model__min_samples_leaf":"Số mẫu tối thiểu tại một nút lá","model__max_features":"Số/tỷ lệ đặc trưng được xét tại mỗi lần tách"}
    table(doc,"Bảng 3.7. Không gian tìm kiếm siêu tham số",["Tham số","Ý nghĩa","Giá trị thử nghiệm"],[[k.replace("model__",""),parameter_meanings.get(k,"Tham số của mô hình"),", ".join(map(str,v))] for k,v in tune['search_space'].items()],[2700,4160,2500])
    para(doc,f"RandomizedSearchCV thử {tune['candidates']} cấu hình với {tune['cv']}. Best CV MAE là {fmt(tune['best_cv_mae'],2)} phương tiện/giờ. Bộ tham số tốt nhất: "+", ".join(f"{k}={v}" for k,v in tune['best_parameters'].items())+".")
    final_heading=heading(doc,"3.2.4.5. Đánh giá mô hình cuối",3)
    final_heading.paragraph_format.page_break_before=True
    table(doc,"Bảng 3.8. Chỉ số mô hình Random Forest đã tối ưu",["Tập dữ liệu","MAE (xe/giờ)","RMSE (xe/giờ)","R²"],[["Huấn luyện (train)",fmt(final['train']['mae'],2),fmt(final['train']['rmse'],2),fmt(final['train']['r2'],4)],["Kiểm tra (test)",fmt(final['test']['mae'],2),fmt(final['test']['rmse'],2),fmt(final['test']['r2'],4)]],[2600,2360,2360,2040])
    para(doc,f"Trên tập test, MAE = {fmt(final['test']['mae'],2)} nghĩa là dự đoán lệch tuyệt đối trung bình khoảng {fmt(final['test']['mae'],0)} phương tiện/giờ. RMSE = {fmt(final['test']['rmse'],2)} lớn hơn MAE, cho thấy vẫn có một số lỗi lớn. R² = {fmt(final['test']['r2'],4)} cho biết mô hình giải thích khoảng {fmt(final['test']['r2']*100,2)}% biến thiên lưu lượng trên giai đoạn kiểm tra.")
    para(doc,f"MAE train là {fmt(final['train']['mae'],2)}, thấp hơn MAE test. Khoảng cách này cho thấy một mức overfitting nhất định; tuy nhiên cần đánh giá cùng hiệu năng test thay vì chỉ dựa vào độ khớp train.")
    heading(doc,"3.2.4.6. Phân tích sai số",3)
    figure(doc,FIGURE_DIR/"09_actual_vs_predicted.png","Hình 3.9. Giá trị thực tế và dự đoán")
    para(doc,"Các điểm bám gần đường chéo cho thấy mô hình tái hiện tốt phần lớn biến thiên, trong khi độ phân tán ở hai đầu phản ánh những thời điểm khó dự đoán.")
    figure(doc,FIGURE_DIR/"10_residual_distribution.png","Hình 3.10. Phân phối phần dư")
    para(doc,f"Phần dư trung bình là {fmt(err['mean_residual'],2)} phương tiện/giờ và trung vị sai số tuyệt đối là {fmt(err['median_absolute_error'],2)}. Phân phối quanh 0 hỗ trợ nhận định mô hình không lệch mạnh theo một hướng trên toàn bộ test.")
    figure(doc,FIGURE_DIR/"11_prediction_timeseries.png","Hình 3.11. Chuỗi thực tế và dự đoán ở 500 quan sát cuối")
    para(doc,"Đường dự đoán theo sát chu kỳ chung nhưng làm trơn một số đỉnh và đáy bất thường, đặc điểm thường gặp khi lấy trung bình dự đoán từ nhiều cây.")
    figure(doc,FIGURE_DIR/"12_mae_by_hour.png","Hình 3.12. MAE theo giờ")
    para(doc,f"Sai số trung bình cao nhất theo giờ xuất hiện ở {err['worst_mae_hour']} giờ, với MAE {fmt(err['worst_mae_hour_value'],2)}. Đây là nhóm cần ưu tiên kiểm tra khi bổ sung biến sự cố hoặc điều kiện đường.")
    figure(doc,FIGURE_DIR/"13_mae_by_weather.png","Hình 3.13. MAE theo nhóm thời tiết")
    para(doc,f"Nhóm có MAE cao nhất là {err['worst_mae_weather']} với {fmt(err['worst_mae_weather_value'],2)} phương tiện/giờ. Kết quả có thể chịu ảnh hưởng bởi kích thước mẫu từng nhóm nên không được diễn giải là quan hệ nhân quả.")
    heading(doc,"3.2.4.7. Feature Importance",3)
    fi_rows=[]
    for i,x in enumerate(data['feature_importance']):
        raw_name=x['feature'].replace('num__','').replace('cat__','')
        fi_rows.append([i+1,raw_name,feature_meanings.get(raw_name,"Biến sau tiền xử lý/mã hóa"),fmt(x['importance'],5)])
    table(doc,"Bảng 3.9. Top 10 Random Forest Feature Importance",["Hạng","Tên biến","Ý nghĩa","Mức quan trọng"],fi_rows,[900,1900,4560,2000])
    figure(doc,FIGURE_DIR/"15_rf_feature_importance.png","Hình 3.14. Random Forest Feature Importance")
    figure(doc,FIGURE_DIR/"14_permutation_importance.png","Hình 3.15. Permutation Importance")
    top=data['feature_importance'][0]; ptop=data['permutation_importance'][0]
    para(doc,f"Đặc trưng đứng đầu theo impurity-based importance là {top['feature'].replace('num__','').replace('cat__','')}; theo permutation importance là {ptop['feature']}. Hai cách đo có cơ chế khác nhau và có thể xếp hạng khác nhau. Importance chỉ phản ánh đóng góp dự báo trong mô hình, không chứng minh đặc trưng gây ra biến đổi giao thông.")
    heading(doc,"3.3. Đánh giá và thảo luận",2)
    para(doc,"Mô hình khai thác tốt các chu kỳ thời gian và tương tác phi tuyến, vượt baseline tuyến tính và dummy. Tuy vậy, train tốt hơn test và sai số tăng ở một số giờ/nhóm thời tiết cho thấy chưa mô tả hết các biến động đột xuất. Dataset chỉ có một trạm, có khoảng trống thời gian, và không chứa tai nạn, công trình đường, sự kiện thể thao, tình trạng đường lân cận hoặc dữ liệu luồng xe mạng lưới.")
    heading(doc,"3.4. Kết luận chương 3",2)
    para(doc,f"Từ {fmt(d['raw_rows'])} dòng gốc, quy trình tạo {fmt(d['processed_rows'])} timestamp đã tổng hợp và chia {fmt(split['train_rows'])}/{fmt(split['test_rows'])} cho train/test theo thời gian. Random Forest tối ưu đạt MAE {fmt(final['test']['mae'],2)}, RMSE {fmt(final['test']['rmse'],2)} và R² {fmt(final['test']['r2'],4)} trên test. Các hình sai số và importance xác định rõ nơi mô hình hoạt động chưa tốt và các đặc trưng đóng góp lớn nhất.")

    chapter(doc,"CHƯƠNG 4. XÂY DỰNG SẢN PHẨM DEMO")
    heading(doc,"4.1. Giới thiệu Flask",2)
    para(doc,"Flask là micro-framework Python phù hợp với demo học máy nhỏ gọn. Ứng dụng khởi tạo model một cách tái sử dụng qua pipeline joblib, cung cấp trang HTML và các endpoint JSON. Server phát triển chỉ dùng cho thử nghiệm nội bộ, không phải cấu hình production.")
    heading(doc,"4.2. Chuẩn bị tài nguyên",2)
    table(doc,"Bảng 4.1. Tài nguyên của demo",["Tài nguyên","Vai trò"],[["traffic_rf_pipeline.joblib","Pipeline tiền xử lý và Random Forest đã huấn luyện"],["report_data.json","Metadata và chỉ số thực nghiệm"],["category_values.json","Danh mục thời tiết hợp lệ"],["templates/index.html","Biểu mẫu HTML"],["static/css/style.css","Giao diện responsive"],["static/js/app.js","Gọi API và hiển thị kết quả"]],[3200,6160])
    heading(doc,"4.3. Kiến trúc hệ thống",2)
    para(doc,"User → Browser → Flask API → Validation → Feature Engineering → Preprocessing Pipeline → Random Forest Regression → traffic_volume prediction → JSON → Browser.",align=WD_ALIGN_PARAGRAPH.CENTER,first=False)
    heading(doc,"4.3.1. Backend",3)
    table(doc,"Bảng 4.2. Các endpoint API",["Method","Endpoint","Chức năng"],[["GET","/","Hiển thị giao diện"],["POST","/api/predict","Nhận dữ liệu và trả dự đoán"],["GET","/api/model-info","Trả thông tin mô hình"],["GET","/health","Kiểm tra dịch vụ và model"]],[1500,2600,5260])
    heading(doc,"4.3.2. Frontend",3)
    para(doc,"Biểu mẫu nhận ngày giờ, nhiệt độ Celsius, mưa, tuyết, mây che phủ, nhóm thời tiết và trạng thái ngày lễ. Backend chuyển Celsius sang Kelvin trước khi xây dựng đúng schema đặc trưng của mô hình. JavaScript gửi JSON và định dạng kết quả theo đơn vị phương tiện/giờ.")
    api_path=ARTIFACT_DIR/"api_test_results.json"
    if api_path.exists():
        api=json.loads(api_path.read_text(encoding="utf-8"))
        table(doc,"Bảng 4.3. Kết quả kiểm thử API",["Ca kiểm thử","HTTP","Kết quả"],[["GET /health",api['health'][0],"Model tồn tại, status ok"],["GET /api/model-info",api['model_info'][0],"Trả thuật toán và metrics"],["POST /api/predict",api['predict'][0],f"Dự đoán {api['predict'][1]['prediction']} xe/giờ"],["POST thiếu dữ liệu",api['validation'][0],"Từ chối payload thiếu trường"]],[3000,1300,5060])
    heading(doc,"4.3.3. Luồng hoạt động",3)
    para(doc,"Người dùng nhập dữ liệu và nhấn Dự đoán. Trình duyệt kiểm tra các trường bắt buộc, gửi POST /api/predict, Flask xác thực payload, tạo các đặc trưng thời gian và chu kỳ, gọi pipeline đã lưu, chặn giá trị âm, rồi trả JSON. Frontend hiển thị dự đoán hoặc thông báo lỗi.")
    demo_dir=FIGURE_DIR/"demo"
    for idx,name,cap in [(1,"01_home.png","Trang chính của demo"),(2,"02_prediction_form.png","Biểu mẫu với dữ liệu đầu vào"),(3,"03_prediction_result.png","Kết quả dự đoán từ model thật")]:
        p=demo_dir/name
        if p.exists(): figure(doc,p,f"Hình 4.{idx}. {cap}",15.2)
    if not any((demo_dir/name).exists() for name in ["01_home.png","02_prediction_form.png","03_prediction_result.png"]):
        para(doc,"Môi trường thực thi không cung cấp trình duyệt cho browser automation, vì vậy báo cáo không chèn ảnh chụp giả. Việc xác nhận demo được thực hiện bằng Flask test client với kết quả ở Bảng 4.3.")
    heading(doc,"4.4. Ưu điểm và hạn chế",2)
    para(doc,"Demo có giao diện đơn giản, dự đoán nhanh, kiểm tra trường bắt buộc và tái sử dụng đúng preprocessing pipeline. Hạn chế gồm không có xác thực người dùng, chưa giám sát drift, chưa kết nối thời tiết/giao thông thời gian thực và dùng Flask development server. Phạm vi mô hình vẫn giới hạn ở trạm ATR 301.")
    heading(doc,"4.5. Kết luận chương 4",2)
    para(doc,"Chương 4 đã đóng gói mô hình đã huấn luyện vào ứng dụng web có API kiểm thử được. Sản phẩm chứng minh luồng từ dữ liệu đầu vào đến dự đoán nhưng cần bổ sung hạ tầng production và dữ liệu thời gian thực nếu triển khai vận hành.")

    chapter(doc,"KẾT LUẬN")
    para(doc,f"Đề tài đã hoàn thành quy trình phân tích và dự đoán lưu lượng giao thông theo giờ trên I-94 westbound tại ATR 301. Dữ liệu được audit, tổng hợp timestamp trùng, xử lý nhiệt độ bất thường, tạo đặc trưng thời gian và thời tiết, sau đó chia theo thời gian để đánh giá thực tế hơn. Random Forest Regression sau tối ưu đạt MAE {fmt(final['test']['mae'],2)}, RMSE {fmt(final['test']['rmse'],2)} và R² {fmt(final['test']['r2'],4)} trên tập test.")
    para(doc,"EDA làm rõ chu kỳ giờ, thứ, tháng và sự khác biệt mô tả giữa các nhóm thời tiết. Phân tích sai số chỉ ra các phân đoạn khó dự đoán, trong khi feature importance hỗ trợ hiểu đóng góp dự báo mà không khẳng định nhân quả. Demo Flask sử dụng đúng model đã lưu và hỗ trợ kiểm thử API.")
    heading(doc,"HƯỚNG PHÁT TRIỂN",1)
    para(doc,"Trong tương lai có thể mở rộng sang nhiều trạm giao thông, bổ sung dữ liệu tai nạn, công trình, sự kiện, tình trạng đường và nguồn thời tiết thời gian thực. Các mô hình Gradient Boosting, XGBoost, LightGBM, LSTM hoặc Transformer có thể được so sánh bằng cùng chronological split. Đây là hướng đề xuất, không phải kết quả đã thực hiện trong báo cáo.")
    heading(doc,"TÀI LIỆU THAM KHẢO",1)
    refs=["[1] J. Hogue, Metro Interstate Traffic Volume, UCI Machine Learning Repository, 2019. DOI: 10.24432/C5X60B. https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume",
          "[2] Scikit-learn Developers, RandomForestRegressor documentation. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html",
          "[3] Scikit-learn Developers, Regression metrics API. https://scikit-learn.org/stable/api/sklearn.metrics.html",
          "[4] Scikit-learn Developers, TimeSeriesSplit documentation. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html",
          "[5] Pallets Projects, Flask Quickstart. https://flask.palletsprojects.com/en/stable/quickstart/"]
    for x in refs: para(doc,x,first=False)
    out=REPORT_DIR/"final_report_updated.docx"; doc.save(out)
    # Machine-check that the key experiment numbers were inserted from report_data.json.
    text="\n".join(p.text for p in doc.paragraphs)
    expected=[fmt(d['raw_rows']),fmt(d['processed_rows']),fmt(final['test']['mae'],2),fmt(final['test']['rmse'],2),fmt(final['test']['r2'],4)]
    missing=[x for x in expected if x not in text]
    if missing: raise RuntimeError(f"Report contract mismatch: {missing}")
    if re.search(r"\[(RUN|TODO)\]|INSERT RESULT HERE",text,re.I): raise RuntimeError("Unresolved experimental placeholder")
    (REPORT_DIR/"final_report.md").write_text(f"# Báo cáo\n\nBáo cáo Word được sinh từ `artifacts/report_data.json`.\n\n- MAE test: {final['test']['mae']:.6f}\n- RMSE test: {final['test']['rmse']:.6f}\n- R2 test: {final['test']['r2']:.6f}\n",encoding="utf-8")
    return out
