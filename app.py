import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ตั้งค่าหน้าตา Web App ให้กว้างเต็มจอ
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

# เมนูหลัก แบ่งตามหมวดหมู่สี
menu = st.sidebar.radio(
    "📌 เมนูหลัก", 
    [
        "📊 Dashboard สรุปรายเดือน", 
        "🟢 ลงทะเบียนพนักงานใหม่", 
        "🟢 บันทึกงานประจำวัน (Admin)",
        "🔴 ข้อมูลตั้งค่า & Agency"
    ]
)

# -------------------------------------------------------------
# ฟังก์ชันดึงรายชื่อ Agency จากแท็บตั้งค่า (🔴 สีแดง)
# -------------------------------------------------------------
def get_agency_list():
    agency_list = ["ไม่พบข้อมูล Agency"]
    if sh is not None:
        try:
            # ดึงจากแท็บ มูลตั้งค่า หรือ ค่าบริการ
            try:
                ws_setting = sh.worksheet("มูลตั้งค่า")
            except:
                ws_setting = sh.worksheet("พนักงาน")
            
            vals = ws_setting.get_all_values()
            # ค้นหารายชื่อ Agency จากตาราง
            temp_list = []
            for row in vals[1:]:
                for cell in row:
                    cell_str = str(cell).strip()
                    if "agency" in cell_str.lower() or "เอเจนซี่" in cell_str.lower():
                        temp_list.append(cell_str)
            if temp_list:
                agency_list = sorted(list(set(temp_list)))
            else:
                agency_list = ["Agency A", "Agency B", "Agency C", "อื่นๆ"]
        except:
            agency_list = ["Agency A", "Agency B", "Agency C", "อื่นๆ"]
    return agency_list

# -------------------------------------------------------------
# 1. หน้า Dashboard สรุปรายเดือน
# -------------------------------------------------------------
if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    if sh is not None:
        try:
            ws_sum = sh.worksheet("สรุปรายเดือน")
            val_total = ws_sum.acell("A4").value or "0.00"
            val_shop = ws_sum.acell("D4").value or "0.00"
            val_owner = ws_sum.acell("G4").value or "0.00"
            val_agency = ws_sum.acell("A8").value or "0.00"

            ws_calc = sh.worksheet("คำนวณ")
            raw_data = ws_calc.get_all_values()

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
            df_display = pd.DataFrame(raw_data[1:])
            df_display.columns = [f"{h} ({i+1})" if raw_data[0].count(h) > 1 else h for i, h in enumerate(raw_data[0])]
            st.dataframe(df_display, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {ex}")

# -------------------------------------------------------------
# 2. หน้าลงทะเบียนพนักงานใหม่ (🟢 แท็บพนักงาน)
# -------------------------------------------------------------
elif menu == "🟢 ลงทะเบียนพนักงานใหม่":
    st.header("👤 ฟอร์มลงทะเบียนพนักงานใหม่ (แท็บ: พนักงาน)")
    st.info("💡 ระบบจะรันรหัส EmpID ให้อัตโนมัติ Admin กรอกเพียงข้อมูลที่จำเป็นครับ")

    if sh is not None:
        try:
            ws_emp = sh.worksheet("พนักงาน")
            emp_data = ws_emp.get_all_values()
            
            # คำนวณ EmpID อัตโนมัติ
            next_id_num = len(emp_data)
            auto_emp_id = f"EMP{next_id_num:03d}"

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
                        agencies = get_agency_list()
                        agency_name = st.selectbox("🏢 เลือกชื่อ Agency", agencies)

                with col2:
                    deposit_option = st.selectbox("💰 เงินมัดจำ", ["ไม่มีค่ามัดจำ", "500", "1,000"])
                    deposit_date = st.date_input("📅 วันที่รับมัดจำ", value=date.today())
                    start_date = st.date_input("🚀 วันเริ่มงาน", value=date.today())
                    
                    promo_option = st.selectbox("📢 ค่าโปรโมท / ค่าป้าย", ["ไม่มีค่าโปรโมท", "1,000", "2,000"])
                    status_option = st.selectbox(
                        "📌 สถานะการทำงาน", 
                        ["ทำงาน", "รอเริ่มงาน", "จบงาน", "ไม่มาทำงาน"]
                    )

                submit_emp = st.form_submit_button("💾 บันทึกข้อมูลพนักงานเข้า Google Sheet", use_container_width=True)

                if submit_emp:
                    if not emp_name:
                        st.error("⚠️ กรุณากรอกชื่อพนักงานก่อนบันทึกครับ")
                    else:
                        new_row = [
                            auto_emp_id,
                            emp_name,
                            time_str,
                            emp_type,
                            agency_name,
                            deposit_option,
                            str(deposit_date) if deposit_option != "ไม่มีค่ามัดจำ" else "-",
                            str(start_date),
                            promo_option,
                            status_option
                        ]
                        ws_emp.append_row(new_row)
                        st.success(f"✅ บันทึกข้อมูล {emp_name} ({auto_emp_id}) เรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 รายชื่อพนักงานที่ลงทะเบียนแล้ว")
            if len(emp_data) > 1:
                df_emp = pd.DataFrame(emp_data[1:], columns=emp_data[0])
                st.dataframe(df_emp, use_container_width=True)
            else:
                st.write("ยังไม่มีข้อมูลพนักงาน")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลพนักงาน: {ex}")

# -------------------------------------------------------------
# 3. หน้าบันทึกงานประจำวัน (🟢 แท็บบันทึกงาน)
# -------------------------------------------------------------
elif menu == "🟢 บันทึกงานประจำวัน (Admin)":
    st.header("📝 บันทึกงานประจำวัน ( Admin )")

    if sh is not None:
        try:
            # ดึงรายชื่อพนักงานจากแท็บ 'พนักงาน' มาให้เลือก
            ws_emp = sh.worksheet("พนักงาน")
            emp_rows = ws_emp.get_all_values()
            
            emp_options = []
            if len(emp_rows) > 1:
                for r in emp_rows[1:]:
                    if len(r) > 1 and r[1]:
                        emp_options.append(f"{r[0]} - {r[1]}") # EmpID - Name
            
            if not emp_options:
                emp_options = ["กรุณาลงทะเบียนพนักงานก่อน"]

            with st.form("job_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    date_input = st.date_input("วันที่บันทึกงาน", value=date.today())
                    selected_emp = st.selectbox("👤 เลือกพนักงาน (EmpID - ชื่อ)", emp_options)
                    branch = st.selectbox("🏢 สาขา", ["ประจวบคีรีขันธ์", "ราชบุรี", "พิษณุโลก"])

                with col_f2:
                    service = st.selectbox("⏱️ เลือกรอบ / บริการ", ["40 นาที", "60 นาที", "90 นาที", "120 นาที", "8 hr (ทั้งคืน)"])
                    job_status = st.selectbox("📌 สถานะงาน", ["ทำงานจบงาน", "ยกเลิกงาน", "ไม่มาทำงาน"])

                submitted = st.form_submit_button("💾 บันทึกงานเข้า Google Sheet", use_container_width=True)
                
                if submitted:
                    emp_id_val = selected_emp.split(" - ")[0] if " - " in selected_emp else ""
                    emp_name_val = selected_emp.split(" - ")[1] if " - " in selected_emp else selected_emp

                    ws_job = sh.worksheet("บันทึกงาน")
                    ws_job.append_row([
                        str(date_input), 
                        "", 
                        emp_id_val, 
                        emp_name_val, 
                        branch, 
                        service, 
                        job_status
                    ])
                    st.success("✅ บันทึกงานเข้าแท็บ 'บันทึกงาน' เรียบร้อยแล้ว!")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกงาน: {ex}")

# -------------------------------------------------------------
# 4. ข้อมูลตั้งค่า & Agency (🔴 แท็บตั้งค่า)
# -------------------------------------------------------------
elif menu == "🔴 ข้อมูลตั้งค่า & Agency":
    st.header("🔴 ข้อมูลการตั้งค่า & รายชื่อ Agency (มูลตั้งค่า / ค่าบริการ)")
    if sh is not None:
        try:
            ws_set = sh.worksheet("มูลตั้งค่า")
            set_data = ws_set.get_all_values()
            if set_data:
                df_set = pd.DataFrame(set_data[1:], columns=set_data[0]) if len(set_data) > 1 else pd.DataFrame(set_data)
                st.dataframe(df_set, use_container_width=True)
        except:
            st.info("ดึงข้อมูลจากแท็บมูลตั้งค่าเรียบร้อยแล้ว")
