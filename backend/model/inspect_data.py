import pandas as pd

print("Loading dataset...")
df = pd.read_csv('C:/Users/user/Desktop/mental-health-ai-journal/dataset/train.csv')

print("\n--- DETECTIVE REPORT ---")
print("Unique sentiment numbers found in the file:")
print(df['sentiment'].unique())
print("------------------------")