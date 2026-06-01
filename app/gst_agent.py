import os
import pandas as pd
import json
from openai import OpenAI
from app.rag import query_gst_rules
from dotenv import load_dotenv

load_dotenv()

def classify_batch(transactions: list) -> list:
    client = OpenAI()
    
    gst_context = query_gst_rules(
        "GST applicable transactions Australia business expenses income food health insurance rent payroll"
    )
    
    transactions_text = "\n".join([
        f"{i+1}. Description: {t['description']}, Amount: AUD {t['amount']:.2f}, Type: {t['category']}"
        for i, t in enumerate(transactions)
    ])
    
    prompt = f"""You are an Australian GST expert. Classify each transaction according to ATO GST rules.

ATO GST Rules:
{gst_context}

Transactions to classify:
{transactions_text}

For each transaction, respond with a JSON array in this exact format:
[
  {{
    "index": 1,
    "gst_status": "APPLICABLE" or "FREE",
    "gst_amount": <calculated numeric value, e.g. 5.45, NOT a formula like "60/11">,
    "rule": "<brief ATO rule explanation>",
    "confidence": "High" or "Medium" or "Low"
  }},
  ...
]

Respond ONLY with the JSON array, no other text."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    try:
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        results = json.loads(content)
        return results
    except Exception as e:
        print(f"Failed to parse batch response: {e}")
        print(f"Raw response: {content[:200]}")
        return [{"index": i+1, "gst_status": "UNKNOWN", "gst_amount": 0, "rule": "Parse error", "confidence": "Low"} for i in range(len(transactions))]

def classify_all_transactions(df: pd.DataFrame, batch_size: int = 10) -> pd.DataFrame:
    all_results = []
    total = len(df)
    
    print(f"Classifying {total} transactions in batches of {batch_size}...")
    
    for start in range(0, total, batch_size):
        batch_df = df.iloc[start:start + batch_size]
        batch = []
        
        for _, row in batch_df.iterrows():
            amount = row["Debit"] if row["Debit"] > 0 else row["Credit"]
            batch.append({
                "description": row["Description"],
                "amount": amount,
                "category": row["Category"]
            })
        
        results = classify_batch(batch)
        
        for result in results:
            idx = start + result["index"] - 1
            all_results.append({
                "original_index": idx,
                "gst_status_verified": result.get("gst_status", "UNKNOWN"),
                "gst_amount_verified": round(float(result.get("gst_amount", 0)), 2),
                "rule": result.get("rule", ""),
                "confidence": result.get("confidence", "Low")
            })
        
        print(f"  Processed {min(start + batch_size, total)}/{total} transactions")
    
    results_df = pd.DataFrame(all_results).set_index("original_index")
    df = df.copy()
    df["gst_status_verified"] = results_df["gst_status_verified"]
    df["gst_amount_verified"] = results_df["gst_amount_verified"]
    df["rule"] = results_df["rule"]
    df["confidence"] = results_df["confidence"]
    
    return df

def generate_bas_summary(df: pd.DataFrame) -> dict:
    income_df = df[df["Category"] == "Income"]
    expense_df = df[df["Category"] == "Expense"]
    
    gst_collected = income_df["GST_Amount"].sum()
    gst_paid = expense_df[expense_df["GST_Applicable"] == True]["GST_Amount"].sum()
    net_gst = gst_collected - gst_paid
    
    total_sales = income_df["Credit"].sum()
    total_expenses = expense_df["Debit"].sum()
    
    gst_free_sales = income_df[income_df["GST_Applicable"] == False]["Credit"].sum()
    gst_free_expenses = expense_df[expense_df["GST_Applicable"] == False]["Debit"].sum()
    
    high_confidence = len(df[df["confidence"] == "High"]) if "confidence" in df.columns else 0
    
    return {
        "period": "Q1 2026",
        "total_sales": round(total_sales, 2),
        "gst_free_sales": round(gst_free_sales, 2),
        "gst_applicable_sales": round(total_sales - gst_free_sales, 2),
        "gst_collected": round(gst_collected, 2),
        "total_expenses": round(total_expenses, 2),
        "gst_free_expenses": round(gst_free_expenses, 2),
        "gst_applicable_expenses": round(total_expenses - gst_free_expenses, 2),
        "gst_paid": round(gst_paid, 2),
        "net_gst_owed": round(net_gst, 2),
        "transaction_count": len(df),
        "income_count": len(income_df),
        "expense_count": len(expense_df),
        "high_confidence_count": high_confidence
    }

def analyze_cashflow(csv_path: str) -> dict:
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} transactions from {csv_path}")
    
    df = classify_all_transactions(df)
    
    output_path = csv_path.replace(".csv", "_classified.csv")
    df.to_csv(output_path, index=False)
    print(f"Classified data saved to {output_path}")
    
    bas_summary = generate_bas_summary(df)
    
    return {
        "bas_summary": bas_summary,
        "dataframe": df
    }

if __name__ == "__main__":
    result = analyze_cashflow("data/bank_statement_Q1_2026.csv")
    
    print("\n===== BAS SUMMARY =====")
    bas = result["bas_summary"]
    print(f"Period:                {bas['period']}")
    print(f"Total Sales:           AUD {bas['total_sales']:,.2f}")
    print(f"GST Collected:         AUD {bas['gst_collected']:,.2f}")
    print(f"GST Paid:              AUD {bas['gst_paid']:,.2f}")
    print(f"Net GST Owed to ATO:   AUD {bas['net_gst_owed']:,.2f}")
    print(f"Total Transactions:    {bas['transaction_count']}")