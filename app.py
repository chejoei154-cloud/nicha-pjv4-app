import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ตั้งค่าหน้าตา Web App
st.set_page_config(page_title="Nicha Pjv4 Dashboard", layout="wide", page_icon="📊")

st.title("📊 Nicha Pjv4 - ระบบสรุปผลรายเดือน & บันทึกงาน")

# เชื่อมต่อ Google Sheets ผ่าน Secrets
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

try:
    gc = init_gspread()
    sh = gc.open("Nicha Pjv4 phyton")
    st.sidebar.success("🟢 เชื่อมต่อ Google Sheet เรียบร้อย")
except Exception as e:
    st.sidebar.error("🔴 รอการตั้งค่า Secrets ความปลอดภัย")

# เมนูเลือกหน้า
menu = st.sidebar.radio("เลือกเมนูการใช้งาน", ["📊 Dashboard สรุปรายเดือน", "📝 ฟอร์มบันทึกงาน (Admin)"])

if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="💰 รายได้รวมทั้งหมด", value="22,700 THB")
    with col2:
        st.metric(label="🏠 รายได้ร้าน", value="22,575 THB")
    with col3:
        st.metric(label="👑 รายได้ Owner", value="17,724.28 THB")
    with col4:
        st.metric(label="👔 รายได้ Admin", value="คำนวณอัตโนมัติ")

elif menu == "📝 ฟอร์มบันทึกงาน (Admin)":
    st.header("📝 บันทึกงานประจำวัน ( Admin )")
    
    with st.form("job_form"):
        date_input = st.date_input("วันที่")
        emp_name = st.text_input("ชื่อพนักงาน")
        branch = st.selectbox("สาขา", ["ประจวบคีรีขันธ์", "ราชบุรี", "พิษณุโลก"])
        service = st.selectbox("บริการ", ["40 นาที", "60 นาที", "90 นาที", "120 นาที", "8 hr (ทั้งคืน)"])
        
        submitted = st.form_submit_button("💾 บันทึกข้อมูลเข้า Google Sheet")
        if submitted:
            try:
                ws = sh.worksheet("บันทึกงาน")
                ws.append_row([str(date_input), "", "", emp_name, branch, service])
                st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
            except Exception as ex:
                st.error("กรุณาเปิดสิทธิ์และตั้งค่า Secrets ก่อนใช้งาน")
