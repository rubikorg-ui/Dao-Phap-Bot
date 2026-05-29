import streamlit as st
import pandas as pd
import io
import re
import hashlib
import datetime
import random
from collections import Counter

# ==============================================================================
# CẤU HÌNH ĐIỂM XẾP HẠNG BOT
# ==============================================================================
DIEM_SO = {"0X": 10, "1X": 9, "2X": 8, "3X": 7, "4X": 6, "5X": 5, "6X": 4, "7X": 3, "8X": 2, "9X": 1, "S": 0}
DANH_SACH_MOC = ["9X", "8X", "7X", "6X", "5X", "4X", "3X", "2X", "1X", "0X"]

# ==============================================================================
# LÕI THUẬT TOÁN ĐỌC NGÀY THÁNG
# ==============================================================================
def parse_to_day_month(date_str):
    date_str = str(date_str).strip()
    if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_str):
        parts = [int(x) for x in re.findall(r'\d+', date_str)]
        return parts[2], parts[1]
    
    try:
        dt = pd.to_datetime(date_str, errors='raise')
        return dt.day, dt.month
    except:
        pass
        
    nums = [int(s) for s in re.findall(r'\d+', date_str)]
    if len(nums) >= 2:
        if nums[0] > 12 and nums[0] <= 31 and nums[1] <= 12:
            return nums[0], nums[1]
        elif nums[1] > 12 and nums[1] <= 31 and nums[0] <= 12:
            return nums[1], nums[0]
        else:
            return nums[0], nums[1]
            
    today = datetime.datetime.now()
    return today.day, today.month

# ==============================================================================
# LÕI THUẬT TOÁN TẠO BOT (SIÊU TỐC ĐỘ VỚI CACHE)
# ==============================================================================
# @st.cache_data: Giúp lưu dữ liệu vào RAM, chạy 100 ngày hay 365 ngày cũng chỉ mất đúng 1 lần tính.
@st.cache_data(show_spinner=False, max_entries=100000)
def get_dan_bot_cached(bot_id, tuple_lich_su):
    lich_su_ket_qua = list(tuple_lich_su)
    scores = {}
    chuoi_hash_ngay = f"Ngay_{bot_id}_{','.join(map(str, lich_su_ket_qua))}"
    
    for n in range(100):
        h = hashlib.md5(f"{chuoi_hash_ngay}_{n}".encode()).hexdigest()
        scores[n] = (int(h, 16) % 100000) / 1000.0  

    if not lich_su_ket_qua:
        nums = sorted(list(range(100)), key=lambda x: (scores[x], -x), reverse=True)
    else:
        so_truoc = lich_su_ket_qua[-1]
        dau_truoc, duoi_truoc = so_truoc // 10, so_truoc % 10
        tong_truoc = (dau_truoc + duoi_truoc) % 10
        tong_so_ngay = len(lich_su_ket_qua)
        
        last_seen = {n: -1 for n in range(100)}
        for idx, num in enumerate(lich_su_ket_qua): last_seen[num] = idx
            
        bot_rng = random.Random(bot_id)
        chien_luoc = bot_rng.choice(['roi', 'gan', 'tong', 'chanle', 'cham'])
        
        for n in range(100):
            nd, nc = n // 10, n % 10
            tong = (nd + nc) % 10
            
            if chien_luoc == 'roi':
                if last_seen[n] != -1: scores[n] += (last_seen[n] / tong_so_ngay) * 120
            elif chien_luoc == 'gan':
                ngay_chua_ve = tong_so_ngay - last_seen[n] if last_seen[n] != -1 else tong_so_ngay
                scores[n] += ngay_chua_ve * 6
            elif chien_luoc == 'tong':
                if tong == tong_truoc: scores[n] += 100
                elif tong == (tong_truoc + 1) % 10 or tong == (tong_truoc - 1) % 10: scores[n] += 40
            elif chien_luoc == 'chanle':
                if (n % 2 == 0) == (so_truoc % 2 == 0): scores[n] += 80
            elif chien_luoc == 'cham':
                if nd == dau_truoc or nc == duoi_truoc: scores[n] += 90

        nums = sorted(list(range(100)), key=lambda x: (scores[x], -x), reverse=True)

    # Đóng gói thành các cột 9X..0X
    nums_str = [f"{n:02d}" for n in nums]
    cac_dan = {
        "9X": sorted(nums_str[:95]), "8X": sorted(nums_str[:88]), "7X": sorted(nums_str[:78]),  
        "6X": sorted(nums_str[:68]), "5X": sorted(nums_str[:58]), "4X": sorted(nums_str[:48]),  
        "3X": sorted(nums_str[:38]), "2X": sorted(nums_str[:28]), "1X": sorted(nums_str[:18]), "0X": sorted(nums_str[:8])
    }
    tat_ca_so = []
    for ten_dan in ["0X", "1X", "2X", "3X", "4X", "5X", "6X", "7X", "8X", "9X"]:
        tat_ca_so.extend(cac_dan[ten_dan])
    dem_so = Counter(tat_ca_so)
    for i in range(1, 11):
        cac_dan[f"M{i}"] = sorted([so for so, freq in dem_so.items() if freq == i])
    so_cua_9x = sorted(nums_str[:95])
    cac_dan["M0"] = sorted([f"{n:02d}" for n in range(100) if f"{n:02d}" not in so_cua_9x])
    cac_dan["M10"] = cac_dan["M10"]
    return cac_dan

def xac_dinh_dan_trung(dan_cua_bot, ket_qua):
    k = f"{int(ket_qua):02d}"
    for ten in ["0X", "1X", "2X", "3X", "4X", "5X", "6X", "7X", "8X", "9X"]:
        if k in dan_cua_bot[ten]: return ten
    return "S"

# ==============================================================================
# HÀM THỰC THI "ĐAO PHÁP CHÉM DÀN"
# ==============================================================================
def lay_so_theo_cat(sorted_nums, phuong_phap, size):
    if size <= 0: return []
    if size >= 100: return sorted_nums.copy()
    
    if phuong_phap == "Chém Trên":
        return sorted_nums[:size]
    elif phuong_phap == "Chém Dưới":
        return sorted_nums[-size:]
    elif phuong_phap == "Chém 2 Đầu":
        loai = 100 - size
        loai_dinh = loai // 2
        loai_day = loai - loai_dinh
        return sorted_nums[loai_dinh : 100 - loai_day]
    elif phuong_phap == "Chém Giữa":
        giu_dinh = size // 2
        giu_day = size - giu_dinh
        if giu_day > 0:
            return sorted_nums[:giu_dinh] + sorted_nums[-giu_day:]
        else:
            return sorted_nums[:giu_dinh]
    return []

def tao_dan_va_danh_gia_rank(danh_sach_dan_top, phuong_phap, so_luong, mien_nguon, kq_str=None):
    diem_so = {f"{n:02d}": 0.0 for n in range(100)}
    so_luong_bot = len(danh_sach_dan_top)
    
    for rank_idx, dan in enumerate(danh_sach_dan_top):
        if mien_nguon in dan:
            micro_weight = (so_luong_bot - rank_idx) / (so_luong_bot * 100.0) if so_luong_bot > 0 else 0
            for so in dan[mien_nguon]:
                diem_so[so] += 1.0 + micro_weight
                
    # Đã khóa Luật: Ưu tiên Số LỚN xếp trên
    sorted_nums = sorted(diem_so.keys(), key=lambda x: (-diem_so[x], -int(x)))
    
    dan_chot = sorted(lay_so_theo_cat(sorted_nums, phuong_phap, so_luong))
    
    rank_thuc_te = 101 
    if kq_str:
        for s in range(1, 101):
            if kq_str in lay_so_theo_cat(sorted_nums, phuong_phap, s):
                rank_thuc_te = s
                break
                
    return dan_chot, rank_thuc_te

# ==============================================================================
# GIAO DIỆN CHÍNH STREAMLIT
# ==============================================================================
st.set_page_config(layout="wide")
st.title("🏆 Hệ Thống Đao Pháp Đa Tuyến (Siêu Tốc Độ)")
uploaded_file = st.sidebar.file_uploader("Tải File Gốc (2 cột)", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=[df.columns[1]])
    
    danh_sach_ngay_dep = []
    for index, row in df.iterrows():
        d, m = parse_to_day_month(str(row.iloc[0]))
        danh_sach_ngay_dep.append(f"{d}/{m}")
    
    st.sidebar.header("⚔️ CẤU HÌNH ĐAO PHÁP")
    
    ngay_bat_dau_bt = st.sidebar.selectbox("📅 Bắt đầu Backtest từ ngày:", danh_sach_ngay_dep, index=0)
    idx_bat_dau = danh_sach_ngay_dep.index(ngay_bat_dau_bt)
    
    col_h1, col_h2 = st.sidebar.columns(2)
    with col_h1:
        tu_hang = st.number_input("Từ Hạng Bot:", min_value=1, max_value=500, value=1)
    with col_h2:
        den_hang = st.number_input("Đến Hạng Bot:", min_value=1, max_value=500, value=20)
        
    if tu_hang > den_hang:
        tu_hang, den_hang = den_hang, tu_hang
    
    st.sidebar.markdown("**🎯 Chọn Mốc Nguồn Đa Tuyến:**")
    cols_cb = st.sidebar.columns(5)
    selected_mocs = []
    for idx, moc in enumerate(DANH_SACH_MOC):
        is_checked = cols_cb[idx % 5].checkbox(moc, value=(moc in ["9X"]))
        if is_checked:
            selected_mocs.append(moc)

    phuong_phap_chem = st.sidebar.selectbox("🌪️ Chọn Chiêu Thức Chém:", ["Chém Trên", "Chém Dưới", "Chém 2 Đầu", "Chém Giữa"])
    so_luong_vip = st.sidebar.number_input("✂️ Số lượng số muốn chốt:", value=70, min_value=1, max_value=99)
    
    btn_chot = st.sidebar.button("🚀 CHẠY BACKTEST SIÊU TỐC", type="primary", use_container_width=True)

    st.sidebar.header("📊 XUẤT FILE PHONG ĐỘ")
    so_ngay_xuat = st.sidebar.number_input("Số ngày xuất Excel (0 = Tất cả):", min_value=0, value=30)
    st.sidebar.info("💡 Mẹo: Nhập 30 để chỉ tạo file Excel 30 ngày gần nhất (nhẹ & tải nhanh).")
    btn_xuat = st.sidebar.button("📥 TẠO FILE EXCEL LIỀN MẠCH")

    if btn_chot:
        if not selected_mocs:
            st.error("⚠️ Vui lòng tick chọn ít nhất 1 Mốc Dàn Nguồn để chạy!")
        else:
            danh_sach_kq = []
            du_lieu_bot = {i: {'tong_diem': 0} for i in range(1, 501)}
            
            bt_results = {"Ngày": [], "KQ": []}
            for moc in selected_mocs:
                bt_results[f"Chém {moc}"] = []
            
            with st.spinner(f"Đang phân tích dữ liệu thần tốc nhờ bộ nhớ Cache..."):
                for index, row in df.iterrows():
                    ngay_gon = danh_sach_ngay_dep[index]
                    kq = int(row.iloc[1])
                    kq_str = f"{kq:02d}"
                    
                    if index >= idx_bat_dau:
                        all_sorted_bots = sorted(du_lieu_bot.keys(), key=lambda x: (du_lieu_bot[x]['tong_diem'], -x), reverse=True)
                        target_bot_ids = all_sorted_bots[tu_hang - 1 : den_hang]
                        # SỬ DỤNG HÀM CACHE SIÊU TỐC
                        danh_sach_dan_target = [get_dan_bot_cached(b, tuple(danh_sach_kq)) for b in target_bot_ids]
                        
                        bt_results["Ngày"].append(ngay_gon)
                        bt_results["KQ"].append(kq_str)
                        
                        for moc in selected_mocs:
                            dan_chot_bt, rank_s = tao_dan_va_danh_gia_rank(
                                danh_sach_dan_target, phuong_phap_chem, int(so_luong_vip), moc, kq_str
                            )
                            if kq_str in dan_chot_bt:
                                text_kq = f"🟢 WIN {so_luong_vip}({rank_s})"
                            else:
                                text_kq = f"🔴 LOSE {so_luong_vip}({rank_s})"
                            
                            bt_results[f"Chém {moc}"].append(text_kq)

                    for i in range(1, 501):
                        dan_nay = get_dan_bot_cached(i, tuple(danh_sach_kq))
                        trung = xac_dinh_dan_trung(dan_nay, kq)
                        du_lieu_bot[i]['tong_diem'] += DIEM_SO[trung]
                    
                    danh_sach_kq.append(kq)
                
                final_bt_results = {"Ngày": bt_results["Ngày"], "KQ": bt_results["KQ"]}
                for moc in selected_mocs:
                    old_col_name = f"Chém {moc}"
                    danh_sach_ket_qua = bt_results[old_col_name]
                    tong_so_ngay_test = len(danh_sach_ket_qua)
                    tong_so_ngay_win = sum(1 for res in danh_sach_ket_qua if "🟢 WIN" in res)
                    
                    if tong_so_ngay_test > 0:
                        new_col_name = f"Chém {moc} (Win {tong_so_ngay_win}/{tong_so_ngay_test})"
                    else:
                        new_col_name = old_col_name
                        
                    final_bt_results[new_col_name] = danh_sach_ket_qua

                st.success(f"⚡ Hoàn thành siêu tốc! Dữ liệu đã được lưu bộ đệm, các lần ấn tiếp theo sẽ trả kết quả tức thì.")
                
                st.subheader("📋 Bảng So Sánh Backtest Đa Tuyến")
                df_bt = pd.DataFrame(final_bt_results)
                st.dataframe(df_bt, use_container_width=True, hide_index=True)
                
                st.divider()
                st.subheader(f"🎯 DÀN CHỐT NGÀY MAI ({so_luong_vip} SỐ)")
                st.markdown(f"*(Áp dụng **{phuong_phap_chem}** cho Bot hạng **{tu_hang} đến {den_hang}**)*")
                
                all_sorted_bots_mai = sorted(du_lieu_bot.keys(), key=lambda x: (du_lieu_bot[x]['tong_diem'], -x), reverse=True)
                target_bot_ids_mai = all_sorted_bots_mai[tu_hang - 1 : den_hang]
                danh_sach_dan_target_mai = [get_dan_bot_cached(b, tuple(danh_sach_kq)) for b in target_bot_ids_mai]
                
                cols_output = st.columns(len(selected_mocs))
                for i, moc in enumerate(selected_mocs):
                    dan_mai, _ = tao_dan_va_danh_gia_rank(danh_sach_dan_target_mai, phuong_phap_chem, int(so_luong_vip), moc, None)
                    with cols_output[i]:
                        st.info(f"**Dàn soi từ mốc {moc}:**")
                        st.code(",".join(dan_mai), language="text")

    if btn_xuat:
        with st.spinner("Đang xử lý dữ liệu và đóng gói file Excel..."):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                danh_sach_kq = []
                danh_sach_tieu_de = []
                du_lieu_bot = {i: {'tong_diem': 0, 'lich_su_trung': []} for i in range(1, 501)}
                danh_sach_cot = ["9X", "8X", "7X", "6X", "5X", "4X", "3X", "2X", "1X", "0X", "M0"] + [f"M{j}" for j in range(1,11)]
                
                tong_so_ngay = len(df)
                # Tính toán mốc xuất dữ liệu: Chỉ lấy N ngày gần nhất (vd: 30 ngày)
                moc_in_file = max(0, tong_so_ngay - so_ngay_xuat) if so_ngay_xuat > 0 else 0
                
                for index, row in df.iterrows():
                    ngay_gon = danh_sach_ngay_dep[index]
                    safe_name = ngay_gon.replace('/', '-')
                    kq = int(row.iloc[1])
                    
                    tieu_de_6_ngay = danh_sach_tieu_de[-6:]
                    while len(tieu_de_6_ngay) < 6:
                        tieu_de_6_ngay.insert(0, "---")
                        
                    data_sheet = []
                    # Nếu ngày hiện tại >= mốc xuất file thì mới tiến hành gom dữ liệu để xuất Excel
                    if index >= moc_in_file:
                        for i in range(1, 501):
                            dan = get_dan_bot_cached(i, tuple(danh_sach_kq))
                            ls_6 = du_lieu_bot[i]['lich_su_trung'][-6:]
                            while len(ls_6) < 6:
                                ls_6.insert(0, "")
                                
                            row_data = {"STT": i, "THÀNH VIÊN": f"Bot_{i:03d}"}
                            for j in range(6): 
                                row_data[tieu_de_6_ngay[j]] = ls_6[j]
                            row_data["TỔNG ĐIỂM"] = du_lieu_bot[i]['tong_diem']
                            for ten in danh_sach_cot: 
                                row_data[ten] = ",".join(map(str, dan.get(ten, [])))
                            data_sheet.append(row_data)
                        
                        # Xuất ra 1 Sheet trong Excel
                        df_day = pd.DataFrame(data_sheet).sort_values(by=["TỔNG ĐIỂM", "STT"], ascending=[False, True]).reset_index(drop=True)
                        df_day["STT"] = df_day.index + 1
                        df_day.to_excel(writer, sheet_name=safe_name, index=False)
                    
                    # Tiến hành cộng điểm và lưu lịch sử (Vẫn phải chạy cho tất cả các ngày từ đầu để chuẩn điểm)
                    tieu_de_nay = f"{ngay_gon}({kq:02d})"
                    for i in range(1, 501):
                        dan_nay = get_dan_bot_cached(i, tuple(danh_sach_kq))
                        trung = xac_dinh_dan_trung(dan_nay, kq)
                        du_lieu_bot[i]['lich_su_trung'].append(trung)
                        du_lieu_bot[i]['tong_diem'] += DIEM_SO[trung]
                    
                    danh_sach_kq.append(kq)
                    danh_sach_tieu_de.append(tieu_de_nay)
                
                # --- PHẦN SHEET DỰ ĐOÁN NGÀY MAI ---
                last_day, last_month = parse_to_day_month(str(df.iloc[-1, 0]))
                current_year = datetime.datetime.now().year
                try:
                    last_dt = datetime.date(current_year, last_month, last_day)
                    next_dt = last_dt + datetime.timedelta(days=1)
                    sheet_mai = f"{next_dt.day}-{next_dt.month}"
                except:
                    sheet_mai = f"{last_day + 1}-{last_month}"
                    
                tieu_de_6_ngay = danh_sach_tieu_de[-6:]
                while len(tieu_de_6_ngay) < 6:
                    tieu_de_6_ngay.insert(0, "---")

                data_sheet_mai = []
                for i in range(1, 501):
                    dan_mai = get_dan_bot_cached(i, tuple(danh_sach_kq))
                    ls_6 = du_lieu_bot[i]['lich_su_trung'][-6:]
                    while len(ls_6) < 6:
                        ls_6.insert(0, "")
                        
                    row_data_mai = {"STT": i, "THÀNH VIÊN": f"Bot_{i:03d}"}
                    for j in range(6): 
                        row_data_mai[tieu_de_6_ngay[j]] = ls_6[j]
                    row_data_mai["TỔNG ĐIỂM"] = du_lieu_bot[i]['tong_diem']
                    for ten in danh_sach_cot: 
                        row_data_mai[ten] = ",".join(map(str, dan_mai.get(ten, [])))
                    data_sheet_mai.append(row_data_mai)
                
                df_mai = pd.DataFrame(data_sheet_mai).sort_values(by=["TỔNG ĐIỂM", "STT"], ascending=[False, True]).reset_index(drop=True)
                df_mai["STT"] = df_mai.index + 1
                df_mai.to_excel(writer, sheet_name=sheet_mai, index=False)
            
            st.success(f"🎉 Hoàn thành! Hệ thống chỉ xuất {so_ngay_xuat} ngày theo đúng cài đặt.")
            st.download_button("📥 TẢI FILE EXCEL MỚI", data=output.getvalue(), file_name="Bang_Phong_Do_Toi_Uu.xlsx")