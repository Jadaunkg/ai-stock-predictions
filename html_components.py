# html_components.py
import pandas as pd
import numpy as np # Make sure numpy is imported
from datetime import datetime # Import datetime

# Helper for icons
def get_icon(type):
    """Returns an HTML span element for common icons."""
    icons = {
        'up': ('icon-up', '▲'),
        'down': ('icon-down', '▼'),
        'neutral': ('icon-neutral', '●'),
        'warning': ('icon-warning', '⚠️'),
        'positive': ('icon-positive', '➕'), # Consider checkmark ✅
        'negative': ('icon-negative', '➖'), # Consider crossmark ❌
        'info': ('icon-info', 'ℹ️'),
        'money': ('icon-money', '💰'),
        'chart': ('icon-chart', '📊'),
        'health': ('icon-health', '⚕️'), # Example for health
        'efficiency': ('icon-efficiency', '⚙️'), # Example for efficiency
        'growth': ('icon-growth', '📈'), # Example for growth
        'tax': ('icon-tax', '🧾'), # Example for tax
        'dividend': ('icon-dividend', '💸'), # Example for dividend
        'stats': ('icon-stats', '📉'), # Example for stats
        'news': ('icon-news', '📰'), # Example for news
        'faq': ('icon-faq', '❓'), # Example for faq
    }
    css_class, symbol = icons.get(type, ('', ''))
    if css_class:
        return f'<span class="icon {css_class}" title="{type.capitalize()}">{symbol}</span>'
    return ''

# Helper to format numbers, handling N/A and potential errors
def format_html_value(value, format_type="number", precision=2, currency='$'):
    """Safely formats values for HTML display."""
    if value is None or value == "N/A" or pd.isna(value):
        return "N/A"
    try:
        # Attempt to convert to float, except for date/string types
        if format_type not in ["date", "string", "factor"]:
            num = float(value)
        else:
            num = value # Keep as original type for date/string

        if format_type == "currency":
            return f"{currency}{num:,.{precision}f}"
        elif format_type == "percent":
            # Assumes input is a fraction (e.g., 0.25 for 25%)
            return f"{num * 100:.{precision}f}%"
        elif format_type == "percent_direct":
            # Assumes input is already a percentage number (e.g., 25 for 25%)
            return f"{num:.{precision}f}%"
        elif format_type == "ratio":
             # Check if number is extremely large or small before formatting
             if abs(num) > 1e6 or (abs(num) < 1e-3 and num != 0):
                 return f"{num:.{precision}e}x" # Use scientific notation for extremes
             return f"{num:.{precision}f}x"
        elif format_type == "large_number":
            # Handles formatting large numbers with B, M, K suffixes
            num = float(value) # Ensure it's float for comparison
            if abs(num) >= 1e12: return f"{currency}{num / 1e12:.{precision}f} T"
            elif abs(num) >= 1e9: return f"{currency}{num / 1e9:.{precision}f} B"
            elif abs(num) >= 1e6: return f"{currency}{num / 1e6:.{precision}f} M"
            elif abs(num) >= 1e3: return f"{currency}{num / 1e3:.{precision}f} K"
            else: return f"{currency}{num:,.0f}" # No decimals for small large numbers
        elif format_type == "integer":
             return f"{int(float(num)):,}" # Convert via float first for safety
        elif format_type == "date":
             # Assuming value might be epoch seconds (common in yfinance)
             try:
                 # Check if it's already a datetime object
                 if isinstance(num, datetime):
                     return num.strftime('%Y-%m-%d')
                 # Otherwise, assume it's a timestamp (integer or float)
                 return pd.to_datetime(num, unit='s').strftime('%Y-%m-%d')
             except (ValueError, TypeError, OverflowError):
                 # Handle potential string dates from other sources
                 try:
                    return pd.to_datetime(str(num)).strftime('%Y-%m-%d')
                 except:
                    return str(value) # Fallback if all conversions fail
        elif format_type == "factor": # For split factors like '2:1'
             return str(value)
        elif format_type == "string":
            return str(value)
        else: # Default number format
            return f"{num:,.{precision}f}"
    except (ValueError, TypeError):
        # Fallback for values that cannot be converted to float (like split factors)
        return str(value)


# --- NEW/UPDATED Component Functions ---

def generate_introduction_html(ticker, rdata):
    """Generates the Introduction and Overview section."""
    profile_data = rdata.get('profile_data', {})
    company_name = profile_data.get('Company Name', ticker)
    current_price_fmt = format_html_value(rdata.get('current_price'), 'currency')
    market_cap_fmt = profile_data.get('Market Cap', 'N/A') # Already formatted in extract
    sector = profile_data.get('Sector', 'N/A')
    industry = profile_data.get('Industry', 'N/A')

    # Dynamic Text Example: Sentiment based on price vs MAs
    price = rdata.get('current_price')
    sma50 = rdata.get('sma_50')
    sma200 = rdata.get('sma_200')
    dynamic_sentiment_text = "market position" # Default
    if price and sma50 and sma200:
        if price < sma50 and price < sma200:
            dynamic_sentiment_text = "short-term weakness relative to its moving averages"
        elif price > sma50 and price > sma200:
             dynamic_sentiment_text = "strength relative to its moving averages"
        elif price < sma50 and price > sma200:
             dynamic_sentiment_text = "mixed signals relative to its moving averages (below SMA50, above SMA200)"
        elif price > sma50 and price < sma200:
             dynamic_sentiment_text = "mixed signals relative to its moving averages (above SMA50, below SMA200)"

    report_purpose = (
        "This detailed analytical report aims to predict stock prices along with technical examinations while providing future forecasting for 2025-2026. This report combines both historical price-related technical indicators and fundamental data examination for creating an extensive market performance forecast."
    )

    intro = (
        f"<p>If you are looking for {ticker} stock price prediction with detailed technical, fundamental, stock forecast analysis. you are at right place. Here, we have analyzed <strong>{company_name} ({ticker})</strong>, a major player in the {industry} industry within the {sector} sector. "
        # Use the specific date from rdata if available
        f"As of {rdata.get('last_date', datetime.now()):%B %d, %Y}, {ticker} trades at <strong>{current_price_fmt}</strong>, reflecting its current {dynamic_sentiment_text}. "
        f"The company holds a market capitalization of approximately <strong>{market_cap_fmt}</strong>.</p>"
        f"<p>{report_purpose}</p>"
    )
    # Add business summary if available
    summary = profile_data.get('Summary', None)
    if summary and summary != 'No summary available.':
        intro += f"<h4>Brief Overview</h4><p>{summary[:300]}...</p>" # Show a snippet

    return intro


def generate_metrics_summary_html(ticker, rdata):
    """Generates the key metrics summary box with interpretations."""
    current_price = rdata.get('current_price')
    sma50 = rdata.get('sma_50')
    sma200 = rdata.get('sma_200')
    volatility = rdata.get('volatility') # Expecting annualized %
    sentiment = rdata.get('sentiment', 'N/A')
    forecast_1m = rdata.get('forecast_1m')
    forecast_1y = rdata.get('forecast_1y')
    overall_pct_change = rdata.get('overall_pct_change', 0.0) # 1-year change
    period_label = rdata.get('period_label', 'Period')

    # Icons and Formatting
    current_price_fmt = format_html_value(current_price, 'currency')
    forecast_1m_fmt = format_html_value(forecast_1m, 'currency')
    forecast_1y_fmt = format_html_value(forecast_1y, 'currency')
    overall_pct_change_fmt = f"{overall_pct_change:+.1f}%"
    volatility_fmt = format_html_value(volatility, 'percent_direct', 1) # Value is already %
    sma50_fmt = format_html_value(sma50, 'currency')
    sma200_fmt = format_html_value(sma200, 'currency')

    forecast_1y_icon = get_icon('up' if overall_pct_change > 1 else ('down' if overall_pct_change < -1 else 'neutral'))
    sma50_comp_icon = get_icon('up' if current_price and sma50 and current_price > sma50 else ('down' if current_price and sma50 and current_price < sma50 else 'neutral'))
    sma200_comp_icon = get_icon('up' if current_price and sma200 and current_price > sma200 else ('down' if current_price and sma200 and current_price < sma200 else 'neutral'))
    sentiment_icon = get_icon('up' if 'Bullish' in sentiment else ('down' if 'Bearish' in sentiment else 'neutral'))

    # Dynamic Text Interpretation
    volatility_interpretation = ""
    if volatility is not None:
        vol_level = "low"
        if volatility > 40: vol_level = "high"
        elif volatility > 20: vol_level = "moderate"
        volatility_interpretation = f"The {volatility_fmt} annualized volatility indicates {vol_level} risk (price fluctuation)."

    price_vs_ma_interpretation = ""
    if current_price and sma50 and sma200:
        if current_price < sma50 and current_price < sma200:
            price_vs_ma_interpretation = f"Price is below both SMA50 ({sma50_fmt}) and SMA200 ({sma200_fmt}), signaling bearish trends."
        elif current_price > sma50 and current_price > sma200:
             price_vs_ma_interpretation = f"Price is above both SMA50 ({sma50_fmt}) and SMA200 ({sma200_fmt}), signaling bullish trends."
        else:
             position_50 = "above" if current_price > sma50 else "below"
             position_200 = "above" if current_price > sma200 else "below"
             price_vs_ma_interpretation = f"Price gives mixed signals ({position_50} SMA50 at {sma50_fmt}, {position_200} SMA200 at {sma200_fmt})."

    forecast_interpretation = ""
    if forecast_1y is not None:
        direction = "upside" if overall_pct_change > 0 else "downside" if overall_pct_change < 0 else "flat movement"
        forecast_interpretation = f"The 1-Year forecast of {forecast_1y_fmt} ({overall_pct_change_fmt}) suggests modest potential {direction}."


    # Use grid layout for metrics
    html = f"""
    <div class="metrics-summary">
        <div class="metric-item">
            <span class="metric-label">Current Price</span>
            <span class="metric-value">{current_price_fmt}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">1-{period_label} Forecast</span>
            <span class="metric-value">{forecast_1m_fmt}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">1-Year Forecast</span>
            <span class="metric-value">{forecast_1y_fmt} <span class="metric-change {('trend-up' if overall_pct_change > 0 else 'trend-down' if overall_pct_change < 0 else 'trend-neutral')}">({overall_pct_change_fmt})</span> {forecast_1y_icon}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Overall Sentiment</span>
            <span class="metric-value sentiment-{sentiment.lower().replace(' ', '-')}">{sentiment_icon} {sentiment}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Volatility (Ann.)</span>
            <span class="metric-value">{volatility_fmt}</span>
        </div>
         <div class="metric-item">
            <span class="metric-label">vs SMA 50</span>
            <span class="metric-value">{sma50_fmt} {sma50_comp_icon}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">vs SMA 200</span>
            <span class="metric-value">{sma200_fmt} {sma200_comp_icon}</span>
        </div>
         """
    # Add green days if available
    green_days = rdata.get('green_days')
    total_days = rdata.get('total_days')
    if green_days is not None and total_days and total_days > 0:
         green_days_fmt = f"{green_days}/{total_days} ({green_days/total_days*100:.0f}%)"
         html += f"""
         <div class="metric-item">
            <span class="metric-label">Green Days (30d)</span>
            <span class="metric-value">{green_days_fmt}</span>
         </div>"""

    html += "</div>" # Close metrics-summary div

    # Add interpretation paragraph combining the pieces
    html += f"""
    <div class="narrative">
        <p>{forecast_interpretation} {volatility_interpretation} {price_vs_ma_interpretation}</p>
    </div>
    """
    return html


def generate_detailed_forecast_table_html(ticker, rdata):
    """Generates the detailed monthly forecast table with commentary."""
    monthly_forecast_table_data = rdata.get('monthly_forecast_table_data', pd.DataFrame())
    current_price = rdata.get('current_price')
    forecast_time_col = rdata.get('time_col', 'Period')
    period_label = rdata.get('period_label', 'Period')
    table_rows = ""
    min_price_overall = None
    max_price_overall = None
    first_range_str = "N/A"
    last_range_str = "N/A"
    range_trend_comment = ""

    if not monthly_forecast_table_data.empty and 'Low' in monthly_forecast_table_data.columns and 'High' in monthly_forecast_table_data.columns:
        min_price_overall = monthly_forecast_table_data['Low'].min()
        max_price_overall = monthly_forecast_table_data['High'].max()

        # Calculate range width and trend
        monthly_forecast_table_data['RangeWidth'] = monthly_forecast_table_data['High'] - monthly_forecast_table_data['Low']
        first_range_width = monthly_forecast_table_data['RangeWidth'].iloc[0] if len(monthly_forecast_table_data) > 0 else None
        last_range_width = monthly_forecast_table_data['RangeWidth'].iloc[-1] if len(monthly_forecast_table_data) > 0 else None

        # Format first/last ranges only if data exists
        if len(monthly_forecast_table_data) > 0:
             first_row = monthly_forecast_table_data.iloc[0]
             last_row = monthly_forecast_table_data.iloc[-1]
             first_range_str = f"{format_html_value(first_row['Low'], 'currency')} – {format_html_value(first_row['High'], 'currency')}"
             last_range_str = f"{format_html_value(last_row['Low'], 'currency')} – {format_html_value(last_row['High'], 'currency')}"


        if first_range_width is not None and last_range_width is not None:
            if last_range_width > first_range_width * 1.1:
                range_trend_comment = f"The widening forecast range from {first_range_str} initially to {last_range_str} towards the end of the forecast period reflects increasing uncertainty or expected volatility over time."
            elif last_range_width < first_range_width * 0.9:
                range_trend_comment = f"The narrowing forecast range from {first_range_str} initially to {last_range_str} towards the end of the forecast period reflects decreasing uncertainty or expected volatility over time."
            else:
                 range_trend_comment = f"The forecast range remains relatively stable, starting at {first_range_str} and ending around {last_range_str}, indicating consistent expected volatility."

        # Generate table rows
        for _, row in monthly_forecast_table_data.iterrows():
            action_class = row.get('Action', 'N/A').lower()
            roi_val = row.get('Potential ROI', 0.0)
            roi_icon = get_icon('up' if roi_val > 1 else ('down' if roi_val < -1 else 'neutral'))
            roi_fmt = format_html_value(roi_val, 'percent_direct', 1) # Value is already %
            low_fmt = format_html_value(row.get('Low', 'N/A'), 'currency')
            avg_fmt = format_html_value(row.get('Average', 'N/A'), 'currency')
            high_fmt = format_html_value(row.get('High', 'N/A'), 'currency')
            action_display = row.get('Action', 'N/A')

            table_rows += (
                f"<tr><td>{row.get(forecast_time_col, 'N/A')}</td><td>{low_fmt}</td><td>{avg_fmt}</td><td>{high_fmt}</td>"
                f"<td>{roi_icon} {roi_fmt}</td><td class='action-{action_class}'>{action_display}</td></tr>\n"
            )

        min_max_summary = f"""<p>Over the forecast period, the price is projected to fluctuate between approximately <strong>{format_html_value(min_price_overall, 'currency')}</strong> and <strong>{format_html_value(max_price_overall, 'currency')}</strong>.</p>"""
        table_html = f"""<div class="table-container"><table><thead><tr><th>{period_label}</th><th>Min. Price</th><th>Avg. Price</th><th>Max. Price</th><th>Potential ROI</th><th>Action Signal</th></tr></thead><tbody>{table_rows}</tbody></table></div>"""
    else:
         min_max_summary = f"<p>No detailed forecast data available for {ticker}.</p>"
         table_html = ""
         range_trend_comment = ""

    # Final HTML structure
    return f"""
        <div class="narrative">
            <p>The table below outlines the forecasted price range (Minimum, Average, Maximum) for {ticker} stock on a {period_label.lower()} basis.
            'Potential ROI' (Return on Investment) is calculated by comparing the forecasted 'Average' price against the current stock price ({format_html_value(current_price, 'currency')}).
            'Action Signal' provides a simplified interpretation based on this ROI: 'Buy' if ROI > +2%, 'Short' if ROI < -2%, and 'Hold' otherwise. The signals originate from the forecast model prediction data exclusively.</p>
            {min_max_summary}
            <p>{range_trend_comment}</p>
        </div>
        {table_html}
        """


def generate_company_profile_html(ticker, rdata):
    """Generates the enhanced Company Profile section, incorporating search results."""
    profile_data = rdata.get('profile_data', {})
    website_link = profile_data.get('Website', '#')
    if not website_link.startswith(('http://', 'https://')) and website_link != '#':
        website_link = f"http://{website_link}"

    # --- Incorporate Search Findings (Examples based on provided results) ---
   
    # --- Assemble HTML ---
    profile_grid = f"""<div class="profile-grid">
        <div class="profile-item"><span>Sector:</span>{profile_data.get('Sector', 'N/A')}</div><div class="profile-item"><span>Industry:</span>{profile_data.get('Industry', 'N/A')}</div>
        <div class="profile-item"><span>Market Cap:</span>{profile_data.get('Market Cap', 'N/A')}</div><div class="profile-item"><span>Employees:</span>{profile_data.get('Employees', 'N/A')}</div>
        <div class="profile-item"><span>Website:</span><a href="{website_link}" target="_blank" rel="noopener noreferrer">{profile_data.get('Website', 'N/A')}</a></div></div>"""

    summary_html = f"""
        <h4>Business Summary</h4>
        <p>{profile_data.get('Summary', 'No summary available.')}</p>
        """

    

    return profile_grid + summary_html 


def generate_total_valuation_html(ticker, rdata):
    """Generates the Total Valuation section."""
    valuation_data = rdata.get('total_valuation_data', {}) # Assumes this key exists from fundamental_analysis.py
    ev_revenue_comparison = ""
    ev_revenue_val_str = valuation_data.get('EV/Revenue (TTM)', "N/A")

    if ev_revenue_val_str != 'N/A':
        try:
             ev_rev_val = float(str(ev_revenue_val_str).replace('x',''))
             # Example comparison (replace with actual industry data if available)
             industry_avg_ev_rev = 2.5 # Dummy value for Beverage/Snack industry - needs refinement
             # Check for beverage sector average EV/Revenue using search? (Approx 2.5-3.5x often)
             if ev_rev_val > industry_avg_ev_rev * 1.15: # 15% premium threshold
                 ev_revenue_comparison = f"which is currently <strong>above</strong> the estimated industry average (~{industry_avg_ev_rev:.1f}x), suggesting a potential premium valuation."
             elif ev_rev_val < industry_avg_ev_rev * 0.85: # 15% discount threshold
                 ev_revenue_comparison = f"which is currently <strong>below</strong> the estimated industry average (~{industry_avg_ev_rev:.1f}x), potentially suggesting undervaluation relative to revenue."
             else:
                 ev_revenue_comparison = f"which is roughly <strong>in line</strong> with the estimated industry average (~{industry_avg_ev_rev:.1f}x)."
        except:
             ev_revenue_comparison = "Comparison to industry average requires numeric data."
             pass # Keep empty if conversion fails
    else:
        ev_revenue_comparison = "EV/Revenue data not available for comparison."


    # Use helper function for table generation
    content = generate_metrics_section_content(valuation_data)


    narrative = f"""
    <div class="narrative">
        <p>Total valuation metrics provide a broader view of the company's worth, including debt and cash.</p>
        <p>With an Enterprise Value of <strong>{valuation_data.get('Enterprise Value (EV TTM)', 'N/A')}</strong> against its Trailing Twelve Months (TTM) revenue, {ticker}'s EV/Revenue ratio stands at <strong>{ev_revenue_val_str}</strong>, {ev_revenue_comparison}</p>
        <p>Important upcoming dates: Next Earnings around {valuation_data.get('Next Earnings Date', 'N/A')}, Last Ex-Dividend Date was {valuation_data.get('Ex-Dividend Date', 'N/A')}.</p>
    </div>"""

    return narrative + content


def generate_share_statistics_html(ticker, rdata):
    """Generates the Share Statistics section."""
    share_data = rdata.get('share_statistics_data', {}) # Assumes this key exists
    insider_ownership = share_data.get('Insider Ownership', 'N/A')
    institutional_ownership = share_data.get('Institutional Ownership', 'N/A')
    ownership_implication = ""

    insider_pct_val = None
    inst_pct_val = None

    if '%' in str(insider_ownership):
        try: insider_pct_val = float(str(insider_ownership).replace('%',''))
        except: pass
    if '%' in str(institutional_ownership):
         try: inst_pct_val = float(str(institutional_ownership).replace('%',''))
         except: pass

    if insider_pct_val is not None and inst_pct_val is not None:
         confidence_level = "moderate"
         if insider_pct_val > 10: confidence_level = "strong"
         elif insider_pct_val < 1: confidence_level = "low"

         trust_level = "moderate"
         if inst_pct_val > 75: trust_level = "robust"
         elif inst_pct_val < 30: trust_level = "limited"

         ownership_implication = f"With {insider_ownership} insider ownership, {ticker} reflects {confidence_level} internal confidence. The {institutional_ownership} institutional holding suggests {trust_level} market trust among large investors."
    elif insider_pct_val is not None:
         ownership_implication = f"Insider ownership stands at {insider_ownership}; institutional ownership data is unavailable."
    elif inst_pct_val is not None:
        ownership_implication = f"Institutional ownership stands at {institutional_ownership}; insider ownership data is unavailable."
    else:
        ownership_implication = "Detailed ownership percentages were not available."

    # Use helper function for table generation
    content = generate_metrics_section_content(share_data)

    narrative = f"""
    <div class="narrative">
        <p>Company equity distribution together with ownership details become visible through share statistics.</p>
        <p>{ownership_implication} Public confidence in a stock market tends to correlate with institutional ownership while large ownership by company insiders helps create shared interests between managers and shareholders. Float includes the shares which the public can buy or sell.</p>
    </div>"""

    return narrative + content


def generate_valuation_metrics_html(ticker, rdata):
    """Generates the VALUATION METRICS section (Existing, but enhanced)."""
    valuation_data = rdata.get('valuation_data', {})
    fwd_pe = valuation_data.get('Forward P/E', 'N/A')
    pb_ratio = valuation_data.get('Price/Book (MRQ)', 'N/A') # Updated key name
    peg_ratio = valuation_data.get('PEG Ratio', 'N/A')
    comparison_text = ""

    # Placeholders for Industry Averages (Needs external data source)
    industry_fwd_pe_avg_str = "20x" # Example
    industry_pb_avg_str = "3.5x" # Example
    industry_peg_avg_str = "1.8x" # Example

    fwd_pe_val = None
    pb_val = None
    peg_val = None

    try: fwd_pe_val = float(str(fwd_pe).replace('x','')) if 'x' in str(fwd_pe) else None
    except: pass
    try: pb_val = float(str(pb_ratio).replace('x','')) if 'x' in str(pb_ratio) else None
    except: pass
    try: peg_val = float(str(peg_ratio).replace('x','')) if 'x' in str(peg_ratio) else None
    except: pass

    valuation_points = []
    if fwd_pe_val is not None:
        # Add comparison logic vs industry_fwd_pe_avg_str here if data available
        valuation_points.append(f"Forward P/E of {fwd_pe}") # vs industry {industry_fwd_pe_avg_str}) indicates..."
    if pb_val is not None:
        # Add comparison logic vs industry_pb_avg_str here
        valuation_points.append(f"Price/Book of {pb_ratio}") # vs industry {industry_pb_avg_str}) suggests..."
    if peg_val is not None:
        peg_interp = "reasonable growth expectations relative to P/E."
        if peg_val < 1.0: peg_interp = "potentially undervalued based on growth expectations."
        elif peg_val > 2.0: peg_interp = "high growth expectations priced in, or potentially overvalued."
        valuation_points.append(f"PEG Ratio of {peg_ratio} suggests {peg_interp}") # vs industry {industry_peg_avg_str})."

    if valuation_points:
         comparison_text = " ".join(valuation_points)
    else:
         comparison_text = "Key valuation metrics like Forward P/E or PEG Ratio were not available for comparison."

    # Use existing helper for the table
    content = generate_metrics_section_content(valuation_data)

    narrative = f"""
    <div class="narrative">
        <p>Stock valuation metrics enable investors to determine the price value relationship between stock market worth and earnings along with sales, book value and anticipated growth potential.</p>
        <p>{comparison_text} Mentoring these financial metrics to industry standards as well historical company values generates deeper understanding.</p>
        <p><i>Note: P/FCF (Price to Free Cash Flow) of {valuation_data.get("Price/FCF (TTM)", "N/A")} is another key valuation indicator. EV/EBITDA is often used for comparing companies with different capital structures.</i></p>
    </div>
    """

    return narrative + content


def generate_financial_health_html(ticker, rdata):
    """Generates the FINANCIAL HEALTH section (Existing, but enhanced)."""
    health_data = rdata.get('financial_health_data', {})
    debt_equity = health_data.get('Debt/Equity (MRQ)', 'N/A') # Use updated key
    current_ratio = health_data.get('Current Ratio (MRQ)', 'N/A') # Use updated key
    quick_ratio = health_data.get('Quick Ratio (MRQ)', 'N/A') # Use updated key
    op_cash_flow = health_data.get('Operating Cash Flow (TTM)', 'N/A') # Use updated key
    roe = health_data.get('Return on Equity (ROE TTM)', 'N/A') # Use updated key
    commentary_points = []

    # Debt/Equity Analysis
    de_val = None
    if 'x' in str(debt_equity):
        try: de_val = float(str(debt_equity).replace('x',''))
        except: pass
    if de_val is not None:
        risk_level = "moderate leverage."
        if de_val > 2.0: risk_level = "high leverage, indicating elevated financial risk."
        elif de_val > 1.0: risk_level = "notable leverage."
        commentary_points.append(f"Debt/Equity ratio of {debt_equity} signals {risk_level}")

    # Liquidity Analysis (Current & Quick Ratio)
    cr_val = None
    qr_val = None
    if 'x' in str(current_ratio):
        try: cr_val = float(str(current_ratio).replace('x',''))
        except: pass
    if 'x' in str(quick_ratio):
        try: qr_val = float(str(quick_ratio).replace('x',''))
        except: pass

    liquidity_comment = "Liquidity assessment requires Current/Quick Ratio data."
    if cr_val is not None:
        if cr_val < 1.0: liquidity_comment = f"Current Ratio ({current_ratio}) below 1.0 suggests potential short-term liquidity challenges."
        elif cr_val < 1.5: liquidity_comment = f"Current Ratio ({current_ratio}) indicates relatively tight short-term liquidity."
        else: liquidity_comment = f"Current Ratio ({current_ratio}) suggests adequate short-term liquidity."
        if qr_val is not None: # Add Quick Ratio context if available
             if qr_val < 0.8: liquidity_comment += f" The Quick Ratio ({quick_ratio}), excluding inventory, reinforces potential liquidity constraints."
             elif qr_val < 1.0: liquidity_comment += f" The Quick Ratio ({quick_ratio}) is also somewhat low."
             else: liquidity_comment += f" The Quick Ratio ({quick_ratio}) confirms reasonable liquidity."
    commentary_points.append(liquidity_comment)

    # ROE Context
    if roe != 'N/A':
        commentary_points.append(f"Return on Equity (ROE) of {roe} indicates the company's profitability relative to shareholder investments.") # Add comparison if industry avg known

    # Cash Flow Context
    if op_cash_flow != 'N/A':
        commentary_points.append(f"Operating Cash Flow (TTM) stands at {op_cash_flow}, demonstrating cash generated from core operations.")


    # Use existing helper for the table
    content = generate_metrics_section_content(health_data)

    narrative = f"""
    <div class="narrative">
        <p>Companies need financial health indicators to determine their capability of handling short-term financial commitments (liquidity) and their ability to repay long-term debt (solvency) as well as their equity and asset return ratios.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>These metrics act as point-in-time measurements yet understanding long-term trends delivers better understanding. ROA (Return on Assets) does not appear frequently in these financial reports.</i></p>
    </div>
    """
    return narrative + content


def generate_financial_efficiency_html(ticker, rdata):
    """Generates the Financial Efficiency section."""
    efficiency_data = rdata.get('financial_efficiency_data', {})
    asset_turnover = efficiency_data.get('Asset Turnover (TTM)', 'N/A') # Updated key
    inventory_turnover = efficiency_data.get('Inventory Turnover (TTM)', 'N/A') # Updated key
    commentary_points = []

    if asset_turnover != 'N/A':
        try:
            at_val = float(str(asset_turnover).replace('x',''))
            # Efficiency level depends heavily on industry
            efficiency_level = "moderate"
            if rdata.get('industry') in ['Retail', 'Consumer Staples'] and at_val > 1.5: efficiency_level = "high"
            elif rdata.get('industry') not in ['Retail', 'Consumer Staples'] and at_val > 0.8: efficiency_level = "high"
            elif at_val < 0.4: efficiency_level = "low"
            commentary_points.append(f"Asset Turnover of {asset_turnover} reflects {efficiency_level} efficiency in using assets to generate revenue for its industry.")
        except:
            commentary_points.append(f"Asset Turnover is reported as {asset_turnover}.")

    if inventory_turnover != 'N/A':
        inv_turn_val = None
        try: inv_turn_val = float(str(inventory_turnover).replace('x',''))
        except: pass
        if inv_turn_val is not None:
             efficiency_level = "moderate"
             if inv_turn_val > 10: efficiency_level = "high (suggesting efficient inventory management)"
             elif inv_turn_val < 4: efficiency_level = "low (suggesting potential overstocking or slow sales)"
             commentary_points.append(f"Inventory Turnover of {inventory_turnover} indicates {efficiency_level} inventory efficiency.")
        else:
             commentary_points.append(f"Inventory Turnover is reported as {inventory_turnover}.")


    if efficiency_data.get('Return on Invested Capital (ROIC TTM)', 'N/A') != 'N/A':
        commentary_points.append(f"Return on Invested Capital (ROIC) is {efficiency_data['Return on Invested Capital (ROIC TTM)']}.")

    if not commentary_points:
        commentary_points.append("Specific financial efficiency metrics were not readily available.")

    # Use helper function for table generation
    content = generate_metrics_section_content(efficiency_data)

    narrative = f"""
    <div class="narrative">
        <p>Financial efficiency ratios evaluate organizational asset management and working capital control (such as inventory and receivables) for generating revenue and profits.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>ROIC stands as an important measurement of total capital efficiency but analysts need full financial statements to generate this metric. Monitoring should focus on equal groups in the same market sector.</i></p>
    </div>"""

    return narrative + content


def generate_profitability_growth_html(ticker, rdata):
    """Generates the PROFITABILITY AND GROWTH section (Existing, but enhanced)."""
    profit_data = rdata.get('profitability_data', {})
    revenue_growth = profit_data.get('Revenue Growth (YoY)', 'N/A')
    earnings_growth = profit_data.get('Earnings Growth (YoY)', 'N/A')
    gross_margin = profit_data.get('Gross Margin (TTM)', 'N/A')
    operating_margin = profit_data.get('Operating Margin (TTM)', 'N/A')
    commentary_points = []

    # Growth Commentary
    growth_comment = "Growth data was partially or fully unavailable."
    rev_g_val = None
    earn_g_val = None
    if '%' in str(revenue_growth):
        try:
            rev_g_val = float(revenue_growth.replace('%', ''))
        except:
            pass
    if '%' in str(earnings_growth):
        try:
            earn_g_val = float(earnings_growth.replace('%', ''))
        except:
            pass

    if rev_g_val is not None and earn_g_val is not None:
        if rev_g_val < 0 or earn_g_val < 0:
            growth_comment = f"Negative recent growth (Revenue: {revenue_growth}, Earnings: {earnings_growth}) suggests potential temporary headwinds or structural challenges."
        elif rev_g_val > 10 or earn_g_val > 15: # Example thresholds for strong growth
             growth_comment = f"Strong recent growth (Revenue: {revenue_growth}, Earnings: {earnings_growth}) indicates positive business momentum."
        else:
            growth_comment = f"Moderate recent growth (Revenue: {revenue_growth}, Earnings: {earnings_growth}) shows a stable performance trajectory."
    elif rev_g_val is not None:
         growth_comment = f"Recent revenue growth was {revenue_growth} (Earnings growth N/A)."
    elif earn_g_val is not None:
         growth_comment = f"Recent earnings growth was {earnings_growth} (Revenue growth N/A)."
    commentary_points.append(growth_comment)

    # Margin Commentary
    margin_comment = "Margin data interpretation requires comparable industry data."
    gm_val = None
    om_val = None
    if '%' in str(gross_margin):
        try:
            gm_val = float(gross_margin.replace('%', ''))
        except:
            pass
    if '%' in str(operating_margin):
        try:
            om_val = float(operating_margin.replace('%', ''))
        except:
            pass

    if gm_val is not None and om_val is not None:
        gm_level = "strong" if gm_val > 40 else "moderate" if gm_val > 20 else "low"
        om_level = "strong" if om_val > 15 else "moderate" if om_val > 5 else "low"
        margin_comment = f"Gross Margin ({gross_margin}) appears {gm_level}, while Operating Margin ({operating_margin}) is {om_level}. Analyzing margin trends over time is important."
    elif gm_val is not None:
         margin_comment = f"Gross Margin is {gross_margin} (Operating Margin N/A)."
    elif om_val is not None:
         margin_comment = f"Operating Margin is {operating_margin} (Gross Margin N/A)."
    commentary_points.append(margin_comment)


    # Use existing helper for the table
    content = generate_metrics_section_content(profit_data)

    narrative = f"""
    <div class="narrative">
        <p>Profitability margins show how much profit is generated per dollar of sales at different stages (Gross, Operating, Net). Growth rates track the expansion of revenue and earnings over time.</p>
         <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>Business owners should measure margins by comparing them against industry competitors and past performance records. Stock value development depends heavily on sustainable growth.</i></p>
    </div>
    """
    return narrative + content


def generate_dividends_shareholder_returns_html(ticker, rdata):
    """Generates the DIVIDENDS AND SHAREHOLDER RETURNS section (Existing, but enhanced)."""
    dividend_data = rdata.get('dividends_data', {})
    yield_val = dividend_data.get('Dividend Yield (Fwd)', 'N/A') # Use Fwd Yield
    payout_ratio = dividend_data.get('Payout Ratio', 'N/A')
    buyback_yield = dividend_data.get('Buyback Yield (Est.)', 'N/A')
    commentary_points = []

    payout_val = None
    if '%' in str(payout_ratio):
        try:
            payout_val = float(payout_ratio.replace('%', ''))
        except ValueError:
            pass

    yield_comment = f"Dividend Yield (Forward) is {yield_val}."
    if yield_val != 'N/A':
         commentary_points.append(yield_comment)

    if payout_val is not None:
         sustainability = "sustainable dividend with room for growth."
         investor_type = "income and growth"
         if payout_val > 90:
             sustainability = "very high, suggesting limited room for future dividend growth and potential risk if earnings decline."
             investor_type = "income-focused (with high caution)"
         elif payout_val > 60:
             sustainability = "relatively high, indicating a mature policy with moderate growth room."
             investor_type = "primarily income"
         elif payout_val < 30 and payout_val > 0:
             sustainability = "low, suggesting significant capacity for future increases."
             investor_type = "primarily growth (low current yield likely)"
         elif payout_val <= 0:
             sustainability = "negative or zero, indicating dividends may not be covered by earnings."
             investor_type = "speculative income (risk)"
         commentary_points.append(f"Payout Ratio of {payout_ratio} indicates a {sustainability}")
         commentary_points.append(f"This dividend profile may appeal most to {investor_type} investors.")

    # Shareholder Yield (Dividend Yield + Buyback Yield)
    shareholder_yield_comment = f"Share buybacks (Yield: {buyback_yield}) also contribute to total shareholder return."
    # Add calculation if yields are available
    commentary_points.append(shareholder_yield_comment)

    # Use existing helper for the table
    content = generate_metrics_section_content(dividend_data)

    narrative = f"""
    <div class="narrative">
        <p>Stock dividends together with share repurchases constitute major methods that corporations use to redistribute wealth to their shareholders. Investors who focus on income require a thorough analysis of both yield ratios and dividend sustainability.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>Shareholders obtain a yield consisting of dividends and buybacks according to the equation Total Shareholder Yield = Dividend Yield + Buyback Yield. Raising dividends to full potential may temporarily restrict future dividend expansion possibilities. Check Ex-Dividend Date for eligibility.</i></p>
    </div>
    """
    return narrative + content


def generate_technical_analysis_summary_html(ticker, rdata):
    """Generates the TECHNICAL ANALYSIS summary section (Refined)."""
    sentiment = rdata.get('sentiment', 'N/A')
    current_price = rdata.get('current_price')
    last_date = rdata.get('last_date')
    detailed_ta_data = rdata.get('detailed_ta_data', {})

    sma20 = detailed_ta_data.get('SMA_20'); sma50 = detailed_ta_data.get('SMA_50')
    sma100 = detailed_ta_data.get('SMA_100'); sma200 = detailed_ta_data.get('SMA_200')
    support = detailed_ta_data.get('Support_30D'); resistance = detailed_ta_data.get('Resistance_30D')
    latest_rsi = detailed_ta_data.get('RSI_14')
    macd_line = detailed_ta_data.get('MACD_Line'); macd_signal = detailed_ta_data.get('MACD_Signal')
    macd_hist = detailed_ta_data.get('MACD_Hist')
    bb_lower = detailed_ta_data.get('BB_Lower'); bb_upper = detailed_ta_data.get('BB_Upper')

    # Helper for MA status
    def price_vs_ma(price, ma):
        if price is None or ma is None or pd.isna(price) or pd.isna(ma): return ('trend-neutral', '')
        if price > ma * 1.001: return ('trend-up', f'{get_icon("up")} (Above)')
        if price < ma * 0.999: return ('trend-down', f'{get_icon("down")} (Below)')
        return ('trend-neutral', f'{get_icon("neutral")} (At MA)')

    sma20_status, sma20_label = price_vs_ma(current_price, sma20)
    sma50_status, sma50_label = price_vs_ma(current_price, sma50)
    sma100_status, sma100_label = price_vs_ma(current_price, sma100)
    sma200_status, sma200_label = price_vs_ma(current_price, sma200)

    # Technical Summary Points
    summary_points = []
    price_fmt = format_html_value(current_price, 'currency')

    # Trend (Price vs MAs)
    trend_desc = "Mixed Trend Signals."
    if current_price and sma50 and sma200:
        if current_price > sma50 and current_price > sma200: trend_desc = "Bullish Trend (Price > SMA50 & SMA200)."
        elif current_price < sma50 and current_price < sma200: trend_desc = "Bearish Trend (Price < SMA50 & SMA200)."
    summary_points.append(f"<strong>Trend:</strong> {trend_desc} Current Price: {price_fmt}.")

    # Momentum (RSI)
    if latest_rsi is not None and not pd.isna(latest_rsi):
        rsi_level = "Neutral"
        rsi_implication = "balanced momentum"
        if latest_rsi > 70: rsi_level = "Overbought"; rsi_implication = "potential pullback risk"
        elif latest_rsi < 30: rsi_level = "Oversold"; rsi_implication = "potential rebound"
        summary_points.append(f"<strong>Momentum (RSI):</strong> {latest_rsi:.1f} ({rsi_level}), suggesting {rsi_implication}.")
    else: summary_points.append("<strong>Momentum (RSI):</strong> Data N/A.")

    # Momentum (MACD)
    if macd_line is not None and macd_signal is not None and macd_hist is not None:
         macd_pos = "above" if macd_line > macd_signal else "below"
         macd_cross = "(Bullish Signal)" if macd_line > macd_signal else "(Bearish Signal)"
         hist_desc = "Positive (Strengthening Bullish)" if macd_hist > 0 else "Negative (Strengthening Bearish)"
         summary_points.append(f"<strong>Momentum (MACD):</strong> Line ({format_html_value(macd_line)}) {macd_pos} Signal ({format_html_value(macd_signal)}) {macd_cross}. Histogram is {hist_desc}.")
    else: summary_points.append("<strong>Momentum (MACD):</strong> Data N/A.")

    # Volatility (Bollinger Bands)
    if current_price is not None and bb_lower is not None and bb_upper is not None:
         bb_pos = "within Bands"
         bb_implication = "normal volatility range"
         if current_price > bb_upper: bb_pos = f"above Upper Band ({format_html_value(bb_upper, 'currency')})"; bb_implication = "high volatility / potential overbought"
         elif current_price < bb_lower: bb_pos = f"below Lower Band ({format_html_value(bb_lower, 'currency')})"; bb_implication = "high volatility / potential oversold"
         summary_points.append(f"<strong>Volatility (BBands):</strong> Price {bb_pos}, indicating {bb_implication}.")
    else: summary_points.append("<strong>Volatility (BBands):</strong> Data N/A.")

    # Support & Resistance
    if support is not None and resistance is not None:
        summary_points.append(f"<strong>Support/Resistance (30d):</strong> ~{format_html_value(support, 'currency')} / ~{format_html_value(resistance, 'currency')}.")
    else: summary_points.append("<strong>Support/Resistance (30d):</strong> Levels N/A.")


    sentiment_icon = get_icon('up' if 'Bullish' in sentiment else ('down' if 'Bearish' in sentiment else 'neutral'))
    last_date_fmt = f"{last_date:%Y-%m-%d}" if last_date else "N/A"

    # Assemble HTML
    summary_list_html = "".join([f"<li>{point}</li>" for point in summary_points])

    return f"""
        <div class="sentiment-indicator">
            <span>Overall Technical Sentiment:</span><span class="sentiment-{sentiment.lower().replace(' ', '-')}">{sentiment_icon} {sentiment}</span>
        </div>
        <div class="narrative">
            <p>Summary based on data up to {last_date_fmt}. Detailed charts follow.</p>
            <ul>{summary_list_html}</ul>
        </div>
        <h4>Moving Average Values</h4>
        <div class="ma-summary">
            <div class="ma-item"><span class="label">SMA 20:</span> <span class="value">{format_html_value(sma20, 'currency')}</span> <span class="status {sma20_status}">{sma20_label}</span></div>
            <div class="ma-item"><span class="label">SMA 50:</span> <span class="value">{format_html_value(sma50, 'currency')}</span> <span class="status {sma50_status}">{sma50_label}</span></div>
            <div class="ma-item"><span class="label">SMA 100:</span> <span class="value">{format_html_value(sma100, 'currency')}</span> <span class="status {sma100_status}">{sma100_label}</span></div>
            <div class="ma-item"><span class="label">SMA 200:</span> <span class="value">{format_html_value(sma200, 'currency')}</span> <span class="status {sma200_status}">{sma200_label}</span></div>
        </div>
        <p class="disclaimer">Technical indicators analyze past price trends, not future guarantees.</p>
        """


def generate_stock_price_statistics_html(ticker, rdata):
    """Generates the Stock Price Statistics section."""
    stats_data = rdata.get('stock_price_stats_data', {})
    beta = stats_data.get('Beta', 'N/A')
    volatility = rdata.get('volatility') # Get calculated annualized volatility
    stats_data['Volatility (30d Ann.)'] = format_html_value(volatility, 'percent_direct', 1) if volatility is not None else "N/A"
    commentary_points = []

    if beta != 'N/A':
        try:
             beta_val = float(beta)
             vol_comp = "similar volatility to"
             risk_level = "average market risk."
             if beta_val > 1.2: vol_comp = "higher volatility than"; risk_level = "above-average market risk."
             elif beta_val < 0.8: vol_comp = "lower volatility than"; risk_level = "below-average market risk."
             commentary_points.append(f"Beta of {beta} implies {ticker} has historically shown {vol_comp} the overall market (S&P 500), indicating {risk_level}")
        except:
             commentary_points.append(f"Beta is reported as {beta}.")

    if volatility is not None:
         commentary_points.append(f"Recent Volatility (30d Annualized) is {stats_data['Volatility (30d Ann.)']}.")

    if stats_data.get('52 Week Change', 'N/A') != 'N/A':
         commentary_points.append(f"The 52-Week Change of {stats_data['52 Week Change']} reflects long-term price momentum.")

    if not commentary_points:
         commentary_points.append("Key stock price statistics were not available.")

    # Use helper function for table generation
    content = generate_metrics_section_content(stats_data)

    narrative = f"""
    <div class="narrative">
        <p>The statistics helps you to understand the stock's volatility along with market-related Beta value and performance range and trading liquidity.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>Note: Beta > 1 indicates higher volatility than the market; Beta < 1 indicates lower. Average Volume shows typical daily trading activity.</i></p>
    </div>"""

    return narrative + content


def generate_short_selling_info_html(ticker, rdata):
    """Generates the Short Selling Information section."""
    short_data = rdata.get('short_selling_data', {})
    short_percent_float = short_data.get('Short % of Float', 'N/A')
    short_ratio = short_data.get('Short Ratio (Days To Cover)', 'N/A')
    commentary_points = []

    spf_val = None
    if '%' in str(short_percent_float):
        try:
            spf_val = float(short_percent_float.replace('%', ''))
        except ValueError:
            pass

    if spf_val is not None:
         sentiment_level = "minimal bearish pressure."
         squeeze_risk = "low short squeeze risk."
         if spf_val > 20: sentiment_level = "very high bearish sentiment."; squeeze_risk = "elevated short squeeze risk."
         elif spf_val > 10: sentiment_level = "significant bearish sentiment."; squeeze_risk = "moderate short squeeze risk."
         elif spf_val > 5: sentiment_level = "moderate bearish sentiment."; squeeze_risk = "some short squeeze potential."
         commentary_points.append(f"Short interest at {short_percent_float} of float suggests {sentiment_level}")
         commentary_points.append(f"This level indicates {squeeze_risk}")
    else:
         commentary_points.append("Short % of Float data is currently unavailable.")

    if short_ratio != 'N/A':
        commentary_points.append(f"The Short Ratio (Days To Cover) is {short_ratio}, meaning it would take about that many days of average volume to cover all short positions.")
    else:
         commentary_points.append("Short Ratio data is unavailable.")

    # Use helper function for table generation
    content = generate_metrics_section_content(short_data)

    narrative = f"""
    <div class="narrative">
        <p>Short selling data indicates the level of bearish bets against the stock.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>Note: High short interest can increase volatility. The Short Ratio helps gauge how quickly short positions could theoretically be covered. Data as of {short_data.get('Short Date', 'N/A')}.</i></p>
    </div>"""

    return narrative + content


def generate_risk_factors_html(ticker, rdata):
    """Generates the enhanced Risk Factors section."""
    risk_items = rdata.get('risk_items', []) # Get pre-calculated risks from helper
    industry = rdata.get('industry', 'the company\'s specific')
    sector = rdata.get('sector', 'its')

    

    # Combine calculated and generic risks
    all_risk_items = risk_items

    risk_list_html = "".join([f"<li>{get_icon('warning')} {item}</li>" for item in all_risk_items])


    narrative = f"""
    <div class="narrative">
        <p>Investing in {ticker} involves various risks. This section outlines potential factors identified through data analysis and general market considerations. It is not exhaustive.</p>
    </div>"""

    return narrative + f"<ul>{risk_list_html}</ul>"


def generate_analyst_insights_html(ticker, rdata):
    """Generates the ANALYST INSIGHTS section (Enhanced)."""
    analyst_data = rdata.get('analyst_info_data', {})
    mean_target = analyst_data.get('Mean Target Price', 'N/A')
    current_price = rdata.get('current_price')
    num_analysts = analyst_data.get('Number of Analyst Opinions', 'N/A')
    recommendation = analyst_data.get('Recommendation', 'N/A')
    commentary_points = []

    if recommendation != 'N/A':
         rec_icon = get_icon('up' if 'Buy' in recommendation else ('down' if 'Sell' in recommendation or 'Underperform' in recommendation else 'neutral'))
         commentary_points.append(f"The consensus recommendation from {num_analysts} analysts is {rec_icon} <strong>{recommendation}</strong>.")

    upside_potential_fmt = "N/A"
    if mean_target != 'N/A' and current_price is not None:
         try:
             mean_target_val = float(str(mean_target).replace('$','').replace(',',''))
             upside_potential = ((mean_target_val - current_price) / current_price) * 100
             upside_potential_fmt = format_html_value(upside_potential, 'percent_direct', 1)
             sentiment_level = "neutral outlook."
             if upside_potential > 15: sentiment_level = "optimism."
             elif upside_potential < -5: sentiment_level = "caution."
             elif upside_potential < 5: sentiment_level = "limited near-term upside."

             commentary_points.append(f"Analysts' mean target price of {mean_target} implies potential {upside_potential_fmt} change from the current price ({format_html_value(current_price, 'currency')}), suggesting analyst {sentiment_level}")
         except:
             commentary_points.append(f"Analysts' mean target price is {mean_target}.")
    elif mean_target != 'N/A':
         commentary_points.append(f"Analysts' mean target price is {mean_target}.")

    # Use helper function for table generation (using analyst-grid layout)
    table_html = generate_analyst_grid_html(analyst_data) # Use a specific helper for grid


    narrative = f"""
    <div class="narrative">
        <p>Wall Street analysts provide ratings and price targets based on their assessment of the company's prospects.</p>
        <ul><li>{ '</li><li>'.join(commentary_points)}</li></ul>
        <p><i>Note: Analyst opinions are subjective and can change. Look at the range of estimates (High/Low Target) and any recent revisions for more context.</i></p>
    </div>
    """
    return narrative + table_html

# Helper specifically for the analyst grid layout
def generate_analyst_grid_html(analyst_data):
    valid_data = {k:v for k,v in analyst_data.items() if v != 'N/A' and not ('N/A' in str(v))};
    if not valid_data:
        return "<p>No specific analyst data available.</p>"

    html = '<div class="analyst-grid">'
    # Define order or use keys directly
    key_order = ["Recommendation", "Mean Target Price", "High Target Price", "Low Target Price", "Number of Analyst Opinions"]
    for key in key_order:
        if key in valid_data:
             html += f'<div class="analyst-item"><span>{key}:</span> {valid_data[key]}</div>'
    # Add any other keys not in the defined order (optional)
    # for key, value in valid_data.items():
    #    if key not in key_order:
    #         html += f'<div class="analyst-item"><span>{key}:</span> {value}</div>'
    html += '</div>'
    return html


def generate_recent_news_html(ticker, rdata):
    """Generates the RECENT NEWS section (Enhanced with Search Results)."""
    news_list = rdata.get('news_list', []) # News from yfinance

    # Example integration of search results (needs refinement based on actual tool output)
    # Let's assume search results are passed or accessible here
    # search_results_summary = "<li>Recent reports highlight lowered 2025 EPS guidance due to tariffs and supply chain costs.</li><li>Completed acquisition of Siete Foods and announced deal for Poppi, focusing on health/wellness trends.</li>"
    search_results_summary = "" # Keep empty if not integrating live search here

    if not news_list and not search_results_summary:
        return """<p>No recent news headlines found via standard sources.</p>"""

    news_items = ""
    if news_list: # Process yfinance news first
        for item in news_list[:3]: # Limit yfinance news if search results are added
             link = item.get('link', '#')
             if not link.startswith(('http://', 'https://')) and link != '#':
                 link = f"https://news.google.com/search?q={ticker}+{item.get('title', '')}"
             news_items += f"""<div class="news-item">
                 <h4><a href="{link}" target="_blank" rel="noopener noreferrer">{item.get('title', 'N/A')}</a></h4>
                 <div class="news-meta">
                     <span>{item.get('publisher', 'N/A')}</span>
                     <span>{item.get('published', 'N/A')}</span>
                 </div>
                 </div>"""

    narrative = f"""
    <div class="narrative">
        <p>Recent news and developments can significantly impact stock performance and investor sentiment.</p>
        """
    # Add summary from search if available
    if search_results_summary:
        narrative += f"<ul>{search_results_summary}</ul>"

    narrative += """</div>"""


    return narrative + f"""<div class="news-container">{news_items}</div>"""


def generate_conclusion_outlook_html(ticker, rdata):
    """Generates the CONCLUSION AND OUTLOOK section (Enhanced with more points and dynamic summary)."""
    # Gather data from rdata
    sentiment = rdata.get('sentiment', 'N/A') # Overall technical sentiment calculated earlier
    current_price = rdata.get('current_price')
    latest_rsi = rdata.get('latest_rsi')
    sma50 = rdata.get('sma_50'); sma200 = rdata.get('sma_200')
    macd_hist = rdata.get('detailed_ta_data', {}).get('MACD_Hist')
    macd_line = rdata.get('detailed_ta_data', {}).get('MACD_Line')
    macd_signal = rdata.get('detailed_ta_data', {}).get('MACD_Signal')
    bb_lower = rdata.get('detailed_ta_data', {}).get('BB_Lower')
    bb_upper = rdata.get('detailed_ta_data', {}).get('BB_Upper')

    forecast_1y = rdata.get('forecast_1y')
    overall_pct_change = rdata.get('overall_pct_change', 0.0) # 1-Year
    roe = rdata.get('financial_health_data', {}).get('Return on Equity (ROE TTM)', 'N/A')
    debt_equity = rdata.get('financial_health_data', {}).get('Debt/Equity (MRQ)', 'N/A')
    fwd_pe = rdata.get('valuation_data', {}).get('Forward P/E', 'N/A')
    analyst_rec = rdata.get('analyst_info_data', {}).get('Recommendation', 'N/A')
    dividend_yield = rdata.get('dividends_data', {}).get('Dividend Yield (Fwd)', 'N/A')
    rev_growth = rdata.get('profitability_data', {}).get('Revenue Growth (YoY)', 'N/A')
    earn_growth = rdata.get('profitability_data', {}).get('Earnings Growth (YoY)', 'N/A')


    # --- Short-Term Outlook Points (Aim for 5+) ---
    st_points = []
    st_icon = get_icon('neutral')
    technical_summary_sentiment = sentiment # Use the already calculated overall sentiment

    if 'Bullish' in technical_summary_sentiment: st_icon = get_icon('up')
    elif 'Bearish' in technical_summary_sentiment: st_icon = get_icon('down')
    st_points.append(f"<span class='icon'>{st_icon}</span><span>Overall Technical Sentiment: <strong>{technical_summary_sentiment}</strong>.</span>")

    # Price vs MAs
    if current_price and sma50 and sma200:
        if current_price < sma50 and current_price < sma200: st_points.append(f"<span class='icon'>{get_icon('down')}</span><span>Price below key SMAs (50, 200), indicating <strong>bearish short/long-term trends</strong>.</span>")
        elif current_price > sma50 and current_price > sma200: st_points.append(f"<span class='icon'>{get_icon('up')}</span><span>Price above key SMAs (50, 200), indicating <strong>bullish short/long-term trends</strong>.</span>")
        else: st_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>Price shows <strong>mixed signals</strong> relative to SMA50/SMA200.</span>")
    else: st_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>Moving average trend analysis incomplete.</span>")

    # RSI
    if latest_rsi is not None:
        rsi_interp = "Neutral momentum."
        rsi_icon = get_icon('neutral')
        if latest_rsi < 30: rsi_interp = f"<strong>Oversold (RSI: {latest_rsi:.1f})</strong>, potential for rebound."; rsi_icon = get_icon('positive')
        elif latest_rsi > 70: rsi_interp = f"<strong>Overbought (RSI: {latest_rsi:.1f})</strong>, potential for pullback."; rsi_icon = get_icon('warning')
        st_points.append(f"<span class='icon'>{rsi_icon}</span><span>{rsi_interp}</span>")
    else: st_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>RSI analysis unavailable.</span>")

    # MACD
    if macd_line is not None and macd_signal is not None and macd_hist is not None:
         macd_bullish = macd_line > macd_signal and macd_hist > 0
         macd_bearish = macd_line < macd_signal and macd_hist < 0
         macd_icon = get_icon('up') if macd_bullish else get_icon('down') if macd_bearish else get_icon('neutral')
         macd_status = "Bullish" if macd_bullish else "Bearish" if macd_bearish else "Mixed/Crossing"
         st_points.append(f"<span class='icon'>{macd_icon}</span><span>MACD indicator shows <strong>{macd_status}</strong> momentum signal.</span>")
    else: st_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>MACD analysis unavailable.</span>")

    # Bollinger Bands
    if current_price is not None and bb_lower is not None and bb_upper is not None:
         bb_icon = get_icon('neutral')
         bb_interp = "within normal volatility range."
         if current_price > bb_upper: bb_icon = get_icon('warning'); bb_interp = "above Upper Band (potential overbought/breakout)."
         elif current_price < bb_lower: bb_icon = get_icon('positive'); bb_interp = "below Lower Band (potential oversold/breakdown)."
         st_points.append(f"<span class='icon'>{bb_icon}</span><span>Price is currently <strong>{bb_interp}</strong></span>")
    else: st_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>Bollinger Band analysis unavailable.</span>")

    # Support/Resistance (Add if available)
    support = rdata.get('detailed_ta_data', {}).get('Support_30D')
    resistance = rdata.get('detailed_ta_data', {}).get('Resistance_30D')
    if support is not None and resistance is not None:
         st_points.append(f"<span class='icon'>{get_icon('info')}</span><span>Key levels to watch: Support ~{format_html_value(support, 'currency')}, Resistance ~{format_html_value(resistance, 'currency')}.</span>")


    # --- Long-Term Outlook Points (Aim for 5+) ---
    lt_points = []
    lt_icon = get_icon('up' if overall_pct_change > 1 else ('down' if overall_pct_change < -1 else 'neutral'))
    forecast_direction_summary = "Flat"
    if overall_pct_change > 1: forecast_direction_summary = "Potential Upside"
    elif overall_pct_change < -1: forecast_direction_summary = "Potential Downside"
    lt_points.append(f"<span class='icon'>{lt_icon}</span><span>Model forecasts ~<strong>{overall_pct_change:+.1f}%</strong> average change over 1 year to ≈{format_html_value(forecast_1y, 'currency')}.</span>")

    # Valuation
    fundamental_strength_summary = "Moderate" # Default
    val_summary = "Valuation appears moderate." # Default
    val_icon = get_icon('neutral')
    if fwd_pe != 'N/A':
        try:
             fpe_val = float(str(fwd_pe).replace('x',''))
             if fpe_val < 15 and fpe_val > 0: val_summary = f"Valuation potentially attractive (Fwd P/E: {fwd_pe})."; val_icon = get_icon('positive')
             elif fpe_val > 30: val_summary = f"Valuation appears elevated (Fwd P/E: {fwd_pe})."; val_icon = get_icon('warning')
             else: val_summary = f"Valuation appears moderate (Fwd P/E: {fwd_pe})."
        except: pass
    lt_points.append(f"<span class='icon'>{val_icon}</span><span>{val_summary} (Needs peer comparison).</span>")

    # Fundamental Health (ROE & Debt)
    roe_val = None; de_val = None
    if '%' in str(roe):
        try:
            roe_val = float(str(roe).replace('%', ''))
        except:
            pass
    if 'x' in str(debt_equity):
        try:
            de_val = float(str(debt_equity).replace('x', ''))
        except:
            pass
    if roe_val is not None and de_val is not None:
        if roe_val > 15 and de_val < 1.5: fundamental_strength_summary = "Strong"; health_icon = get_icon('up')
        elif roe_val < 5 or de_val > 2.5: fundamental_strength_summary = "Weak"; health_icon = get_icon('down')
        else: fundamental_strength_summary = "Moderate"; health_icon = get_icon('neutral')
        lt_points.append(f"<span class='icon'>{health_icon}</span><span>Fundamental health appears <strong>{fundamental_strength_summary}</strong> (ROE: {roe}, Debt/Equity: {debt_equity}).</span>")
    else: lt_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>Fundamental health assessment incomplete.</span>")


    # Growth
    growth_summary = "Recent growth trajectory is mixed or unclear."
    growth_icon = get_icon('neutral')
    if '%' in str(rev_growth) and '%' in str(earn_growth):
         try:
             rg = float(rev_growth.replace('%',''))
             eg = float(earn_growth.replace('%',''))
             if rg > 5 and eg > 10: growth_summary = f"Positive recent growth (Rev: {rev_growth}, Earn: {earn_growth})."; growth_icon = get_icon('up')
             elif rg < 0 or eg < 0: growth_summary = f"Negative recent growth (Rev: {rev_growth}, Earn: {earn_growth})."; growth_icon = get_icon('down')
             else: growth_summary = f"Moderate recent growth (Rev: {rev_growth}, Earn: {earn_growth})."
         except: pass
    lt_points.append(f"<span class='icon'>{growth_icon}</span><span>{growth_summary}</span>")

    # Analyst Consensus
    if analyst_rec != 'N/A':
        rec_icon = get_icon('up' if 'Buy' in analyst_rec else ('down' if 'Sell' in analyst_rec or 'Underperform' in analyst_rec else 'neutral'))
        lt_points.append(f"<span class='icon'>{rec_icon}</span><span>Analyst consensus: <strong>{analyst_rec}</strong>.</span>")
    else: lt_points.append(f"<span class='icon'>{get_icon('neutral')}</span><span>Analyst consensus data unavailable.</span>")

    # Dividend
    if dividend_yield != 'N/A' and dividend_yield != '0.00%':
        lt_points.append(f"<span class='icon'>{get_icon('dividend')}</span><span>Offers a dividend yield of <strong>{dividend_yield}</strong>.</span>")


    # --- Assemble HTML lists ---
    short_term_html = "".join([f"<li>{p}</li>" for p in st_points])
    long_term_html = "".join([f"<li>{p}</li>" for p in lt_points])

    # --- Create the final HTML for the conclusion columns ---
    outlook_summary = f"""
        <div class="conclusion-columns">
            <div class="conclusion-column">
                <h3>Short-Term Outlook</h3>
                <ul>{short_term_html}</ul>
            </div>
            <div class="conclusion-column">
                <h3>Long-Term Outlook (1 Year)</h3>
                <ul>{long_term_html}</ul>
            </div>
        </div>
         """

    # --- Generate the dynamic overall assessment string ---
    # Use the summarized variables calculated above
    overall_recommendation = (
        f"Overall assessment requires careful consideration of all factors. "
        f"Technicals currently show <strong>{technical_summary_sentiment}</strong> signals. "
        f"Fundamentals appear <strong>{fundamental_strength_summary}</strong>. "
        f"The forecast suggests <strong>{forecast_direction_summary}</strong>. "
        f"Consider risks before investing."
    )

    # --- Return the combined HTML ---
    return outlook_summary + f"<div class='narrative'><h4>Overall Assessment:</h4><p>{overall_recommendation}</p></div>" + "<p class='disclaimer'>This is an analysis report and not investment advice. Review all data and consult a professional.</p>"

def generate_faq_html(ticker, rdata):
    """Generates the FAQ section with more detailed answers."""
    current_price = rdata.get('current_price')
    forecast_1m = rdata.get('forecast_1m')
    forecast_1y = rdata.get('forecast_1y')
    overall_pct_change = rdata.get('overall_pct_change', 0.0)
    monthly_forecast_table_data = rdata.get('monthly_forecast_table_data', pd.DataFrame())
    sentiment = rdata.get('sentiment', 'N/A')
    volatility = rdata.get('volatility')
    valuation_data = rdata.get('valuation_data', {})
    period_label = rdata.get('period_label', 'Month')
    latest_rsi = rdata.get('latest_rsi')
    risk_items = rdata.get('risk_items', []) # Get risks

    faq_items = []

    # Q1: Forecast Next Year
    q1_ans = f"The current 1-year average price forecast for {ticker} is approximately <strong>{format_html_value(forecast_1y, 'currency')}</strong>. This represents a potential change of {overall_pct_change:+.1f}% from the current price of {format_html_value(current_price, 'currency')}. Keep in mind this is an estimate, and the actual price could fall within the forecast range (see table) or outside it due to market factors."
    faq_items.append((f"What is the {ticker} stock forecast for the next year?", q1_ans))

    # Q2: Up or Down?
    up_down = "go up" if overall_pct_change > 1 else "go down" if overall_pct_change < -1 else "remain relatively flat"
    q2_ans = f"The 1-year forecast ({overall_pct_change:+.1f}% potential change) suggests the stock might <strong>{up_down}</strong> on average. However, short-term movements can differ significantly based on technical factors ({sentiment}) and market news. Refer to the detailed forecast table for projected monthly ranges."
    faq_items.append((f"Will {ticker} stock go up or down?", q2_ans))

    # Q3: Good to Buy?
    rsi_condition = ""
    if latest_rsi is not None:
         rsi_level = "neutral territory"
         rsi_icon = get_icon('neutral')
         if latest_rsi < 30: rsi_level = f"oversold (RSI: {latest_rsi:.1f})"; rsi_icon = get_icon('positive')
         elif latest_rsi > 70: rsi_level = f"overbought (RSI: {latest_rsi:.1f})"; rsi_icon = get_icon('warning')
         rsi_condition = f"The stock is currently {rsi_icon} {rsi_level}."

    buy_lean = ('positive' if 'Bullish' in sentiment else ('negative' if 'Bearish' in sentiment else 'neutral'))
    risk_count = len(risk_items)
    risk_mention = f"However, {risk_count} potential risk factor(s) were identified (see Risk section)." if risk_count > 0 else "Key specific risks were not automatically flagged, but standard market risks apply."

    q3_ans = f"Current technical sentiment is <strong>{sentiment}</strong> ({buy_lean} leaning). {rsi_condition} The forecast shows a {overall_pct_change:+.1f}% potential 1-year change. {risk_mention} <strong>This is not investment advice.</strong> Evaluate risks, fundamentals (like valuation, debt), and your own investment strategy. Consider consulting a financial advisor."
    faq_items.append((f"Is {ticker} a good stock to buy now?", q3_ans))

    # Q4: Volatility
    vol_level = "N/A"
    vol_icon = get_icon('neutral')
    if volatility is not None:
        if volatility > 40: vol_level = "high"; vol_icon = get_icon('warning')
        elif volatility > 20: vol_level = "moderate"
        else: vol_level = "low"
    q4_ans = f"The recent annualized volatility for {ticker} is calculated at {vol_icon} <strong>{format_html_value(volatility, 'percent_direct', 1)}</strong>, indicating {vol_level} price fluctuations compared to typical market averages. Check the 'Stock Price Statistics' section for Beta comparison if available."
    faq_items.append((f"How volatile is {ticker} stock?", q4_ans))

    # Q5: P/E Valuation
    pe_ratio = valuation_data.get('Trailing P/E', 'N/A')
    pe_comment = "N/A"
    pe_icon = get_icon('neutral')
    if pe_ratio != 'N/A':
         try:
             pe_val = float(str(pe_ratio).replace('x',''))
             if pe_val > 50: pe_comment = "quite high"; pe_icon = get_icon('warning')
             elif pe_val > 25: pe_comment = "moderately high"; pe_icon = get_icon('warning')
             elif pe_val < 15 and pe_val > 0: pe_comment = "relatively low"; pe_icon = get_icon('positive')
             elif pe_val <= 0: pe_comment = "negative"; pe_icon = get_icon('negative')
             else: pe_comment = "moderate"
         except: pe_comment = "numeric interpretation unavailable"
    q5_ans = f"The Trailing P/E ratio is {pe_icon} <strong>{pe_ratio}</strong>. This is considered {pe_comment} relative to typical benchmarks. Refer to the 'Valuation Metrics' section for Forward P/E and other ratios, ideally compared to industry peers for full context."
    faq_items.append((f"Is {ticker} considered expensive based on P/E ratio?", q5_ans))

    # Generate HTML details elements
    details_html = ""
    for question, answer in faq_items:
        details_html += f"<details><summary>{question}</summary><p>{answer}</p></details>"
    return f"{details_html}" # Return only the details elements


def generate_report_info_disclaimer_html(generation_time):
    """Generates the final disclaimer and timestamp section."""
    try:
        # Format time, including timezone if available
        time_str = f"{generation_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except ValueError: # Handle cases where timezone might be naive
         time_str = f"{generation_time.strftime('%Y-%m-%d %H:%M:%S')}"

    return f"""
         <div class="general-info">
             <p><strong>Report Generated:</strong> {time_str}</p>
             <p><strong>Data Sources:</strong> Yahoo Finance API (via yfinance library), FRED Economic Data (via pandas_datareader or fallback).</p>
             Limitations:</strong>The accuracy of the data depends on the source providers that include Yahoo Finance and FRED. Technical market indicators always operate with a delay because of their design. This document operates with past data because it have not real-time functionality.</p>
             <div class="disclaimer"><strong>Disclaimer:</strong> This report is generated for informational purposes only and does not constitute financial, investment, or trading advice, nor a recommendation or solicitation to buy, sell, or hold any security. All investments involve risk, and past performance is not indicative of future results. Market conditions are volatile. Readers should conduct their own thorough due diligence and consult with a qualified financial professional before making any investment decisions. The creators of this report assume no liability for any actions taken based on the information provided herein.</div>
         </div>
    """

# Placeholder for the missing helper function (if it was indeed removed)
# This function is called by several others like generate_valuation_metrics_html etc.
def generate_metrics_section_content(metrics):
    """Helper to generate table body content for metrics sections."""
    rows = ""
    # Ensure metrics is a dictionary before iterating
    if isinstance(metrics, dict):
        # Generate a table row for each key-value pair where value is not 'N/A'
        rows = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>"
                        for k, v in metrics.items() if v != 'N/A'])

    # Provide a message if no valid data was found
    if not rows:
        rows = "<tr><td colspan='2' style='text-align: center; font-style: italic;'>No specific data available for this section.</td></tr>"

    # Return the HTML structure including the table container and table body
    return f"""<div class="table-container">
                   <table class="metrics-table">
                       <tbody>
                           {rows}
                       </tbody>
                   </table>
               </div>"""