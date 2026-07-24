import streamlit as st
import pandas as pd
import os
import tempfile
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from models import OnlineSystem

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="Enterprise Academic Tracker & Analytics", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI/UX (Clean typography, cards, badges, and smooth spacing)
st.markdown("""
    <style>
        /* Main background & font styling */
        .main {
            background-color: #f8fafc;
        }
        
        /* Custom Card Containers */
        .metric-card {
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        
        /* Header Banner styling */
        .hero-banner {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 30px;
            border-radius: 16px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* Status Badges */
        .badge-success {
            background-color: #dcfce7;
            color: #166534;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-danger {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        /* Custom Streamlit Button Styling */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
    </style>
""", unsafe_allow_html=True)

# --- Direct Data Management Logic ---
DATA_FILE = "student_data.csv"
HISTORY_FILE = "prediction_history.csv"

def initialize_files():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'student_id', 'student_name', 'subject', 'academic_year', 
            'term', 'study_time_hours', 'attendance_percent', 'previous_grade', 'final_grade'
        ])
        df.to_csv(DATA_FILE, index=False)
        
    if not os.path.exists(HISTORY_FILE):
        hist_df = pd.DataFrame(columns=[
            'timestamp', 'student_id', 'subject', 'term', 'predicted_score', 'risk_status'
        ])
        hist_df.to_csv(HISTORY_FILE, index=False)

initialize_files()

def save_new_student_subject_record(record_dict):
    if not os.path.exists(DATA_FILE):
        initialize_files()
    df = pd.read_csv(DATA_FILE, dtype={'student_id': str})
    
    mask = (
        (df['student_id'].astype(str).str.strip() == str(record_dict['student_id']).strip()) & 
        (df['subject'] == record_dict['subject']) & 
        (df['term'] == record_dict['term'])
    )
    
    if not df[mask].empty:
        for key, value in record_dict.items():
            df.loc[mask, key] = value
    else:
        new_row = pd.DataFrame([record_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        
    df.to_csv(DATA_FILE, index=False)
    return True

def log_prediction(student_id, term, predicted_score, risk_status, subject="General"):
    if not os.path.exists(HISTORY_FILE):
        initialize_files()
    hist_df = pd.read_csv(HISTORY_FILE, dtype={'student_id': str})
    new_entry = pd.DataFrame([{
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'student_id': str(student_id),
        'subject': subject,
        'term': term,
        'predicted_score': round(float(predicted_score), 2),
        'risk_status': risk_status
    }])
    hist_df = pd.concat([hist_df, new_entry], ignore_index=True)
    hist_df.to_csv(HISTORY_FILE, index=False)

def bulk_import_data(uploaded_file):
    try:
        imported_df = pd.read_csv(uploaded_file, dtype={'student_id': str})
        required_cols = ['student_id', 'subject', 'term', 'study_time_hours', 'attendance_percent', 'previous_grade', 'final_grade']
        if not all(col in imported_df.columns for col in required_cols):
            return False, f"CSV missing required columns. Must contain: {required_cols}"
        imported_df.to_csv(DATA_FILE, index=False)
        return True, "Bulk dataset successfully imported with per-subject records."
    except Exception as e:
        return False, str(e)

SUBJECT_LIST = [
    "Mathematics", 
    "Information Technology", 
    "Integrated Science", 
    "English Language", 
    "Social Studies"
]

# --- PDF Export Helper Functions ---
def generate_pdf_report(dataframe_to_print, title="System Audit Log"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    
    pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 9)
    headers_mapped = ["Timestamp", "Student ID", "Period", "Subject", "Score", "Risk Status"]
    widths_mapped = [35, 22, 28, 30, 22, 33]
    
    for i, header in enumerate(headers_mapped):
        pdf.cell(widths_mapped[i], 8, header, border=1, align="C", fill=False)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    for _, row in dataframe_to_print.iterrows():
        pdf.cell(widths_mapped[0], 7, str(row.get('timestamp', '')), border=1)
        pdf.cell(widths_mapped[1], 7, str(row.get('student_id', '')), border=1, align="C")
        pdf.cell(widths_mapped[2], 7, str(row.get('term', '')), border=1, align="C")
        pdf.cell(widths_mapped[3], 7, str(row.get('subject', 'General')), border=1, align="C")
        pdf.cell(widths_mapped[4], 7, str(row.get('predicted_score', '')), border=1, align="C")
        pdf.cell(widths_mapped[5], 7, str(row.get('risk_status', '')), border=1, align="C")
        pdf.ln()
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
        
    pdf.output(tmp_path)
    return tmp_path

def generate_comprehensive_student_report(student_id, df_records, history_df):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Comprehensive Per-Subject Academic Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, f"Student ID: {student_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "Current Subject Baseline Records", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "B", 9)
    b_headers = ["Subject", "Period", "Study Hrs", "Attendance", "Prev Grade", "Final Grade"]
    b_widths = [45, 30, 25, 25, 25, 25]
    for i, h in enumerate(b_headers):
        pdf.cell(b_widths[i], 7, h, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if df_records.empty:
        pdf.cell(sum(b_widths), 7, "No baseline records found.", border=1, align="C")
        pdf.ln()
    else:
        for _, row in df_records.iterrows():
            pdf.cell(b_widths[0], 6, str(row.get('subject', '')), border=1, align="L")
            pdf.cell(b_widths[1], 6, str(row.get('term', '')), border=1, align="C")
            pdf.cell(b_widths[2], 6, str(row.get('study_time_hours', '')), border=1, align="C")
            pdf.cell(b_widths[3], 6, f"{row.get('attendance_percent', '')}%", border=1, align="C")
            pdf.cell(b_widths[4], 6, str(row.get('previous_grade', '')), border=1, align="C")
            pdf.cell(b_widths[5], 6, str(row.get('final_grade', '')), border=1, align="C")
            pdf.ln()
            
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "Evaluation & Intervention Logs History", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "B", 9)
    h_headers = ["Period", "Subject", "Score", "Risk Status", "Date Logged"]
    h_widths = [38, 42, 25, 25, 60]
    for i, h in enumerate(h_headers):
        pdf.cell(h_widths[i], 7, h, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    student_hist = history_df[history_df['student_id'].astype(str).str.strip() == str(student_id)]
    if student_hist.empty:
        pdf.cell(sum(h_widths), 7, "No evaluation logs found.", border=1, align="C")
        pdf.ln()
    else:
        for _, row in student_hist.iterrows():
            pdf.cell(h_widths[0], 6, str(row.get('term', '')), border=1, align="C")
            pdf.cell(h_widths[1], 6, str(row.get('subject', 'General')), border=1, align="L")
            pdf.cell(h_widths[2], 6, str(row.get('predicted_score', '')), border=1, align="C")
            pdf.cell(h_widths[3], 6, str(row.get('risk_status', '')), border=1, align="C")
            pdf.cell(h_widths[4], 6, str(row.get('timestamp', '')), border=1, align="C")
            pdf.ln()
            
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
        
    pdf.output(tmp_path)
    return tmp_path

# --- Sidebar Navigation UX ---
st.sidebar.markdown("### 🎓 Academic Portal")
st.sidebar.markdown("---")
role = st.sidebar.radio(
    "Select Portal View:",
    ["🛡️ Administrator Dashboard", "📚 Teacher & Subject Hub", "🎓 Student / Parent Portal"]
)
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Use the Administrator tab to batch upload records or monitor overall institutional metrics.")

# Load Data Safely
@st.cache_data(ttl=5)
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    df = pd.read_csv(DATA_FILE, dtype={'student_id': str})
    if df.empty:
        return df
    df = df.dropna(subset=['study_time_hours', 'attendance_percent', 'previous_grade', 'final_grade'])
    grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
    df['final_grade'] = df['final_grade'].replace(grade_map)
    df['final_grade'] = pd.to_numeric(df['final_grade'], errors='coerce')
    return df.dropna(subset=['final_grade'])

df = load_data()

# Initialize Model
online_model = OnlineSystem()
if not df.empty:
    online_model.train_on_history(df)

# ==========================================
# 1. ADMINISTRATOR VIEW
# ==========================================
if role == "🛡️ Administrator Dashboard":
    st.markdown("""
        <div class="hero-banner">
            <h2>🛡️ Administrator Executive Dashboard</h2>
            <p>Comprehensive system monitoring, master record datasets, and institutional performance audits.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Baseline Records", value=len(df))
    with col2:
        mean_att = f"{df['attendance_percent'].mean():.1f}%" if not df.empty else "0%"
        st.metric(label="Mean Institutional Attendance", value=mean_att)
    with col3:
        mean_study = f"{df['study_time_hours'].mean():.1f} hrs" if not df.empty else "0%"
        st.metric(label="Mean Weekly Study Hours", value=mean_study)
    
    st.markdown("### 📊 Master Student Database")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No student baseline records registered in the database yet.")
        
    st.markdown("---")
    c_imp, c_aud = st.columns(2)
    with c_imp:
        st.markdown("### 📁 Bulk Dataset Management")
        uploaded_file = st.file_uploader("Upload CSV Batch Dataset (Per-Subject Format)", type=["csv"])
        if uploaded_file is not None:
            if st.button("Process Bulk Import", type="primary"):
                success, msg = bulk_import_data(uploaded_file)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"Import failed: {msg}")
                    
    with c_aud:
        st.markdown("### 📜 System Audit Log & Reports")
        if os.path.exists(HISTORY_FILE):
            hist_df = pd.read_csv(HISTORY_FILE)
            st.dataframe(hist_df, use_container_width=True)
            if not hist_df.empty:
                pdf_path = generate_pdf_report(hist_df, "Per-Subject Academic Audit Log")
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download Audit Log as PDF",
                        data=pdf_file,
                        file_name="per_subject_audit.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("No prediction history logs recorded yet.")

# ==========================================
# 2. TEACHER VIEW
# ==========================================
elif role == "📚 Teacher & Subject Hub":
    st.markdown("""
        <div class="hero-banner">
            <h2>📚 Teacher Performance & Intervention Hub</h2>
            <p>Evaluate student metrics across subjects, track academic terms, and generate multi-year report cards.</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🎯 Subject Evaluation & Intervention", "📋 View All Records", "📝 Register / Update Record"])
    
    with tab1:
        existing_ids = df['student_id'].astype(str).str.strip().unique().tolist() if not df.empty else []
        
        if not existing_ids:
            st.warning("No student records found. Please register student metrics under the 'Register / Update Record' tab.")
        else:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                selected_id = st.selectbox("Select Student ID", existing_ids)
            with col_sel2:
                subject_selection = st.selectbox("Select Subject for Evaluation", SUBJECT_LIST)
            
            col_y1, col_y2 = st.columns(2)
            with col_y1:
                year_selection = st.selectbox("Select Academic Year", ["Year 1", "Year 2", "Year 3"])
            with col_y2:
                term_selection = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"])
            
            academic_period = f"{year_selection} - {term_selection}"
            
            student_sub_records = df[
                (df['student_id'].astype(str).str.strip() == selected_id) & 
                (df['subject'] == subject_selection) & 
                (df['term'] == academic_period)
            ]
            
            if student_sub_records.empty:
                st.warning(f"No specific baseline data found for Student **{selected_id}** in **{subject_selection}** for **{academic_period}**. Please update records in the third tab.")
            else:
                student_record = student_sub_records.iloc[0]
                
                st.markdown("---")
                c_res1, c_res2 = st.columns(2)
                with c_res1:
                    st.markdown("#### Student Performance Metrics")
                    st.write(f"**Subject:** {subject_selection}")
                    st.write(f"**Academic Period:** {academic_period}")
                    st.write(f"**Weekly Study Hours:** {student_record['study_time_hours']} hrs")
                    st.write(f"**Attendance Rate:** {student_record['attendance_percent']}%")
                    st.write(f"**Previous Baseline Grade:** {student_record['previous_grade']}")
                    
                with c_res2:
                    pred = online_model.predict(
                        float(student_record['study_time_hours']), 
                        float(student_record['attendance_percent']), 
                        float(student_record['previous_grade'])
                    )
                    st.metric(label=f"Predicted Score ({subject_selection})", value=f"{pred:.2f}")
                    
                    if pred < 2.0 or float(student_record['attendance_percent']) < 70.0:
                        status = "At Risk"
                        st.markdown('<p><span class="badge-danger">⚠️ Status: At Risk</span></p>', unsafe_allow_html=True)
                        st.info("Recommended Action: Assign targeted remediation modules and schedule parent consultation.")
                    else:
                        status = "On Track"
                        st.markdown('<p><span class="badge-success">✅ Status: On Track</span></p>', unsafe_allow_html=True)
                        st.success("Recommended Action: Maintain consistent study habits and positive reinforcement.")
                    
                    if st.button("Save Academic Prediction Log", type="primary"):
                        log_prediction(selected_id, academic_period, pred, status, subject=subject_selection)
                        st.success(f"Prediction for {subject_selection} ({academic_period}) saved successfully!")

            st.markdown("---")
            st.markdown("### 📄 Printable Comprehensive Report Card")
            if st.button("Generate Full Multi-Year & Subject PDF Report Card"):
                history_df = pd.read_csv(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame()
                student_all_records = df[df['student_id'].astype(str).str.strip() == selected_id]
                pdf_path = generate_comprehensive_student_report(selected_id, student_all_records, history_df)
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download Complete Report (.pdf)",
                        data=pdf_file,
                        file_name=f"Comprehensive_Report_{selected_id}.pdf",
                        mime="application/pdf",
                        key=f"download_comprehensive_{selected_id}"
                    )

    with tab2:
        st.markdown("### 📋 Complete Master Record Table On Screen")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No student records registered yet.")
            
        st.markdown("### 📜 Recorded Evaluation & Prediction Logs")
        if os.path.exists(HISTORY_FILE):
            h_screen_df = pd.read_csv(HISTORY_FILE)
            st.dataframe(h_screen_df, use_container_width=True)
        else:
            st.info("No prediction logs saved yet.")

    with tab3:
        st.markdown("### 📝 Register or Update Student Performance per Subject")
        
        c_reg1, c_reg2 = st.columns(2)
        with c_reg1:
            s_id = st.text_input("Student ID")
            s_name = st.text_input("Student Name (Optional)")
            sub_choice = st.selectbox("Subject", SUBJECT_LIST, key="reg_sub")
        with c_reg2:
            reg_year = st.selectbox("Academic Year", ["Year 1", "Year 2", "Year 3"], key="reg_yr")
            reg_term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="reg_trm")
        
        reg_period = f"{reg_year} - {reg_term}"
        
        st.markdown("---")
        c_sl1, c_sl2 = st.columns(2)
        with c_sl1:
            study = st.slider("Weekly Study Hours for this Subject", 0.0, 10.0, 5.0, key="reg_study")
            attn = st.slider("Subject Attendance %", 0.0, 100.0, 90.0, key="reg_attn")
        with c_sl2:
            prev = st.number_input("Previous Grade in Subject", 0.0, 100.0, 70.0, key="reg_prev")
            final = st.selectbox("Baseline Letter Grade Equivalent", ["A", "B", "C", "D", "F"], key="reg_final")
        
        if st.button("Save / Update Student Subject Baseline", type="primary"):
            if not s_id.strip():
                st.error("Please enter a valid Student ID.")
            else:
                record_data = {
                    'student_id': s_id.strip(),
                    'student_name': s_name.strip(),
                    'subject': sub_choice,
                    'academic_year': reg_year,
                    'term': reg_period,
                    'study_time_hours': study,
                    'attendance_percent': attn,
                    'previous_grade': prev,
                    'final_grade': final
                }
                save_new_student_subject_record(record_data)
                st.success(f"Successfully saved record for Student {s_id} in {sub_choice} ({reg_period})!")
                st.rerun()

# ==========================================
# 3. STUDENT / PARENT PORTAL
# ==========================================
elif role == "🎓 Student / Parent Portal":
    st.markdown("""
        <div class="hero-banner">
            <h2>🎓 Student & Parent Portal</h2>
            <p>Access your personalized per-subject breakdown, academic progress history, and performance forecasts.</p>
        </div>
    """, unsafe_allow_html=True)
    
    portal_id = st.text_input("Enter Your Student ID").strip()
    
    if portal_id:
        student_match = df[df['student_id'].astype(str).str.strip() == portal_id]
        
        if student_match.empty:
            st.warning("No records found matching this Student ID. Please check your ID or contact your administrator.")
        else:
            st.success(f"Welcome back! Displaying records for Student ID: **{portal_id}**")
            
            st.markdown("### 📊 Your Per-Subject Performance Baselines")
            st.dataframe(student_match[['subject', 'term', 'study_time_hours', 'attendance_percent', 'previous_grade', 'final_grade']], use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📜 Your Historical Evaluation & Intervention Logs")
            if os.path.exists(HISTORY_FILE):
                h_df = pd.read_csv(HISTORY_FILE, dtype={'student_id': str})
                user_hist = h_df[h_df['student_id'].astype(str).str.strip() == portal_id]
                if not user_hist.empty:
                    st.dataframe(user_hist[['timestamp', 'term', 'subject', 'predicted_score', 'risk_status']], use_container_width=True)
                else:
                    st.info("No saved historical evaluations for this ID yet.")
