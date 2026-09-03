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

# ฟังก์ชันดึง Worksheet แบบปลอดภัย (อ่านจากแท็บเดิมเท่านั้น ไม่แอดแท็บใหม่เด็ดขาด)
def get_existing_sheet(sheet_name):
    if sh is None:
        return None
    try:
        return sh.worksheet(sheet_name)
    except Exception:
        return None

# ฟังก์ชันดึงรายการ Dropdown จากแท็บเดิมที่มีอยู่
def get_dropdown_data(sheet_name, col_idx=0):
    ws = get_existing_sheet(sheet_name)
    if ws:
        try:
            vals = ws.get_all_values()
            if len(vals) > 1:
                items = [r[col_idx].strip() for r in vals[1:] if len(r) > col_idx and r[col_idx].strip() != ""]
                return list(dict.fromkeys(items))
        except:
            pass
    return []

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

# -------------------------------------------------------------
# 1. หน้า Dashboard สรุปรายเดือน (ดึงจากแท็บ 'สรุปรายเดือน' และ 'คำนวณ')
# -------------------------------------------------------------
if menu == "📊 Dashboard สรุปรายเดือน":
    st.header("📈 สรุปผลภาพรวมประจำเดือน")
    if sh is not None:
        try:
            ws_sum = get_existing_sheet("สรุปรายเดือน")
            val_total = ws_sum.acell("A4").value if ws_sum else "0.00"
            val_shop = ws_sum.acell("D4").value if ws_sum else "0.00"
            val_owner = ws_sum.acell("G4").value if ws_sum else "0.00"
            val_agency = ws_sum.acell("A8").value if ws_sum else "0.00"

            ws_calc = get_existing_sheet("คำนวณ")
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
            c1.metric("💰 รายได้รวมทั้งหมด", f"{val_total or '0.00'} THB")
            c2.metric("🏠 รายได้ร้าน", f"{val_shop or '0.00'} THB")
            c3.metric("👑 รายได้ Owner", f"{val_owner or '0.00'} THB")
            c4.metric("👔 รายได้ Admin", f"฿{total_admin:,.2f} THB")

            st.markdown("---")

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("🤝 รายได้เอเจนซี่", f"{val_agency or '0.00'} THB")
            c6.metric("🔄 จำนวนรอบ", f"{total_rounds} รอบ")
            c7.metric("👥 จำนวนพนักงาน", f"{len(emp_set)} คน")
            c8.metric("📊 รายได้เฉลี่ย/รอบ", f"฿{avg_num:,.2f} THB")

            st.markdown("---")
            st.subheader("📋 ตารางข้อมูลคำนวณทั้งหมด (แท็บ: คำนวณ)")
            if len(raw_data) > 1:
                df_display = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                st.dataframe(df_display, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {ex}")

# -------------------------------------------------------------
# 2. หน้าลงทะเบียนพนักงานใหม่ (ดึง/ลงข้อมูลที่แท็บ 'พนักงาน')
# -------------------------------------------------------------
elif menu == "🟢 ลงทะเบียนพนักงานใหม่":
    st.header("👤 ฟอร์มลงทะเบียนพนักงานใหม่ (แท็บ: พนักงาน)")

    if sh is not None:
        try:
            ws_emp = get_existing_sheet("พนักงาน")
            emp_data = ws_emp.get_all_values() if ws_emp else []
            
            next_id_num = len(emp_data) if len(emp_data) > 0 else 1
            auto_emp_id = f"EMP{next_id_num:03d}"

            # ดึงรายชื่อ Agency จากแท็บ 'ข้อมูลตั้งค่า' คอลัมน์ C (Index 2)
            agencies = get_dropdown_data("ข้อมูลตั้งค่า", col_idx=2)
            if not agencies:
                agencies = ["จอย", "โมนา", "ฝุ่น"]

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
                    elif ws_emp:
                        new_row = [
                            auto_emp_id, emp_name, time_str, emp_type, agency_name,
                            deposit_option, str(deposit_date) if deposit_option != "ไม่มีค่ามัดจำ" else "-",
                            str(start_date), promo_option, status_option
                        ]
                        ws_emp.append_row(new_row)
                        st.success(f"✅ บันทึกข้อมูล {emp_name} ({auto_emp_id}) เข้าแท็บ 'พนักงาน' เรียบร้อย!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📋 รายชื่อพนักงานปัจจุบัน (แท็บ: พนักงาน)")
            if len(emp_data) > 0:
                df_emp = pd.DataFrame(emp_data[1:], columns=emp_data[0]) if len(emp_data) > 1 else pd.DataFrame(emp_data)
                st.dataframe(df_emp, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลพนักงาน: {ex}")

# -------------------------------------------------------------
# 3. หน้าบันทึกงานประจำวัน (ลงข้อมูลที่แท็บ 'บันทึกงาน')
# -------------------------------------------------------------
elif menu == "🟢 บันทึกงานประจำวัน (Admin)":
    st.header("📝 บันทึกงานประจำวัน ( Admin )")

    if sh is not None:
        try:
            ws_emp = get_existing_sheet("พนักงาน")
            emp_rows = ws_emp.get_all_values() if ws_emp else []
            
            emp_options = []
            if len(emp_rows) > 1:
                for r in emp_rows[1:]:
                    if len(r) > 1 and r[1]:
                        emp_options.append(f"{r[0]} - {r[1]}")
            
            if not emp_options:
                emp_options = ["ไม่มีข้อมูลพนักงาน"]

            branches = get_dropdown_data("ข้อมูลตั้งค่า", col_idx=0) or ["ประจวบคีรีขันธ์", "ราชบุรี"]
            admins = get_dropdown_data("ข้อมูลตั้งค่า", col_idx=1) or ["Admin 1", "Admin 2"]
            services = get_dropdown_data("ค่าบริการ", col_idx=0) or ["40 นาที", "60 นาที", "90 นาที"]

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

                    ws_job = get_existing_sheet("บันทึกงาน")
                    if ws_job:
                        ws_job.append_row([
                            str(date_input), selected_admin, emp_id_val, emp_name_val, branch, service, job_status
                        ])
                        st.success("✅ บันทึกงานเข้าแท็บ 'บันทึกงาน' เรียบร้อยแล้ว!")

            st.markdown("---")
            ws_job = get_existing_sheet("บันทึกงาน")
            job_data = ws_job.get_all_values() if ws_job else []
            st.subheader("📋 ประวัติบันทึกงานทั้งหมด (แท็บ: บันทึกงาน)")
            if len(job_data) > 0:
                df_job = pd.DataFrame(job_data[1:], columns=job_data[0]) if len(job_data) > 1 else pd.DataFrame(job_data)
                st.dataframe(df_job, use_container_width=True)

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกงาน: {ex}")

# -------------------------------------------------------------
# 4. หน้าสำหรับ OWNER (จัดการแท็บ 'ข้อมูลตั้งค่า' และ 'ค่าบริการ')
# -------------------------------------------------------------
elif menu == "👑 [Owner Only] จัดการตั้งค่า & ค่าบริการ":
    st.header("👑 [Owner Only] ระบบจัดการข้อมูลตั้งค่า & อัตราค่าบริการ")

    tab_form1, tab_form2, tab_form3 = st.tabs([
        "1️⃣ ลงทะเบียนสาขา & แอดมิน (แท็บ: ข้อมูลตั้งค่า)", 
        "2️⃣ ปรับเปลี่ยนราคาค่าบริการ (แท็บ: ค่าบริการ)", 
        "3️⃣ บันทึกรายการค่าใช้จ่าย (แท็บ: ข้อมูลตั้งค่า)"
    ])

    # ---------------------------------------------------------
    # ฟอร์มที่ 1: ลงทะเบียนสาขา + แอดมิน
    # ---------------------------------------------------------
    with tab_form1:
        st.subheader("1️⃣ ฟอร์มลงทะเบียนสาขา & แอดมิน (แท็บ: ข้อมูลตั้งค่า)")
        if sh is not None:
            try:
                ws_set = get_existing_sheet("ข้อมูลตั้งค่า")
                set_vals = ws_set.get_all_values() if ws_set else []

                with st.form("form_owner_1"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        val_branch = st.text_input("🏢 สาขา (Col A)")
                        val_admin = st.text_input("👔 แอดมิน (Col B)")
                    with col_b:
                        val_agency = st.text_input("🤝 รายชื่อเอเจนซี่ (Col C)")
                        val_workdays = st.text_input("📅 จำนวนวันทำงาน (Col D)")
                    with col_c:
                        val_sys_status = st.selectbox("⚙️ สถานะระบบ (Col E)", ["ใช้งานปกติ", "ปิดปรับปรุง", "ระงับ"])
                        val_pay_status = st.selectbox("💳 สถานะจ่ายเอเจนซี่ (Col F)", ["จ่ายแล้ว", "รอจ่าย", "ค้างชำระ"])

                    submit_f1 = st.form_submit_button("💾 บันทึกข้อมูล ลงแท็บ 'ข้อมูลตั้งค่า'", use_container_width=True)

                    if submit_f1 and ws_set:
                        new_row_f1 = [
                            val_branch or "-", val_admin or "-", val_agency or "-",
                            val_workdays or "-", val_sys_status, val_pay_status
                        ]
                        ws_set.append_row(new_row_f1)
                        st.success("✅ บันทึกข้อมูลลงแท็บ 'ข้อมูลตั้งค่า' เรียบร้อย!")
                        st.rerun()

                st.markdown("---")
                if ws_set:
                    st.write("📋 **ตารางข้อมูลตั้งค่าปัจจุบัน (แท็บ: ข้อมูลตั้งค่า)**")
                    if len(set_vals) > 0:
                        df_set = pd.DataFrame(set_vals[1:], columns=set_vals[0]) if len(set_vals) > 1 else pd.DataFrame(set_vals)
                        st.dataframe(df_set, use_container_width=True)

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 1: {ex}")

    # ---------------------------------------------------------
    # ฟอร์มที่ 2: ปรับเปลี่ยนราคาค่าบริการ (เขียนทับแท็บ 'ค่าบริการ')
    # ---------------------------------------------------------
    with tab_form2:
        st.subheader("2️⃣ ฟอร์มปรับแต่งราคาค่าบริการ (เขียนทับแท็บ 'ค่าบริการ')")
        if sh is not None:
            try:
                ws_svc = get_existing_sheet("ค่าบริการ")
                svc_vals = ws_svc.get_all_values() if ws_svc else []

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

                        if submit_f2 and ws_svc:
                            ws_svc.update_cell(selected_row_idx, 2, new_price_total)
                            ws_svc.update_cell(selected_row_idx, 3, new_price_emp)
                            ws_svc.update_cell(selected_row_idx, 4, new_price_shop)
                            ws_svc.update_cell(selected_row_idx, 5, new_price_agency)
                            st.success(f"✅ ปรับปรุงราคาของ '{selected_svc}' เรียบร้อยแล้ว!")
                            st.rerun()

                    st.markdown("---")
                    st.write("📋 **ตารางอัตราค่าบริการทั้งหมด (แท็บ: ค่าบริการ)**")
                    st.dataframe(df_svc, use_container_width=True)

                else:
                    st.warning("ไม่พบข้อมูลในแท็บ 'ค่าบริการ'")

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 2: {ex}")

    # ---------------------------------------------------------
    # ฟอร์มที่ 3: บันทึกค่าใช้จ่าย (ลงแท็บ 'ข้อมูลตั้งค่า')
    # ---------------------------------------------------------
    with tab_form3:
        st.subheader("3️⃣ ฟอร์มบันทึกรายการค่าใช้จ่าย (แท็บ: ข้อมูลตั้งค่า Col A-B)")
        if sh is not None:
            try:
                ws_set = get_existing_sheet("ข้อมูลตั้งค่า")

                with st.form("form_owner_3"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        exp_item = st.text_input("📝 รายการค่าใช้จ่าย *")
                    with col_e2:
                        exp_type = st.selectbox("🏷️ ประเภทค่าใช้จ่าย", ["ค่าใช้จ่ายประจำ", "ค่าอุปกรณ์/ซ่อมบำรุง", "ค่าการตลาด/โปรโมท", "ค่าน้ำ/ค่าไฟ", "อื่นๆ"])

                    submit_f3 = st.form_submit_button("💾 บันทึกค่าใช้จ่ายลงแท็บ 'ข้อมูลตั้งค่า'", use_container_width=True)

                    if submit_f3:
                        if not exp_item:
                            st.error("⚠️ กรุณาระบุรายการค่าใช้จ่ายก่อนบันทึกครับ")
                        elif ws_set:
                            ws_set.append_row([exp_item, exp_type])
                            st.success(f"✅ บันทึกรายการ '{exp_item}' ลงแท็บ 'ข้อมูลตั้งค่า' เรียบร้อยแล้ว!")
                            st.rerun()

            except Exception as ex:
                st.error(f"เกิดข้อผิดพลาดในฟอร์มที่ 3: {ex}")
