import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker('en_AU')
random.seed(42)

SYDNEY_EXPENSES = [
    {"description": "Office Rent - Martin Place CBD", "min": 4500, "max": 7000, "gst": True, "frequency": "monthly"},
    {"description": "Office Rent - George Street Sydney", "min": 3500, "max": 5500, "gst": True, "frequency": "monthly"},
    {"description": "AGL Energy - Sydney Office", "min": 350, "max": 800, "gst": True, "frequency": "monthly"},
    {"description": "Sydney Water - Office", "min": 150, "max": 300, "gst": True, "frequency": "monthly"},
    {"description": "Optus Business Internet", "min": 100, "max": 250, "gst": True, "frequency": "monthly"},
    {"description": "Telstra Business Phone", "min": 80, "max": 200, "gst": True, "frequency": "monthly"},
    {"description": "Staff Payroll - CBA PaySmart", "min": 15000, "max": 45000, "gst": False, "frequency": "fortnightly"},
    {"description": "Woolworths - Office Supplies", "min": 50, "max": 300, "gst": True, "frequency": "weekly"},
    {"description": "Coles - Staff Kitchen", "min": 80, "max": 200, "gst": False, "frequency": "weekly"},
    {"description": "Harvey Norman - Equipment", "min": 500, "max": 3000, "gst": True, "frequency": "occasional"},
    {"description": "JB Hi-Fi - Tech Equipment", "min": 300, "max": 2000, "gst": True, "frequency": "occasional"},
    {"description": "NRMA Business Insurance", "min": 800, "max": 2000, "gst": True, "frequency": "quarterly"},
    {"description": "Xero Accounting Software", "min": 60, "max": 60, "gst": True, "frequency": "monthly"},
    {"description": "Microsoft 365 Business", "min": 150, "max": 400, "gst": True, "frequency": "monthly"},
    {"description": "Google Workspace", "min": 80, "max": 200, "gst": True, "frequency": "monthly"},
    {"description": "Sydney CBD Parking", "min": 30, "max": 80, "gst": True, "frequency": "weekly"},
    {"description": "Uber Business - Client Travel", "min": 40, "max": 150, "gst": True, "frequency": "weekly"},
    {"description": "Cafe Sydney - Client Meeting", "min": 50, "max": 200, "gst": True, "frequency": "weekly"},
    {"description": "ATO - PAYG Withholding", "min": 5000, "max": 15000, "gst": False, "frequency": "monthly"},
    {"description": "NSW WorkCover Insurance", "min": 400, "max": 1200, "gst": True, "frequency": "quarterly"},
    {"description": "Officeworks - Stationery", "min": 50, "max": 300, "gst": True, "frequency": "monthly"},
    {"description": "Australia Post - Postage", "min": 30, "max": 150, "gst": True, "frequency": "monthly"},
]

SYDNEY_INCOME = [
    {"description": "Invoice Payment - {client}", "min": 5000, "max": 25000, "gst": True},
    {"description": "Consulting Fee - {client}", "min": 3000, "max": 15000, "gst": True},
    {"description": "Project Payment - {client}", "min": 8000, "max": 40000, "gst": True},
    {"description": "Retainer Fee - {client}", "min": 2000, "max": 8000, "gst": True},
    {"description": "Service Fee - {client}", "min": 1500, "max": 6000, "gst": True},
]

SYDNEY_CLIENTS = [
    "Macquarie Bank", "Westpac", "ANZ", "Commonwealth Bank",
    "Atlassian", "Canva", "Afterpay", "Zip Co",
    "Deloitte Sydney", "PwC Australia", "KPMG Sydney",
    "Transport NSW", "Service NSW", "NSW Health",
    "Woolworths Group", "Wesfarmers", "Scentre Group"
]

def generate_mock_bank_statement(
    business_name: str = "Sydney Tech Solutions Pty Ltd",
    abn: str = "51 824 753 556",
    quarter: str = "Q1 2026",
    start_date: str = "2026-01-01",
    end_date: str = "2026-03-31"
):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    transactions = []
    current_balance = 500000.00

    for expense in SYDNEY_EXPENSES:
        if expense["frequency"] == "monthly":
            dates = [
                start + timedelta(days=random.randint(1, 5)),
                start + timedelta(days=32 + random.randint(1, 5)),
                start + timedelta(days=62 + random.randint(1, 5))
            ]
        elif expense["frequency"] == "fortnightly":
            dates = [start + timedelta(days=i * 14 + random.randint(0, 3)) for i in range(6)]
        elif expense["frequency"] == "weekly":
            dates = [start + timedelta(weeks=i) for i in range(13)]
        elif expense["frequency"] == "quarterly":
            dates = [start + timedelta(days=random.randint(5, 15))]
        else:
            dates = [start + timedelta(days=random.randint(0, 89))] if random.random() > 0.5 else []

        for date in dates:
            if date <= end:
                amount = round(random.uniform(expense["min"], expense["max"]), 2)
                gst_amount = round(amount / 11, 2) if expense["gst"] else 0.00
                amount_ex_gst = round(amount - gst_amount, 2)
                current_balance = round(current_balance - amount, 2)

                transactions.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Description": expense["description"],
                    "Debit": amount,
                    "Credit": 0.00,
                    "GST_Applicable": expense["gst"],
                    "GST_Amount": gst_amount,
                    "Amount_Ex_GST": amount_ex_gst,
                    "Category": "Expense",
                    "Balance": current_balance
                })

    num_invoices = random.randint(15, 25)
    for _ in range(num_invoices):
        income = random.choice(SYDNEY_INCOME)
        client = random.choice(SYDNEY_CLIENTS)
        description = income["description"].format(client=client)
        amount = round(random.uniform(income["min"], income["max"]), 2)
        gst_amount = round(amount / 11, 2)
        amount_ex_gst = round(amount - gst_amount, 2)
        date = start + timedelta(days=random.randint(0, 89))

        if date <= end:
            current_balance = round(current_balance + amount, 2)
            transactions.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Description": description,
                "Debit": 0.00,
                "Credit": amount,
                "GST_Applicable": True,
                "GST_Amount": gst_amount,
                "Amount_Ex_GST": amount_ex_gst,
                "Category": "Income",
                "Balance": current_balance
            })

    df = pd.DataFrame(transactions)
    df = df.sort_values("Date").reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    output_path = f"data/bank_statement_{quarter.replace(' ', '_')}.csv"
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} transactions for {business_name}")
    print(f"ABN: {abn}")
    print(f"Period: {quarter}")
    print(f"Saved to: {output_path}")
    print(f"\nSummary:")
    print(f"  Total Income:    AUD {df['Credit'].sum():,.2f}")
    print(f"  Total Expenses:  AUD {df['Debit'].sum():,.2f}")
    print(f"  GST Collected:   AUD {df[df['Category']=='Income']['GST_Amount'].sum():,.2f}")
    print(f"  GST Paid:        AUD {df[df['Category']=='Expense']['GST_Amount'].sum():,.2f}")
    print(f"  Net GST Owed:    AUD {df[df['Category']=='Income']['GST_Amount'].sum() - df[df['Category']=='Expense']['GST_Amount'].sum():,.2f}")

    return df

if __name__ == "__main__":
    generate_mock_bank_statement()