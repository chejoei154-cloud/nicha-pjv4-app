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

# เมนูหลัก แบ่งตามหมวดหมู่และสิทธิ์การใช้งาน
menu = st.sidebar.radio(
    "📌 เมนูหลัก", 
    [
        "📊 Dashboard สรุปรายเดือน", 
        "🟢 ลงทะเบียนพนักงานใหม่", 
        "🟢 บันทึกงานประจำวัน (Admin)",
        "🔴 [Owner Only] ตั้งค่าสาขา/แอดมิน (มูลตั้งค่า)",
        "🔴 [Owner Only] ตั้งค่าราคาบริการ & ส่วนแบ่ง (ค่าบริการ)"
    ]
)

# -------------------------------------------------------------
# ฟังก์ชันดึงรายชื่อ Agency, สาขา และแอดมิน จากแท็บตั้งค่า
# -------------------------------------------------------------
def get_setting_list(worksheet_name, col_name_keyword, default_list):
    if sh is not None:
        try:
            ws = sh.worksheet(worksheet_name)
            data = ws.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                matched_cols = [c for c in df.columns if col_name_keyword.lower() in str(c).lower()]
                if matched_cols:
                    items = df[matched_cols[0]].dropna().unique().tolist()
                    clean_items = [str(x).strip() for x in items if str(x).strip() != ""]
                    if clean_items:
                        return clean_items
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
            
            next_id_num = len(emp_data)
            auto_emp_id = f"EMP{next_id_num:03d}"

            # ดึงข้อมูล Agency จากแท็บตั้งค่า
            agencies = get_setting_list("มูลตั้งค่า", "เอเจนซี่", ["Agency A", "Agency B", "อื่นๆ"])

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
            ws_emp = sh.worksheet("พนักงาน")
            emp_rows = ws_emp.get_all_values()
            
            emp_options = []
            if len(emp_rows) > 1:
                for r in emp_rows[1:]:
                    if len(r) > 1 and r[1]:
                        emp_options.append(f"{r[0]} - {r[1]}")
            
            if not emp_options:
                emp_options = ["กรุณาลงทะเบียนพนักงานก่อน"]

            # ดึงข้อมูล สาขา และ แอดมิน จากแท็บมูลตั้งค่า
            branches = get_setting_list("มูลตั้งค่า", "สาขา", ["ประจวบคีรีขันธ์", "ราชบุรี", "พิษณุโลก"])
            admins = get_setting_list("มูลตั้งค่า", "แอดมิน", ["Admin 1", "Admin 2"])
            services = get_setting_list("ค่าบริการ", "บริการ", ["40 นาที", "60 นาที", "90 นาที", "120 นาที", "8 hr (ทั้งคืน)"])

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

                    ws_job = sh.worksheet("บันทึกงาน")
                    ws_job.append_row([
                        str(date_input), 
                        selected_admin, 
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
# 4. หน้าตั้งค่าสาขา/แอดมิน/เอเจนซี่ (🔴 แท็บมูลตั้งค่า - Owner Only)
# -------------------------------------------------------------
elif menu == "🔴 [Owner Only] ตั้งค่าสาขา/แอดมิน (มูลตั้งค่า)":
    st.header("🔴 จัดการข้อมูลตั้งค่า (แท็บ: มูลตั้งค่า)")
    st.info("👑 ส่วนนี้สำหรับ Owner ในการเพิ่ม/จัดการ สาขา, รายชื่อแอดมิน, และ รายชื่อ Agency")

    if sh is not None:
        try:
            ws_set = sh.worksheet("มูลตั้งค่า")
            set_data = ws_set.get_all_values()

            tab_add, tab_view = st.tabs(["➕ เพิ่มข้อมูลตั้งค่าใหม่", "📋 ดูตารางมูลตั้งค่าทั้งหมด"])

            with tab_add:
                with st.form("add_setting_form"):
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        new_branch = st.text_input("🏢 เพิ่มสาขาใหม่")
                    with col_s2:
                        new_admin = st.text_input("👔 เพิ่มชื่อแอดมินใหม่")
                    with col_s3:
                        new_agency = st.text_input("🤝 เพิ่มชื่อ Agency ใหม่")

                    submit_set = st.form_submit_button("💾 บันทึกข้อมูลลงแท็บมูลตั้งค่า", use_container_width=True)

                    if submit_set:
                        if not new_branch and not new_admin and not new_agency:
                            st.warning("⚠️ กรุณากรอกข้อมูลอย่างน้อย 1 ช่องครับ")
                        else:
                            ws_set.append_row([new_branch or "-", new_admin or "-", new_agency or "-"])
                            st.success("✅ เพิ่มข้อมูลเรียบร้อยแล้ว!")
                            st.rerun()

            with tab_view:
                if len(set_data) > 0:
                    df_set = pd.DataFrame(set_data[1:], columns=set_data[0]) if len(set_data) > 1 else pd.DataFrame(set_data)
                    st.dataframe(df_set, use_container_width=True)
                else:
                    st.write("ยังไม่มีข้อมูลตั้งค่า")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในแท็บมูลตั้งค่า: {ex}")

# -------------------------------------------------------------
# 5. หน้าตั้งค่าอัตราค่าบริการ & ส่วนแบ่ง (🔴 แท็บค่าบริการ - Owner Only)
# -------------------------------------------------------------
elif menu == "🔴 [Owner Only] ตั้งค่าราคาบริการ & ส่วนแบ่ง (ค่าบริการ)":
    st.header("🔴 จัดการอัตราค่าบริการ & ส่วนแบ่ง (แท็บ: ค่าบริการ)")
    st.info("👑 สำหรับ Owner ปรับแต่งราคาบริการ ส่วนแบ่งร้าน, พนักงาน, Admin, และ เอเจนซี่")

    if sh is not None:
        try:
            ws_service = sh.worksheet("ค่าบริการ")
            service_data = ws_service.get_all_values()

            tab_add_svc, tab_view_svc = st.tabs(["➕ เพิ่ม/ปรับราคาบริการ", "📋 ดูตารางค่าบริการทั้งหมด"])

            with tab_add_svc:
                with st.form("add_service_form"):
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        svc_name = st.text_input("⏱️ ชื่อรอบ / บริการ (เช่น 40 นาที, 60 นาที)")
                        price_total = st.number_input("💰 ค่าบริการรวม (บาท)", min_value=0.0, step=100.0)
                        price_emp = st.number_input("👤 ส่วนแบ่งพนักงาน (บาท)", min_value=0.0, step=50.0)
                    with col_v2:
                        price_shop = st.number_input("🏠 ส่วนแบ่งร้าน (บาท)", min_value=0.0, step=50.0)
                        price_admin = st.number_input("👔 ส่วนแบ่ง Admin (บาท)", min_value=0.0, step=10.0)
                        price_agency = st.number_input("🤝 ส่วนแบ่ง Agency (บาท)", min_value=0.0, step=50.0)

                    submit_svc = st.form_submit_button("💾 บันทึกอัตราค่าบริการเข้า Google Sheet", use_container_width=True)

                    if submit_svc:
                        if not svc_name:
                            st.error("⚠️ กรุณาระบุชื่อบริการก่อนบันทึกครับ")
                        else:
                            new_svc_row = [
                                svc_name,
                                str(price_total),
                                str(price_emp),
                                str(price_shop),
                                str(price_admin),
                                str(price_agency)
                            ]
                            ws_service.append_row(new_svc_row)
                            st.success(f"✅ บันทึกอัตราค่าบริการ '{svc_name}' เรียบร้อยแล้ว!")
                            st.rerun()

            with tab_view_svc:
                if len(service_data) > 0:
                    df_svc = pd.DataFrame(service_data[1:], columns=service_data[0]) if len(service_data) > 1 else pd.DataFrame(service_data)
                    st.dataframe(df_svc, use_container_width=True)
                else:
                    st.write("ยังไม่มีข้อมูลค่าบริการ")

        except Exception as ex:
            st.error(f"เกิดข้อผิดพลาดในแท็บค่าบริการ: {ex}")
