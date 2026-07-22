import pandas as pd
import os

DATA_FILE = "student_data.csv"
HISTORY_FILE = "prediction_history.csv"

def initialize_files():
    # Primary student dataset supporting per-subject tracking
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'student_id', 'student_name', 'subject', 'academic_year', 
            'term', 'study_time_hours', 'attendance_percent', 'previous_grade', 'final_grade'
        ])
        df.to_csv(DATA_FILE, index=False)
        
    # History file for logged predictions/interventions
    if not os.path.exists(HISTORY_FILE):
        hist_df = pd.DataFrame(columns=[
            'timestamp', 'student_id', 'subject', 'term', 'predicted_score', 'risk_status'
        ])
        hist_df.to_csv(HISTORY_FILE, index=False)

def save_new_student_subject_record(record_dict):
    """Saves a new student record tied to a specific subject and academic period."""
    if not os.path.exists(DATA_FILE):
        initialize_files()
    df = pd.read_csv(DATA_FILE, dtype={'student_id': str})
    
    # Check if a record for this student, subject, and term already exists
    mask = (
        (df['student_id'].astype(str).str.strip() == str(record_dict['student_id']).strip()) & 
        (df['subject'] == record_dict['subject']) & 
        (df['term'] == record_dict['term'])
    )
    
    if not df[mask].empty:
        # Update existing record
        for key, value in record_dict.items():
            df.loc[mask, key] = value
    else:
        # Append new row
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