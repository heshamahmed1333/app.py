import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import io

# --- 1. إعدادات قاعدة البيانات (SQL Connection) ---
# هنا بنحط بيانات الـ IT اللي هيوفروها لينا
# مثال لـ SQL Server: 'mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server'
DB_URL = "sqlite:///court_system.db" # حالياً شغالين بقاعدة بيانات داخلية للتجربة
engine = create_engine(DB_URL)

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="منظومة الدوائر الجنائية الرقمية", layout="wide")

# --- 3. إدارة الجلسة (Session State) ---
if 'user_type' not in st.session_state: st.session_state.user_type = None
if 'circuit_id' not in st.session_state: st.session_state.circuit_id = None

# --- 4. وظائف الأدمن (Admin Functions) ---
def create_admin_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, circuit_name TEXT)"))
        conn.commit()

def add_user(user, pwd, circuit):
    with engine.connect() as conn:
        conn.execute(text("INSERT OR REPLACE INTO users VALUES (:u, :p, :c)"), {"u":user, "p":pwd, "c":circuit})
        conn.commit()

# --- 5. واجهة تسجيل الدخول ---
def login_page():
    st.title("⚖️ تسجيل دخول المنظومة")
    col1, col2 = st.columns([1, 2])
    with col1:
        user = st.text_input("اسم المستخدم")
        pwd = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if user == "admin" and pwd == "123": # كلمة سر الأدمن
                st.session_state.user_type = "admin"
                st.rerun()
            else:
                # التحقق من قاعدة البيانات للموظفين
                with engine.connect() as conn:
                    res = conn.execute(text("SELECT circuit_name FROM users WHERE username=:u AND password=:p"), {"u":user, "p":pwd}).fetchone()
                    if res:
                        st.session_state.user_type = "staff"
                        st.session_state.circuit_id = res[0]
                        st.rerun()
                    else:
                        st.error("خطأ في البيانات!")

# --- 6. لوحة تحكم الأدمن ---
def admin_dashboard():
    st.title("🚩 لوحة تحكم الإدارة العليا")
    create_admin_tables()
    
    # --- القسم الأول: إضافة دائرة جديدة ---
    with st.expander("➕ إضافة دائرة جديدة"):
        new_user = st.text_input("اسم مستخدم الدائرة")
        new_pwd = st.text_input("باسورد الدائرة")
        new_circuit = st.text_input("اسم الدائرة (مثلاً: الدائرة 15 جنايات)")
        if st.button("إنشاء الحساب"):
            add_user(new_user, new_pwd, new_circuit)
            st.success(f"تم إنشاء حساب {new_circuit}")
            st.rerun()

    # --- القسم الثاني: تعديل أو حذف دائرة ---
    with st.expander("🛠️ إدارة الحسابات الحالية (تعديل / حذف)"):
        with engine.connect() as conn:
            # سحب قائمة المستخدمين لعرضهم في قائمة الاختيار
            users_list = pd.read_sql("SELECT username FROM users", conn)['username'].tolist()
            
        target_user = st.selectbox("اختر اسم المستخدم المراد إدارته", ["---"] + users_list)
        
        if target_user != "---":
            col_edit, col_del = st.columns(2)
            
            with col_edit:
                st.subheader("🔐 تغيير الباسورد")
                new_pass = st.text_input("كلمة المرور الجديدة", type="password")
                if st.button("تحديث الباسورد"):
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE users SET password = :p WHERE username = :u"), {"p": new_pass, "u": target_user})
                        conn.commit()
                    st.success(f"تم تغيير باسورد {target_user} بنجاح")

            with col_del:
                st.subheader("⚠️ حذف الحساب")
                st.warning(f"هل أنت متأكد من حذف حساب {target_user}؟")
                if st.button("تأكيد الحذف النهائي"):
                    with engine.connect() as conn:
                        conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": target_user})
                        conn.commit()
                    st.error(f"تم حذف حساب {target_user}")
                    st.rerun()

    # --- القسم الثالث: عرض الجدول للمراقبة ---
    st.subheader("📋 الدوائر المسجلة حالياً")
    with engine.connect() as conn:
        users_df = pd.read_sql("SELECT username, circuit_name FROM users", conn)
        st.table(users_df)

    st.subheader("📋 الدوائر المسجلة حالياً")
    with engine.connect() as conn:
        users_df = pd.read_sql("SELECT username, circuit_name FROM users", conn)
        st.table(users_df)
    
    if st.button("تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- 7. واجهة الموظف (التقفيل والتحضير) ---
def staff_dashboard():
    st.title(f"🏛️ منصة عمل: {st.session_state.circuit_id}")
    
    # محاكاة سحب البيانات من SQL (هنا نربط مع جداول السيستم الحقيقية)
    st.sidebar.header("🔄 مزامنة السيستم")
    if st.sidebar.button("سحب حصة اليوم"):
        # هنا نضع الكود الذي يسحب البيانات بناءً على st.session_state.circuit_id
        st.session_state.current_cases = [
            {'رقم الطعن': '101', 'السنة': '94', 'اسم الطاعن': 'محمد حسن', 'المحكمة': 'بنها'},
            {'رقم الطعن': '202', 'السنة': '94', 'اسم الطاعن': 'إبراهيم علي', 'المحكمة': 'المنصورة'}
        ]
        st.sidebar.success("تم سحب البيانات!")

    if 'current_cases' in st.session_state:
        tab1, tab2 = st.tabs(["📑 تحضير وتوزيع", "🔨 تقفيل الأحكام"])
        
        with tab1:
            df = pd.DataFrame(st.session_state.current_cases)
            judges = ["نبيل الكشكى", "سامح عبد الرحيم", "محمود صديق", "ماجد ابراهيم", "محسن أبو بكر"]
            for j in judges: 
                if j not in df.columns: df[j] = ""
            
            edited = st.data_editor(df, use_container_width=True, key="staff_editor")
            if st.button("حفظ التوزيع"):
                st.session_state.current_cases = edited.to_dict('records')
                st.success("تم الحفظ!")

        with tab2:
            st.write("إدخال المنطوق والحضور...")
            # كود التقفيل (نفس اللي عملناه في المرات السابقة)
            # ...
    
    if st.sidebar.button("تسجيل خروج"):
        st.session_state.user_type = None
        st.rerun()

# --- 8. المحرك الأساسي ---
if st.session_state.user_type == "admin":
    admin_dashboard()
elif st.session_state.user_type == "staff":
    staff_dashboard()
else:
    login_page()
