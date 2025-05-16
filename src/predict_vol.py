import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from datetime import datetime

def load_sequence(df, sequence_length=8, target_time="2006-10-31 08:00"):
    """
    For each SCATS site, extract the last `sequence_length` flow values before `target_time`
    """
    target_dt = pd.to_datetime(target_time)
    df["Datetime"] = pd.to_datetime(df["Datetime"])

    input_data = []

    grouped = df.groupby("SCATS Number")
    for site_id, group in grouped:
        site_df = group[["Datetime", "Traffic_flow"]].sort_values("Datetime")
        site_df = site_df[site_df["Datetime"] < target_dt]

        if len(site_df) < sequence_length:
            continue

        last_sequence = site_df.iloc[-sequence_length:]["Traffic_flow"].values
        input_data.append((site_id, last_sequence))

    return input_data


def predict_volume(input_data, model, x_scaler, y_scaler):
    """
    Takes a list of (site_id, last_8_flows) and returns site_id → predicted volume
    """
    volume_dict = {}

    for site_id, sequence in input_data:
        X = x_scaler.transform(sequence.reshape(-1, 1)).reshape(1, -1, 1)
        y_pred_scaled = model.predict(X, verbose=0)
        y_pred = y_scaler.inverse_transform(y_pred_scaled)[0][0]
        volume_dict[site_id] = round(float(y_pred), 2)

    return volume_dict


def pred_vol_for_time(target_time, save_debug_version=False):
    """
    Load model, scalers, and predict volume_dict for a given time.
    """
    # load necessary data and models
    df = pd.read_csv("datasets/processed/df_15min.csv")
    model = load_model("models/lstm_model_08step.h5", compile=False)
    x_scaler = joblib.load("models/x_scaler_08step.pkl")
    y_scaler = joblib.load("models/y_scaler_08step.pkl")

    # prep inputs and predict
    input_data = load_sequence(df, target_time=target_time)
    volume_dict = predict_volume(input_data, model, x_scaler, y_scaler)

    # saving with time stamp - DEBUGGING
    if save_debug_version:
        safe_time = target_time.replace(":", "-").replace(" ", "_")
        joblib.dump(volume_dict, f"models/volume_dict_{safe_time}.pkl")
        print(f" saved debugging volume_dict for {target_time} at: volume_dict_{safe_time}.pkl")

    return volume_dict


#  test runner
#if __name__ == "__main__":
 #   selected_time = "2006-10-31 08:00"
  #  volume_dict = pred_vol_for_time(selected_time, save_debug_version=True)
   # print(f"Predicted {len(volume_dict)} volumes at {selected_time}")
