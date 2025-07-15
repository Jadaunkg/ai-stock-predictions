# pipeline.py (MODIFIED - Pass app_root to fetch functions and handle new return from report_generator)
import os
import time
import traceback
import re
import logging # For potential direct use in this file, though auto_publisher has its own

import pandas as pd
import yfinance as yf

from config import TICKERS # Assuming TICKERS is still used for the __main__ block test runs
from data_collection import fetch_stock_data
from macro_data import fetch_macro_indicators
from data_preprocessing import preprocess_data
from prophet_model import train_prophet_model
from report_generator import create_full_report, create_wordpress_report_assets # This now returns html, forecast_chart_filepath

# If you want to use logging within this pipeline.py directly:
# pipeline_logger = logging.getLogger(__name__) # Or specific name
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Basic config if not configured elsewhere

# --- Original pipeline function (for full HTML reports - Unchanged) ---
def run_pipeline(ticker, ts, app_root):
    """
    Runs the full analysis pipeline for a given stock ticker.
    Relies on fetch functions for caching, passing app_root for path consistency.
    """
    # Using print for consistency with the original file, but consider a logger
    print(f"\n----- Starting ORIGINAL pipeline for {ticker} -----")
    static_dir_path = os.path.join(app_root, 'static')
    os.makedirs(static_dir_path, exist_ok=True)

    processed_csv = report_path = report_html = None
    model = forecast = None

    try:
        valid_ticker_pattern = r'^[A-Z0-9\^.-]+$'
        if not ticker or not re.match(valid_ticker_pattern, ticker):
             raise ValueError(f"[Original Pipeline] Invalid ticker format: {ticker}.")

        print("Step 1: Fetching stock data (checking cache)...")
        stock_data = fetch_stock_data(ticker, app_root=app_root)
        if stock_data is None or stock_data.empty:
            raise RuntimeError(f"Failed to fetch or load stock data for ticker: {ticker}.")

        print("Step 1b: Fetching macroeconomic data (checking cache)...")
        macro_data = fetch_macro_indicators(app_root=app_root)
        if macro_data is None or macro_data.empty:
            print("Warning: Failed to fetch or load macroeconomic data. Proceeding without it.")

        print("Step 2: Preprocessing data...")
        processed_data = preprocess_data(stock_data, macro_data if macro_data is not None else None)
        if processed_data is None or processed_data.empty:
            raise RuntimeError("Preprocessing resulted in empty dataset.")
        processed_csv = os.path.join(static_dir_path, f"{ticker}_processed_{ts}.csv")
        processed_data.to_csv(processed_csv, index=False)
        print(f"   Saved processed data -> {os.path.basename(processed_csv)}")

        print("Step 3: Training Prophet model & predicting...")
        model, forecast, actual_df, forecast_df = train_prophet_model(
            processed_data, ticker, forecast_horizon='1y', timestamp=ts
        )
        if model is None or forecast is None or actual_df is None or forecast_df is None:
             raise RuntimeError("Prophet model training or forecasting failed.")
        print(f"   Model trained. Forecast generated for {len(forecast_df)} periods.")

        print("Step 4: Fetching fundamentals via yfinance...")
        try:
            yf_ticker_obj = yf.Ticker(ticker) # Renamed to avoid conflict if yf_ticker is used elsewhere
            info_data = {}
            recs_data = pd.DataFrame()
            news_data = []
            try: info_data = yf_ticker_obj.info or {}
            except Exception as info_err: print(f"  Warning: Could not fetch .info for {ticker}: {info_err}")
            try: recs_data = yf_ticker_obj.recommendations if hasattr(yf_ticker_obj, 'recommendations') and yf_ticker_obj.recommendations is not None else pd.DataFrame()
            except Exception as rec_err: print(f"  Warning: Could not fetch .recommendations for {ticker}: {rec_err}")
            try: news_data = yf_ticker_obj.news if hasattr(yf_ticker_obj, 'news') and yf_ticker_obj.news is not None else []
            except Exception as news_err: print(f"  Warning: Could not fetch .news for {ticker}: {news_err}")

            fundamentals = {
                'info': info_data,
                'recommendations': recs_data,
                'news': news_data
            }
            if not fundamentals['info'].get('symbol'):
                 print(f"Warning: Could not fetch detailed info symbol for {ticker} via yfinance.")
        except Exception as yf_err:
             print(f"Warning: Error fetching yfinance fundamentals object for {ticker}: {yf_err}.")
             fundamentals = {'info': {}, 'recommendations': pd.DataFrame(), 'news': []}

        print("Step 5: Generating FULL HTML report...")
        report_path, report_html = create_full_report(
            ticker=ticker, actual_data=actual_df, forecast_data=forecast_df,
            historical_data=processed_data, fundamentals=fundamentals, ts=ts,
            app_root=app_root
        )
        if report_html is None or "Error Generating Report" in report_html:
            raise RuntimeError(f"Original report generator failed or returned error HTML for {ticker}")
        if report_path:
            print(f"   Report saved -> {os.path.basename(report_path)}")
        else:
             print(f"   Report HTML generated, but failed to save file.")

        print(f"----- ORIGINAL Pipeline successful for {ticker} -----")
        return model, forecast, report_path, report_html

    except (ValueError, RuntimeError) as err:
        print(f"----- ORIGINAL Pipeline Error for {ticker} -----")
        print(f"Error: {err}")
        return None, None, None, None
    except Exception as e:
        print(f"----- ORIGINAL Pipeline failure for {ticker} -----")
        print(f"Unexpected Error: {e}")
        traceback.print_exc()
        if processed_csv and os.path.exists(processed_csv):
            try: os.remove(processed_csv)
            except OSError as rm_err: print(f"Error removing file {processed_csv}: {rm_err}")
        return None, None, None, None


# --- WordPress Pipeline Function (MODIFIED) ---
def run_wp_pipeline(ticker, ts, app_root):
    """
    Runs the analysis pipeline specifically to generate WordPress assets.
    Returns model, forecast, HTML content, and filepath of the generated forecast chart.
    Relies on fetch functions for caching, passing app_root.
    """
    # Using print for consistency, consider a logger
    print(f"\n>>>>> Starting WORDPRESS pipeline for {ticker} <<<<<")
    static_dir_path = os.path.join(app_root, 'static') # Used for processed_csv
    os.makedirs(static_dir_path, exist_ok=True)

    processed_csv = None
    text_report_html = None
    forecast_chart_filepath = None # MODIFIED: To store the filepath
    model = forecast = None

    try:
        valid_ticker_pattern = r'^[A-Z0-9\^.-]+$' # Regex for valid tickers
        if not ticker or not re.match(valid_ticker_pattern, ticker):
             raise ValueError(f"[WP Pipeline] Invalid ticker format: {ticker}.")

        # --- Steps 1-4: Data Fetching, Preprocessing, Model Training, Fundamentals ---
        # (These steps remain logically the same as in your provided file)
        print("WP Step 1: Fetching stock data (checking cache)...")
        stock_data = fetch_stock_data(ticker, app_root=app_root)
        if stock_data is None or stock_data.empty:
            raise RuntimeError(f"Failed to fetch/load stock data for {ticker}.")

        print("WP Step 1b: Fetching macroeconomic data (checking cache)...")
        macro_data = fetch_macro_indicators(app_root=app_root)
        if macro_data is None or macro_data.empty:
            print("Warning: Failed to fetch/load macro data for {ticker}. Proceeding without it.")

        print("WP Step 2: Preprocessing data...")
        processed_data = preprocess_data(stock_data, macro_data if macro_data is not None else None)
        if processed_data is None or processed_data.empty:
            raise RuntimeError(f"Preprocessing resulted in empty dataset for {ticker}.")
        processed_csv = os.path.join(static_dir_path, f"{ticker}_wp_processed_{ts}.csv")
        processed_data.to_csv(processed_csv, index=False)
        print(f"   Saved WP processed data for {ticker} -> {os.path.basename(processed_csv)}")

        print("WP Step 3: Training Prophet model & predicting for {ticker}...")
        model, forecast, actual_df, forecast_df = train_prophet_model(
            processed_data, ticker, forecast_horizon='1y', timestamp=ts
        )
        if model is None or forecast is None or actual_df is None or forecast_df is None:
             raise RuntimeError(f"Prophet model training or forecasting failed for {ticker}.")
        print(f"   WP Model trained for {ticker}. Forecast generated for {len(forecast_df)} periods.")

        print(f"WP Step 4: Fetching fundamentals for {ticker}...")
        try:
            yf_ticker_obj = yf.Ticker(ticker) # Renamed to avoid conflict
            info_data = {}
            recs_data = pd.DataFrame()
            news_data = []
            try: info_data = yf_ticker_obj.info or {}
            except Exception as info_err: print(f"  Warning: Could not fetch .info for {ticker}: {info_err}")
            try: recs_data = yf_ticker_obj.recommendations if hasattr(yf_ticker_obj, 'recommendations') and yf_ticker_obj.recommendations is not None else pd.DataFrame()
            except Exception as rec_err: print(f"  Warning: Could not fetch .recommendations for {ticker}: {rec_err}")
            try: news_data = yf_ticker_obj.news if hasattr(yf_ticker_obj, 'news') and yf_ticker_obj.news is not None else []
            except Exception as news_err: print(f"  Warning: Could not fetch .news for {ticker}: {news_err}")
            
            fundamentals = {
                'info': info_data,
                'recommendations': recs_data,
                'news': news_data
            }
            if not fundamentals['info'].get('symbol'):
                print(f"Warning: Could not fetch detailed info symbol for {ticker} via yfinance.")
        except Exception as yf_err:
             print(f"Warning: Error fetching yfinance fundamentals object for {ticker}: {yf_err}.")
             fundamentals = {'info': {}, 'recommendations': pd.DataFrame(), 'news': []}

        # --- Step 5: Generate WORDPRESS Assets ---
        print(f"WP Step 5: Generating WordPress assets for {ticker} (HTML + Forecast Chart Image)...")
        
        # MODIFIED: Unpack html and forecast_chart_filepath
        text_report_html, forecast_chart_filepath = create_wordpress_report_assets(
            ticker=ticker, actual_data=actual_df, forecast_data=forecast_df,
            historical_data=processed_data, fundamentals=fundamentals, ts=ts,
            app_root=app_root # Make sure app_root is passed
        )
        
        if text_report_html is None or "Error Generating Report" in text_report_html:
            print(f"Error HTML from report_generator for {ticker}: {text_report_html}")
            raise RuntimeError(f"WordPress asset generator failed or returned error HTML for {ticker}")

        print(f"   Text HTML generated for {ticker}.")
        if forecast_chart_filepath:
            print(f"   Forecast chart for featured image saved to: {forecast_chart_filepath}")
        else:
            print(f"   WARNING: Forecast chart for featured image was not generated or path not returned for {ticker}.")

        print(f">>>>> WORDPRESS Pipeline successful for {ticker} <<<<<")
        # MODIFIED: Return text_report_html and forecast_chart_filepath
        return model, forecast, text_report_html, forecast_chart_filepath

    except (ValueError, RuntimeError) as err:
        print(f">>>>> WORDPRESS Pipeline Error for {ticker} <<<<<")
        print(f"Error: {err}")
        return None, None, None, None # Ensure four values are returned
    except Exception as e:
        print(f">>>>> WORDPRESS Pipeline failure for {ticker} <<<<<")
        print(f"Unexpected Error: {e}")
        traceback.print_exc()
        if processed_csv and os.path.exists(processed_csv):
            try: os.remove(processed_csv)
            except OSError as rm_err: print(f"Error removing file {processed_csv}: {rm_err}")
        return None, None, None, None # Ensure four values are returned


# --- Main execution block (for standalone testing - Unchanged from your file) ---
if __name__ == "__main__":
    print("Starting batch pipeline execution (with Caching)...")
    # Ensure APP_ROOT_STANDALONE is correctly defined if this block is used.
    # Usually, it's the directory containing this pipeline.py script.
    APP_ROOT_STANDALONE = os.path.dirname(os.path.abspath(__file__))
    print(f"Running standalone from: {APP_ROOT_STANDALONE}")

    # This TICKERS list is from config.py, used for this standalone test run
    # auto_publisher.py will use its own ticker list from Excel via environment variable

    successful_orig, failed_orig = [], []
    successful_wp, failed_wp = [], []

    print("\n--- Running Original Pipeline Batch (Full HTML Reports) ---")
    for ticker_item in TICKERS: # Using ticker_item to avoid conflict with ticker variable inside loop
        run_ts = str(int(time.time()))
        m, f, rp, rh = run_pipeline(ticker_item, run_ts, APP_ROOT_STANDALONE)
        if rp and rh and "Error Generating Report" not in rh:
            successful_orig.append(ticker_item)
            print(f"[✔ Orig] {ticker_item} - Report HTML generated and saved.")
        elif rh and "Error Generating Report" not in rh:
            successful_orig.append(f"{ticker_item} (HTML Only)")
            print(f"[✔ Orig] {ticker_item} - Report HTML generated (Save Failed).")
        else:
            failed_orig.append(ticker_item)
            print(f"[✖ Orig] {ticker_item} - Failed.")
        time.sleep(1) # Brief pause

    print("\nBatch Summary (Original Reports):")
    print(f"  Successful: {', '.join(successful_orig) or 'None'}")
    print(f"  Failed:     {', '.join(failed_orig) or 'None'}")

    print("\n--- Running WP Asset Pipeline Batch (for WordPress assets) ---")
    for ticker_item in TICKERS: # Using ticker_item
        run_ts_wp = str(int(time.time()))
        # MODIFIED: Unpack four values
        model_wp, forecast_wp, text_html_wp, chart_path_wp = run_wp_pipeline(ticker_item, run_ts_wp, APP_ROOT_STANDALONE)
        
        # Check if HTML is generated and if chart_path_wp is either None (ok if chart failed) or a string (path)
        if text_html_wp and "Error Generating Report" not in text_html_wp:
            successful_wp.append(ticker_item)
            print(f"[✔ WP] {ticker_item} - Text HTML generated.")
            if chart_path_wp:
                 print(f"[✔ WP] {ticker_item} - Forecast chart saved to: {chart_path_wp}")
            else:
                 print(f"[✔ WP] {ticker_item} - Forecast chart was not generated or path not returned.")
        else:
            failed_wp.append(ticker_item)
            print(f"[✖ WP] {ticker_item} - WP Asset Generation Failed.")
        time.sleep(1) # Brief pause

    print("\nBatch Summary (WordPress Assets):")
    print(f"  Successful: {', '.join(successful_wp) or 'None'}")
    print(f"  Failed:     {', '.join(failed_wp) or 'None'}")

    print("\nBatch pipeline execution completed.")