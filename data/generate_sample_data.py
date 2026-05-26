"""
Generates synthetic GL and subledger CSV files for testing.
Run: python data/generate_sample_data.py

55 accounts total: 30 USD (AMER), 15 GBP (EMEA-GBP), 10 EUR (EMEA-EUR).
10 intentional mismatches are injected above the $10,000 USD variance threshold.
"""
import csv
import random
from pathlib import Path
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

PERIOD = "2026-04"

# FX rates (local → USD)
FX_RATES = {"USD": 1.0, "GBP": 1.27, "EUR": 1.08}

# Chart of accounts: (series_code, account_name, balance_min, balance_max)
CHART = [
    ("1001", "Cash and Cash Equivalents",       500_000,  5_000_000),
    ("1100", "Accounts Receivable",             200_000,  4_000_000),
    ("1200", "Prepaid Expenses",                 10_000,    250_000),
    ("1300", "Inventory",                       100_000,  2_000_000),
    ("1400", "Short-term Investments",           50_000,  1_000_000),
    ("1500", "Fixed Assets - Gross",            500_000,  8_000_000),
    ("1501", "Accumulated Depreciation",        200_000,  3_000_000),
    ("1600", "Intercompany Receivables",         50_000,  1_500_000),
    ("1700", "Goodwill",                      1_000_000, 10_000_000),
    ("1800", "Intangible Assets",               100_000,  2_000_000),
    ("2001", "Accounts Payable",                150_000,  3_000_000),
    ("2100", "Accrued Liabilities",              50_000,    800_000),
    ("2200", "Deferred Revenue",                 30_000,    600_000),
    ("2300", "Long-term Debt",                  500_000, 10_000_000),
    ("2400", "Intercompany Payables",            50_000,  1_500_000),
    ("2500", "Income Tax Payable",               20_000,    500_000),
    ("3001", "Retained Earnings",               500_000, 15_000_000),
    ("3100", "Share Capital",                   100_000,  5_000_000),
    ("4001", "Revenue - Product",             1_000_000, 20_000_000),
    ("4002", "Revenue - Services",              500_000,  8_000_000),
    ("4003", "Revenue - Licensing",             100_000,  3_000_000),
    ("5001", "Cost of Goods Sold",              500_000, 10_000_000),
    ("6001", "Salaries and Wages",              300_000,  5_000_000),
    ("6002", "Rent and Facilities",              50_000,    500_000),
    ("6003", "Marketing Expenses",               30_000,    800_000),
    ("6004", "IT and Infrastructure",            40_000,    600_000),
    ("6005", "Professional Fees",                20_000,    300_000),
    ("6006", "Travel and Entertainment",         10_000,    150_000),
    ("6007", "Depreciation Expense",             50_000,    800_000),
    ("6008", "Research and Development",         80_000,  2_000_000),
    ("6009", "Insurance Premiums",                5_000,    100_000),
    ("6010", "Utilities",                         5_000,     80_000),
    ("7001", "Interest Expense",                 10_000,    500_000),
    ("7002", "Tax Provision",                    50_000,  2_000_000),
]  # 34 definitions — enough for 30 USD accounts with no repeats

# Currency distribution: 30 USD, 15 GBP, 10 EUR = 55 total
ENTITY_DIST = [
    ("USD", "AMER",     30),
    ("GBP", "EMEA-GBP", 15),
    ("EUR", "EMEA-EUR", 10),
]

# Intentional mismatch amounts (local currency) — all exceed $10k USD after FX conversion
# Smallest: 11,500 × min(FX) = 11,500 × 1.08 = $12,420 USD > threshold ✓
MISMATCH_AMOUNTS = [15_000, 23_400, 45_200, 11_500, 88_500,
                    31_200, 14_750, 27_800, 55_000, 19_600]


def build_accounts() -> list[dict]:
    accounts = []
    for currency, entity, count in ENTITY_DIST:
        pool = list(CHART)
        random.shuffle(pool)
        for i in range(count):
            series, name, lo, hi = pool[i]  # count ≤ len(CHART), so no wrapping needed
            balance = round(random.uniform(lo, hi), 2)
            accounts.append({
                "account_code": series,
                "account_name": name,
                "currency": currency,
                "gl_balance": balance,
                "period": PERIOD,
                "entity": entity,
            })
    return accounts


def write_csv(path: Path, fieldnames: list, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    accounts = build_accounts()

    # Select 10 random accounts to receive intentional mismatches
    mismatch_indices = set(random.sample(range(len(accounts)), 10))
    mismatch_pool = iter(MISMATCH_AMOUNTS)

    gl_rows, sl_rows = [], []

    for i, acc in enumerate(accounts):
        gl_rows.append({
            "account_code": acc["account_code"],
            "account_name": acc["account_name"],
            "currency": acc["currency"],
            "gl_balance": acc["gl_balance"],
            "period": acc["period"],
            "entity": acc["entity"],
        })

        if i in mismatch_indices:
            delta = next(mismatch_pool)
            direction = random.choice([-1, 1])
            sl_balance = round(max(0.0, acc["gl_balance"] + direction * delta), 2)
        else:
            # Noise well within $10k threshold even after FX: max $2k local ≈ $2.54k USD
            noise = round(random.uniform(-2_000, 2_000), 2)
            sl_balance = round(max(0.0, acc["gl_balance"] + noise), 2)

        sl_rows.append({
            "account_code": acc["account_code"],
            "account_name": acc["account_name"],
            "currency": acc["currency"],
            "subledger_balance": sl_balance,
            "period": acc["period"],
            "entity": acc["entity"],
        })

    out_dir = Path(__file__).parent / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        out_dir / "gl_balances.csv",
        ["account_code", "account_name", "currency", "gl_balance", "period", "entity"],
        gl_rows,
    )
    write_csv(
        out_dir / "subledger.csv",
        ["account_code", "account_name", "currency", "subledger_balance", "period", "entity"],
        sl_rows,
    )

    usd_count = sum(1 for a in accounts if a["currency"] == "USD")
    gbp_count = sum(1 for a in accounts if a["currency"] == "GBP")
    eur_count = sum(1 for a in accounts if a["currency"] == "EUR")

    print(f"Generated {len(accounts)} accounts: {usd_count} USD / {gbp_count} GBP / {eur_count} EUR")
    print(f"10 intentional mismatches injected (all exceed $10,000 USD threshold after FX)")
    print(f"Files written to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
