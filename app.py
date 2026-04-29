import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. إعدادات قاعدة البيانات ---
DB_URL = "sqlite:///court_system_final.db"
engine = create_engine(DB_URL)

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

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="منظومة الدوائر الجنائية المتكاملة", layout="wide")

if 'user_type' not in st.session_state: st.session_state.user_type = None
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'cases' not in st.session_state: st.session_state.cases = []

# --- 3. واجهة تسجيل الدخول ---
def login_page():
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚖️ تسجيل دخول منظومة الجنايات</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("اسم المستخدم")
            pwd = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول للمنظومة"):
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
                            st.error("❌ بيانات الدخول غير صحيحة")

# --- 4. لوحة تحكم الأدمن (قوة التحكم الكاملة) ---
def admin_dashboard():
    st.title("🚩 لوحة تحكم الإدارة العليا")
    
    tabs = st.tabs([
        "➕ إضافة دائرة جديدة", 
        "🔐 تعديل الحساب (يوزر وباسورد)", 
        "⚖️ تعديل الهيئة والأقدمية", 
        "📋 عرض وحذف الدوائر"
    ])
    
    # --- التبويب 1: إضافة دائرة ---
    with tabs[0]:
        with st.form("add_form"):
            st.subheader("بيانات الحساب والهيئة")
            c1, c2 = st.columns(2)
            with c1:
                u = st.text_input("اسم المستخدم الجديد")
                p = st.text_input("كلمة المرور")
                name = st.text_input("اسم الدائرة (مثلاً: الدائرة 15 جنايات)")
            with c2:
                js = [st.text_input(f"المستشار {i+1}", key=f"new_j{i}") for i in range(9)]
            if st.form_submit_button("✅ حفظ وإضافة"):
                try:
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO users VALUES (:u, :p, :n, :j1, :j2, :j3, :j4, :j5, :j6, :j7, :j8, :j9)"),
                                     {"u":u, "p":p, "n":name, "j1":js[0], "j2":js[1], "j3":js[2], "j4":js[3], "j5":js[4], "j6":js[5], "j7":js[6], "j8":js[7], "j9":js[8]})
                        conn.commit()
                    st.success("تم إضافة الدائرة بنجاح")
                    st.rerun()
                except: st.error("اسم المستخدم موجود مسبقاً!")

    # --- التبويب 2: تعديل اسم المستخدم والباسورد ---
    with tabs[1]:
        st.subheader("🔄 تحديث بيانات الدخول")
        with engine.connect() as conn:
            all_u = pd.read_sql("SELECT username, circuit_name FROM users", conn)
        
        target_u = st.selectbox("اختر الحساب المراد تعديله", ["---"] + all_u['username'].tolist(), key="change_acc")
        if target_u != "---":
            curr_name = all_u[all_u['username'] == target_u]['circuit_name'].values[0]
            st.info(f"تعديل حساب: {curr_name}")
            
            new_u_name = st.text_input("اسم المستخدم الجديد", value=target_u)
            new_p_val = st.text_input("كلمة المرور الجديدة", placeholder="اتركها فارغة لو لا تريد تغييرها")
            
            if st.button("💾 تحديث بيانات الحساب"):
                with engine.connect() as conn:
                    if new_p_val:
                        conn.execute(text("UPDATE users SET username=:nu, password=:np WHERE username=:ou"), 
                                     {"nu": new_u_name, "np": new_p_val, "ou": target_u})
                    else:
                        conn.execute(text("UPDATE users SET username=:nu WHERE username=:ou"), 
                                     {"nu": new_u_name, "ou": target_u})
                    conn.commit()
                st.success("✅ تم تحديث بيانات الدخول")
                st.rerun()

    # --- التبويب 3: تعديل الهيئة والأقدمية فقط ---
    with tabs[2]:
        st.subheader("⚖️ تحديث تشكيل وأقدمية المستشارين")
        with engine.connect() as conn:
            circuits = pd.read_sql("SELECT circuit_name, username FROM users", conn)
        
        sel_c = st.selectbox("اختر الدائرة لتعديل مستشاريها", ["---"] + circuits['circuit_name'].tolist())
        if sel_c != "---":
            with engine.connect() as conn:
                curr = conn.execute(text("SELECT * FROM users WHERE circuit_name=:c"), {"c":sel_c}).fetchone()
            
            st.write("رتب المستشارين حسب الأقدمية (من 1 لـ 9):")
            up_js = []
            c_a, c_b = st.columns(2)
            for i in range(9):
                with c_a if i < 5 else c_b:
                    up_js.append(st.text_input(f"المستشار رقم {i+1}", value=curr[i+3], key=f"up_j{i}"))
            
            if st.button("💾 حفظ تشكيل الهيئة الجديد"):
                with engine.connect() as conn:
                    conn.execute(text("UPDATE users SET j1=:j1, j2=:j2, j3=:j3, j4=:j4, j5=:j5, j6=:j6, j7=:j7, j8=:j8, j9=:j9 WHERE circuit_name=:c"),
                                 {"c":sel_c, "j1":up_js[0], "j2":up_js[1], "j3":up_js[2], "j4":up_js[3], "j5":up_js[4], "j6":up_js[5], "j7":up_js[6], "j8":up_js[7], "j9":up_js[8]})
                    conn.commit()
                st.success("✅ تم تحديث أقدمية المستشارين بنجاح")

    # --- التبويب 4: العرض الكلي والحذف ---
    with tabs[3]:
        st.subheader("📋 الرقابة العامة على الدوائر")
        with engine.connect() as conn:
            df = pd.read_sql("SELECT circuit_name as 'الدائرة', username as 'المستخدم', password as 'الباسورد' FROM users", conn)
        st.table(df)
        
        target_del = st.selectbox("حذف دائرة نهائياً", ["---"] + df['المستخدم'].tolist())
        if target_del != "---":
            if st.button("❌ تأكيد حذف الحساب"):
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM users WHERE username=:u"), {"u":target_del})
                    conn.commit()
                st.rerun()

    if st.sidebar.button("🚪 تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- 5. واجهة الموظف (سحب البيانات والتقفيل) ---
def staff_dashboard():
    data = st.session_state.user_data
    # جلب المستشارين الخاصين بهذه الدائرة فقط بالترتيب
    my_judges = [data[i] for i in range(3, 12) if data[i]]
    
    st.title(f"🏛️ {data[2]}") # اسم الدائرة
    st.sidebar.markdown(f"**الهيئة الحالية:**\n" + "\n".join([f"- {j}" for j in my_judges[:3]]))
    
    if st.sidebar.button("🔄 سحب حصة الطعون"):
        st.session_state.cases = [
            {'م': 1, 'رقم الطعن': '2500', 'السنة': '94', 'الطاعن': 'عباس العقاد', 'المحكمة': 'شمال القاهرة'},
            {'م': 2, 'رقم الطعن': '3100', 'السنة': '94', 'الطاعن': 'طه حسين', 'المحكمة': 'جنوب الجيزة'}
        ]
        st.rerun()

    if st.session_state.cases:
        tab1, tab2 = st.tabs(["📑 تحضير وتوزيع", "🔨 تقفيل الجلسة"])
        with tab1:
            df = pd.DataFrame(st.session_state.cases)
            for j in my_judges:
                if j not in df.columns: df[j] = ""
            st.data_editor(df, use_container_width=True)
            
        with tab2:
            st.info("هنا تظهر خانات منطوق الحكم وحضور المحامين...")

    if st.sidebar.button("🚪 تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- المحرك الرئيسي ---
if st.session_state.user_type == "admin":
    admin_dashboard()
elif st.session_state.user_type == "staff":
    staff_dashboard()
else:
    login_page()
