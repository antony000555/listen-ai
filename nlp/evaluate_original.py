import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
import importlib.util
import sys

# Load the original app module
spec = importlib.util.spec_from_file_location("app_original", "app-original.py")
app_original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_original)

# Read the CSV file
df = pd.read_csv('sentiment_result_augmented.csv')

# Ensure SENTIMENT column is lowercase and handle missing values
df['SENTIMENT'] = df['SENTIMENT'].str.lower().fillna('neutral')

# Predict using original algorithm
def get_prediction(text):
    if pd.isna(text):
        return 'neutral'
    return app_original.classify_text(str(text))[0]

df['predicted'] = df['content'].apply(get_prediction)

# Calculate metrics
y_true = df['SENTIMENT']
y_pred = df['predicted']

print("=== Evaluation Results (Original Algorithm vs LLM Labels) ===")
print("Accuracy:", accuracy_score(y_true, y_pred))
print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=['negative', 'neutral', 'positive'], labels=['negative', 'neutral', 'positive']))