import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. ตั้งค่าหน้าตา Web App ให้กว้างเต็มจอ (layout="wide")
st.set_page_config(
    page_title="Nicha Pjv4 Dashboard", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

st.title("📊 Nicha Pjv4 - ระบบสรุปผลรายเดือน & บันทึกงาน")

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

# เมนูเลือกหน้า
menu = st.sidebar.radio("เลือกเมนูการใช้งาน", ["📊 Dashboard สรุปรายเดือน", "📝 ฟอร์มบันทึกงาน (Admin)"])

# -------------------------------------------------------------
# หน้าที่ 1: Dashboard สรุปรายเดือน
# -------------------------------------------------------------
if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    
    if sh is not None:
        try:
            # ดึงข้อมูลจาก Sheet "บันทึกงาน"
            ws_job = sh.worksheet("บันทึกงาน")
            data_job = ws_job.get_all_records()
            df_job = pd.DataFrame(data_job)

            # คำนวณตัวเลขอัตโนมัติจาก Google Sheet (ปรับแปลงเป็นตัวเลข)
            total_income = 0
            shop_income = 0
            owner_income = 0
            admin_income = 0

            # ตัวอย่างการคำนวณถ้าระบุคอลัมน์ไว้ (เช่น 'รายได้รวม', 'รายได้ร้าน')
            if not df_job.empty:
                # แปลงค่าในคอลัมน์เป็นตัวเลข (ป้องกันการติด string/เครื่องหมายคอมม่า)
                for col in df_job.columns:
                    df_job[col] = pd.to_numeric(df_job[col].astype(str).str.replace(',', ''), errors='ignore')
                
                # รวมยอดถ้ามีคอลัมน์ที่ตรงกัน
                if "รายได้รวม" in df_job.columns:
                    total_income = df_job["รายได้รวม"].sum()
                if "รายได้ร้าน" in df_job.columns:
                    shop_income = df_job["รายได้ร้าน"].sum()
                if "รายได้ Owner" in df_job.columns:
                    owner_income = df_job["รายได้ Owner"].sum()
                if "รายได้ Admin" in df_job.columns:
                    admin_income = df_job["รายได้ Admin"].sum()

            # แสดงผลการคำนวณจริง
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="💰 รายได้รวมทั้งหมด", value=f"{total_income:,.2f} THB")
            with col2:
                st.metric(label="🏠 รายได้ร้าน", value=f"{shop_income:,.2f} THB")
            with col3:
                st.metric(label="👑 รายได้ Owner", value=f"{owner_income:,.2f} THB")
            with col4:
                st.metric(label="👔 รายได้ Admin", value=f"{admin_income:,.2f} THB")

            st.markdown("---")
            st.subheader("📋 ตารางข้อมูลบันทึกงานล่าสุด")
            st.dataframe(df_job, use_container_width=True)

        except Exception as ex:
            st.warning(f"ดึงข้อมูลสำเร็จ แต่ปรับรูปแบบตารางไม่ได้: {ex}")
            st.info("กำลังใช้ตัวเลข Mockup แสดงผลชั่วคราว:")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric(label="💰 รายได้รวมทั้งหมด", value="22,700 THB")
            with col2: st.metric(label="🏠 รายได้ร้าน", value="22,575 THB")
            with col3: st.metric(label="👑 รายได้ Owner", value="17,724.28 THB")
            with col4: st.metric(label="👔 รายได้ Admin", value="คำนวณอัตโนมัติ")

# -------------------------------------------------------------
# หน้าที่ 2: ฟอร์มบันทึกงาน (Admin)
# -------------------------------------------------------------
elif menu == "📝 ฟอร์มบันทึกงาน (Admin)":
    st.header("📝 บันทึกงานประจำวัน ( Admin )")
    
    with st.form("job_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            date_input = st.date_input("วันที่")
            emp_name = st.text_input("ชื่อพนักงาน")
        with col_f2:
            branch = st.selectbox("สาขา", ["ประจวบคีรีขันธ์", "ราชบุรี", "พิษณุโลก"])
            service = st.selectbox("บริการ", ["40 นาที", "60 นาที", "90 นาที", "120 นาที", "8 hr (ทั้งคืน)"])
        
        submitted = st.form_submit_button("💾 บันทึกข้อมูลเข้า Google Sheet", use_container_width=True)
        if submitted:
            if sh is not None:
                try:
                    ws = sh.worksheet("บันทึกงาน")
                    ws.append_row([str(date_input), "", "", emp_name, branch, service])
                    st.success("✅ บันทึกข้อมูลเข้า Google Sheet เรียบร้อยแล้ว!")
                except Exception as ex:
                    st.error(f"เกิดข้อผิดพลาดในการบันทึก: {ex}")
            else:
                st.error("ไม่สามารถบันทึกได้ เนื่องจากยังไม่ได้เชื่อมต่อ Google Sheet")
