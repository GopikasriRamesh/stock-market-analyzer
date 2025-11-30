import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np          
import plotly.express as px

# 1. Page Config (Tab Title)
st.set_page_config(page_title="Stock Risk Analyzer", layout="wide")

st.title("📊 Real-Time Stock Portfolio Risk Analyzer")

# 2. Sidebar for User Input
st.sidebar.header("User Input")
# Default tickers: Apple, Tesla, Google, Microsoft, Amazon
tickers = st.sidebar.text_input("Enter Stock Tickers (comma separated)", "AAPL,TSLA,GOOGL,MSFT,AMZN")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# 3. The "Engine": Fetch Data
def get_data(tickers_list, start, end):
    # Add auto_adjust=False to ensure 'Adj Close' column exists
    data = yf.download(tickers_list, start=start, end=end, auto_adjust=False)['Adj Close']
    return data

# 4. Button to Trigger Analysis
if st.button("Analyze Portfolio"):
    # Clean the input (remove spaces, make uppercase)
    ticker_list = [x.strip().upper() for x in tickers.split(',')]
    
    with st.spinner('Fetching real-time data...'):
        stock_data = get_data(ticker_list, start_date, end_date)
        
        # Check if data is empty (Error handling)
        if stock_data.empty:
            st.error("No data found. Please check ticker symbols.")
        else:
            st.success("Data loaded successfully!")
            
            # Show the raw dataframe (Just to check Phase 1 worked)
            st.subheader("Raw Data Preview (Last 5 Days)")
            st.dataframe(stock_data.tail())
            
            # Simple Chart
            st.subheader("Price History")
            st.line_chart(stock_data)
            
            # 1. Calculate Daily Returns (Percent change day-to-day)
            daily_returns = stock_data.pct_change().dropna()
            
            # 2. Risk Analysis (Standard Deviation)
            # We multiply by sqrt(252) to annualize the risk (252 trading days in a year)
            daily_std = daily_returns.std()
            annualized_risk = daily_std * np.sqrt(252) * 100  # Convert to percentage

            # Create a DataFrame for the chart
            risk_df = pd.DataFrame({
                'Ticker': annualized_risk.index, 
                'Risk (%)': annualized_risk.values
            })

            st.markdown("---") # Separator line
            st.subheader("⚠️ Risk Analysis (Annualized Volatility)")
            st.write("Higher bars mean higher risk. Investors expect higher returns for taking higher risks.")
            
            # Interactive Bar Chart using Plotly
            fig_risk = px.bar(risk_df, x='Ticker', y='Risk (%)', 
                              color='Risk (%)', 
                              color_continuous_scale='Redor',
                              title="Annualized Volatility per Stock")
            st.plotly_chart(fig_risk, use_container_width=True)

            # 3. Correlation Matrix (Do they move together?)
            st.markdown("---")
            st.subheader("🔗 Correlation Heatmap")
            st.write("1.0 = Perfect Positive Correlation (Move exactly together)")
            st.write("0.0 = No Correlation")
            
            # Calculate correlation
            correlation_matrix = daily_returns.corr()
            
            # Interactive Heatmap using Plotly
            fig_corr = px.imshow(correlation_matrix, 
                                 text_auto=True, 
                                 aspect="auto",
                                 color_continuous_scale='Viridis',
                                 title="Stock Correlation Matrix")
            st.plotly_chart(fig_corr, use_container_width=True)

            # 4. Calculator: Portfolio Return
            st.markdown("---")
            st.subheader("💰 Cumulative Return")
            st.write("If you invested $1 on the start date, how much is it worth now?")
            
            cumulative_returns = (1 + daily_returns).cumprod()
            st.line_chart(cumulative_returns)
            
            # 5. Monte Carlo Simulation (The "Advanced" Feature)
            st.markdown("---")
            st.subheader("🔮 Monte Carlo Simulation (Future Prediction)")
            st.write("Simulating 50 possible future paths for your portfolio over the next year.")

            # Get the last close price
            last_price = stock_data.iloc[-1]
            
            # Simulation parameters
            num_simulations = 50
            num_days = 252
            simulation_df = pd.DataFrame()

            for x in range(num_simulations):
                count = 0
                # Generate random daily returns based on history
                daily_vol = daily_returns.std()
                
                # Simple random walk
                price_series = []
                price = last_price * (1 + np.random.normal(0, daily_vol, len(last_price))) # Start point
                price_series.append(price)
                
                for y in range(num_days):
                    if count == 251:
                        break
                    price = price_series[count] * (1 + np.random.normal(0, daily_vol, len(last_price)))
                    price_series.append(price)
                    count += 1
                
                # We only plot the first stock in the list for clarity in this example
                simulation_df[x] = [p[0] for p in price_series] # Plotting first ticker only

            # Plot the simulation
            st.line_chart(simulation_df)
            st.caption("This chart shows 50 different 'what-if' scenarios for the first stock in your list.")