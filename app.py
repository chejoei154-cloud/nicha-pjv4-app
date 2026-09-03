import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ตั้งค่าหน้าตา Web App
st.set_page_config(
    page_title="Nicha Pjv4 System", 
    layout="wide", 
    page_icon="⚙️",
    initial_sidebar_state="expanded"
)

st.title("⚙️ Nicha Pjv4 - ระบบบริหารจัดการ & บันทึกงาน")

# เชื่อมต่อ Google Sheets
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

sh = None
try:
    gc = init_gspread()
    sh = gc.open("Nicha Pjv4 phyton")
    st.sidebar.success("🟢 เชื่อมต่อ Google Sheet เรียบร้อย")
except Exception as e:
    st.sidebar.error("🔴 พบข้อผิดพลาดในการเชื่อมต่อ")
    st.error(f"⚠️ รายละเอียดข้อผิดพลาด: {e}")

# ฟังก์ชันดึง Worksheet แบบการันตี (ถ้าไม่มีแท็บ ให้สร้างให้อัตโนมัติ)
def get_or_create_worksheet(sheet_names, default_headers=None):
    if sh is None:
        return None
    
    # ลองหาชื่อแท็บตามรายการที่ส่งมา
    all_worksheets = [ws.title for ws in sh.worksheets()]
    for name in sheet_names:
        if name in all_worksheets:
            return sh.worksheet(name)
            
    # ถ้าหาไม่เจอเลย ให้สร้างแท็บใหม่ด้วยชื่อแรก
    primary_name = sheet_names[0]
    new_ws = sh.add_worksheet(title=primary_name, rows=100, cols=20)
    if default_headers:
        new_ws.append_row(default_headers)
    return new_ws

# เมนูหลัก
menu = st.sidebar.radio(
    "📌 เมนูหลัก", 
    [
        "📊 Dashboard สรุปรายเดือน", 
        "🟢 ลงทะเบียนพนักงานใหม่", 
        "🟢 บันทึกงานประจำวัน (Admin)",
        "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ"
    ]
)

# ฟังก์ชันดึงรายการไปใส่ Dropdown
def get_setting_list(possible_sheets, col_idx=0, default_list=[]):
    ws = get_or_create_worksheet(possible_sheets)
    if ws:
        try:
            data = ws.get_all_values()
            if len(data) > 1:
                items = [row[col_idx].strip() for row in data[1:] if len(row) > col_idx and row[col_idx].strip() != ""]
                if items:
                    return list(dict.fromkeys(items)) # ลบตัวซ้ำ
        except:
            pass
    return default_list

# -------------------------------------------------------------
# 1. หน้า Dashboard สรุปรายเดือน
# -------------------------------------------------------------
if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    if sh is not None:
        try:
            ws_sum = get_or_create_worksheet(["สรุปรายเดือน"])
            val_total = ws_sum.acell("A4").value or "0.00" if ws_sum else "0.00"
            val_shop = ws_sum.acell("D4").value or "0.00" if ws_sum else "0.00"
            val_owner = ws_sum.acell("G4").value or "0.00" if ws_sum else "0.00"
            val_agency = ws_sum.acell("A8").value or "0.00" if ws_sum else "0.00"

            ws_calc = get_or_create_worksheet(["คำนวณ"])
            raw_data = ws_calc.get_all_values() if ws_calc else []

            total_admin = 0.0
            emp_set = set()
            total_rounds = 0

            if len(raw_data) > 1:
                headers = raw_data[0]
                rows = raw_data[1:]
                total_rounds = len(rows)

                admin_col_idx = -1
                emp_col_idx = -1

                for idx, h in enumerate(headers):
                    h_clean = str(h).strip().lower()
                    if "ส่วนแบ่ง admin" in h_clean or "ส่วนแบ่งadmin" in h_clean:
                        admin_col_idx = idx
                    if "พนักงาน" in h_clean or "ชื่อพนักงาน" in h_clean or "empid" in h_clean:
                        if emp_col_idx == -1:
                            emp_col_idx = idx

                for r in rows:
                    if admin_col_idx != -1 and len(r) > admin_col_idx:
                        try:
                            val_str = str(r[admin_col_idx]).replace(',', '').replace('฿', '').strip()
                            total_admin += float(val_str) if val_str else 0.0
                        except:
                            pass
                    
                    if emp_col_idx != -1 and len(r) > emp_col_idx:
                        emp_name = str(r[emp_col_idx]).strip()
                        if emp_name and emp_name.lower() != 'none':
                            emp_set.add(emp_name)

            try:
                tot_num = float(str(val_total).replace(',', '').replace('฿', '').strip())
                avg_num = tot_num / total_rounds if total_rounds > 0 else 0.0
            except:
                avg_num = 0.0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 รายได้รวมทั้งหมด", f"{val_total} THB" if "THB" not in str(val_total) else val_total)
            c2.metric("🏠 รายได้ร้าน", f"{val_shop} THB" if "THB" not in str(val_shop) else val_shop)
            c3.metric("👑 รายได้ Owner", f"{val_owner} THB" if "THB" not in str(val_owner) else val_owner)
            c4.metric("👔 รายได้ Admin", f"฿{total_admin:,.2f} THB")

            st.markdown("---")

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("🤝 รายได้เอเจนซี่", f"{val_agency} THB" if "THB" not in str(val_agency) else val_agency)
            c6.metric("🔄 จำนวนรอบ", f"{total_rounds} รอบ")
            c7.metric("👥 จำนวนพนักงาน", f"{len(emp_set)} คน")
            c8.metric("📊 รายได้เฉลี่ย/รอบ", f"฿{avg_num:,.2f} THB")

            st.markdown("---")
            st.subheader("📋 ตารางข้อมูลคำนวณทั้งหมด")
            if len(raw_data) > 1:
                df_display = pd.DataFrame(raw_data[1:])
                df_display.columns = [f"{h} ({i+1})" if raw_data[0].count(h) > 1 else h for i, h in enumerate(raw_data[0])]
                st.dataframe(df_display, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {ex}")

# -------------------------------------------------------------
# 2. หน้าลงทะเบียนพนักงานใหม่
# -------------------------------------------------------------
elif menu == "🟢 ลงทะเบียนพนักงานใหม่":
    st.header("👤 ฟอร์มลงทะเบียนพนักงานใหม่ (แท็บ: พนักงาน)")

    if sh is not None:
        try:
            ws_emp = get_or_create_worksheet(["พนักงาน"], ["EmpID", "ชื่อ-นามสกุล", "เวลาทำงาน", "ประเภทพนักงาน", "เอเจนซี่", "มัดจำ", "วันมัดจำ", "วันเริ่มงาน", "ค่าโปรโมท", "สถานะ"])
            emp_data = ws_emp.get_all_values()
            
            next_id_num = len(emp_data)
            auto_emp_id = f"EMP{next_id_num:03d}"

            agencies = get_setting_list(["ข้อมูลตั้งค่า", "มูลตั้งค่า", "สาขา"], col_idx=2, default_list=["Agency A", "Agency B"])

            with st.form("emp_reg_form"):
                col1, col2 = st.columns(2)

                with col1:
                    st.text_input("🆔 รหัสพนักงาน (EmpID)", value=auto_emp_id, disabled=True)
                    emp_name = st.text_input("ชื่อ-นามสกุล / ชื่อเล่นพนักงาน *")
                    
                    work_time_type = st.radio("⏰ ประเภทเวลาทำงาน", ["เวลาปกติ (11:00 - 14:00 น.)", "กำหนดเวลาเอง"])
                    if work_time_type == "กำหนดเวลาเอง":
                        time_in = st.time_input("เวลาเข้างาน", value=datetime.strptime("11:00", "%H:%M").time())
                        time_out = st.time_input("เวลาเลิกงาน", value=datetime.strptime("14:00", "%H:%M").time())
                        time_str = f"{time_in.strftime('%H:%M')} - {time_out.strftime('%H:%M')}"
                    else:
                        time_str = "11:00 - 14:00"

                    emp_type = st.selectbox("🏷️ ประเภทพนักงาน", ["พนักงานปกติ", "พนักงาน Agency"])
                    agency_name = "-"
                    if emp_type == "พนักงาน Agency":
                        agency_name = st.selectbox("🏢 เลือกชื่อ Agency", agencies)

                with col2:
                    deposit_option = st.selectbox("💰 เงินมัดจำ", ["ไม่มีค่ามัดจำ", "500", "1,000"])
                    deposit_date = st.date_input("📅 วันที่รับมัดจำ", value=date.today())
                    start_date = st.date_input("🚀 วันเริ่มงาน", value=date.today())
                    
                    promo_option = st.selectbox("📢 ค่าโปรโมท / ค่าป้าย", ["ไม่มีค่าโปรโมท", "1,000", "2,000"])
                    status_option = st.selectbox("📌 สถานะการทำงาน", ["ทำงาน", "รอเริ่มงาน", "จบงาน", "ไม่มาทำงาน"])

                submit_emp = st.form_submit_button("💾 บันทึกข้อมูลพนักงานเข้า Google Sheet", use_container_width=True)

                if submit_emp:
                    if not emp_name:
                        st.error("⚠️ กรุณากรอกชื่อพนักงานก่อนบันทึกครับ")
                    else:
                        new_row = [
                            auto_emp_id, emp_name, time_str, emp_type, agency_name,
                            deposit_option, str(deposit_date) if deposit_option != "ไม่มีค่ามัดจำ" else "-",
                            str(start_date), promo_option, status_option
                        ]
                        ws_emp.append_row(new_row)
                        st.success(f"✅ บันทึกข้อมูล {emp_name} ({auto_emp_id}) เรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 รายชื่อพนักงานที่ลงทะเบียนแล้ว")
            if len(emp_data) > 1:
                df_emp = pd.DataFrame(emp_data[1:], columns=emp_data[0])
                st.dataframe(df_emp, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลพนักงาน: {ex}")

# -------------------------------------------------------------
# 3. หน้าบันทึกงานประจำวัน
# -------------------------------------------------------------
elif menu == "🟢 บันทึกงานประจำวัน (Admin)":
    st.header("📝 บันทึกงานประจำวัน ( Admin )")

    if sh is not None:
        try:
            ws_emp = get_or_create_worksheet(["พนักงาน"])
            emp_rows = ws_emp.get_all_values() if ws_emp else []
            
            emp_options = []
            if len(emp_rows) > 1:
                for r in emp_rows[1:]:
                    if len(r) > 1 and r[1]:
                        emp_options.append(f"{r[0]} - {r[1]}")
            
            if not emp_options:
                emp_options = ["ไม่มีข้อมูลพนักงาน"]

            branches = get_setting_list(["ข้อมูลตั้งค่า", "มูลตั้งค่า", "สาขา"], col_idx=0, default_list=["ประจวบคีรีขันธ์", "ราชบุรี"])
            admins = get_setting_list(["ข้อมูลตั้งค่า", "มูลตั้งค่า", "แอดมิน"], col_idx=1, default_list=["Admin 1", "Admin 2"])
            services = get_setting_list(["ค่าบริการ"], col_idx=0, default_list=["40 นาที", "60 นาที", "90 นาที"])

            with st.form("job_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    date_input = st.date_input("วันที่บันทึกงาน", value=date.today())
                    selected_emp = st.selectbox("👤 เลือกพนักงาน (EmpID - ชื่อ)", emp_options)
                    selected_admin = st.selectbox("👔 ผู้บันทึกงาน (Admin)", admins)
                    branch = st.selectbox("🏢 สาขา", branches)

                with col_f2:
                    service = st.selectbox("⏱️ เลือกรอบ / บริการ", services)
                    job_status = st.selectbox("📌 สถานะงาน", ["ทำงานจบงาน", "ยกเลิกงาน", "ไม่มาทำงาน"])

                submitted = st.form_submit_button("💾 บันทึกงานเข้า Google Sheet", use_container_width=True)
                
                if submitted:
                    emp_id_val = selected_emp.split(" - ")[0] if " - " in selected_emp else ""
                    emp_name_val = selected_emp.split(" - ")[1] if " - " in selected_emp else selected_emp

                    ws_job = get_or_create_worksheet(["บันทึกงาน"], ["วันที่", "Admin", "EmpID", "ชื่อพนักงาน", "สาขา", "บริการ", "สถานะ"])
                    ws_job.append_row([
                        str(date_input), selected_admin, emp_id_val, emp_name_val, branch, service, job_status
                    ])
                    st.success("✅ บันทึกงานเข้าแท็บ 'บันทึกงาน' เรียบร้อยแล้ว!")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกงาน: {ex}")
# -------------------------------------------------------------
# 4. หน้าสำหรับ OWNER (จัดการ 3 ฟอร์มหลัก)
# -------------------------------------------------------------
elif menu == "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ":
    st.header("👑 [Owner Only] ระบบจัดการข้อมูลตั้งค่า & อัตราค่าบริการ")

    tab_form1, tab_form2, tab_form3 = st.tabs([
        "1️⃣ ลงทะเบียนสาขา & แอดมิน (แท็บ: สาขาบวกแอดมิน)", 
        "2️⃣ ปรับเปลี่ยนราคาค่าบริการ (เขียนทับ)", 
        "3️⃣ บันทึกรายการค่าใช้จ่าย (คอลัมน์ A-B)"
    ])
    # ---------------------------------------------------------
    # ฟอร์มที่ 1: ข้อมูลเบื้องต้น (เพิ่ม/แก้ไขข้อมูลตามชื่อหัวข้อ Row 1 Col A-F)
    # ---------------------------------------------------------
    with tab_form1:
        st.subheader("1️⃣ ข้อมูลเบื้องต้น")
        if sh is not None:
            try:
                # เชื่อมต่อแท็บ "ข้อมูลเบื้องต้น"
                ws_info = get_or_create_worksheet(
                    ["ข้อมูลเบื้องต้น"], 
                    ["สาขา", "ชื่อแอดมิน", "เปอร์เซ็นต์ส่วนแบ่งค่ารอบ", "เปอร์เซ็นต์ค่าโปรโมท", "เปอร์เซ็นต์ส่วนแบ่งเงิน agency", "ชื่อ agency"]
                )
                
                # ดึงข้อมูลทั้งหมดในชีท
                all_vals = ws_info.get_all_values()
                
                # ดึงชื่อคอลัมน์ A-F จาก แถวที่ 1 (Row 1)
                headers = all_vals[0] if len(all_vals) > 0 else []
                def get_header(col_idx, default_name):
                    if len(headers) > col_idx and headers[col_idx].strip():
                        return headers[col_idx].strip()
                    return default_name

                label_a = get_header(0, "สาขา")
                label_b = get_header(1, "ชื่อแอดมิน")
                label_c = get_header(2, "เปอร์เซ็นต์ส่วนแบ่งค่ารอบ")
                label_d = get_header(3, "เปอร์เซ็นต์ค่าโปรโมท")
                label_e = get_header(4, "เปอร์เซ็นต์ส่วนแบ่งเงิน agency")
                label_f = get_header(5, "ชื่อ agency")

                # ระบบเลือกโหมด: เพิ่มรายการใหม่ หรือ แก้ไขแถวเดิม
                st.write("📝 **กรอกข้อมูลเบื้องต้น**")
                
                mode = st.radio("เลือกรูปแบบการบันทึก:", ["➕ เพิ่มข้อมูลใหม่ (ต่อแถวล่างสุด)", "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม"], horizontal=True)
                
                row_to_edit = None
                default_a, default_b, default_c, default_d, default_e, default_f = "", "", "", "", "", ""

                # ถ้าเลือกโหมดแก้ไข ให้มี Dropdown ดึงรายการมาให้เลือก
                if mode == "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม" and len(all_vals) > 1:
                    row_options = [f"แถวที่ {idx+1}: {row[0] if len(row)>0 else ''} - {row[1] if len(row)>1 else ''}" for idx, row in enumerate(all_vals[1:], start=1)]
                    selected_option = st.selectbox("🎯 เลือกแถวที่ต้องการแก้ไขข้อมูล:", row_options)
                    
                    # หาเลขแถวใน Google Sheets (index + 1)
                    row_to_edit = int(selected_option.split(":")[0].replace("แถวที่ ", ""))
                    target_row_data = all_vals[row_to_edit - 1]

                    default_a = target_row_data[0] if len(target_row_data) > 0 else ""
                    default_b = target_row_data[1] if len(target_row_data) > 1 else ""
                    default_c = target_row_data[2] if len(target_row_data) > 2 else ""
                    default_d = target_row_data[3] if len(target_row_data) > 3 else ""
                    default_e = target_row_data[4] if len(target_row_data) > 4 else ""
                    default_f = target_row_data[5] if len(target_row_data) > 5 else ""

                with st.form("form_owner_1"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        val_a = st.text_input(f"📌 {label_a}", value=default_a)
                        val_b = st.text_input(f"📌 {label_b}", value=default_b)
                    with col2:
                        val_c = st.text_input(f"📌 {label_c}", value=default_c)
                        val_d = st.text_input(f"📌 {label_d}", value=default_d)
                    with col3:
                        val_e = st.text_input(f"📌 {label_e}", value=default_e)
                        val_f = st.text_input(f"📌 {label_f}", value=default_f)

                    btn_label = "💾 บันทึกทับแถวที่เลือก" if mode == "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม" else "➕ บันทึกเพิ่มข้อมูลต่อแถวล่างสุด"
                    submit_f1 = st.form_submit_button(btn_label, use_container_width=True)

                    if submit_f1:
                        new_data = [val_a, val_b, val_c, val_d, val_e, val_f]
                        
                        if mode == "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม" and row_to_edit:
                            # แก้ไขทับแถวเดิมช่วง Col A ถึง F
                            range_to_update = f"A{row_to_edit}:F{row_to_edit}"
                            ws_info.update(range_to_update, [new_data])
                            st.success(f"✅ แก้ไขและบันทึกทับข้อมูลใน {range_to_update} เรียบร้อยแล้ว!")
                        else:
                            # เพิ่มข้อมูลใหม่ต่อแถวล่างสุด
                            ws_info.append_row(new_data)
                            st.success("✅ บันทึกเพิ่มข้อมูลใหม่ต่อแถวล่างสุดเรียบร้อยแล้ว!")
                        
                        st.rerun()

                st.markdown("---")
                st.subheader(f"📋 ตารางข้อมูลเบื้องต้นทั้งหมด (แท็บ: {ws_info.title} - แสดง คอลัมน์ A ถึง F)")
                
                if len(all_vals) > 0:
                    # แปลงข้อมูลเป็น DataFrame และตัดแสดงเฉพาะคอลัมน์ A ถึง F
                    df_all = pd.DataFrame(all_vals)
                    df_a_f = df_all.iloc[:, :6]
                    
                    # ตั้งชื่อหัวข้อตารางตามแถวที่ 1
                    df_a_f.columns = [label_a, label_b, label_c, label_d, label_e, label_f][:df_a_f.shape[1]]
                    
                    st.dataframe(df_a_f.iloc[1:], use_container_width=True) # แสดงข้อมูลตั้งแต่แถวที่ 2 เป็นต้นไป
                else:
                    st.info("ยังไม่มีข้อมูลในแท็บ 'ข้อมูลเบื้องต้น'")

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มข้อมูลเบื้องต้น: {ex}")

    # ---------------------------------------------------------
    # ฟอร์มที่ 2: ปรับเปลี่ยนราคาค่าบริการ (เขียนทับชีท ค่าบริการ)
    # ---------------------------------------------------------
    with tab_form2:
        st.subheader("2️⃣ ฟอร์มปรับแต่งราคาค่าบริการ (บันทึกเขียนทับชีท 'ค่าบริการ')")
        if sh is not None:
            try:
                ws_svc = get_or_create_worksheet(
                    ["ค่าบริการ"], 
                    ["ชื่อบริการ", "เงินบริการ", "เงินพนักงาน", "เงินร้าน", "เงินเอเจนซี่"]
                )
                svc_vals = ws_svc.get_all_values()

                if len(svc_vals) > 1:
                    headers = svc_vals[0]
                    df_svc = pd.DataFrame(svc_vals[1:], columns=headers)
                    
                    service_col = headers[0]
                    service_names = df_svc[service_col].tolist()

                    selected_svc = st.selectbox("⏱️ เลือกชื่อบริการที่ต้องการปรับเปลี่ยนราคา", service_names)

                    selected_row_idx = service_names.index(selected_svc) + 2
                    row_data = df_svc[df_svc[service_col] == selected_svc].iloc[0]

                    with st.form("form_owner_2"):
                        st.info(f"✏️ กำลังแก้ไขบริการ: **{selected_svc}** (แถวที่ {selected_row_idx})")
                        col_p1, col_p2 = st.columns(2)

                        with col_p1:
                            new_price_total = st.text_input("💰 ราคาเงินบริการ / เงินรวม (บาท)", value=str(row_data.iloc[1]) if len(row_data) > 1 else "0")
                            new_price_emp = st.text_input("👤 เงินพนักงาน (บาท)", value=str(row_data.iloc[2]) if len(row_data) > 2 else "0")

                        with col_p2:
                            new_price_shop = st.text_input("🏠 เงินร้าน (บาท)", value=str(row_data.iloc[3]) if len(row_data) > 3 else "0")
                            new_price_agency = st.text_input("🤝 เงินเอเจนซี่ (บาท)", value=str(row_data.iloc[4]) if len(row_data) > 4 else "0")

                        submit_f2 = st.form_submit_button("🔄 เขียนทับราคาใหม่ลง Google Sheet", use_container_width=True)

                        if submit_f2:
                            ws_svc.update_cell(selected_row_idx, 2, new_price_total)
                            ws_svc.update_cell(selected_row_idx, 3, new_price_emp)
                            ws_svc.update_cell(selected_row_idx, 4, new_price_shop)
                            ws_svc.update_cell(selected_row_idx, 5, new_price_agency)
                            st.success(f"✅ ปรับปรุงราคาของ '{selected_svc}' เรียบร้อยแล้ว!")
                            st.rerun()

                    st.markdown("---")
                    st.write("📋 **ตารางอัตราค่าบริการทั้งหมด**")
                    st.dataframe(df_svc, use_container_width=True)

                else:
                    st.warning("ไม่พบข้อมูลในแท็บ 'ค่าบริการ'")

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 2: {ex}")

    # ---------------------------------------------------------
    # ฟอร์มที่ 3: บันทึกค่าใช้จ่าย (ลงคอลัมน์ A และ B แท็บ ข้อมูลตั้งค่า)
    # ---------------------------------------------------------
    with tab_form3:
        st.subheader("3️⃣ ฟอร์มบันทึกรายการค่าใช้จ่าย (แท็บ 'ข้อมูลตั้งค่า' คอลัมน์ A และ B)")
        if sh is not None:
            try:
                # ฟอร์มนี้ใช้แท็บ "ข้อมูลตั้งค่า" หรือ "มูลตั้งค่า"
                ws_set = get_or_create_worksheet(["ข้อมูลตั้งค่า", "มูลตั้งค่า"])

                with st.form("form_owner_3"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        exp_item = st.text_input("📝 รายการค่าใช้จ่าย (Col A) *")
                    with col_e2:
                        exp_type = st.selectbox("🏷️ ประเภทค่าใช้จ่าย (Col B)", ["ค่าใช้จ่ายประจำ", "ค่าอุปกรณ์/ซ่อมบำรุง", "ค่าการตลาด/โปรโมท", "ค่าน้ำ/ค่าไฟ", "อื่นๆ"])

                    submit_f3 = st.form_submit_button("💾 บันทึกค่าใช้จ่ายลง Google Sheet (Col A-B)", use_container_width=True)

                    if submit_f3:
                        if not exp_item:
                            st.error("⚠️ กรุณาระบุรายการค่าใช้จ่ายก่อนบันทึกครับ")
                        else:
                            ws_set.append_row([exp_item, exp_type])
                            st.success(f"✅ บันทึกรายการ '{exp_item}' ลงคอลัมน์ A-B ในแท็บ '{ws_set.title}' เรียบร้อยแล้ว!")
                            st.rerun()

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 3: {ex}")


