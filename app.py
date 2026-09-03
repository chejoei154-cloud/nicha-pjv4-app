import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ตั้งค่าหน้าตา Web App
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

menu = st.sidebar.radio("เลือกเมนูการใช้งาน", ["📊 Dashboard สรุปรายเดือน", "📝 ฟอร์มบันทึกงาน (Admin)"])

# -------------------------------------------------------------
# หน้าที่ 1: Dashboard สรุปรายเดือน
# -------------------------------------------------------------
if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    
    if sh is not None:
        try:
            # ดึงข้อมูลจากแท็บ "คำนวณ"
            ws_calc = sh.worksheet("คำนวณ")
            data_calc = ws_calc.get_all_values()
            
            if len(data_calc) > 1:
                # แปลงเป็น DataFrame และดึงเฉพาะคอลัมน์ A ถึง AD (30 คอลัมน์แรก)
                df_calc = pd.DataFrame(data_calc[1:], columns=data_calc[0])
                df_calc = df_calc.iloc[:, :30] 
                
                # ทำความสะอาดข้อมูลตัวเลข (ตัดเครื่องหมาย , หรือตัวอักษรรวมถึงช่องว่าง)
                def clean_num(val):
                    try:
                        val_str = str(val).replace(',', '').replace('฿', '').strip()
                        return float(val_str) if val_str else 0.0
                    except:
                        return 0.0

                # ฟังก์ชันช่วยรวมยอดตามชื่อคอลัมน์
                def get_sum(col_keyword):
                    matched_cols = [c for c in df_calc.columns if col_keyword.lower() in str(c).lower()]
                    if matched_cols:
                        return df_calc[matched_cols[0]].apply(clean_num).sum()
                    return 0.0

                # คำนวณยอดต่างๆ จากตารางคำนวณอัตโนมัติ
                total_inc = get_sum("รวม") or get_sum("ทั้งหมด")
                shop_inc  = get_sum("ร้าน")
                owner_inc = get_sum("owner")
                admin_inc = get_sum("แอดมิน") or get_sum("admin")
                agency_inc = get_sum("เอเจนซี่") or get_sum("agency")
                
                # คำนวณรอบและจำนวนพนักงาน
                rounds_count = len(df_calc)
                emp_count = df_calc['ชื่อพนักงาน'].nunique() if 'ชื่อพนักงาน' in df_calc.columns else 0
                avg_inc = total_inc / rounds_count if rounds_count > 0 else 0

                # แสดงผลการคำนวณ แถวที่ 1
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💰 รายได้รวมทั้งหมด", f"{total_inc:,.2f} THB")
                c2.metric("🏠 รายได้ร้าน", f"{shop_inc:,.2f} THB")
                c3.metric("👑 รายได้ Owner", f"{owner_inc:,.2f} THB")
                c4.metric("👔 รายได้ Admin", f"{admin_inc:,.2f} THB")

                st.markdown("---")

                # แสดงผลการคำนวณ แถวที่ 2
                c5, c6, c7, c8 = st.columns(4)
                c5.metric("🤝 รายได้เอเจนซี่", f"{agency_inc:,.2f} THB")
                c6.metric("🔄 จำนวนรอบ", f"{rounds_count:,} รอบ")
                c7.metric("👥 จำนวนพนักงาน", f"{emp_count:,} คน")
                c8.metric("📊 รายได้เฉลี่ย/รอบ", f"{avg_inc:,.2f} THB")

                st.markdown("---")
                st.subheader("📋 ตารางข้อมูลจากชีทคำนวณ (คอลัมน์ A - AD)")
                st.dataframe(df_calc, use_container_width=True)

            else:
                st.warning("ไม่พบข้อมูลในแท็บ 'คำนวณ'")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {ex}")

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
