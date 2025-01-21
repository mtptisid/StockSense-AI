import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from phi.agent.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.googlesearch import GoogleSearch

# Replace with your Groq API key
GROQ_API_KEY = "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"

# Expanded list of stocks
COMMON_STOCKS = {
    'NVIDIA': 'NVDA', 'APPLE': 'AAPL', 'GOOGLE': 'GOOGL', 'MICROSOFT': 'MSFT',
    'TESLA': 'TSLA', 'AMAZON': 'AMZN', 'META': 'META', 'NETFLIX': 'NFLX',
    'TCS': 'TCS.NS', 'RELIANCE': 'RELIANCE.NS', 'INFOSYS': 'INFY.NS',
    'WIPRO': 'WIPRO.NS', 'HDFC': 'HDFCBANK.NS', 'TATAMOTORS': 'TATAMOTORS.NS',
    'ICICIBANK': 'ICICIBANK.NS', 'SBIN': 'SBIN.NS',
    'ALPHABET': 'GOOG', 'WALMART': 'WMT', 'COCA-COLA': 'KO', 'PEPSI': 'PEP',
    'BOEING': 'BA', 'JOHNSON & JOHNSON': 'JNJ', 'VISA': 'V', 'MASTERCARD': 'MA'
}

# Streamlit page configuration
st.set_page_config(page_title="Stocks Analysis AI Agents", page_icon="📈", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stApp { max-width: 1400px; margin: 0 auto; }
    .card {
        background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e1e4e8;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0366d6;
    }
    .metric-label {
        font-size: 14px;
        color: #586069;
        text-transform: uppercase;
    }
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e1e4e8;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize AI agents
def initialize_agents():
    if not st.session_state.get('agents_initialized', False):
        try:
            st.session_state.web_agent = Agent(
                name="Web Search Agent",
                role="Search the web for information",
                model=Groq(api_key=GROQ_API_KEY),
                tools=[GoogleSearch(fixed_max_results=5), DuckDuckGo(fixed_max_results=5)]
            )
            st.session_state.finance_agent = Agent(
                name="Financial AI Agent",
                role="Providing financial insights",
                model=Groq(api_key=GROQ_API_KEY),
                tools=[YFinanceTools()]
            )
            st.session_state.multi_ai_agent = Agent(
                name='Stock Market Agent',
                role='Stock market analysis specialist',
                model=Groq(api_key=GROQ_API_KEY),
                team=[st.session_state.web_agent, st.session_state.finance_agent]
            )
            st.session_state.agents_initialized = True
            return True
        except Exception as e:
            st.error(f"Agent initialization error: {str(e)}")
            return False

# Fetch stock data
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None, None

# Fetch options data
def get_options_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        options_dates = stock.options  # Get available expiration dates
        options_data = {}
        for date in options_dates:
            options_chain = stock.option_chain(date)
            options_data[date] = {
                'calls': options_chain.calls,
                'puts': options_chain.puts
            }
        return options_data
    except Exception as e:
        st.error(f"Error fetching options data: {str(e)}")
        return None

# Create interactive price chart
def create_price_chart(hist_data, symbol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist_data.index, open=hist_data['Open'],
        high=hist_data['High'], low=hist_data['Low'],
        close=hist_data['Close'], name='OHLC'
    ))
    fig.update_layout(
        title=f'{symbol} Price Movement',
        template='plotly_white',
        xaxis_rangeslider_visible=True,  # Enable range slider
        hovermode="x unified",  # Show unified hover data
        height=500
    )
    return fig

# Main function
def main():
    st.title("Stocks Analysis AI Agents")
    
    # Dropdown for stock selection
    selected_stock = st.selectbox(
        "Select a Company", 
        list(COMMON_STOCKS.keys()), 
        help="Select a company from the list"
    )
    
    if st.button("Analyze", use_container_width=True):
        symbol = COMMON_STOCKS.get(selected_stock.upper())
        if not symbol:
            st.error("Invalid stock selection")
            return
        
        if initialize_agents():
            with st.spinner("Analyzing..."):
                info, hist = get_stock_data(symbol)
                options_data = get_options_data(symbol)
                
                if info and hist is not None:
                    # Display stock metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"<div class='card'><div class='metric-value'>${info.get('currentPrice', 'N/A')}</div><div class='metric-label'>Current Price</div></div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div class='card'><div class='metric-value'>{info.get('forwardPE', 'N/A')}</div><div class='metric-label'>Forward P/E</div></div>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<div class='card'><div class='metric-value'>{info.get('recommendationKey', 'N/A').title()}</div><div class='metric-label'>Recommendation</div></div>", unsafe_allow_html=True)
                    
                    # Display price chart
                    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                    st.plotly_chart(create_price_chart(hist, symbol), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display company overview
                    if 'longBusinessSummary' in info:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("### Company Overview")
                        st.write(info['longBusinessSummary'])
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display options data
                    if options_data:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("### Options Data")
                        for date, data in options_data.items():
                            st.write(f"**Expiration Date: {date}**")
                            st.write("**Calls:**")
                            st.dataframe(data['calls'])
                            st.write("**Puts:**")
                            st.dataframe(data['puts'])
                        st.markdown("</div>", unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()