# app.py (MODIFIED: Removed site_name requirement from /generate-wp-assets)

from flask import Flask, render_template, request, send_from_directory, jsonify, url_for
import os
import time # Import the time module
import traceback
import re
from pipeline import run_pipeline, run_wp_pipeline # Keep both pipelines
from urllib.parse import urljoin, quote

# --- Setup (Unchanged) ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(APP_ROOT, 'static')
TEMPLATE_FOLDER_PATH = os.path.join(APP_ROOT, 'templates')
app = Flask(__name__,
            static_folder=STATIC_FOLDER_PATH,
            template_folder=TEMPLATE_FOLDER_PATH)
app.jinja_env.globals.update(zip=zip)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = os.urandom(24)
os.makedirs(STATIC_FOLDER_PATH, exist_ok=True)

# --- Rate Limiting Delay (Unchanged from your provided code) ---
API_DELAY_SECONDS = 1.0

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename, cache_timeout=0)

# --- Original Routes (Unchanged) ---
@app.route('/', methods=['GET'])
def index():
    # Ensure the template file exists relative to TEMPLATE_FOLDER_PATH
    template_path = os.path.join(app.template_folder, 'stock-analysis-homepage.html')
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found at {template_path}")
        return "Error: Homepage template not found.", 500
    return render_template('stock-analysis-homepage.html')

@app.route('/report/view')
def show_report_page():
    report_url = request.args.get('url')
    ticker = request.args.get('ticker', 'Unknown')
    # Ensure the template file exists relative to TEMPLATE_FOLDER_PATH
    template_path = os.path.join(app.template_folder, 'report_display.html')
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found at {template_path}")
        return "Error: Report display template not found.", 500
    return render_template('report_display.html', report_url=report_url, ticker=ticker)

@app.route('/generate', methods=['POST'])
def generate_report():
    """
    Handles the asynchronous request to generate the standard stock analysis report.
    Includes an increased delay to help prevent rate limiting.
    """
    start_time = time.time()
    print("\n--- Received /generate request (Original Report) ---")

    # --- ADD DELAY ---
    print(f"Adding {API_DELAY_SECONDS}s delay before processing...")
    time.sleep(API_DELAY_SECONDS)
    # ---------------

    if not request.is_json: # ... (rest of the function unchanged)
        print("Error: Request must be JSON")
        return jsonify({'status': 'error', 'message': 'Invalid request format. Expected JSON.'}), 400
    data = request.get_json(); ticker = data.get('ticker', '').strip().upper(); print(f"Received ticker: {ticker}")
    valid_ticker_pattern = r'^[A-Z0-9\^.-]+$'
    # Get site_name - still needed for the original pipeline logic branch
    site_name = data.get('site_name', '').strip()
    print(f"Received site_name: {site_name}")

    if not ticker or not re.match(valid_ticker_pattern, ticker):
        error_message = "Invalid ticker symbol format."; print(f"Validation Error: {error_message}"); return jsonify({'status': 'error', 'message': error_message}), 400
    try:
        timestamp = str(int(time.time()))
        viewer_url = "#" # Default viewer URL
        status_message = "error" # Default status

        # --- Conditional Logic based on site_name ---
        # Check if site_name exists AND matches for the WP path
        if site_name and site_name == 'moneystockers':
            print(f"Running WP pipeline for {ticker} (Site: {site_name}) with ts {timestamp}...")
            model, forecast, text_report_html, image_urls = run_wp_pipeline(ticker, timestamp, APP_ROOT) # Call WP pipeline
            if text_report_html and "Error Generating Report" not in text_report_html:
                 wp_report_filename = f"{ticker}_wp_asset_{timestamp}.html"
                 wp_report_path = os.path.join(STATIC_FOLDER_PATH, wp_report_filename)
                 try:
                     with open(wp_report_path, 'w', encoding='utf-8') as f: f.write(text_report_html)
                     print(f"Saved WP HTML fragment to: {wp_report_filename}")
                     report_file_url = url_for('serve_static', filename=wp_report_filename, _external=False)
                     # Still using report_display for WP assets temporarily, can be adjusted
                     viewer_url = url_for('show_report_page', ticker=ticker, url=report_file_url, _external=False)
                     status_message = 'success'
                 except Exception as save_err:
                     print(f"Error saving WP HTML fragment: {save_err}"); status_message = 'success_html_only'
            else:
                 error_message = f"WordPress asset generation failed for {ticker}."; print(f"Pipeline Error: {error_message}"); return jsonify({'status': 'error', 'message': error_message}), 500

        else: # Default to original pipeline
            print(f"Running ORIGINAL pipeline for {ticker} (Site: {site_name or 'Standard'}) with ts {timestamp}...")
            pipeline_result = run_pipeline(ticker, timestamp, APP_ROOT) # Call the original pipeline function
            # Check return value type before unpacking
            if pipeline_result and isinstance(pipeline_result, tuple) and len(pipeline_result) >= 4:
                 model, forecast, report_path, report_html_content = pipeline_result
            else: # Handle unexpected return from pipeline
                 model, forecast, report_path, report_html_content = None, None, None, None
                 print(f"Warning: Original pipeline for {ticker} returned unexpected result: {pipeline_result}")

            if (report_path and os.path.exists(report_path)) or (report_html_content and "Error Generating Report" not in report_html_content):
                if report_path and os.path.exists(report_path):
                    report_filename = os.path.basename(report_path)
                    report_file_url = url_for('serve_static', filename=report_filename, _external=False)
                    viewer_url = url_for('show_report_page', ticker=ticker, url=report_file_url, _external=False)
                    status_message = 'success'
                else:
                    status_message = 'success_html_only'; print("Original report HTML generated but save failed.")
            else:
                error_message = f"Original report generation failed for {ticker}."; print(f"Pipeline Error: {error_message}"); return jsonify({'status': 'error', 'message': error_message}), 500

        # --- Return success response ---
        end_time = time.time(); duration = end_time - start_time
        print(f"Pipeline ({site_name or 'Standard'}) completed for {ticker} in {duration:.2f}s.")
        print(f"Generated viewer page URL: {viewer_url}")
        return jsonify({
            'status': status_message, 'ticker': ticker,
            'viewer_url': viewer_url, 'duration': f"{duration:.2f}"
        })

    except Exception as e:
         print(f"An unexpected error occurred in /generate for {ticker}: {e}")
         traceback.print_exc()
         return jsonify({'status': 'error', 'message': f"An unexpected error occurred processing {ticker}."}), 500


# --- Routes for WordPress Asset Generation (MODIFIED) ---

@app.route('/wp-admin-generator')
def wp_generator_page():
    # IMPORTANT: Add authentication/authorization here if needed
    print("Serving WP Generator page")
    template_path = os.path.join(app.template_folder, 'wp_generator.html')
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found at {template_path}")
        return "Error: WP Generator template not found.", 500
    return render_template('wp_generator.html')

@app.route('/generate-wp-assets', methods=['POST'])
def generate_wp_assets():
    """
    Handles the asynchronous request to generate WordPress assets.
    Site_name requirement removed. Returns HTML directly.
    Includes an increased delay to help prevent rate limiting.
    """
    start_time = time.time()
    print("\n+++ Received /generate-wp-assets request +++")

    # --- ADD DELAY ---
    print(f"Adding {API_DELAY_SECONDS}s delay before processing...")
    time.sleep(API_DELAY_SECONDS)
    # ---------------

    if not request.is_json:
        print("Error: WP Asset Request must be JSON"); return jsonify({'status': 'error', 'message': 'Invalid request format. Expected JSON.'}), 400

    data = request.get_json()
    ticker = data.get('ticker', '').strip().upper()
    # site_name = data.get('site_name', '').strip() # REMOVED site_name retrieval
    print(f"Received WP ticker: {ticker}")
    # print(f"Received WP site name: {site_name}") # REMOVED site_name log

    valid_ticker_pattern = r'^[A-Z0-9\^.-]+$'
    error_message = ''

    # --- Validation Block (Removed site_name check) ---
    if not ticker or not re.match(valid_ticker_pattern, ticker):
        error_message = 'Invalid ticker symbol format.'

    # If any error message was set, return the error
    if error_message:
        print(f"WP Validation Error: {error_message}")
        return jsonify({'status': 'error', 'message': error_message}), 400
    # --- End Validation Block ---

    try:
        timestamp = str(int(time.time()))
        # Pass site_name=None or remove it from the call if the pipeline doesn't need it
        print(f"Running WP pipeline for {ticker} with ts {timestamp}...")
        pipeline_result = run_wp_pipeline(ticker, timestamp, APP_ROOT) # Pass None for site_name if needed

        # Check return value type before unpacking
        if pipeline_result and isinstance(pipeline_result, tuple) and len(pipeline_result) >= 4:
            model_wp, forecast_wp, text_report_html, img_urls_wp = pipeline_result
        else: # Handle unexpected return
             model_wp, forecast_wp, text_report_html, img_urls_wp = None, None, None, {}
             print(f"Warning: WP pipeline for {ticker} returned unexpected result: {pipeline_result}")

        if text_report_html is not None and "Error Generating Report" not in text_report_html:
            end_time = time.time(); duration = end_time - start_time; print(f"WP pipeline completed for {ticker} in {duration:.2f}s.")
            print(f"Returning Chart Image URLs: {img_urls_wp}") # Keep image URLs for potential use
            # Ensure chart_urls is always a dictionary, even if empty
            # Removed site_name from the response JSON
            return jsonify({
                'status': 'success',
                'ticker': ticker,
                'report_html': text_report_html, # HTML code is here
                'chart_urls': img_urls_wp or {},
                'duration': f"{duration:.2f}"
            })
        else:
            error_message = f"WP Asset HTML generation failed for {ticker}."; print(f"WP Pipeline Error: {error_message}"); return jsonify({'status': 'error', 'message': error_message}), 500
    except Exception as e:
        print(f"Unexpected error in /generate-wp-assets for {ticker}: {e}"); traceback.print_exc(); error_message = f"Unexpected error processing {ticker}."; return jsonify({'status': 'error', 'message': error_message}), 500


# --- Main execution (Unchanged) ---
if __name__ == "__main__":
    # Use PORT from environment if available, otherwise default to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)
