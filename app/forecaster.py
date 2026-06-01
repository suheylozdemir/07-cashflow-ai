import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings("ignore")

def load_classified_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def forecast_cashflow(df: pd.DataFrame, forecast_days: int = 90) -> dict:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    
    daily_income = df[df["Category"] == "Income"].groupby("Date")["Credit"].sum()
    daily_expenses = df[df["Category"] == "Expense"].groupby("Date")["Debit"].sum()
    
    avg_daily_income = daily_income.mean()
    avg_daily_expenses = daily_expenses.mean()
    avg_net_daily = avg_daily_income - avg_daily_expenses
    
    last_balance = df["Balance"].iloc[-1]
    last_date = df["Date"].max().to_pydatetime()
    
    forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    forecast_balances = []
    current = last_balance
    
    daily_net = avg_daily_income - avg_daily_expenses
    for i, date in enumerate(forecast_dates):
        current += daily_net
        forecast_balances.append(round(current, 2))
    
    cashflow_negative_day = None
    for i, balance in enumerate(forecast_balances):
        if balance < 0:
            cashflow_negative_day = i + 1
            break
    
    critical_threshold = last_balance * 0.2
    low_cash_day = None
    for i, balance in enumerate(forecast_balances):
        if balance < critical_threshold:
            low_cash_day = i + 1
            break
    
    return {
        "current_balance": round(last_balance, 2),
        "forecast_period_days": forecast_days,
        "avg_daily_income": round(avg_daily_income, 2),
        "avg_daily_expenses": round(avg_daily_expenses, 2),
        "avg_net_daily": round(avg_net_daily, 2),
        "projected_balance_30d": round(forecast_balances[29], 2),
        "projected_balance_60d": round(forecast_balances[59], 2),
        "projected_balance_90d": round(forecast_balances[89], 2),
        "cashflow_negative_day": cashflow_negative_day,
        "low_cash_warning_day": low_cash_day,
        "forecast_dates": [d.strftime("%Y-%m-%d") for d in forecast_dates],
        "forecast_balances": forecast_balances
    }

def detect_anomalies(df: pd.DataFrame) -> list:
    anomalies = []
    
    expense_df = df[df["Category"] == "Expense"].copy()
    expense_df["Date"] = pd.to_datetime(expense_df["Date"])
    
    categories = expense_df["Description"].apply(lambda x: x.split(" - ")[0] if " - " in x else x.split()[0])
    expense_df["category_group"] = categories
    
    for category, group in expense_df.groupby("category_group"):
        if len(group) < 3:
            continue
        
        amounts = group["Debit"].values.reshape(-1, 1)
        
        clf = IsolationForest(contamination=0.1, random_state=42)
        predictions = clf.fit_predict(amounts)
        
        anomaly_indices = group.index[predictions == -1]
        
        mean_amount = group["Debit"].mean()
        
        for idx in anomaly_indices:
            row = df.loc[idx]
            deviation = (row["Debit"] - mean_amount) / mean_amount * 100
            if deviation < 0:
                continue
            
            if deviation > 30:
                anomalies.append({
                    "date": pd.to_datetime(row["Date"]).strftime("%Y-%m-%d"),
                    "description": row["Description"],
                    "amount": row["Debit"],
                    "category_avg": round(mean_amount, 2),
                    "deviation_pct": round(deviation, 1),
                    "severity": "High" if deviation > 50 else "Medium"
                })
    
    anomalies.sort(key=lambda x: x["deviation_pct"], reverse=True)
    return anomalies

def generate_insights(forecast: dict, anomalies: list) -> list:
    insights = []
    
    if forecast["avg_net_daily"] > 0:
        insights.append({
            "type": "positive",
            "message": f"Business is cash flow positive. Average daily net: AUD {forecast['avg_net_daily']:,.2f}"
        })
    else:
        insights.append({
            "type": "warning",
            "message": f"Business is cash flow negative. Average daily net: AUD {forecast['avg_net_daily']:,.2f}"
        })
    
    if forecast["low_cash_warning_day"]:
        insights.append({
            "type": "critical",
            "message": f"Cash balance projected to fall below 20% threshold in {forecast['low_cash_warning_day']} days."
        })
    
    if forecast["cashflow_negative_day"]:
        insights.append({
            "type": "critical",
            "message": f"Cash balance projected to go negative in {forecast['cashflow_negative_day']} days. Immediate action required."
        })
    
    high_anomalies = [a for a in anomalies if a["severity"] == "High"]
    if high_anomalies:
        insights.append({
            "type": "warning",
            "message": f"{len(high_anomalies)} high-severity spending anomalies detected. Review: {', '.join([a['description'] for a in high_anomalies[:3]])}"
        })
    
    if forecast["projected_balance_90d"] > forecast["current_balance"]:
        growth = forecast["projected_balance_90d"] - forecast["current_balance"]
        insights.append({
            "type": "positive",
            "message": f"Projected balance growth of AUD {growth:,.2f} over next 90 days."
        })
    
    return insights

def run_full_analysis(csv_path: str) -> dict:
    df = load_classified_data(csv_path)
    
    print("Running cash flow forecast...")
    forecast = forecast_cashflow(df)
    
    print("Detecting anomalies...")
    anomalies = detect_anomalies(df)
    
    print("Generating insights...")
    insights = generate_insights(forecast, anomalies)
    
    print("\n===== CASH FLOW FORECAST =====")
    print(f"Current Balance:        AUD {forecast['current_balance']:,.2f}")
    print(f"Projected 30 days:      AUD {forecast['projected_balance_30d']:,.2f}")
    print(f"Projected 60 days:      AUD {forecast['projected_balance_60d']:,.2f}")
    print(f"Projected 90 days:      AUD {forecast['projected_balance_90d']:,.2f}")
    
    if forecast["low_cash_warning_day"]:
        print(f"\n⚠️  LOW CASH WARNING: Day {forecast['low_cash_warning_day']}")
    
    print(f"\n===== ANOMALIES DETECTED ({len(anomalies)}) =====")
    for a in anomalies[:5]:
        print(f"  [{a['severity']}] {a['description']}: AUD {a['amount']:.2f} (avg: AUD {a['category_avg']:.2f}, +{a['deviation_pct']}%)")
    
    print(f"\n===== INSIGHTS =====")
    for insight in insights:
        emoji = "✅" if insight["type"] == "positive" else "⚠️" if insight["type"] == "warning" else "🚨"
        print(f"  {emoji} {insight['message']}")
    
    return {
        "forecast": forecast,
        "anomalies": anomalies,
        "insights": insights,
        "dataframe": df
    }

if __name__ == "__main__":
    run_full_analysis("data/bank_statement_Q1_2026_classified.csv")