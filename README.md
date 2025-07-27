Stock Price Predictions Model

This project is a Flask web application that provides stock market analysis and price predictions using time-series forecasting and technical indicators. Users can input a stock ticker symbol to generate a detailed HTML report.

## Overview

The application fetches historical stock data, fundamental company information, and relevant macroeconomic indicators. It then preprocesses this data, applies feature engineering (including technical indicators), trains a Facebook Prophet model for forecasting, and generates a comprehensive report summarizing the findings with interactive charts.

## Features

* **Web Interface:** Simple Flask-based UI to input stock tickers.
* **Data Collection:**
    * Fetches historical stock price data (Open, High, Low, Close, Volume) using yfinance.
    * Fetches fundamental company data (Sector, Industry, Market Cap, P/E, etc.) using yfinance.
    * Fetches macroeconomic indicators (e.g., Federal Funds Rate, S&P 500) from FRED using pandas\_datareader.
* **Data Processing:** Cleans, merges, and aligns stock and macroeconomic data.
* **Feature Engineering:** Calculates technical indicators like RSI, MACD, Bollinger Bands, and Moving Averages.
* **Forecasting:** Utilizes Facebook Prophet for time-series price forecasting.
* **Report Generation:** Creates detailed HTML reports including:
    * Forecast charts (vs. actuals).
    * Historical price/volume charts.
    * Technical indicator charts (Bollinger Bands, RSI, MACD).
    * Key metrics summary.
    * Fundamental data summary.
    * Risk analysis summary.
    * Overall sentiment and outlook.

## Tech Stack

* **Backend:** Python, Flask
* **Data Handling:** pandas, numpy
* **Time Series Forecasting:** Prophet (fbprophet)
* **Data Fetching:** yfinance, pandas-datareader
* **Technical Analysis:** ta (Technical Analysis Library)
* **Plotting:** Plotly
* **Web:** HTML, CSS

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Jadaunkg/ai-stock-predictions.git](https://github.com/Jadaunkg/ai-stock-predictions.git)
    cd ai-stock-predictions
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Activate the environment
    # Windows:
    .\venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    * *You need to create a `requirements.txt` file.* Create a file named `requirements.txt` in the `ai-stock-predictions` directory and add the following (you might need to adjust versions based on your setup):
        ```txt
        flask
        pandas
        numpy
        yfinance
        pandas-datareader
        prophet
        plotly
        ta
        pytz
        ```
    * Then run:
        ```bash
        pip install -r requirements.txt
        ```
4.  **FRED API Key (Optional but Recommended):**
    * The `macro_data.py` script uses a fallback if a FRED API key isn't found. For reliable macroeconomic data fetching, get a free API key from the [FRED website](https://fred.stlouisfed.org/docs/api/api_key.html).
    * Replace `'your fred api key'` in `macro_data.py` with your actual key, or preferably, use environment variables to store it securely (recommended).

## How to Run

1.  Make sure you are in the `ai-stock-predictions` directory and your virtual environment is activated.
2.  Run the Flask application:
    ```bash
    python app.py
    ```
3.  Open your web browser and navigate to:
    `http://127.0.0.1:5000` (or the address shown in the terminal).
4.  Enter a valid stock ticker symbol (e.g., MSFT, AAPL, GOOGL) in the input field.
5.  Click "Generate Report".
6.  The analysis will run in the background (check the terminal for progress).
7.  Once complete, a link to the HTML report will be displayed. Generated reports are saved in the `static/` folder.

## Project Structure

## Disclaimer

This tool is for informational and educational purposes only. The predictions and analyses provided are based on algorithms and historical data, which may not be accurate and are subject to change. **This is not financial advice.** Always conduct your own thorough research and consult with a qualified financial advisor before making any investment decisions.

## Future Improvements (Optional)

* Integrate real sentiment analysis (e.g., from news headlines, social media).
* Add more sophisticated models (e.g., LSTM, ARIMA alongside Prophet).
* Allow users to select different forecast horizons.
* Implement user accounts and portfolio tracking.
* Improve error handling and user feedback.
* Deploy the application to a cloud platform (e.g., Heroku, AWS, Google Cloud).
