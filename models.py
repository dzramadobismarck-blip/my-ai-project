from river import linear_model
from river import preprocessing
from river import compose

class OnlineSystem:
    def __init__(self):
        # We use a pipeline that handles numeric scaling and one-hot encoding for categorical text like 'subject'
        # For simplicity with River, we can map subjects or use standard numeric processing. 
        # If keeping it lightweight, we scale study hours, attendance, and previous grade.
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            linear_model.LinearRegression()
        )
        self.is_trained = False

    def train_on_history(self, df):
        for _, row in df.iterrows():
            features = {
                'study_time_hours': float(row['study_time_hours']),
                'attendance_percent': float(row['attendance_percent']),
                'previous_grade': float(row['previous_grade'])
            }
            target = float(row['final_grade'])
            self.model.learn_one(features, target)
        self.is_trained = True

    def predict(self, study_hours, attendance, prev_grade):
        features = {
            'study_time_hours': float(study_hours),
            'attendance_percent': float(attendance),
            'previous_grade': float(prev_grade)
        }
        pred = self.model.predict_one(features)
        return max(0.0, min(4.0, pred))  # Clamp between 0 and 4 GPA scale