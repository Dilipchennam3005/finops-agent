"""
Generates two large synthetic test case datasets for the FinOps Agent.

Test Case 1 — Global Mid-Cap Enterprise (200 accounts)
  Entities: AMER, EMEA-GBP, EMEA-EUR, APAC
  Mismatches: 25 large variances + 5 GL_ONLY + 5 SUBLEDGER_ONLY

Test Case 2 — Large Multinational Corporation (500 accounts)
  Entities: AMER, AMER-WEST, EMEA-GBP, EMEA-EUR, EMEA-CHF (mapped→EUR), APAC, LATAM
  Mismatches: 60 large variances + 10 GL_ONLY + 10 SUBLEDGER_ONLY
  Severe cases: several variances above $100,000 USD

Run: python data/generate_test_cases.py
"""
import csv
import random
from pathlib import Path

PERIOD_1 = "2026-04"
PERIOD_2 = "2026-03"

FX_RATES = {"USD": 1.0, "GBP": 1.27, "EUR": 1.08}

# Expanded chart — 50 account series to support large entity × account combos
CHART = [
    ("1001", "Cash and Cash Equivalents",        500_000,   8_000_000),
    ("1002", "Petty Cash",                         1_000,      50_000),
    ("1003", "Restricted Cash",                   50_000,   1_000_000),
    ("1100", "Accounts Receivable",              200_000,   6_000_000),
    ("1101", "Trade Receivables",                100_000,   3_000_000),
    ("1102", "Other Receivables",                 20_000,     500_000),
    ("1200", "Prepaid Expenses",                  10_000,     400_000),
    ("1201", "Prepaid Insurance",                  5_000,     120_000),
    ("1300", "Inventory - Raw Materials",        100_000,   3_000_000),
    ("1301", "Inventory - Finished Goods",       200_000,   5_000_000),
    ("1302", "Inventory - WIP",                   50_000,   1_500_000),
    ("1400", "Short-term Investments",            50_000,   2_000_000),
    ("1401", "Marketable Securities",            100_000,   4_000_000),
    ("1500", "Fixed Assets - Gross",             500_000,  15_000_000),
    ("1501", "Accumulated Depreciation",         200_000,   6_000_000),
    ("1502", "Capital Work in Progress",         100_000,   5_000_000),
    ("1600", "Intercompany Receivables",          50_000,   3_000_000),
    ("1601", "Intercompany Loans Receivable",    100_000,   5_000_000),
    ("1700", "Goodwill",                       1_000_000,  20_000_000),
    ("1800", "Intangible Assets",               100_000,   4_000_000),
    ("1801", "Patents and Licenses",             50_000,   2_000_000),
    ("1900", "Deferred Tax Asset",               20_000,     500_000),
    ("2001", "Accounts Payable",               150_000,   5_000_000),
    ("2002", "Accrued Purchases",               50_000,   1_200_000),
    ("2100", "Accrued Liabilities",             50_000,   1_500_000),
    ("2101", "Accrued Payroll",                 80_000,   2_000_000),
    ("2102", "Accrued Bonuses",                 30_000,     800_000),
    ("2200", "Deferred Revenue",                30_000,   1_000_000),
    ("2300", "Long-term Debt",                 500_000,  20_000_000),
    ("2301", "Bonds Payable",                  500_000,  15_000_000),
    ("2400", "Intercompany Payables",           50_000,   3_000_000),
    ("2401", "Intercompany Loans Payable",     100_000,   5_000_000),
    ("2500", "Income Tax Payable",              20_000,   1_000_000),
    ("2600", "Lease Liabilities",               50_000,   2_000_000),
    ("3001", "Retained Earnings",              500_000,  20_000_000),
    ("3100", "Share Capital",                  100_000,  10_000_000),
    ("3200", "Additional Paid-in Capital",     200_000,  15_000_000),
    ("3300", "Treasury Stock",                  50_000,   5_000_000),
    ("4001", "Revenue - Product",            1_000_000,  30_000_000),
    ("4002", "Revenue - Services",            500_000,  12_000_000),
    ("4003", "Revenue - Licensing",           100_000,   4_000_000),
    ("4004", "Revenue - Subscriptions",       200_000,   8_000_000),
    ("5001", "Cost of Goods Sold",            500_000,  15_000_000),
    ("5002", "Direct Labour",                 200_000,   4_000_000),
    ("6001", "Salaries and Wages",            300_000,   8_000_000),
    ("6002", "Rent and Facilities",            50_000,   1_000_000),
    ("6003", "Marketing Expenses",             30_000,   1_500_000),
    ("6004", "IT and Infrastructure",          40_000,   1_200_000),
    ("6005", "Professional Fees",              20_000,     600_000),
    ("6006", "Travel and Entertainment",       10_000,     300_000),
    ("6007", "Depreciation Expense",           50_000,   1_500_000),
    ("6008", "Research and Development",       80_000,   4_000_000),
    ("6009", "Insurance Premiums",              5_000,     200_000),
    ("6010", "Utilities",                       5_000,     150_000),
    ("6011", "Advertising",                    20_000,     800_000),
    ("6012", "Customer Support",               30_000,     600_000),
    ("7001", "Interest Expense",               10_000,   1_000_000),
    ("7002", "Tax Provision",                  50_000,   4_000_000),
    ("7003", "Foreign Exchange Gain/Loss",      5_000,   2_000_000),
    ("7004", "Investment Income",              10_000,     500_000),
    ("8001", "Dividend Income",                 5_000,     300_000),
]


def write_csv(path: Path, fieldnames: list, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_accounts(entity_dist: list[tuple], period: str, seed: int) -> list[dict]:
    rng = random.Random(seed)
    accounts = []
    for currency, entity, count in entity_dist:
        pool = list(CHART)
        rng.shuffle(pool)
        for i in range(count):
            series, name, lo, hi = pool[i % len(pool)]
            balance = round(rng.uniform(lo, hi), 2)
            accounts.append({
                "account_code": series,
                "account_name": name,
                "currency": currency,
                "gl_balance": balance,
                "period": period,
                "entity": entity,
            })
    return accounts


def inject_mismatches(
    accounts: list[dict],
    n_mismatch: int,
    mismatch_sizes: list[float],
    n_gl_only: int,
    n_sl_only: int,
    seed: int,
) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed + 1)

    all_indices = list(range(len(accounts)))
    rng.shuffle(all_indices)

    mismatch_indices  = set(all_indices[:n_mismatch])
    gl_only_indices   = set(all_indices[n_mismatch: n_mismatch + n_gl_only])
    sl_only_indices   = set(all_indices[n_mismatch + n_gl_only: n_mismatch + n_gl_only + n_sl_only])
    mismatch_pool     = list(mismatch_sizes)
    rng.shuffle(mismatch_pool)
    mismatch_iter     = iter(mismatch_pool)

    gl_rows, sl_rows = [], []

    for i, acc in enumerate(accounts):
        gl_row = {
            "account_code": acc["account_code"],
            "account_name": acc["account_name"],
            "currency"    : acc["currency"],
            "gl_balance"  : acc["gl_balance"],
            "period"      : acc["period"],
            "entity"      : acc["entity"],
        }

        if i in gl_only_indices:
            # Exists in GL only — no subledger row
            gl_rows.append(gl_row)
            continue

        if i in sl_only_indices:
            # Exists in subledger only — no GL row
            sl_rows.append({
                "account_code"     : acc["account_code"],
                "account_name"     : acc["account_name"],
                "currency"         : acc["currency"],
                "subledger_balance": round(acc["gl_balance"] + rng.uniform(12_000, 80_000), 2),
                "period"           : acc["period"],
                "entity"           : acc["entity"],
            })
            continue

        gl_rows.append(gl_row)

        if i in mismatch_indices:
            delta = next(mismatch_iter, rng.uniform(15_000, 120_000))
            direction = rng.choice([-1, 1])
            sl_balance = round(max(0.0, acc["gl_balance"] + direction * delta), 2)
        else:
            noise = round(rng.uniform(-2_000, 2_000), 2)
            sl_balance = round(max(0.0, acc["gl_balance"] + noise), 2)

        sl_rows.append({
            "account_code"     : acc["account_code"],
            "account_name"     : acc["account_name"],
            "currency"         : acc["currency"],
            "subledger_balance": sl_balance,
            "period"           : acc["period"],
            "entity"           : acc["entity"],
        })

    return gl_rows, sl_rows


# ── Test Case 1 ───────────────────────────────────────────────────────────────

def generate_test_case_1(out_dir: Path) -> None:
    entity_dist = [
        ("USD", "AMER",     80),
        ("USD", "APAC",     30),
        ("GBP", "EMEA-GBP", 55),
        ("EUR", "EMEA-EUR", 35),
    ]  # 200 accounts total

    mismatch_sizes = [
        15_000, 23_400, 45_200, 11_500, 88_500,
        31_200, 14_750, 27_800, 55_000, 19_600,
        62_300, 17_400, 38_900, 92_100, 24_750,
        43_000, 11_800, 76_500, 33_200, 18_600,
        105_000, 28_400, 51_700, 13_900, 67_800,
    ]  # 25 mismatches

    accounts = build_accounts(entity_dist, PERIOD_1, seed=101)
    gl_rows, sl_rows = inject_mismatches(
        accounts, n_mismatch=25, mismatch_sizes=mismatch_sizes,
        n_gl_only=5, n_sl_only=5, seed=101,
    )

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

    total = len(accounts)
    n_exc = 25 + 5 + 5
    print(f"Test Case 1 — Global Mid-Cap Enterprise")
    print(f"  Accounts  : {total}  (80 USD/AMER · 30 USD/APAC · 55 GBP · 35 EUR)")
    print(f"  Mismatches: {n_exc}  (25 variance · 5 GL_ONLY · 5 SUBLEDGER_ONLY)")
    print(f"  Period    : {PERIOD_1}")
    print(f"  Files     : {out_dir.resolve()}\n")


# ── Test Case 2 ───────────────────────────────────────────────────────────────

def generate_test_case_2(out_dir: Path) -> None:
    entity_dist = [
        ("USD", "AMER",      140),
        ("USD", "AMER-WEST",  60),
        ("USD", "LATAM",      40),
        ("USD", "APAC",       60),
        ("GBP", "EMEA-GBP",  100),
        ("GBP", "EMEA-SCO",   50),
        ("EUR", "EMEA-EUR",   80),
        ("EUR", "EMEA-DACH",  30) ,
    ]  # 560 → trim to 500 by reducing AMER

    mismatch_sizes = [
        # Medium (11k–50k)
        15_000, 23_400, 45_200, 11_500, 38_500,
        31_200, 14_750, 27_800, 42_000, 19_600,
        22_300, 17_400, 38_900, 36_100, 24_750,
        43_000, 11_800, 46_500, 33_200, 18_600,
        # Large (50k–120k)
        105_000, 78_400, 91_700, 63_900, 87_800,
        112_000, 55_300, 98_200, 67_100, 74_500,
        # Severe (>120k) — same-day escalation territory
        145_000, 188_000, 223_500, 165_000, 201_000,
        134_700, 176_300, 258_000, 192_400, 143_600,
        # Additional medium
        29_400, 37_800, 51_200, 44_600, 16_900,
        61_300, 33_700, 48_100, 22_800, 71_200,
        # Extra 10
        13_500, 26_700, 57_400, 84_300, 39_100,
        68_900, 42_500, 77_600, 18_200, 53_800,
    ]  # 60 mismatches

    accounts = build_accounts(entity_dist, PERIOD_2, seed=202)
    gl_rows, sl_rows = inject_mismatches(
        accounts, n_mismatch=60, mismatch_sizes=mismatch_sizes,
        n_gl_only=10, n_sl_only=10, seed=202,
    )

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

    total = len(accounts)
    n_exc = 60 + 10 + 10
    print(f"Test Case 2 — Large Multinational Corporation")
    print(f"  Accounts  : {total}  (300 USD · 150 GBP · 110 EUR across 8 entities)")
    print(f"  Mismatches: {n_exc}  (60 variance · 10 GL_ONLY · 10 SUBLEDGER_ONLY)")
    print(f"  Severe    : 10 exceptions above $120,000 USD — same-day escalation tier")
    print(f"  Period    : {PERIOD_2}")
    print(f"  Files     : {out_dir.resolve()}\n")


if __name__ == "__main__":
    base = Path(__file__).parent
    generate_test_case_1(base / "test_cases" / "test_case_1")
    generate_test_case_2(base / "test_cases" / "test_case_2")
    print("Done. Upload via the Streamlit UI or use sample data.")
