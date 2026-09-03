import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
from datetime import datetime

# -------------------------------------------------------------
# 1. ตั้งค่าหน้าตา Web App (Page Config)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Nicha Pjv4 System",
    page_icon="⚙️",
    layout="wide"
)

# -------------------------------------------------------------
# 2. ฟังก์ชันเชื่อมต่อ Google Sheets
# -------------------------------------------------------------
@st.cache_resource
def init_connection():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        json_file_path = "service_account.json"
        
        if os.path.exists(json_file_path):
            creds = Credentials.from_service_account_file(json_file_path, scopes=scope)
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        else:
            st.error("❌ ไม่พบข้อมูลยืนยันตัวตน Google Account")
            return None

        client = gspread.authorize(creds)
        
        target_sheet = st.secrets.get("spreadsheet_name", "Nicha_Pjv4_Database")
        target_sheet_str = str(target_sheet).strip()
        
        if target_sheet_str.startswith("http"):
            spreadsheet = client.open_by_url(target_sheet_str)
        else:
            try:
                spreadsheet = client.open(target_sheet_str)
            except Exception:
                spreadsheet = client.open_by_key(target_sheet_str)
            
        return spreadsheet
    except Exception as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets ได้: {e}")
        return None

sh = init_connection()

def get_or_create_worksheet(spreadsheet, possible_names, default_headers=None):
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
    
    for name in possible_names:
        if name in existing_sheets:
            return spreadsheet.worksheet(name)
            
    new_sheet_name = possible_names[0]
    ws = spreadsheet.add_worksheet(title=new_sheet_name, rows="500", cols="20")
    if default_headers:
        ws.append_row(default_headers)
    return ws

# -------------------------------------------------------------
# 3. ส่วนของ Sidebar (เมนูหลัก)
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/dashboard-layout.png", width=60)
st.sidebar.title("📌 เมนูหลัก")

if sh is not None:
    st.sidebar.success("🟢 เชื่อมต่อ Google Sheet เรียบร้อย")
else:
    st.sidebar.error("🔴 ยังไม่ได้เชื่อมต่อ Google Sheet")

menu = st.sidebar.radio(
    "เลือกหน้าการทำงาน:",
    [
        "📊 Dashboard สรุปรายเดือน",
        "🟢 ลงทะเบียนพนักงานใหม่",
        "🟢 บันทึกงานประจำวัน (Admin)",
        "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ"
    ]
)

# -------------------------------------------------------------
# 4. การจัดการแต่ละหน้าตามเมนู
# -------------------------------------------------------------

# =========================================================
# หน้าที่ 1: Dashboard สรุปรายเดือน
# =========================================================
if menu == "📊 Dashboard สรุปรายเดือน":
    st.title("📊 Dashboard สรุปรายเดือน")
    
    if sh is not None:
        try:
            ws_daily = get_or_create_worksheet(
                sh, 
                ["บันทึกงานประจำวัน", "งานประจำวัน"], 
                ["วันที่", "แอดมิน", "พนักงาน", "บริการ", "ยอดเงิน", "หมายเหตุ"]
            )
            records = ws_daily.get_all_records()
            
            if records:
                df = pd.DataFrame(records)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📝 รายการบันทึกทั้งหมด", f"{len(df)} รายการ")
                with col2:
                    if "ยอดเงิน" in df.columns:
                        total_income = pd.to_numeric(df["ยอดเงิน"], errors='coerce').sum()
                        st.metric("💰 ยอดเงินรวม", f"{total_income:,.2f} บาท")
                    else:
                        st.metric("💰 ยอดเงินรวม", "0.00 บาท")
                with col3:
                    st.metric("🟢 สถานะระบบ", "พร้อมใช้งาน")
                
                st.markdown("---")
                st.subheader("📋 ตารางรายการบันทึกงานล่าสุด")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("💡 เชื่อมต่อ Google Sheet เรียบร้อยแล้ว แต่ยังไม่มีรายการบันทึกงานประจำวัน")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล Dashboard: {e}")
    else:
        st.error("🔴 ไม่สามารถดึงข้อมูลได้ เนื่องจากยังไม่ได้เชื่อมต่อ Google Sheet")

# =========================================================
# หน้าที่ 2: ลงทะเบียนพนักงานใหม่
# =========================================================
elif menu == "🟢 ลงทะเบียนพนักงานใหม่":
    st.title("🟢 ลงทะเบียนพนักงานใหม่")
    
    if sh is not None:
        try:
            ws_emp = get_or_create_worksheet(
                sh, 
                ["ทะเบียนพนักงาน", "ข้อมูลพนักงาน"], 
                ["วันที่ลงทะเบียน", "รหัสพนักงาน", "ชื่อ-นามสกุล", "ชื่อเล่น", "เบอร์โทรศัพท์", "สาขา", "สถานะ"]
            )
            
            with st.form("form_register_employee"):
                st.subheader("📝 กรอกข้อมูลพนักงานใหม่")
                col_e1, col_e2 = st.columns(2)
                
                with col_e1:
                    emp_id = st.text_input("🆔 รหัสพนักงาน *")
                    emp_fullname = st.text_input("👤 ชื่อ-นามสกุล *")
                    emp_nickname = st.text_input("💬 ชื่อเล่น")
                    
                with col_e2:
                    emp_phone = st.text_input("📞 เบอร์โทรศัพท์")
                    emp_branch = st.text_input("สาขา")
                    emp_status = st.selectbox("📌 สถานะพนักงาน", ["ทำงานอยู่", "ลาหยุด", "พ้นสภาพ"])
                    
                submit_emp = st.form_submit_button("➕ บันทึกลงทะเบียนพนักงาน", use_container_width=True)
                
                if submit_emp:
                    if not emp_id or not emp_fullname:
                        st.error("⚠️ กรุณากรอกรหัสพนักงานและชื่อ-นามสกุลให้ครบถ้วน")
                    else:
                        reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        new_emp_data = [reg_date, emp_id, emp_fullname, emp_nickname, emp_phone, emp_branch, emp_status]
                        ws_emp.append_row(new_emp_data)
                        st.success(f"✅ บันทึกพนักงาน '{emp_fullname}' เรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 รายชื่อพนักงานทั้งหมด")
            emp_vals = ws_emp.get_all_values()
            if len(emp_vals) > 1:
                df_emp = pd.DataFrame(emp_vals[1:], columns=emp_vals[0])
                st.dataframe(df_emp, use_container_width=True)
            else:
                st.info("💡 ยังไม่มีข้อมูลพนักงานในระบบ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการลงทะเบียนพนักงาน: {e}")

# =========================================================
# หน้าที่ 3: บันทึกงานประจำวัน (Admin)
# =========================================================
elif menu == "🟢 บันทึกงานประจำวัน (Admin)":
    st.title("🟢 บันทึกงานประจำวัน (Admin)")
    
    if sh is not None:
        try:
            ws_daily = get_or_create_worksheet(
                sh, 
                ["บันทึกงานประจำวัน", "งานประจำวัน"], 
                ["วันที่-เวลา", "แอดมินผู้บันทึก", "ชื่อพนักงาน", "บริการ/รายการ", "ยอดเงิน", "หมายเหตุ"]
            )
            
            with st.form("form_daily_work"):
                st.subheader("📝 ฟอร์มบันทึกการทำงานประจำวัน")
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    admin_name = st.text_input("👤 ชื่อแอดมินผู้บันทึก *")
                    emp_name = st.text_input("👤 ชื่อพนักงาน *")
                    service_detail = st.text_input("⚙️ บริการ / รายการงาน *")
                    
                with col_d2:
                    amount = st.number_input("💰 ยอดเงิน (บาท)", min_value=0.0, step=100.0)
                    note = st.text_area("📝 หมายเหตุเพิ่มเติม")
                    
                submit_daily = st.form_submit_button("💾 บันทึกงานประจำวัน", use_container_width=True)
                
                if submit_daily:
                    if not admin_name or not emp_name or not service_detail:
                        st.error("⚠️ กรุณากรอกชื่อแอดมิน พนักงาน และรายการบริการให้ครบถ้วน")
                    else:
                        work_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        daily_data = [work_time, admin_name, emp_name, service_detail, amount, note]
                        ws_daily.append_row(daily_data)
                        st.success("✅ บันทึกงานประจำวันเรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 ประวัติการบันทึกงานประจำวัน")
            daily_vals = ws_daily.get_all_values()
            if len(daily_vals) > 1:
                df_daily = pd.DataFrame(daily_vals[1:], columns=daily_vals[0])
                st.dataframe(df_daily, use_container_width=True)
            else:
                st.info("💡 ยังไม่มีประวัติการบันทึกงานประจำวัน")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกงานประจำวัน: {e}")

# =========================================================
# หน้าที่ 4: [Owner Only] จัดการตั้งค่า & ค่าบริการ
# =========================================================
elif menu == "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ":
    st.title("👑 [Owner Only] ระบบจัดการข้อมูลตั้งค่า & อัตราค่าบริการ")

    tab_form1, tab_form2, tab_form3 = st.tabs([
        "1️⃣ ข้อมูลเบื้องต้น",
        "2️⃣ ปรับเปลี่ยนราคาค่าบริการ",
        "3️⃣ บันทึกรายการค่าใช้จ่าย"
    ])

    # --- ฟอร์มที่ 1: ข้อมูลเบื้องต้น ---
    with tab_form1:
        st.subheader("1️⃣ ฟอร์มข้อมูลเบื้องต้น")
        if sh is not None:
            try:
                fixed_headers = [
                    "สาขา",
                    "ชื่อแอดมิน",
                    "เปอร์เซ็นต์ส่วนแบ่งค่ารอบ",
                    "เปอร์เซ็นต์ค่าโปรโมท",
                    "เปอร์เซ็นต์ส่วนแบ่งเงิน agency",
                    "ชื่อ agency"
                ]

                ws_info = get_or_create_worksheet(sh, ["ข้อมูลเบื้องต้น"], fixed_headers)
                all_vals = ws_info.get_all_values()

                if len(all_vals) == 0:
                    ws_info.append_row(fixed_headers)
                    all_vals = [fixed_headers]

                label_a, label_b, label_c, label_d, label_e, label_f = fixed_headers

                st.write("📝 **กรอกรายละเอียดข้อมูลเบื้องต้น**")
                mode = st.radio("เลือกรูปแบบการบันทึก:", ["➕ เพิ่มข้อมูลใหม่ (ต่อแถวล่างสุด)", "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม"], horizontal=True)
                
                row_to_edit = None
                default_a, default_b, default_c, default_d, default_e, default_f = "", "", "", "", "", ""

                data_rows = all_vals[1:] if len(all_vals) > 1 else []

                if mode == "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม" and len(data_rows) > 0:
                    row_options = [f"แถวที่ {idx+2}: {row[0] if len(row)>0 else ''} - {row[1] if len(row)>1 else ''}" for idx, row in enumerate(data_rows)]
                    selected_option = st.selectbox("🎯 เลือกแถวที่ต้องการแก้ไขข้อมูล:", row_options)
                    
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
                            ws_info.update(f"A{row_to_edit}:F{row_to_edit}", [new_data])
                            st.success(f"✅ แก้ไขและบันทึกทับข้อมูลในแถวที่ {row_to_edit} เรียบร้อยแล้ว!")
                        else:
                            ws_info.append_row(new_data)
                            st.success("✅ บันทึกเพิ่มข้อมูลใหม่ต่อแถวล่างสุดเรียบร้อยแล้ว!")
                        
                        st.rerun()

                st.markdown("---")
                st.subheader(f"📋 ตารางข้อมูลเบื้องต้นทั้งหมด (แท็บ: {ws_info.title})")
                
                if len(data_rows) > 0:
                    df_display = pd.DataFrame(data_rows)
                    df_display = df_display.iloc[:, :6]
                    df_display.columns = fixed_headers[:df_display.shape[1]]
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.info("💡 ยังไม่มีข้อมูลในแท็บ 'ข้อมูลเบื้องต้น'")

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มข้อมูลเบื้องต้น: {ex}")

    # --- ฟอร์มที่ 2: ปรับเปลี่ยนราคาค่าบริการ ---
    with tab_form2:
        st.subheader("2️⃣ ฟอร์มปรับแต่งราคาค่าบริการ")
        if sh is not None:
            try:
                ws_svc = get_or_create_worksheet(
                    sh,
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

    # --- ฟอร์มที่ 3: บันทึกรายการค่าใช้จ่าย ---
    with tab_form3:
        st.subheader("3️⃣ ฟอร์มบันทึกรายการค่าใช้จ่าย")
        if sh is not None:
            try:
                ws_set = get_or_create_worksheet(sh, ["ข้อมูลตั้งค่า", "มูลตั้งค่า"], ["รายการค่าใช้จ่าย", "ประเภทค่าใช้จ่าย"])

                with st.form("form_owner_3"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        exp_item = st.text_input("📝 รายการค่าใช้จ่าย *")
                    with col_e2:
                        exp_type = st.selectbox("🏷️ ประเภทค่าใช้จ่าย", ["ค่าใช้จ่ายประจำ", "ค่าอุปกรณ์/ซ่อมบำรุง", "ค่าการตลาด/โปรโมท", "ค่าน้ำ/ค่าไฟ", "อื่นๆ"])

                    submit_f3 = st.form_submit_button("💾 บันทึกค่าใช้จ่ายลง Google Sheet", use_container_width=True)

                    if submit_f3:
                        if not exp_item:
                            st.error("⚠️ กรุณาระบุรายการค่าใช้จ่ายก่อนบันทึกครับ")
                        else:
                            ws_set.append_row([exp_item, exp_type])
                            st.success(f"✅ บันทึกรายการ '{exp_item}' เรียบร้อยแล้ว!")
                            st.rerun()

                st.markdown("---")
                set_vals = ws_set.get_all_values()
                if len(set_vals) > 0:
                    df_set = pd.DataFrame(set_vals[1:], columns=set_vals[0]) if len(set_vals) > 1 else pd.DataFrame(set_vals)
                    st.dataframe(df_set, use_container_width=True)

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 3: {ex}")
