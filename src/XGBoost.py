
import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

#Load the processed dataset
df = pd.read_csv('datasets/processed/df_15min.csv', parse_dates=['Datetime'])
df.set_index('Datetime', inplace=True)

# Prepare lag features
def create_lag_features(data, lag=5):
    for i in range(1, lag + 1):
        data[f'lag_{i}'] = data['Traffic_flow'].shift(i)
    return data.dropna()

df = create_lag_features(df, lag=5)

# Scale features 
x_scaler = MinMaxScaler()
y_scaler = MinMaxScaler()

X = x_scaler.fit_transform(df.drop('Traffic_flow', axis=1))
y = y_scaler.fit_transform(df[['Traffic_flow']])

# Train/Test split 
split_index = int(len(X) * 0.8)
X_train, X_test = X[:split_index], X[split_index:]
y_train, y_test = y[:split_index], y[split_index:]

# Train model 
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
model.fit(X_train, y_train.ravel())

# Evaluate 
y_pred = model.predict(X_test)
y_pred_inv = y_scaler.inverse_transform(y_pred.reshape(-1, 1))
y_test_inv = y_scaler.inverse_transform(y_test)

mae = mean_absolute_error(y_test_inv, y_pred_inv)
rmse = mean_squared_error(y_test_inv, y_pred_inv, squared=False)

print(f"XGBoost MAE: {mae:.2f}, RMSE: {rmse:.2f}")

# Save model and scalers 
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/xgb_model.pkl')
joblib.dump(x_scaler, 'models/xgb_x_scaler.pkl')
joblib.dump(y_scaler, 'models/xgb_y_scaler.pkl')
