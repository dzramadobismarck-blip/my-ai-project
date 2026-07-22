import pandas as pd
import os

FILE_PATH = 'student_performance_dataset.csv'

def clean_dataset():
    if not os.path.exists(FILE_PATH):
        print(f"Error: {FILE_PATH} not found.")
        return

    print("Reading dataset...")
    # Read everything with student_id forced as a string
    df = pd.read_csv(FILE_PATH, dtype={'student_id': str})

    # 1. Clean student_id: strip spaces and remove trailing decimal zeros if any exist
    if 'student_id' in df.columns:
        df['student_id'] = (
            df['student_id']
            .astype(str)
            .str.replace(r'\.0$', '', regex=True)
            .str.strip()
        )

    # 2. Drop completely empty rows
    df = df.dropna(how='all')

    # 3. Save the cleaned dataset back to CSV
    df.to_csv(FILE_PATH, index=False)
    print(f"Successfully cleaned {FILE_PATH}! Total records: {len(df)}")
    print(df.head())

if __name__ == "__main__":
    clean_dataset()