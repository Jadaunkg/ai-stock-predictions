# ai-stock-predictions/evaluation.py
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pandas as pd

def calculate_mape(y_true, y_pred):
    """
    Calculate Mean Absolute Percentage Error (MAPE).
    Handles potential division by zero.
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # Remove pairs where true value is zero to avoid division by zero
    non_zero_mask = y_true != 0
    y_true_filtered = y_true[non_zero_mask]
    y_pred_filtered = y_pred[non_zero_mask]

    if len(y_true_filtered) == 0:
        return np.nan # Or 0, or raise an error, depending on desired behavior

    return np.mean(np.abs((y_true_filtered - y_pred_filtered) / y_true_filtered)) * 100

def calculate_evaluation_metrics(y_true, y_pred):
    """
    Calculates and returns various evaluation metrics.

    Args:
        y_true (pd.Series or np.array): Actual target values.
        y_pred (pd.Series or np.array): Predicted values from the model.

    Returns:
        dict: A dictionary containing the calculated metrics:
              'MSE', 'MAE', 'RMSE', 'MAPE', 'R2 Score'.
              Returns None if inputs are invalid or calculation fails.
    """
    # Input validation
    if y_true is None or y_pred is None:
        print("Error: Input y_true or y_pred is None.")
        return None
    if len(y_true) != len(y_pred):
        print(f"Error: Length mismatch between y_true ({len(y_true)}) and y_pred ({len(y_pred)}).")
        return None
    if len(y_true) == 0:
        print("Error: Input arrays are empty.")
        return None

    # Ensure numpy arrays for calculations
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Check for NaN/inf values that can break calculations
    if np.isnan(y_true).any() or np.isinf(y_true).any() or \
       np.isnan(y_pred).any() or np.isinf(y_pred).any():
        print("Warning: NaN or Inf values detected in y_true or y_pred. Attempting to proceed by removing them.")
        # Create a mask for valid (non-NaN, non-Inf) pairs
        valid_mask = ~np.isnan(y_true) & ~np.isinf(y_true) & \
                     ~np.isnan(y_pred) & ~np.isinf(y_pred)
        y_true = y_true[valid_mask]
        y_pred = y_pred[valid_mask]
        if len(y_true) == 0:
            print("Error: No valid data points remaining after removing NaN/Inf.")
            return None

    try:
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mape = calculate_mape(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        metrics = {
            'MSE': mse,
            'MAE': mae,
            'RMSE': rmse,
            'MAPE (%)': mape,  # Indicate MAPE is a percentage
            'R2 Score': r2
        }
        return metrics
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None

def print_metrics(metrics_dict):
    """Prints the calculated metrics in a formatted way."""
    if metrics_dict:
        print("\n--- Model Evaluation Metrics ---")
        for name, value in metrics_dict.items():
             # Format MAPE with % sign, others with fixed decimals
             if "MAPE" in name:
                 print(f"  {name:<10}: {value:.2f}%")
             else:
                 print(f"  {name:<10}: {value:.4f}")
        print("------------------------------\n")
    else:
        print("\n--- Model Evaluation Metrics ---")
        print("  Metrics could not be calculated.")
        print("------------------------------\n")