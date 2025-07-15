import time
import schedule
import requests
import json
import base64
import random
import os
import re
import pickle
from dotenv import load_dotenv
from datetime import datetime
from itertools import cycle
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# --- Setup Logging ---
LOG_FILE = "auto_publisher.log"
app_logger = logging.getLogger("AutoPublisherLogger")
if not app_logger.handlers:
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    APP_ROOT_PATH_FOR_LOG = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(APP_ROOT_PATH_FOR_LOG, LOG_FILE)
    handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    app_logger.addHandler(handler)
# --- End Logging Setup ---

# --- Configuration from Environment Variables ---
WORDPRESS_URL = os.environ.get("WORDPRESS_URL")
NUM_WRITERS_STR = os.environ.get("NUM_WRITERS")
FRED_API_KEY = os.environ.get("FRED_API_KEY")
# MODIFIED: Defaulting interval to 75-100 minutes if not set or invalid in .env
MIN_INTERVAL_MINUTES_STR = os.environ.get("MIN_INTERVAL_MINUTES", "1")
MAX_INTERVAL_MINUTES_STR = os.environ.get("MAX_INTERVAL_MINUTES", "2")
WP_CATEGORY_STOCKFORECAST_ID_STR = os.environ.get("WP_CATEGORY_STOCKFORECAST_ID")
EXCEL_FILE_PATH = os.environ.get("EXCEL_FILE_PATH")
EXCEL_TICKER_COLUMN_NAME = os.environ.get("EXCEL_TICKER_COLUMN_NAME")

APP_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_ROOT_PATH, "auto_publisher_state.pkl")

# --- Validate essential configurations ---
if not WORDPRESS_URL: app_logger.error("WORDPRESS_URL not found. Exiting."); exit(1)
WORDPRESS_URL = WORDPRESS_URL.rstrip('/')
if not EXCEL_FILE_PATH or not os.path.exists(EXCEL_FILE_PATH): app_logger.error(f"EXCEL_FILE_PATH invalid: {EXCEL_FILE_PATH}. Exiting."); exit(1)
if not EXCEL_TICKER_COLUMN_NAME: app_logger.error("EXCEL_TICKER_COLUMN_NAME not found. Exiting."); exit(1)
try: NUM_WRITERS = int(NUM_WRITERS_STR) if NUM_WRITERS_STR else 0
except ValueError: app_logger.error(f"NUM_WRITERS ('{NUM_WRITERS_STR}') invalid. Exiting."); exit(1)

try:
    MIN_INTERVAL_MINUTES = int(MIN_INTERVAL_MINUTES_STR)
    MAX_INTERVAL_MINUTES = int(MAX_INTERVAL_MINUTES_STR)
    if MIN_INTERVAL_MINUTES <= 0 or MAX_INTERVAL_MINUTES <= 0:
        app_logger.warning("Interval minutes must be positive. Using defaults 1-2 min.")
        MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES = 1, 2
    elif MIN_INTERVAL_MINUTES > MAX_INTERVAL_MINUTES :
        app_logger.warning(f"MIN_INTERVAL_MINUTES ({MIN_INTERVAL_MINUTES}) must be less than or equal to MAX_INTERVAL_MINUTES ({MAX_INTERVAL_MINUTES}). Using defaults 75-100 min.")
        MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES = 1, 2
except ValueError:
    app_logger.warning(f"Intervals from .env invalid. Defaulting to 1-2 min.")
    MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES = 1, 2

WP_CATEGORY_STOCKFORECAST_ID = None
if WP_CATEGORY_STOCKFORECAST_ID_STR:
    try: WP_CATEGORY_STOCKFORECAST_ID = int(WP_CATEGORY_STOCKFORECAST_ID_STR)
    except ValueError: app_logger.warning(f"WP_CATEGORY_STOCKFORECAST_ID ('{WP_CATEGORY_STOCKFORECAST_ID_STR}') invalid.")

WRITERS_CONFIG = []
if NUM_WRITERS > 0:
    for i in range(1, NUM_WRITERS + 1):
        username, app_password_env, wp_user_id_str = os.environ.get(f'WRITER_{i}_USERNAME'), os.environ.get(f'WRITER_{i}_APP_PASSWORD'), os.environ.get(f'WRITER_{i}_WP_USER_ID')
        if username and app_password_env and wp_user_id_str:
            try:
                wp_user_id = int(wp_user_id_str)
                app_password_cleaned = app_password_env.replace('\u00a0', '').replace(' ', '')
                WRITERS_CONFIG.append({"username": username, "app_password": app_password_cleaned, "wp_user_id": wp_user_id})
            except ValueError: app_logger.warning(f"Invalid WP_USER_ID for writer {i}. Skipping.")
        else: app_logger.warning(f"Missing details for writer {i}. Skipping.")
if not WRITERS_CONFIG: app_logger.error("No valid writers configured. Exiting."); exit(1)

try:
    from pipeline import run_wp_pipeline
except ImportError: app_logger.error("Could not import run_wp_pipeline. Exiting."); exit(1)

HEADLINE_TEMPLATES = [ # Your existing headlines
    "{ticker} Stock Price Forecast & Expert Insights for {year_range}",
    "{ticker} Stock Prediction, and Price Target ({year_range}) - What Experts Say",
    "{ticker} Future Stock Price & Technical Analysis {year_range}",
    "{ticker} Stock Forecast {year_range}: Expert Analysis and Predictions",
    "{ticker} Stock Price Targets and Technical Analysis for {year_range}",
    "Analyst View on {ticker}: Key Predictions and Price Forecast {year_range}",
    "The Future of {ticker} Stock Price Predictions and Analysis for {year_range}",
    "Expert Take: {ticker} Stock Forecast, Analysis, and Predictions {year_range}",
    "Is {ticker} a Buy? {year_range} Stock Analysis and Price Forecast",
    "{ticker} {year_range} Forecast: Technical Analysis & Price Predictions"
]

# --- Ticker and Writer State Management ---
def load_tickers_from_excel(file_path, column_name):
    # This function extracts the first "word" as the ticker (e.g., "INTEL" from "INTEL stock")
    # No mapping dictionary is used here as per your request.
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        if column_name not in df.columns:
            app_logger.error(f"Column '{column_name}' not in Excel '{file_path}'. Cols: {df.columns.tolist()}")
            return []
        raw_entries = df[column_name].dropna().astype(str).str.strip().tolist()
        ordered_unique_tickers, seen_tickers = [], set()
        for item in raw_entries:
            if item:
                # Extract the first "word", assume it's the ticker symbol, and convert to uppercase
                symbol_candidate = item.split(' ')[0].upper()
                # Clean it for typical ticker patterns (letters, numbers, dot, hyphen)
                symbol_candidate = re.sub(r'[^A-Z0-9.-]', '', symbol_candidate)
                if symbol_candidate and symbol_candidate not in seen_tickers:
                    ordered_unique_tickers.append(symbol_candidate)
                    seen_tickers.add(symbol_candidate)
        app_logger.info(f"Loaded {len(ordered_unique_tickers)} order-preserved unique tickers from Excel.")
        return ordered_unique_tickers
    except Exception as e:
        app_logger.exception(f"Error loading tickers from Excel '{file_path}':")
        return []

MASTER_TICKERS_LIST = load_tickers_from_excel(EXCEL_FILE_PATH, EXCEL_TICKER_COLUMN_NAME)
if not MASTER_TICKERS_LIST:
    app_logger.error("No tickers loaded from Excel. Exiting.")
    exit(1)

def load_state():
    default_state = {
        'pending_tickers': list(MASTER_TICKERS_LIST),
        'last_writer_index': -1,
        'failed_tickers_retry_later': [] # Initialize new state key
    }
    if os.path.exists(STATE_FILE):
        app_logger.info(f"Attempting to load state from '{STATE_FILE}'")
        try:
            with open(STATE_FILE, 'rb') as f:
                state = pickle.load(f)
                # Validate pending tickers
                loaded_pending = state.get('pending_tickers', [])
                state['pending_tickers'] = [t for t in loaded_pending if t in MASTER_TICKERS_LIST]
                if not state['pending_tickers'] and MASTER_TICKERS_LIST:
                     app_logger.info("Pending tickers from state empty/invalid; re-initializing from master.")
                     state['pending_tickers'] = list(MASTER_TICKERS_LIST)
                
                # Load and validate failed tickers
                loaded_failed = state.get('failed_tickers_retry_later', [])
                state['failed_tickers_retry_later'] = [t for t in loaded_failed if t in MASTER_TICKERS_LIST] # Ensure they are still relevant

                # Validate last_writer_index
                current_last_writer_index = state.get('last_writer_index', -1)
                if not isinstance(current_last_writer_index, int) or \
                   current_last_writer_index >= len(WRITERS_CONFIG) or \
                   current_last_writer_index < -1:
                    state['last_writer_index'] = -1
                
                app_logger.info(f"Loaded state: {len(state.get('pending_tickers',[]))} pending, {len(state.get('failed_tickers_retry_later',[]))} failed, last writer index {state.get('last_writer_index', -1)}.")
                return state
        except Exception as e:
            app_logger.warning(f"Could not load state from '{STATE_FILE}': {e}. Using default state.")
    app_logger.info("No state file. Initializing with default state.")
    return default_state

def save_state(current_pending_tickers, current_writer_index, current_failed_tickers):
    app_logger.info(f"Attempting to save state: {len(current_pending_tickers)} pending, {len(current_failed_tickers)} failed, writer index {current_writer_index}.")
    try:
        with open(STATE_FILE, 'wb') as f:
            pickle.dump({
                'pending_tickers': current_pending_tickers,
                'last_writer_index': current_writer_index,
                'failed_tickers_retry_later': current_failed_tickers # Save new state key
            }, f)
        app_logger.info(f"Successfully saved state to {STATE_FILE}")
    except Exception as e:
        app_logger.exception(f"Could not save state to '{STATE_FILE}':")

# --- Global State Initialization ---
current_state = load_state()
pending_tickers = current_state['pending_tickers']
last_writer_idx_processed = current_state['last_writer_index']
failed_tickers = current_state.get('failed_tickers_retry_later', []) # Initialize

if WRITERS_CONFIG:
    writer_start_offset = (last_writer_idx_processed + 1) % len(WRITERS_CONFIG)
    reordered_writers = WRITERS_CONFIG[writer_start_offset:] + WRITERS_CONFIG[:writer_start_offset]
    writer_iterator = cycle(reordered_writers)
    if reordered_writers: app_logger.info(f"Writer iterator will start with: {reordered_writers[0]['username']}")
else: writer_iterator = cycle([])

posts_published_today = 0
last_publish_time = None

# --- Helper Functions (generate_post_title, create_slug, etc. - keep your existing unless specified) ---
def get_report_html_and_chart(ticker, app_root):
    app_logger.info(f"Generating report and chart for ticker: {ticker}")
    timestamp = str(int(time.time()))
    report_html, forecast_chart_file = None, None
    try:
        # Assuming run_wp_pipeline returns: model, forecast, html_output, forecast_chart_filepath
        _model, _forecast, report_html, forecast_chart_file = run_wp_pipeline(ticker, timestamp, app_root)
        if report_html and "Error Generating Report" not in report_html:
            app_logger.info(f"Report HTML generated for {ticker}.")
            if forecast_chart_file: app_logger.info(f"Forecast chart file generated: {forecast_chart_file}")
            else: app_logger.warning(f"Forecast chart file NOT generated for {ticker}.")
        else: # This case includes when pipeline itself signals an error like data not found
            app_logger.error(f"Failed to generate report HTML (or pipeline error) for {ticker}.")
            report_html, forecast_chart_file = None, None 
    except Exception as e: # Catch any other unexpected errors from pipeline
        app_logger.exception(f"Exception during pipeline run for {ticker}:")
        report_html, forecast_chart_file = None, None
    return report_html, forecast_chart_file

def generate_post_title(ticker, writer_info): # As per your script
    year_range_fixed = "2025-26"
    template = random.choice(HEADLINE_TEMPLATES)
    title = template.format(ticker=ticker, year_range=year_range_fixed, writer_name=writer_info['username'])
    max_title_length = 90
    if len(title) > max_title_length:
        last_space = title.rfind(' ', 0, max_title_length - 3)
        title = title[:last_space] + "..." if last_space != -1 else title[:max_title_length - 3] + "..."
    return title

def create_slug(title, max_length=60): # As per your script
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug); slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug); slug = slug.strip('-')
    if len(slug) > max_length:
        trimmed_slug = slug[:max_length]
        last_hyphen_index = trimmed_slug.rfind('-')
        slug = trimmed_slug[:last_hyphen_index] if last_hyphen_index > 0 else trimmed_slug
    return slug

def upload_featured_image_to_wordpress(image_path, ticker, writer_info, post_title_for_image): # As per your script
    if not image_path or not os.path.exists(image_path):
        app_logger.warning(f"Featured image path DNE: '{image_path}' for {ticker}"); return None
    media_api_url = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
    credentials = f"{writer_info['username']}:{writer_info['app_password']}"
    token = base64.b64encode(credentials.encode())
    headers = {"Authorization": f"Basic {token.decode('utf-8')}"}
    image_filename = f"{create_slug(ticker, 30)}-fc-{datetime.now().strftime('%Y%m%d%H%M')}.png"
    with open(image_path, 'rb') as img_file:
        files = {'file': (image_filename, img_file, 'image/png')}
        data_payload = {'title': f"{ticker} Stock Forecast Chart - Featured", 'alt_text': f"Featured: {ticker} stock forecast chart", 'caption': f"Forecast chart for {post_title_for_image}"}
        try:
            app_logger.info(f"Uploading feat img '{image_filename}' for {ticker} from {image_path}")
            response = requests.post(media_api_url, headers=headers, files=files, data=data_payload, timeout=60)
            response.raise_for_status()
            media_data = response.json(); uploaded_image_id = media_data.get('id')
            app_logger.info(f"Uploaded feat img for {ticker}, Media ID: {uploaded_image_id}"); return uploaded_image_id
        except Exception as e:
            app_logger.error(f"Error uploading feat img for {ticker}: {e}")
            if 'response' in locals() and response is not None: app_logger.error(f"WP Img Upload Resp: {response.text}")
            return None
        finally:
            try:
                if os.path.exists(image_path): os.remove(image_path); app_logger.info(f"Cleaned temp img: {image_path}")
            except Exception as e_clean: app_logger.warning(f"Could not clean temp img {image_path}: {e_clean}")

def publish_to_wordpress(writer_info, ticker, report_html_content, forecast_chart_file_path): # As per your script
    post_title = generate_post_title(ticker, writer_info)
    post_slug = create_slug(post_title, max_length=60)
    post_status = "draft" # Publishing as draft
    credentials = f"{writer_info['username']}:{writer_info['app_password']}"
    token = base64.b64encode(credentials.encode())
    headers = {"Authorization": f"Basic {token.decode('utf-8')}", "Content-Type": "application/json"}
    api_url = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    payload = {"title": post_title, "content": report_html_content, "status": post_status, "author": writer_info['wp_user_id'], "slug": post_slug}
    if WP_CATEGORY_STOCKFORECAST_ID: payload["categories"] = [WP_CATEGORY_STOCKFORECAST_ID]
    uploaded_feature_image_id = upload_featured_image_to_wordpress(forecast_chart_file_path, ticker, writer_info, post_title) if forecast_chart_file_path else None
    if uploaded_feature_image_id: payload["featured_media"] = uploaded_feature_image_id
    else: app_logger.warning(f"No feat img ID for post on {ticker}.")
    app_logger.info(f"Attempting publish '{post_title}' (Slug: {post_slug}) by {writer_info['username']}.")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        app_logger.info(f"Report uploaded for {ticker} by {writer_info['username']}! Post ID: {response.json().get('id')}")
        return True
    except Exception as e:
        app_logger.error(f"Error publishing for {ticker} by {writer_info['username']}: {e}")
        if 'response' in locals() and response is not None: app_logger.error(f"WP Post Resp: {response.text}")
        return False
# --- End Helper Functions ---

def job():
    global posts_published_today, last_publish_time, writer_iterator, \
           pending_tickers, MASTER_TICKERS_LIST, last_writer_idx_processed, failed_tickers
    current_time = datetime.now()

    if last_publish_time and last_publish_time.date() != current_time.date():
        app_logger.info("New day. Resetting daily post count.")
        posts_published_today = 0

    if posts_published_today >= 15:
        app_logger.info(f"Daily post limit (15) reached for {current_time.date()}. Skipping.")
        return

    if not pending_tickers: # Current cycle's main pending list is empty
        if failed_tickers: # Check if there are previously failed tickers to retry
            app_logger.info(f"Main pending list exhausted. Processing {len(failed_tickers)} previously failed tickers from retry list.")
            pending_tickers = list(failed_tickers) # Process these now
            failed_tickers.clear() # Clear the retry list as we are now processing them
            # State will be saved at the end of the job with the new pending_tickers (from failed) and cleared failed_tickers
        else: # No failed tickers, so truly start a new cycle from master
            app_logger.info("All tickers (including any retries) processed. Re-initializing pending_tickers from master list.")
            pending_tickers = list(MASTER_TICKERS_LIST)
        
        if not pending_tickers: # If master list was also empty OR failed list was processed and now empty
            app_logger.warning("Master/failed ticker list is empty. No tickers to process for this cycle.")
            save_state(pending_tickers, last_writer_idx_processed, failed_tickers) 
            return
        # If pending_tickers was repopulated, save_state will happen at the end of this job attempt

    if not pending_tickers: # Should be populated now if MASTER_TICKERS_LIST had items
        app_logger.warning("Pending ticker list is still empty after re-init attempt. Skipping job.")
        return

    selected_ticker_to_process = pending_tickers[0] # Peek at the next ticker
    selected_writer_info = next(writer_iterator)
    
    try:
        current_writer_original_index = WRITERS_CONFIG.index(selected_writer_info)
    except ValueError:
        app_logger.error(f"Critical: Writer {selected_writer_info['username']} not in WRITERS_CONFIG! Defaulting index.")
        current_writer_original_index = (last_writer_idx_processed + 1) % len(WRITERS_CONFIG) if WRITERS_CONFIG else -1

    app_logger.info(f"--- Starting job for Ticker: {selected_ticker_to_process}, Writer: {selected_writer_info['username']} (Original Idx: {current_writer_original_index}) ---")
    app_logger.info(f"    (Pending this cycle: {len(pending_tickers)}, For later retry: {len(failed_tickers)})")

    # Attempt to get report data. This will use the exact ticker string from Excel (after basic cleaning).
    # No additional mapping is done here as per request.
    report_html, forecast_chart_file = get_report_html_and_chart(selected_ticker_to_process, APP_ROOT_PATH)
    
    # Regardless of success or failure of getting data, remove the ticker from the current pending list.
    # It will either be processed or moved to the failed_tickers list.
    processed_ticker_from_pending = pending_tickers.pop(0)
    if processed_ticker_from_pending != selected_ticker_to_process: # Should always be true
        app_logger.warning(f"Popped ticker {processed_ticker_from_pending} differs from selected {selected_ticker_to_process}. Using {selected_ticker_to_process}.")
        # This case is unlikely if logic is sound, means pending_tickers was modified unexpectedly.

    if report_html: # If HTML/Chart generation itself was somewhat successful
        if publish_to_wordpress(selected_writer_info, selected_ticker_to_process, report_html, forecast_chart_file):
            # Successfully published to WordPress
            posts_published_today += 1
            last_publish_time = current_time
            app_logger.info(f"    Posts published today ({current_time.date()}): {posts_published_today}")
            # Ticker was already popped from pending_tickers.
        else:
            # Failed to publish to WordPress (but HTML was generated)
            app_logger.error(f"    Failed to publish WP post for {selected_ticker_to_process}. Adding to retry list.")
            if selected_ticker_to_process not in failed_tickers:
                 failed_tickers.append(selected_ticker_to_process)
    else:
        # Failed to generate HTML/Chart (e.g., data collection error for 'INTEL')
        app_logger.error(f"    Failed to generate report data for {selected_ticker_to_process}. Adding to retry list.")
        if selected_ticker_to_process not in failed_tickers: # Avoid duplicates in retry list
            failed_tickers.append(selected_ticker_to_process)

    last_writer_idx_processed = current_writer_original_index 
    save_state(pending_tickers, last_writer_idx_processed, failed_tickers) # Save all three state parts
    app_logger.info(f"--- Job finished for Ticker: {selected_ticker_to_process} ---")

# --- Scheduling Logic (Unchanged) ---
def schedule_next_job():
    delay_minutes = random.randint(MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES)
    app_logger.info(f"Scheduling next job in {delay_minutes} minutes.")
    schedule.clear()
    schedule.every(delay_minutes).minutes.do(run_job_and_reschedule)

def run_job_and_reschedule():
    job()
    schedule_next_job()
    return schedule.CancelJob

if __name__ == "__main__":
    app_logger.info("--- Starting Auto Publisher Service ---")
    app_logger.info(f"    State file: {STATE_FILE}")
    app_logger.info(f"    Publishing to: {WORDPRESS_URL}")
    # ... (rest of your existing __main__ startup logging - unchanged) ...
    app_logger.info(f"    Writers Configured: {len(WRITERS_CONFIG)}")
    app_logger.info(f"    Tickers in Master List (Excel): {len(MASTER_TICKERS_LIST)}")
    app_logger.info(f"    Tickers Initially Pending: {len(pending_tickers)}")
    app_logger.info(f"    Tickers Initially in Retry List: {len(failed_tickers)}")
    app_logger.info(f"    Posting Interval: {MIN_INTERVAL_MINUTES}-{MAX_INTERVAL_MINUTES} minutes")
    if WP_CATEGORY_STOCKFORECAST_ID:
        app_logger.info(f"    Default Category ID: {WP_CATEGORY_STOCKFORECAST_ID}")
    
    app_logger.info("Scheduling the first job...")
    schedule_next_job()

    app_logger.info("Scheduler started. Waiting for first scheduled run...")
    while True:
        schedule.run_pending()
        time.sleep(30)