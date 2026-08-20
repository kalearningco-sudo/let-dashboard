import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import uuid
import snowflake.connector

# ==========================================
# SNOWFLAKE CONNECTION — YOUR EXACT DETAILS ❄️
# ==========================================
def get_snowflake_connection():
    return snowflake.connector.connect(
        account="jx67793.ap-southeast-7.aws",
        user="KALEARNINGCO",
        password="KaryllAnnQuitaleg20",
        warehouse="COMPUTE_WH",
        database="LET_DASHBOARD",
        schema="PUBLIC"
    )

# ==========================================
# PAGE SETUP
# ==========================================
st.set_page_config(
    page_title="LET Dashboard — Powered by Snowflake ❄️",
    page_icon="🎓",
    layout="wide"
)

# Session State
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'is_premium' not in st.session_state:
    st.session_state.is_premium = False

st.title("🎓 LET Study Dashboard — Powered by Snowflake ❄️")

# Login / Signup
if not st.session_state.user_id:
    st.subheader("👤 Welcome! Please Login or Sign Up")
    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab_signup:
        email = st.text_input("📧 Email Address", key="signup_email")
        if st.button("Create Account"):
            if email:
                conn = get_snowflake_connection()
                user_id = str(uuid.uuid4())
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO LET_DASHBOARD.PUBLIC.USERS (USER_ID, EMAIL)
                        VALUES (%s, %s)
                    """, (user_id, email))
                    conn.commit()
                    st.session_state.user_id = user_id
                    st.session_state.email = email
                    st.success(f"✅ Account created! Welcome, {email}! 🎉")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: Email may already exist! {e}")
                finally:
                    conn.close()
    
    with tab_login:
        email_login = st.text_input("📧 Your Email", key="login_email")
        if st.button("🔑 Login"):
            conn = get_snowflake_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT USER_ID, IS_PREMIUM FROM LET_DASHBOARD.PUBLIC.USERS 
                    WHERE EMAIL = %s
                """, (email_login,))
                result = cursor.fetchone()
                if result:
                    st.session_state.user_id = result[0]
                    st.session_state.is_premium = result[1]
                    st.session_state.email = email_login
                    st.success(f"✅ Welcome back! 💛")
                    st.rerun()
                else:
                    st.error("❌ Email not found — please sign up first!")
            finally:
                conn.close()
    st.stop()

# User Header
if st.session_state.is_premium:
    st.subheader(f"👤 {st.session_state.email} — 💎 PREMIUM MEMBER")
else:
    st.subheader(f"👤 {st.session_state.email} — 🆓 FREE PLAN")

# Logout
if st.sidebar.button("🚪 Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Premium System
PREMIUM_CODE = "LET2026PRO"
st.sidebar.markdown("---")
st.sidebar.header("💎 Premium Access")
user_code = st.sidebar.text_input("Enter Premium Code:", type="password")
if st.sidebar.button("🔓 Activate Premium"):
    if user_code.strip().upper() == PREMIUM_CODE:
        conn = get_snowflake_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE LET_DASHBOARD.PUBLIC.USERS 
                SET IS_PREMIUM = TRUE 
                WHERE USER_ID = %s
            """, (st.session_state.user_id,))
            conn.commit()
            st.session_state.is_premium = True
            st.sidebar.success("✅ PREMIUM ACTIVATED! Thank you! 💎🎉")
            st.snow()
        finally:
            conn.close()
    else:
        st.sidebar.error("❌ Invalid code!")

def require_premium(feature_name):
    if not st.session_state.is_premium:
        st.warning(f"🔒 **'{feature_name}' is PREMIUM only!** Upgrade for ₱299 LIFETIME! 💎")
        st.info("📱 Pay via GCash/Maya: 09XX-XXX-XXXX — Send screenshot + email!")
        st.stop()

# Data Functions
def save_mock_exam_to_snowflake(exam_date, ge, pe, major, overall, status):
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO LET_DASHBOARD.PUBLIC.MOCK_EXAMS 
            (USER_ID, EXAM_DATE, GEN_ED_SCORE, PRO_ED_SCORE, MAJOR_SCORE, OVERALL_SCORE, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (st.session_state.user_id, exam_date, ge, pe, major, overall, status))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"❌ Save failed: {e}")
        return False
    finally:
        conn.close()

def load_mock_exams_from_snowflake():
    conn = get_snowflake_connection()
    try:
        df = pd.read_sql("""
            SELECT EXAM_DATE, GEN_ED_SCORE, PRO_ED_SCORE, MAJOR_SCORE, OVERALL_SCORE, STATUS
            FROM LET_DASHBOARD.PUBLIC.MOCK_EXAMS
            WHERE USER_ID = %s
            ORDER BY EXAM_DATE
        """, conn, params=(st.session_state.user_id,))
        return df
    finally:
        conn.close()

# Load Data
mock_exams_df = load_mock_exams_from_snowflake()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📝 Mock Exams", "🎯 Weak Topics", "📅 22-Week Plan"])

with tab1:
    st.subheader("📊 Your Progress Overview")
    if len(mock_exams_df) > 0:
        latest = mock_exams_df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("🎯 Latest Overall", f"{latest['OVERALL_SCORE']}%")
        col2.metric("📈 Total Exams", len(mock_exams_df))
        col3.metric("✅ Status", latest['STATUS'])
        
        fig = px.line(mock_exams_df, x='EXAM_DATE', y=['OVERALL_SCORE','GEN_ED_SCORE','PRO_ED_SCORE','MAJOR_SCORE'],
                      markers=True, title='Score Progress — Saved to Snowflake ❄️')
        fig.add_hline(y=75, line_dash='dash', line_color='red')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📖 No mock exams yet! Go to the Mock Exams tab and log your first one!")

with tab2:
    st.subheader("📝 Log New Mock Exam")
    c1, c2, c3 = st.columns(3)
    ge = c1.number_input("GenEd Score (%)", 0, 100, 75)
    pe = c2.number_input("ProfEd Score (%)", 0, 100, 75)
    ma = c3.number_input("Major Score (%)", 0, 100, 75)
    exam_date = st.date_input("Exam Date", value=date.today())
    
    if st.button("💾 Save to Snowflake ❄️"):
        overall = round(ge*0.20 + pe*0.40 + ma*0.40, 1)
        status = "✅ PASS" if overall >= 75 else "⚠️ REVIEW"
        if save_mock_exam_to_snowflake(exam_date, ge, pe, ma, overall, status):
            st.success(f"✅ Saved! Weighted Score: {overall}% — {status} ❄️")
            st.rerun()
    
    if len(mock_exams_df) > 0:
        st.subheader("📋 Exam History (from Snowflake)")
        st.dataframe(mock_exams_df, use_container_width=True, hide_index=True)

with tab3:
    require_premium("Weak Topics Detection")
    st.subheader("🎯 Your Weak Topics — Study These FIRST!")
    st.info("🔒 Unlock Premium to see your personalized study recommendations! 💎")

with tab4:
    st.subheader("📅 22-Week LET Review Schedule")
    schedule = pd.DataFrame({
        'Week': list(range(1,23)),
        'Focus': [
            'Purposive Comm • Filipino Comm','Math in Modern World • Rizal','Science & Tech • History','Contemporary World • Ethics',
            'Art Appreciation • Understanding Self','Teaching Profession • Laws','Child & Adolescent Development','Learning Theories & Motivation',
            'Curriculum • Pedagogy • 7Es','EdTech • TPACK • SAMR','Assessment of Learning 1 • Statistics','Assessment Grading & Reporting',
            'Linguistics: Phonology • Morphology','Syntax • Semantics • Pragmatics','Sociolinguistics • Language Policy','Teaching Macroskills: L/S/R/W',
            'Language Assessment • Materials','Literature: PH • Afro-Asian • Western','Remedial Reading • Research','Review ALL GenEd',
            'Review ALL ProfEd • Mock Exam','Comprehensive Mock Exam • Polish Weaknesses'
        ]
    })
    st.dataframe(schedule, use_container_width=True, hide_index=True, height=600)

st.markdown("---")
st.caption("🎓 LET Dashboard • Powered by Snowflake ❄️ • PRC TOS-Aligned • Data securely stored in the cloud! ☁️💛")