import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from app.forecaster import forecast_cashflow, detect_anomalies, generate_insights
from app.gst_agent import generate_bas_summary

def make_sample_df():
    data = {
        "Date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05",
                 "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09", "2026-01-10"],
        "Description": ["Invoice Payment - CBA", "Office Rent - Sydney", "Staff Payroll",
                        "Invoice Payment - ANZ", "AGL Energy", "Woolworths - Office Supplies",
                        "Invoice Payment - Westpac", "Telstra Business Phone", "Sydney CBD Parking",
                        "Invoice Payment - Atlassian"],
        "Debit": [0, 5000, 30000, 0, 500, 150, 0, 100, 50, 0],
        "Credit": [15000, 0, 0, 12000, 0, 0, 8000, 0, 0, 20000],
        "GST_Applicable": [True, True, False, True, True, True, True, True, True, True],
        "GST_Amount": [1363.64, 454.55, 0, 1090.91, 45.45, 13.64, 727.27, 9.09, 4.55, 1818.18],
        "Amount_Ex_GST": [13636.36, 4545.45, 30000, 10909.09, 454.55, 136.36, 7272.73, 90.91, 45.45, 18181.82],
        "Category": ["Income", "Expense", "Expense", "Income", "Expense", "Expense",
                     "Income", "Expense", "Expense", "Income"],
        "Balance": [515000, 510000, 480000, 492000, 491500, 491350, 499350, 499250, 499200, 519200],
        "gst_status_verified": ["APPLICABLE", "APPLICABLE", "FREE", "APPLICABLE", "APPLICABLE",
                                "APPLICABLE", "APPLICABLE", "APPLICABLE", "APPLICABLE", "APPLICABLE"],
        "gst_amount_verified": [1363.64, 454.55, 0, 1090.91, 45.45, 13.64, 727.27, 9.09, 4.55, 1818.18],
        "confidence": ["High", "High", "High", "High", "High", "High", "High", "High", "High", "High"]
    }
    return pd.DataFrame(data)

def test_generate_bas_summary_structure():
    df = make_sample_df()
    bas = generate_bas_summary(df)
    assert "total_sales" in bas
    assert "total_expenses" in bas
    assert "gst_collected" in bas
    assert "gst_paid" in bas
    assert "net_gst_owed" in bas
    assert "transaction_count" in bas

def test_generate_bas_summary_values():
    df = make_sample_df()
    bas = generate_bas_summary(df)
    assert bas["total_sales"] == 55000
    assert bas["total_expenses"] == 35800
    assert bas["transaction_count"] == 10

def test_generate_bas_summary_net_gst():
    df = make_sample_df()
    bas = generate_bas_summary(df)
    assert bas["net_gst_owed"] == round(bas["gst_collected"] - bas["gst_paid"], 2)

def test_forecast_cashflow_structure():
    df = make_sample_df()
    forecast = forecast_cashflow(df)
    assert "current_balance" in forecast
    assert "projected_balance_30d" in forecast
    assert "projected_balance_60d" in forecast
    assert "projected_balance_90d" in forecast
    assert "forecast_dates" in forecast
    assert "forecast_balances" in forecast

def test_forecast_cashflow_length():
    df = make_sample_df()
    forecast = forecast_cashflow(df, forecast_days=90)
    assert len(forecast["forecast_dates"]) == 90
    assert len(forecast["forecast_balances"]) == 90

def test_detect_anomalies_returns_list():
    df = make_sample_df()
    anomalies = detect_anomalies(df)
    assert isinstance(anomalies, list)

def test_detect_anomalies_structure():
    df = make_sample_df()
    anomalies = detect_anomalies(df)
    for a in anomalies:
        assert "date" in a
        assert "description" in a
        assert "amount" in a
        assert "deviation_pct" in a
        assert "severity" in a

def test_generate_insights_returns_list():
    df = make_sample_df()
    forecast = forecast_cashflow(df)
    anomalies = detect_anomalies(df)
    insights = generate_insights(forecast, anomalies)
    assert isinstance(insights, list)
    assert len(insights) > 0

def test_generate_insights_types():
    df = make_sample_df()
    forecast = forecast_cashflow(df)
    anomalies = detect_anomalies(df)
    insights = generate_insights(forecast, anomalies)
    for insight in insights:
        assert "type" in insight
        assert "message" in insight
        assert insight["type"] in ["positive", "warning", "critical"]