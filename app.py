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

# ฟังก์ชันดึง Sheet โดยอิงจากชื่อแท็บเดิมของคุณแบบเป๊ะๆ (ไม่แอดเพิ่มเอง)
def get_existing_worksheet(spreadsheet, sheet_name):
    try:
        return spreadsheet.worksheet(sheet_name)
    except Exception:
        st.warning(f"⚠️ ไม่พบแท็บชื่อ '{sheet_name}' ใน Google Sheet")
        return None

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
        "🟢 ทะเบียนพนักงาน",
        "🟢 บันทึกงาน (Admin)",
        "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ"
    ]
)

# -------------------------------------------------------------
# 4. การจัดการแต่ละหน้าตามเมนู
# -------------------------------------------------------------

# =========================================================
# หน้าที่ 1: Dashboard สรุปรายเดือน (ดึงจากแท็บ 'สรุปรายเดือน')
# =========================================================
if menu == "📊 Dashboard สรุปรายเดือน":
    st.title("📊 Dashboard สรุปรายเดือน")
    
    if sh is not None:
        try:
            ws_monthly = get_existing_worksheet(sh, "สรุปรายเดือน")
            if ws_monthly:
                vals = ws_monthly.get_all_values()
                if vals:
                    df = pd.DataFrame(vals)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("💡 แท็บ 'สรุปรายเดือน' ยังไม่มีข้อมูล")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลด Dashboard: {e}")

# =========================================================
# หน้าที่ 2: ทะเบียนพนักงาน (ดึงจากแท็บ 'พนักงาน')
# =========================================================
elif menu == "🟢 ทะเบียนพนักงาน":
    st.title("🟢 รายชื่อและลงทะเบียนพนักงาน")
    
    if sh is not None:
        try:
            ws_emp = get_existing_worksheet(sh, "พนักงาน")
            if ws_emp:
                emp_vals = ws_emp.get_all_values()
                
                # แสดงตารางข้อมูลเดิมก่อน
                st.subheader("📋 รายชื่อพนักงานทั้งหมดในระบบ")
                if len(emp_vals) > 0:
                    df_emp = pd.DataFrame(emp_vals[1:], columns=emp_vals[0]) if len(emp_vals) > 1 else pd.DataFrame(emp_vals)
                    st.dataframe(df_emp, use_container_width=True)
                
                st.markdown("---")
                
                # ฟอร์มเพิ่มข้อมูลพนักงาน
                with st.form("form_add_employee"):
                    st.subheader("➕ ลงทะเบียนพนักงานใหม่")
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        emp_name = st.text_input("ชื่อ-นามสกุล/ชื่อเล่น *")
                        emp_phone = st.text_input("เบอร์โทรศัพท์")
                    with col_e2:
                        emp_branch = st.text_input("สาขา")
                        emp_status = st.selectbox("สถานะ", ["ทำงาน", "จบงาน", "ลาหยุด"])
                        
                    submit_emp = st.form_submit_button("💾 บันทึกลง Google Sheet", use_container_width=True)
                    if submit_emp:
                        if emp_name:
                            ws_emp.append_row([emp_name, emp_phone, emp_branch, emp_status])
                            st.success("✅ บันทึกเรียบร้อย!")
                            st.rerun()
                        else:
                            st.error("กรุณากรอกชื่อพนักงาน")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# =========================================================
# หน้าที่ 3: บันทึกงาน (Admin) (ดึงจากแท็บ 'บันทึกงาน')
# =========================================================
elif menu == "🟢 บันทึกงาน (Admin)":
    st.title("🟢 บันทึกงานประจำวัน (Admin)")
    
    if sh is not None:
        try:
            ws_work = get_existing_worksheet(sh, "บันทึกงาน")
            if ws_work:
                work_vals = ws_work.get_all_values()
                
                st.subheader("📋 ประวัติการบันทึกงานทั้งหมด")
                if len(work_vals) > 0:
                    df_work = pd.DataFrame(work_vals[1:], columns=work_vals[0]) if len(work_vals) > 1 else pd.DataFrame(work_vals)
                    st.dataframe(df_work, use_container_width=True)
                
                st.markdown("---")
                st.info("💡 สามารถกรอกข้อมูลบันทึกงานผ่านหน้าตาราง หรือใช้ฟอร์มบันทึกข้อมูลเพิ่มได้")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# =========================================================
# หน้าที่ 4: [Owner Only] จัดการตั้งค่า & ค่าบริการ (ดึงจาก 'ข้อมูลเบื้องต้น' และ 'ค่าบริการ')
# =========================================================
elif menu == "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ":
    st.title("👑 [Owner Only] ระบบจัดการข้อมูลตั้งค่า & อัตราค่าบริการ")

    tab1, tab2, tab3 = st.tabs(["1️⃣ ข้อมูลเบื้องต้น", "2️⃣ ค่าบริการ", "3️⃣ ข้อมูลตั้งค่า"])

    with tab1:
        st.subheader("📋 ข้อมูลเบื้องต้น")
        ws_info = get_existing_worksheet(sh, "ข้อมูลเบื้องต้น")
        if ws_info:
            info_vals = ws_info.get_all_values()
            if len(info_vals) > 0:
                df_info = pd.DataFrame(info_vals[1:], columns=info_vals[0]) if len(info_vals) > 1 else pd.DataFrame(info_vals)
                st.dataframe(df_info, use_container_width=True)

    with tab2:
        st.subheader("📋 ตารางค่าบริการ")
        ws_svc = get_existing_worksheet(sh, "ค่าบริการ")
        if ws_svc:
            svc_vals = ws_svc.get_all_values()
            if len(svc_vals) > 0:
                df_svc = pd.DataFrame(svc_vals[1:], columns=svc_vals[0]) if len(svc_vals) > 1 else pd.DataFrame(svc_vals)
                st.dataframe(df_svc, use_container_width=True)

    with tab3:
        st.subheader("📋 ข้อมูลตั้งค่า")
        ws_cfg = get_existing_worksheet(sh, "ข้อมูลตั้งค่า")
        if ws_cfg:
            cfg_vals = ws_cfg.get_all_values()
            if len(cfg_vals) > 0:
                df_cfg = pd.DataFrame(cfg_vals[1:], columns=cfg_vals[0]) if len(cfg_vals) > 1 else pd.DataFrame(cfg_vals)
                st.dataframe(df_cfg, use_container_width=True)
