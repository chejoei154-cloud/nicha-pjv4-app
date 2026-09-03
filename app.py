import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# -------------------------------------------------------------
# 1. ตั้งค่าหน้าตา Web App (Page Config)
# -------------------------------------------------------------
st.set_page_config(
    page_title="Nicha Pjv4 System",
    page_icon="⚙️",
    layout="wide"
)

# -------------------------------------------------------------
# 2. ฟังก์ชันเชื่อมต่อ Google Sheets & ดึง/สร้าง Worksheet
# -------------------------------------------------------------
@st.cache_resource
def init_connection():
    try:
        # ดึง Credentials จาก Streamlit Secrets และแปลงรูปแบบ private_key ให้ถูกต้อง
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            # แก้ไขเรื่อง \n และจัดฟอร์แมต private key ให้เป็นสเปกมาตรฐานของ PEM
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=scope
        )
        client = gspread.authorize(creds)
        
        # ดึงค่าเป้าหมายจาก Secrets
        target_sheet = st.secrets.get("spreadsheet_name", "Nicha_Pjv4_Database")
        target_sheet_str = str(target_sheet).strip()
        
        # ตรวจสอบรูปแบบเพื่อเปิด Google Sheet ให้ถูกต้อง
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
    """ฟังก์ชันช่วยค้นหาแท็บ หรือสร้างแท็บใหม่ถ้ายังไม่มี"""
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
    
    # 1. ลองหาแท็บตามชื่อที่ต้องการ
    for name in possible_names:
        if name in existing_sheets:
            return spreadsheet.worksheet(name)
            
    # 2. ถ้าหาไม่เจอ ให้สร้างแท็บใหม่ด้วยชื่อแรกในรายการ
    new_sheet_name = possible_names[0]
    ws = spreadsheet.add_worksheet(title=new_sheet_name, rows="100", cols="20")
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

# --- หน้าที่ 1: Dashboard ---
if menu == "📊 Dashboard สรุปรายเดือน":
    st.title("📊 Dashboard สรุปรายเดือน")
    st.info("ระบบกำลังเตรียมความพร้อมสำหรับการแสดงผลรายงานสรุปประจำเดือน...")

# --- หน้าที่ 2: ลงทะเบียนพนักงาน ---
elif menu == "🟢 ลงทะเบียนพนักงานใหม่":
    st.title("🟢 ลงทะเบียนพนักงานใหม่")
    st.info("แบบฟอร์มลงทะเบียนข้อมูลพนักงานใหม่เข้าสู่ระบบ...")

# --- หน้าที่ 3: บันทึกงานประจำวัน ---
elif menu == "🟢 บันทึกงานประจำวัน (Admin)":
    st.title("🟢 บันทึกงานประจำวัน (Admin)")
    st.info("แบบฟอร์มสำหรับแอดมินบันทึกการทำงานประจำวัน...")

# --- หน้าที่ 4: OWNER ONLY (ระบบจัดการหลัก 3 ฟอร์ม) ---
elif menu == "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ":
    st.title("👑 [Owner Only] ระบบจัดการข้อมูลตั้งค่า & อัตราค่าบริการ")

    # แท็บแบ่ง 3 ฟอร์มหลัก
    tab_form1, tab_form2, tab_form3 = st.tabs([
        "1️⃣ ข้อมูลเบื้องต้น",
        "2️⃣ ปรับเปลี่ยนราคาค่าบริการ",
        "3️⃣ บันทึกรายการค่าใช้จ่าย"
    ])

    # =========================================================
    # ฟอร์มที่ 1: ข้อมูลเบื้องต้น
    # =========================================================
    with tab_form1:
        st.subheader("1️⃣ ฟอร์มข้อมูลเบื้องต้น")
        if sh is not None:
            try:
                # กำหนดชื่อหัวข้อ คอลัมน์ A ถึง F
                fixed_headers = [
                    "สาขา",
                    "ชื่อแอดมิน",
                    "เปอร์เซ็นต์ส่วนแบ่งค่ารอบ",
                    "เปอร์เซ็นต์ค่าโปรโมท",
                    "เปอร์เซ็นต์ส่วนแบ่งเงิน agency",
                    "ชื่อ agency"
                ]

                # ดึง/สร้างแท็บ "ข้อมูลเบื้องต้น"
                ws_info = get_or_create_worksheet(sh, ["ข้อมูลเบื้องต้น"], fixed_headers)
                
                # ดึงข้อมูลทั้งหมดในแท็บ
                all_vals = ws_info.get_all_values()

                # กรณีชีทว่าง ให้ใส่ แถวที่ 1 เป็น Header ทันที
                if len(all_vals) == 0:
                    ws_info.append_row(fixed_headers)
                    all_vals = [fixed_headers]

                label_a, label_b, label_c, label_d, label_e, label_f = fixed_headers

                st.write("📝 **กรอกรายละเอียดข้อมูลเบื้องต้น**")
                mode = st.radio("เลือกรูปแบบการบันทึก:", ["➕ เพิ่มข้อมูลใหม่ (ต่อแถวล่างสุด)", "✏️ แก้ไข/ปรับปรุงข้อมูลเดิม"], horizontal=True)
                
                row_to_edit = None
                default_a, default_b, default_c, default_d, default_e, default_f = "", "", "", "", "", ""

                # ข้อมูลรายการตั้งแต่แถวที่ 2 เป็นต้นไป
                data_rows = all_vals[1:] if len(all_vals) > 1 else []

                # หากเลือกโหมดแก้ไขข้อมูล ให้เลือกแถวที่ต้องการแก้ไข
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
                st.subheader(f"📋 ตารางข้อมูลเบื้องต้นทั้งหมด (แท็บ: {ws_info.title} - แสดง คอลัมน์ A ถึง F)")
                
                # แสดงผลตารางเฉพาะคอลัมน์ A ถึง F
                if len(data_rows) > 0:
                    df_display = pd.DataFrame(data_rows)
                    df_display = df_display.iloc[:, :6] # ดึงเฉพาะ 6 คอลัมน์แรก
                    df_display.columns = fixed_headers[:df_display.shape[1]]
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.info("💡 ยังไม่มีข้อมูลในแท็บ 'ข้อมูลเบื้องต้น' (กรอกข้อมูลด้านบนแล้วกดบันทึกเพื่อเพิ่มข้อมูลลงตาราง)")

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มข้อมูลเบื้องต้น: {ex}")

    # =========================================================
    # ฟอร์มที่ 2: ปรับเปลี่ยนราคาค่าบริการ
    # =========================================================
    with tab_form2:
        st.subheader("2️⃣ ฟอร์มปรับแต่งราคาค่าบริการ (บันทึกเขียนทับชีท 'ค่าบริการ')")
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

    # =========================================================
    # ฟอร์มที่ 3: บันทึกรายการค่าใช้จ่าย
    # =========================================================
    with tab_form3:
        st.subheader("3️⃣ ฟอร์มบันทึกรายการค่าใช้จ่าย (แท็บ 'ข้อมูลตั้งค่า' คอลัมน์ A และ B)")
        if sh is not None:
            try:
                ws_set = get_or_create_worksheet(sh, ["ข้อมูลตั้งค่า", "มูลตั้งค่า"], ["รายการค่าใช้จ่าย", "ประเภทค่าใช้จ่าย"])

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

                st.markdown("---")
                set_vals = ws_set.get_all_values()
                if len(set_vals) > 0:
                    df_set = pd.DataFrame(set_vals[1:], columns=set_vals[0]) if len(set_vals) > 1 else pd.DataFrame(set_vals)
                    st.dataframe(df_set, use_container_width=True)

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 3: {ex}")
