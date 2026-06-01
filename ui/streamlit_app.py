import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import tempfile
from app.gst_agent import analyze_cashflow
from app.forecaster import forecast_cashflow, detect_anomalies, generate_insights, load_classified_data

st.set_page_config(
    page_title="CashFlow AI",
    page_icon="💼",
    layout="wide"
)

st.title("💼 CashFlow AI")
st.caption("AI-powered GST classification and cash flow analysis for Australian small businesses")

with st.sidebar:
    st.header("Upload Bank Statement")
    st.caption("Upload your Australian business bank statement in CSV format")
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")
        analyze_btn = st.button("Run Analysis", type="primary", use_container_width=True)
    else:
        st.info("Upload a CSV file to get started")
        analyze_btn = False
    
    st.divider()
    st.caption("Powered by OpenAI GPT-4.1-mini + ATO GST Rules")
    st.caption("Data sources: Australian Taxation Office")

if not uploaded_file:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("GST Classification", "AI-powered", "ATO Rules")
    with col2:
        st.metric("Cash Flow Forecast", "90 Days", "Forward-looking")
    with col3:
        st.metric("Anomaly Detection", "IsolationForest", "ML-based")
    
    st.info("Upload your bank statement CSV to begin analysis. The system will classify all transactions for GST, calculate your BAS summary, forecast cash flow, and detect spending anomalies.")
    st.stop()

if analyze_btn and uploaded_file:
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    with st.spinner("Running AI GST classification... This may take 2-3 minutes."):
        try:
            result = analyze_cashflow(tmp_path)
            classified_path = tmp_path.replace(".csv", "_classified.csv")
            st.session_state["result"] = result
            st.session_state["classified_path"] = classified_path
            st.success("Analysis complete!")
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

if "result" not in st.session_state:
    st.info("Click 'Run Analysis' to analyze your uploaded file.")
    st.stop()

result = st.session_state["result"]
bas = result["bas_summary"]
df = result["dataframe"]

forecast = forecast_cashflow(df)
anomalies = detect_anomalies(df)
insights = generate_insights(forecast, anomalies)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Cash Flow", "🧾 GST & BAS", "⚠️ Anomalies"])

with tab1:
    st.subheader("Business Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Balance", f"AUD {forecast['current_balance']:,.2f}")
    with col2:
        st.metric("Total Income", f"AUD {bas['total_sales']:,.2f}")
    with col3:
        st.metric("Total Expenses", f"AUD {bas['total_expenses']:,.2f}")
    with col4:
        net = bas['total_sales'] - bas['total_expenses']
        st.metric("Net Profit", f"AUD {net:,.2f}", delta=f"{net/bas['total_sales']*100:.1f}%")
    
    st.divider()
    st.subheader("AI Insights")
    for insight in insights:
        if insight["type"] == "positive":
            st.success(insight["message"])
        elif insight["type"] == "warning":
            st.warning(insight["message"])
        else:
            st.error(insight["message"])
    
    st.divider()
    st.subheader("BAS Summary — Q1 2026")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("GST Collected", f"AUD {bas['gst_collected']:,.2f}")
        st.metric("GST Paid", f"AUD {bas['gst_paid']:,.2f}")
    with col2:
        st.metric("Net GST Owed to ATO", f"AUD {bas['net_gst_owed']:,.2f}", 
                 delta="Payment due" if bas['net_gst_owed'] > 0 else "Refund due",
                 delta_color="inverse")
        st.metric("Total Transactions", bas['transaction_count'])

with tab2:
    st.subheader("90-Day Cash Flow Forecast")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("30 Days", f"AUD {forecast['projected_balance_30d']:,.2f}",
                 delta=f"{forecast['projected_balance_30d'] - forecast['current_balance']:+,.2f}")
    with col2:
        st.metric("60 Days", f"AUD {forecast['projected_balance_60d']:,.2f}",
                 delta=f"{forecast['projected_balance_60d'] - forecast['current_balance']:+,.2f}")
    with col3:
        st.metric("90 Days", f"AUD {forecast['projected_balance_90d']:,.2f}",
                 delta=f"{forecast['projected_balance_90d'] - forecast['current_balance']:+,.2f}")
    
    fig = go.Figure()
    
    historical_dates = pd.to_datetime(df.sort_values("Date")["Date"]).dt.strftime("%Y-%m-%d").tolist()
    historical_balances = df.sort_values("Date")["Balance"].tolist()
    
    fig.add_trace(go.Scatter(
        x=historical_dates,
        y=historical_balances,
        mode="lines",
        name="Historical Balance",
        line=dict(color="#00C49F", width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast["forecast_dates"],
        y=forecast["forecast_balances"],
        mode="lines",
        name="Projected Balance",
        line=dict(color="#4A90D9", width=2, dash="dash")
    ))
    
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Balance (AUD)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Daily Income", f"AUD {forecast['avg_daily_income']:,.2f}")
    with col2:
        st.metric("Avg Daily Expenses", f"AUD {forecast['avg_daily_expenses']:,.2f}")

with tab3:
    st.subheader("GST Classification & BAS")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("GST Applicable Sales", f"AUD {bas['gst_applicable_sales']:,.2f}")
        st.metric("GST Collected", f"AUD {bas['gst_collected']:,.2f}")
    with col2:
        st.metric("GST Applicable Expenses", f"AUD {bas['gst_applicable_expenses']:,.2f}")
        st.metric("GST Paid", f"AUD {bas['gst_paid']:,.2f}")
    with col3:
        st.metric("GST Free Sales", f"AUD {bas['gst_free_sales']:,.2f}")
        st.metric("Net GST Owed", f"AUD {bas['net_gst_owed']:,.2f}")
    
    st.divider()
    
    if "gst_status_verified" in df.columns:
        st.subheader("Transaction Classifications")
        
        display_cols = ["Date", "Description", "Debit", "Credit", "Category", "gst_status_verified", "gst_amount_verified", "confidence"]
        available_cols = [c for c in display_cols if c in df.columns]
        display_df = df[available_cols].copy()
        display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
        
        col_filter = st.selectbox("Filter by", ["All", "Income", "Expense", "GST Applicable", "GST Free"])
        
        if col_filter == "Income":
            display_df = display_df[display_df["Category"] == "Income"]
        elif col_filter == "Expense":
            display_df = display_df[display_df["Category"] == "Expense"]
        elif col_filter == "GST Applicable":
            display_df = display_df[display_df["gst_status_verified"] == "APPLICABLE"]
        elif col_filter == "GST Free":
            display_df = display_df[display_df["gst_status_verified"] == "FREE"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab4:
    st.subheader(f"Spending Anomalies Detected: {len(anomalies)}")
    
    if not anomalies:
        st.success("No significant spending anomalies detected.")
    else:
        high = [a for a in anomalies if a["severity"] == "High"]
        medium = [a for a in anomalies if a["severity"] == "Medium"]
        
        if high:
            st.error(f"🚨 {len(high)} High Severity Anomalies")
            for a in high:
                with st.expander(f"{a['description']} — AUD {a['amount']:.2f} (+{a['deviation_pct']}% above average)"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Transaction Amount", f"AUD {a['amount']:.2f}")
                    with col2:
                        st.metric("Category Average", f"AUD {a['category_avg']:.2f}")
                    with col3:
                        st.metric("Deviation", f"+{a['deviation_pct']}%")
                    st.caption(f"Date: {a['date']}")
        
        if medium:
            st.warning(f"⚠️ {len(medium)} Medium Severity Anomalies")
            for a in medium:
                with st.expander(f"{a['description']} — AUD {a['amount']:.2f} (+{a['deviation_pct']}% above average)"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Transaction Amount", f"AUD {a['amount']:.2f}")
                    with col2:
                        st.metric("Category Average", f"AUD {a['category_avg']:.2f}")
                    with col3:
                        st.metric("Deviation", f"+{a['deviation_pct']}%")
                    st.caption(f"Date: {a['date']}")
        
        fig_anomaly = px.bar(
            pd.DataFrame(anomalies),
            x="description",
            y="deviation_pct",
            color="severity",
            color_discrete_map={"High": "#E24B4A", "Medium": "#EF9F27"},
            title="Anomaly Deviation from Category Average (%)",
            labels={"deviation_pct": "Deviation (%)", "description": "Transaction"}
        )
        fig_anomaly.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            height=350
        )
        st.plotly_chart(fig_anomaly, use_container_width=True)