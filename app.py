import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import io

# --- 1. إعدادات قاعدة البيانات (SQLite للتجربة ويمكن تحويلها لـ SQL Server لاحقاً) ---
DB_URL = "sqlite:///court_system_v2.db"
engine = create_engine(DB_URL)

# --- 2. تهيئة الجداول الأساسية (يتم تشغيلها مرة واحدة) ---
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                circuit_name TEXT,
                j1 TEXT, j2 TEXT, j3 TEXT, j4 TEXT, j5 TEXT, j6 TEXT, j7 TEXT, j8 TEXT, j9 TEXT
            )
        """))
        conn.commit()

init_db()

# --- 3. إعدادات الصفحة ---
st.set_page_config(page_title="منظومة الدوائر الجنائية المتكاملة", layout="wide")

# إدارة الحالة (Session State)
if 'user_type' not in st.session_state: st.session_state.user_type = None
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'cases' not in st.session_state: st.session_state.cases = []

# --- 4. واجهة تسجيل الدخول ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>⚖️ تسجيل دخول منظومة الجنايات</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("اسم المستخدم")
            pwd = st.text_input("كلمة المرور", type="password")
            submit = st.form_submit_button("دخول")
            
            if submit:
                if user == "admin" and pwd == "123":
                    st.session_state.user_type = "admin"
                    st.rerun()
                else:
                    with engine.connect() as conn:
                        res = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p"), {"u":user, "p":pwd}).fetchone()
                        if res:
                            st.session_state.user_type = "staff"
                            st.session_state.user_data = res
                            st.rerun()
                        else:
                            st.error("بيانات الدخول غير صحيحة")

# --- 5. لوحة تحكم الأدمن (الإدارة العليا) ---
def admin_dashboard():
    st.title("🚩 لوحة تحكم الإدارة العليا")
    
    tab_add, tab_manage = st.tabs(["➕ إضافة دائرة جديدة", "🛠️ إدارة الدوائر الحالية"])
    
    with tab_add:
        with st.form("add_circuit_form"):
            st.subheader("إعداد بيانات الدائرة والهيئة")
            c1, c2 = st.columns(2)
            with c1:
                u = st.text_input("اسم المستخدم (Username)")
                p = st.text_input("باسورد الدائرة")
                name = st.text_input("اسم الدائرة (مثال: الدائرة 15 جنايات)")
            with c2:
                js = [st.text_input(f"المستشار {i+1}", key=f"j{i}") for i in range(9)]
            
            if st.form_submit_button("حفظ الدائرة الجديدة"):
                with engine.connect() as conn:
                    conn.execute(text("INSERT OR REPLACE INTO users VALUES (:u, :p, :n, :j1, :j2, :j3, :j4, :j5, :j6, :j7, :j8, :j9)"),
                                 {"u":u, "p":p, "n":name, "j1":js[0], "j2":js[1], "j3":js[2], "j4":js[3], "j5":js[4], "j6":js[5], "j7":js[6], "j8":js[7], "j9":js[8]})
                    conn.commit()
                st.success("تم إنشاء الدائرة وتخصيص الهيئة بنجاح")
                st.rerun()

    with tab_manage:
        with engine.connect() as conn:
            all_users = pd.read_sql("SELECT * FROM users", conn)
        
        st.subheader("📋 قائمة الدوائر المسجلة")
        st.dataframe(all_users[['username', 'circuit_name']], use_container_width=True)
        
        target = st.selectbox("اختر دائرة للحذف أو التعديل", ["---"] + all_users['username'].tolist())
        if target != "---":
            if st.button("❌ حذف هذه الدائرة نهائياً"):
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM users WHERE username=:u"), {"u":target})
                    conn.commit()
                st.rerun()

    if st.sidebar.button("تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- 6. واجهة الموظف (التحضير والتقفيل) ---
def staff_dashboard():
    data = st.session_state.user_data
    # ترتيب المستشارين المسجلين لهذه الدائرة فقط
    circuit_judges = [data[i] for i in range(3, 12) if data[i]]
    
    st.title(f"🏛️ {data[2]}") # عرض اسم الدائرة
    st.sidebar.info(f"مرحباً بك.. الهيئة الحالية: {', '.join(circuit_judges[:3])}...")

    # سحب البيانات من السيستم (Simulation)
    with st.sidebar:
        st.header("📂 إدارة الحصة")
        if st.button("🔄 سحب طعون اليوم من السيستم"):
            st.session_state.cases = [
                {'رقم الطعن': '1500', 'السنة': '94', 'اسم الطاعن': 'أحمد مجدي', 'المحكمة': 'الجيزة', 'التهمة': 'سرقة'},
                {'رقم الطعن': '1620', 'السنة': '94', 'اسم الطاعن': 'سعيد حسن', 'المحكمة': 'القاهرة', 'التهمة': 'تزوير'}
            ]
            st.rerun()

    if st.session_state.cases:
        t1, t2 = st.tabs(["📑 تحضير وتوزيع", "🔨 تقفيل الجلسة"])
        
        with t1:
            df_prep = pd.DataFrame(st.session_state.cases)
            for j in circuit_judges:
                if j not in df_prep.columns: df_prep[j] = ""
            
            st.subheader("توزيع العمل على هيئة الدائرة")
            edited = st.data_editor(df_prep, use_container_width=True, key="p_edit")
            if st.button("💾 حفظ التوزيع الحالي"):
                st.session_state.cases = edited.to_dict('records')
                st.success("تم حفظ التوزيع!")

        with t2:
            st.subheader("إدخال منطوق الأحكام والحضور")
            # منطق ترتيب البيانات بناء على التوزيع
            final_list = []
            rank_map = {name: i for i, name in enumerate(circuit_judges)}
            for c in st.session_state.cases:
                row = c.copy()
                row['المقرر'], row['sort_idx'] = "", 999
                for j in circuit_judges:
                    if str(c.get(j, "")).strip() == "+":
                        row['المقرر'] = j
                        row['sort_idx'] = rank_map[j]
                final_list.append(row)
            
            final_df = pd.DataFrame(final_list).sort_values('sort_idx')
            cases_list = final_df.to_dict('records')
            
            # واجهة الإدخال
            idx = st.number_input("المسلسل (م)", 1, len(cases_list), step=1) - 1
            curr = cases_list[idx]
            st.warning(f"📍 طعن رقم {curr['رقم الطعن']} | {curr['اسم الطاعن']}")
            
            c_h, c_ho = st.columns(2)
            with c_h:
                h = st.text_area("منطوق الحكم", value=curr.get('منطوق الحكم', ""), key=f"h{idx}")
            with c_ho:
                ho = st.text_area("حضور المحامين", value=curr.get('حضور المحامين', ""), key=f"ho{idx}")
            
            if st.button("💾 حفظ الحكم"):
                for c in st.session_state.cases:
                    if str(c['رقم الطعن']) == str(curr['رقم الطعن']):
                        c['منطوق الحكم'] = h
                        c['حضور المحامين'] = ho
                st.rerun()
            
            st.divider()
            st.subheader("📊 معاينة الجدول النهائي")
            st.dataframe(pd.DataFrame(st.session_state.cases), use_container_width=True)

    if st.sidebar.button("تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- 7. المحرك الرئيسي ---
if st.session_state.user_type == "admin":
    admin_dashboard()
elif st.session_state.user_type == "staff":
    staff_dashboard()
else:
    login_page()
