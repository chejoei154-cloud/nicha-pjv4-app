import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ตั้งค่าหน้าตา Web App ให้กว้างเต็มจอ
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
            # 1. ดึงข้อมูลตัวเลขที่คำนวณผ่านใน Google Sheet มาก่อน
            ws_sum = sh.worksheet("สรุปรายเดือน")
            val_total = ws_sum.acell("A4").value or "0.00"
            val_shop = ws_sum.acell("D4").value or "0.00"
            val_owner = ws_sum.acell("G4").value or "0.00"
            val_agency = ws_sum.acell("A8").value or "0.00"

            # 2. ดึงข้อมูลตารางบันทึกงานเพื่อนำมาคำนวณยอดที่ติด #N/A แบบสดๆ ด้วย Python
            ws_calc = sh.worksheet("คำนวณ")
            raw_data = ws_calc.get_all_values()

            total_admin = 0.0
            emp_set = set()
            total_rounds = 0

            if len(raw_data) > 1:
                headers = raw_data[0]
                rows = raw_data[1:]
                total_rounds = len(rows)

                # ค้นหาตำแหน่ง Index ของคอลัมน์สำคัญ ป้องกันปัญหา Duplicate Column Names
                admin_col_idx = -1
                emp_col_idx = -1

                for idx, h in enumerate(headers):
                    h_clean = str(h).strip().lower()
                    if "ส่วนแบ่ง admin" in h_clean or "ส่วนแบ่งadmin" in h_clean:
                        admin_col_idx = idx
                    if "พนักงาน" in h_clean or "ชื่อพนักงาน" in h_clean or "empid" in h_clean:
                        if emp_col_idx == -1: # เอาคอลัมน์แรกที่เจอ
                            emp_col_idx = idx

                # คำนวณรายได้ Admin และนับจำนวนพนักงาน
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

            # คำนวณรายได้เฉลี่ยต่อรอบ (นำรายได้รวมมาหารจำนวนรอบ)
            try:
                tot_num = float(str(val_total).replace(',', '').replace('฿', '').strip())
                avg_num = tot_num / total_rounds if total_rounds > 0 else 0.0
            except:
                avg_num = 0.0

            # 3. แสดงผลตัวเลขทั้งหมดบน Metric Cards
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
            st.subheader("📋 ตารางข้อมูลบันทึกงานทั้งหมด")

            # แสดงตารางแบบปลอดภัยเพื่อไม่ให้ติด Duplicate column names
            df_display = pd.DataFrame(raw_data[1:])
            # ตั้งชื่อหัวคอลัมน์ชั่วคราวเพื่อหลีกเลี่ยงชื่อซ้ำ
            df_display.columns = [f"{h} ({i+1})" if raw_data[0].count(h) > 1 else h for i, h in enumerate(raw_data[0])]
            st.dataframe(df_display, use_container_width=True)

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
