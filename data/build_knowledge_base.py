"""
Builds the ChromaDB knowledge base with 32 historical financial exception records.
Run once before the first pipeline execution (or whenever you want to rebuild).

Usage: python data/build_knowledge_base.py
"""
import random
from pathlib import Path

import chromadb
from faker import Faker

fake = Faker()
random.seed(99)
Faker.seed(99)

COLLECTION_NAME = "finops_exceptions"

# ── Historical exception records ──────────────────────────────────────────────
# Each "document" is the text embedded by ChromaDB for similarity search.
# Metadata is returned alongside results for context injection into Claude.

RECORDS = [
    # ── FX_TIMING (8 records) ─────────────────────────────────────────────────
    {
        "id": "KB-001",
        "document": (
            "FX_DISCREPANCY on account 1001 Cash and Cash Equivalents EMEA-GBP entity GBP currency. "
            "Variance $23,812 USD. Trade-date vs settlement-date FX rate mismatch. Treasury system "
            "booked GBP transaction at trade date spot rate 1.2701 while GL applied settlement date "
            "rate 1.2888. Two-day settlement lag on £18,750 cash position produced the USD variance. "
            "Resolution: aligned rate booking date convention in treasury-to-GL interface."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "1001", "currency": "GBP",
            "variance_usd": 23812, "entity": "EMEA-GBP", "category": "FX_TIMING",
            "root_cause": "Treasury booked at trade date rate (1.2701); GL applied settlement date rate (1.2888). £18,750 × rate delta = $23,812 variance.",
            "resolution": "Updated treasury-to-GL interface to use settlement date rate consistently. Posted correcting FX journal.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-002",
        "document": (
            "FX_DISCREPANCY on account 1001 Cash EMEA-EUR entity EUR currency. "
            "Variance $30,240 USD. Month-end FX revaluation not applied to subledger. "
            "GL month-end revaluation journal applied ECB closing rate 1.08 to all EUR balances "
            "but the subledger revaluation job failed silently due to a scheduler error. "
            "Resolution: reran subledger revaluation job and verified output matched GL."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "1001", "currency": "EUR",
            "variance_usd": 30240, "entity": "EMEA-EUR", "category": "FX_TIMING",
            "root_cause": "Month-end subledger FX revaluation job failed silently (scheduler misconfiguration). GL revaluation ran; subledger remained at prior-month rate.",
            "resolution": "Reran subledger revaluation batch. Added monitoring alert for scheduler job failures.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-003",
        "document": (
            "FX_DISCREPANCY on account 4002 Revenue Services EMEA-GBP entity GBP currency. "
            "Variance $18,733 USD. Bloomberg closing mid-rate vs Reuters ECB fix rate mismatch. "
            "Billing system used Bloomberg GBP/USD 1.2755 while GL used Reuters ECB fix 1.2902. "
            "Revenue recognised on same day but at different exchange rates in the two systems. "
            "Resolution: standardised all systems to use Reuters ECB 4pm London fix."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "4002", "currency": "GBP",
            "variance_usd": 18733, "entity": "EMEA-GBP", "category": "FX_TIMING",
            "root_cause": "Rate source mismatch: billing system used Bloomberg mid (1.2755); GL used Reuters ECB fix (1.2902). £14,750 revenue × rate delta = $18,733.",
            "resolution": "Standardised rate source to Reuters ECB fix across all systems. Updated billing-to-GL interface configuration.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-004",
        "document": (
            "FX_DISCREPANCY on account 6001 Salaries and Wages EMEA-EUR entity EUR currency. "
            "Variance $54,000 USD. Forward contract rate vs spot rate booking error in payroll. "
            "Payroll system booked EUR salary payments at the hedged forward rate 1.04 while "
            "GL recorded at the prevailing spot rate 1.09. Difference of 5 cents per EUR on "
            "a €1,000,000 payroll run produced the variance. "
            "Resolution: updated payroll system to use spot rate consistent with GL."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "6001", "currency": "EUR",
            "variance_usd": 54000, "entity": "EMEA-EUR", "category": "FX_TIMING",
            "root_cause": "Payroll system applied hedged forward rate (1.04) to EUR salaries; GL used market spot rate (1.09). €1M payroll × $0.05 delta = $54,000.",
            "resolution": "Updated payroll-to-GL interface to post at spot rate. Treasury handles FX hedge accounting separately via mark-to-market journal.",
            "resolution_days": 3,
        },
    },
    {
        "id": "KB-005",
        "document": (
            "FX_DISCREPANCY on account 2001 Accounts Payable EMEA-GBP entity GBP currency. "
            "Variance $14,732 USD. AP system applied invoice date FX rate while GL used payment date rate. "
            "Invoice dated 28th of month converted at 1.2600; payment processed 3rd of following month "
            "when GL applied rate of 1.2716. £11,600 AP balance produced the GBP timing variance. "
            "Resolution: configured AP system to revalue open invoices at payment date rate."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "2001", "currency": "GBP",
            "variance_usd": 14732, "entity": "EMEA-GBP", "category": "FX_TIMING",
            "root_cause": "AP system locked FX rate at invoice date (1.2600); GL revalued at payment date (1.2716). £11,600 × rate delta = $14,732 on month-end cutover.",
            "resolution": "Enabled AP revaluation to payment date rate. Added monthly AP revaluation to close checklist.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-006",
        "document": (
            "FX_DISCREPANCY on account 1600 Intercompany Receivables EMEA-EUR entity EUR currency. "
            "Variance $21,168 USD. Intraday FX rate fluctuation on IC settlement. "
            "IC payment confirmed at 09:00 London time at EUR/USD 1.0720 but GL batch processed "
            "at midnight using end-of-day rate 1.1007. €19,600 IC receivable settlement produced "
            "the overnight rate difference. Resolution: moved IC settlement batch to intraday."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "1600", "currency": "EUR",
            "variance_usd": 21168, "entity": "EMEA-EUR", "category": "FX_TIMING",
            "root_cause": "IC settlement confirmed at 09:00 rate (1.0720); GL batch ran at midnight using EOD rate (1.1007). €19,600 × $0.028 delta = $21,168.",
            "resolution": "Rescheduled IC GL batch to run within 30 minutes of settlement confirmation to minimise intraday FX exposure.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-007",
        "document": (
            "FX_DISCREPANCY on account 6003 Marketing Expenses EMEA-GBP entity GBP currency. "
            "Variance $19,050 USD. Rounding accumulation on high-volume FX transactions. "
            "GBP marketing invoices processed at 4-decimal-place rate 1.2701 in AP system "
            "but GL truncated to 2 decimal places 1.27. Over 1,500 transactions of average "
            "£10 each, cumulative rounding difference reached $19,050 USD threshold. "
            "Resolution: extended GL FX rate precision to 6 decimal places."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "6003", "currency": "GBP",
            "variance_usd": 19050, "entity": "EMEA-GBP", "category": "FX_TIMING",
            "root_cause": "GL FX rate precision truncated at 2 decimal places vs AP system 4 decimal places. 1,500 small GBP transactions accumulated a $19,050 rounding difference.",
            "resolution": "Extended GL FX rate field to 6 decimal places. Posted one-line correcting journal to clear accumulated rounding. Added monthly rounding review to close checklist.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-008",
        "document": (
            "FX_DISCREPANCY on account 5001 Cost of Goods Sold EMEA-EUR entity EUR currency. "
            "Variance $11,664 USD. Procurement system used prior-month average rate for COGS. "
            "Procurement module applied the prior month average EUR/USD rate 1.05 to inventory "
            "costs while the GL used the current month closing rate 1.08 after standard cost update. "
            "€10,800 COGS balance produced the rate difference at month-end standard cost roll. "
            "Resolution: aligned standard cost rate update to use same period as GL closing rate."
        ),
        "metadata": {
            "exception_type": "FX_DISCREPANCY", "account_series": "5001", "currency": "EUR",
            "variance_usd": 11664, "entity": "EMEA-EUR", "category": "FX_TIMING",
            "root_cause": "Procurement used prior-month average rate (1.05) for standard COGS; GL applied current closing rate (1.08) after standard cost roll. €10,800 × $0.03 = $11,664.",
            "resolution": "Aligned standard cost update schedule to run after GL closing rate is confirmed. Updated procurement integration to use current-period rate.",
            "resolution_days": 2,
        },
    },

    # ── GL_CODING_ERROR (5 records) ───────────────────────────────────────────
    {
        "id": "KB-009",
        "document": (
            "GL_MISMATCH on account 4001 Revenue Product AMER entity USD currency. "
            "Variance $45,200 USD. Revenue coded to wrong account during ERP account code migration. "
            "A chart-of-accounts re-mapping during the SAP upgrade mapped old account 4001-US "
            "to new account 4003 Licensing Revenue instead of 4001 Product Revenue. "
            "Three months of product revenue postings landed in wrong account. "
            "Resolution: corrected mapping table and posted reclassification journals."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "4001", "currency": "USD",
            "variance_usd": 45200, "entity": "AMER", "category": "GL_CODING_ERROR",
            "root_cause": "ERP migration chart-of-accounts mapping error: old 4001-US mapped to new 4003 (Licensing) instead of 4001 (Product). Three months of revenue misclassified.",
            "resolution": "Corrected CoA mapping table in SAP configuration. Posted reclassification journals to move misposted revenue. Updated migration validation checklist.",
            "resolution_days": 3,
        },
    },
    {
        "id": "KB-010",
        "document": (
            "GL_MISMATCH on account 6005 Professional Fees AMER entity USD currency. "
            "Variance $31,200 USD. Expense posted to balance sheet account instead of P&L. "
            "Legal invoice for $31,200 posted by AP team to account 1800 Intangible Assets "
            "instead of 6005 Professional Fees due to a transposed account code. "
            "Error discovered during month-end account review. "
            "Resolution: reversed balance sheet posting and reposted to correct P&L account."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "6005", "currency": "USD",
            "variance_usd": 31200, "entity": "AMER", "category": "GL_CODING_ERROR",
            "root_cause": "AP team entered account 1800 (Intangibles) instead of 6005 (Professional Fees) — transposed digits 6→1, 0→8. $31,200 legal invoice misclassified to balance sheet.",
            "resolution": "Reversed 1800 posting, reposted to 6005. Implemented mandatory account-type validation check in AP workflow to prevent P&L postings to balance sheet accounts.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-011",
        "document": (
            "GL_MISMATCH on account 2200 Deferred Revenue AMER entity USD currency. "
            "Variance $15,000 USD. Revenue recognised immediately instead of being deferred. "
            "Subscription contract for $15,000 annual fee posted directly to account 4002 Revenue "
            "instead of 2200 Deferred Revenue. Under IFRS 15 the fee should be recognised monthly. "
            "Resolution: reversed revenue posting and established deferred revenue schedule."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "2200", "currency": "USD",
            "variance_usd": 15000, "entity": "AMER", "category": "GL_CODING_ERROR",
            "root_cause": "Annual subscription $15,000 posted direct to revenue (4002) instead of deferred revenue (2200). IFRS 15 requires monthly recognition over 12-month term.",
            "resolution": "Reversed revenue posting. Created deferred revenue schedule ($1,250/month). Implemented contract-type flag in billing system to auto-route subscriptions to 2200.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-012",
        "document": (
            "GL_MISMATCH on account 6007 Depreciation Expense AMER entity USD currency. "
            "Variance $27,800 USD. Fixed asset account code migrated incorrectly in new asset module. "
            "Depreciation for asset class Buildings was calculating correctly in the asset sub-ledger "
            "but posting to account 6010 Utilities instead of 6007 Depreciation due to wrong "
            "account assignment in the asset class configuration table. "
            "Resolution: corrected asset class posting rule and posted period reclassification."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "6007", "currency": "USD",
            "variance_usd": 27800, "entity": "AMER", "category": "GL_CODING_ERROR",
            "root_cause": "Asset class 'Buildings' had wrong GL account assignment in fixed asset module: posting to 6010 (Utilities) instead of 6007 (Depreciation). Configuration error from module setup.",
            "resolution": "Corrected asset class GL account assignment. Posted reclassification journal for year-to-date misposted depreciation. Added asset class configuration to annual review checklist.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-013",
        "document": (
            "GL_MISMATCH on account 6008 Research and Development AMER entity USD currency. "
            "Variance $11,500 USD. Cost centre code transposed causing wrong department allocation. "
            "R&D expense of $11,500 posted to cost centre CC800 Engineering instead of CC900 R&D "
            "due to a data entry error in the journal voucher. Expense correctly classified on "
            "P&L account 6008 but in wrong cost centre, creating a subledger mismatch. "
            "Resolution: reversed and reposted to correct cost centre."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "6008", "currency": "USD",
            "variance_usd": 11500, "entity": "AMER", "category": "GL_CODING_ERROR",
            "root_cause": "Manual journal posted to wrong cost centre (CC800 Engineering vs CC900 R&D). Account 6008 correct; cost centre allocation incorrect. Subledger reports by cost centre creating reconciliation gap.",
            "resolution": "Reversed and reposted journal to correct cost centre CC900. Implemented cost centre validation lookup in journal entry screen.",
            "resolution_days": 1,
        },
    },

    # ── INTERCOMPANY (5 records) ──────────────────────────────────────────────
    {
        "id": "KB-014",
        "document": (
            "GL_MISMATCH on account 1600 Intercompany Receivables EMEA-GBP entity GBP currency. "
            "Variance $32,454 USD. Intercompany payable not booked in counterparty entity. "
            "EMEA-GBP entity recorded IC receivable for GBP services rendered to AMER entity "
            "but AMER entity had not yet booked the corresponding payable. "
            "IC netting run not yet completed. "
            "Resolution: AMER entity posted IC payable; IC netting journal eliminated both sides."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "1600", "currency": "GBP",
            "variance_usd": 32454, "entity": "EMEA-GBP", "category": "INTERCOMPANY",
            "root_cause": "One-sided IC trade: EMEA-GBP booked IC receivable for services rendered; AMER entity pending approval for corresponding IC payable. Pre-netting timing difference.",
            "resolution": "AMER entity controller approved and posted IC payable. IC netting run eliminated both entries. Added bilateral booking requirement to IC approval workflow.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-015",
        "document": (
            "GL_MISMATCH on account 2400 Intercompany Payables EMEA-EUR entity EUR currency. "
            "Variance $55,000 USD. IC elimination adjustment missing from consolidation run. "
            "Parent consolidation system failed to eliminate IC payable-receivable pair due to "
            "mismatched entity codes: EMEA-EUR entity used code EU01 while consolidation system "
            "expected code DE01. Uneliminated IC balance surfaced as unexplained variance. "
            "Resolution: corrected entity code mapping in consolidation configuration."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "2400", "currency": "EUR",
            "variance_usd": 55000, "entity": "EMEA-EUR", "category": "INTERCOMPANY",
            "root_cause": "IC elimination failed because entity code mismatch: local system uses 'EU01', consolidation system expects 'DE01'. €50,925 IC payable not eliminated, creating balance sheet variance.",
            "resolution": "Updated entity code mapping table in Hyperion consolidation. Reran elimination and verified net IC balance is zero. Added entity code alignment to monthly pre-close checklist.",
            "resolution_days": 3,
        },
    },
    {
        "id": "KB-016",
        "document": (
            "GL_MISMATCH on account 1600 Intercompany Receivables AMER entity USD currency. "
            "Variance $88,500 USD. IC management fee charged in one direction only. "
            "AMER head-office charged quarterly management fee of $88,500 to EMEA-GBP entity "
            "and booked IC receivable in AMER GL. EMEA-GBP entity disputed the charge and "
            "did not post the corresponding IC payable, awaiting resolution of fee calculation. "
            "Resolution: fee calculation agreed; EMEA entity posted accrual pending formal invoice."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "1600", "currency": "USD",
            "variance_usd": 88500, "entity": "AMER", "category": "INTERCOMPANY",
            "root_cause": "IC management fee dispute: AMER booked $88,500 IC receivable; EMEA-GBP withheld corresponding payable pending fee calculation review. Bilateral booking requirement not enforced.",
            "resolution": "Fee calculation agreed between controllers. EMEA-GBP posted IC payable accrual. Formal invoice raised and settled in following period. Added IC fee pre-approval process.",
            "resolution_days": 5,
        },
    },
    {
        "id": "KB-017",
        "document": (
            "SUBLEDGER_ONLY on account 2400 Intercompany Payables EMEA-EUR entity EUR currency. "
            "Variance $19,600 USD. IC loan interest accrual booked in subledger but rejected by GL. "
            "Treasury subledger correctly accrued IC loan interest for the period but the GL "
            "interface rejected the posting because the IC loan account was closed mid-period "
            "and the GL account was marked inactive. "
            "Resolution: reactivated GL account and reprocessed the accrual."
        ),
        "metadata": {
            "exception_type": "SUBLEDGER_ONLY", "account_series": "2400", "currency": "EUR",
            "variance_usd": 19600, "entity": "EMEA-EUR", "category": "INTERCOMPANY",
            "root_cause": "GL interface validation rejected IC loan interest accrual because GL account 2400-IC-LOAN was marked inactive. Subledger posted successfully; GL rejected silently with no alert.",
            "resolution": "Reactivated GL account. Reprocessed subledger accrual batch. Added inactive-account rejection alert to interface monitoring dashboard.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-018",
        "document": (
            "GL_MISMATCH on account 4001 Revenue Product AMER entity USD currency. "
            "Variance $15,750 USD. IC recharge for shared services coded to revenue instead of expense recovery. "
            "AMER entity received IC recharge of $15,750 from EMEA for shared IT services and "
            "incorrectly posted it as revenue credit to account 4001 instead of reducing "
            "IT expense account 6004. Created inflated revenue and understated expense simultaneously. "
            "Resolution: reversed revenue posting and reclassified to expense reduction."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "4001", "currency": "USD",
            "variance_usd": 15750, "entity": "AMER", "category": "INTERCOMPANY",
            "root_cause": "IC recharge for shared IT services posted as revenue credit (4001) instead of expense offset (6004). AP team misclassified the credit note from EMEA entity.",
            "resolution": "Reversed 4001 revenue posting. Posted to 6004 as expense reduction. Updated IC recharge coding instructions and AP training materials.",
            "resolution_days": 1,
        },
    },

    # ── PERIOD_CUTOFF (5 records) ─────────────────────────────────────────────
    {
        "id": "KB-019",
        "document": (
            "GL_MISMATCH on account 2100 Accrued Liabilities AMER entity USD currency. "
            "Variance $23,400 USD. Accrual reversed into wrong accounting period. "
            "Month-end accrual of $23,400 for consulting services posted correctly in March "
            "but the reversal was processed on 1st April in the accrual system while "
            "the GL period for March was still open, causing the reversal to post back into March. "
            "Resolution: reversed the incorrect March reversal and reposted it in April."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "2100", "currency": "USD",
            "variance_usd": 23400, "entity": "AMER", "category": "PERIOD_CUTOFF",
            "root_cause": "Accrual reversal processed 1st April while March GL period was still open. System posted reversal into March (net zero accrual) instead of April. Consulting expense understated for March.",
            "resolution": "Reversed incorrect March posting. Reposted accrual reversal in April. Updated GL period close schedule to lock periods on 1st of following month.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-020",
        "document": (
            "GL_ONLY on account 4002 Revenue Services EMEA-GBP entity GBP currency. "
            "Variance $39,624 USD. Revenue recognised in GL before customer acceptance. "
            "Milestone-based revenue of £31,200 recognised in GL on 28th based on project "
            "manager's verbal confirmation, but formal customer acceptance certificate not "
            "received until 3rd of following month. Subledger revenue recognition rule "
            "requires formal acceptance. GL posted; subledger did not. "
            "Resolution: reversed GL entry and deferred to following period upon acceptance."
        ),
        "metadata": {
            "exception_type": "GL_ONLY", "account_series": "4002", "currency": "GBP",
            "variance_usd": 39624, "entity": "EMEA-GBP", "category": "PERIOD_CUTOFF",
            "root_cause": "Revenue recognised in GL on verbal PM confirmation; IFRS 15 subledger requires written customer acceptance. £31,200 posted to GL; subledger recognition pending acceptance.",
            "resolution": "Reversed GL revenue entry. Reposted in following month upon receipt of signed acceptance certificate. Implemented mandatory acceptance-certificate upload in project billing workflow.",
            "resolution_days": 4,
        },
    },
    {
        "id": "KB-021",
        "document": (
            "SUBLEDGER_ONLY on account 5001 Cost of Goods Sold AMER entity USD currency. "
            "Variance $45,200 USD. Goods received in subledger but GL period already closed. "
            "Warehouse received $45,200 of inventory on 31st and GRN was processed in the "
            "procurement subledger same day. However, the GL closing run had already executed "
            "at 6pm locking the period. GRN batch ran at 11pm. Cost posted to subledger in "
            "correct period; GL period lock prevented the posting, routing it to next period. "
            "Resolution: reopened GL period and processed the late GRN posting."
        ),
        "metadata": {
            "exception_type": "SUBLEDGER_ONLY", "account_series": "5001", "currency": "USD",
            "variance_usd": 45200, "entity": "AMER", "category": "PERIOD_CUTOFF",
            "root_cause": "GL period locked at 18:00 on period-end date; warehouse GRN batch processed at 23:00. $45,200 COGS posted to subledger in correct period; GL routed to next period.",
            "resolution": "GL period reopened under Finance Director approval. GRN batch reprocessed. Extended GL period-end close deadline to midnight to accommodate late operational postings.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-022",
        "document": (
            "GL_MISMATCH on account 6002 Rent and Facilities EMEA-EUR entity EUR currency. "
            "Variance $21,600 USD. Quarterly rent provision double-reversed at period end. "
            "Quarter-end rent provision of €20,000 was reversed correctly on 1st of following "
            "quarter but a second reversal was triggered by an automated schedule that had not "
            "been updated after a process change. Double-reversal created a net debit of €20,000 "
            "where zero balance was expected. "
            "Resolution: posted single correcting credit and disabled duplicate reversal schedule."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "6002", "currency": "EUR",
            "variance_usd": 21600, "entity": "EMEA-EUR", "category": "PERIOD_CUTOFF",
            "root_cause": "Quarterly rent provision double-reversed: manual process and stale automated schedule both triggered on 1st of following quarter. Net debit balance €20,000 where zero expected.",
            "resolution": "Posted correcting credit journal. Disabled stale automated reversal schedule. Added schedule review to quarterly close process.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-023",
        "document": (
            "GL_MISMATCH on account 1200 Prepaid Expenses AMER entity USD currency. "
            "Variance $27,800 USD. Annual insurance premium expensed immediately instead of prepaid. "
            "Annual insurance renewal of $27,800 paid and posted directly to insurance expense "
            "account 6009 by AP team. Under GAAP the premium should be capitalised to prepaid "
            "account 1200 and amortised monthly over the 12-month coverage period. "
            "Resolution: reversed expense posting, established prepaid amortisation schedule."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "1200", "currency": "USD",
            "variance_usd": 27800, "entity": "AMER", "category": "PERIOD_CUTOFF",
            "root_cause": "Annual insurance premium ($27,800) expensed in full on payment date. GAAP requires capitalisation to prepaid (1200) and 12-month straight-line amortisation. AP team incorrectly routed to expense account.",
            "resolution": "Reversed expense posting. Created prepaid asset and amortisation schedule ($2,317/month). Updated AP coding guide for annual insurance invoices.",
            "resolution_days": 1,
        },
    },

    # ── SYSTEM_ERROR (5 records) ──────────────────────────────────────────────
    {
        "id": "KB-024",
        "document": (
            "GL_MISMATCH on account 1100 Accounts Receivable AMER entity USD currency. "
            "Variance $55,000 USD. Overnight batch feed from CRM billing system to GL failed silently. "
            "CRM system processed $55,000 of new AR invoices overnight but the nightly batch "
            "interface to GL failed at 02:17 due to a database connection timeout. No alert fired. "
            "GL AR balance reflects previous day; subledger AR includes new invoices. "
            "Resolution: restarted interface batch and verified all records transmitted."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "1100", "currency": "USD",
            "variance_usd": 55000, "entity": "AMER", "category": "SYSTEM_ERROR",
            "root_cause": "Nightly CRM-to-GL AR interface batch failed at 02:17 due to database connection timeout. $55,000 of new AR invoices posted to CRM subledger; GL feed was not retried.",
            "resolution": "Restarted interface batch after connection restored. All 47 invoices transmitted successfully. Implemented interface failure alerting via PagerDuty. Added retry logic to batch job.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-025",
        "document": (
            "GL_MISMATCH on account 3001 Retained Earnings AMER entity USD currency. "
            "Variance $32,000 USD. ERP migration duplicate opening balance posting. "
            "During SAP to Oracle migration, the opening balance load script executed twice "
            "for retained earnings account 3001 due to a checkpoint restart after a failed "
            "validation. The second run was not detected and doubled the opening balance. "
            "Resolution: identified and reversed the duplicate opening balance entry."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "3001", "currency": "USD",
            "variance_usd": 32000, "entity": "AMER", "category": "SYSTEM_ERROR",
            "root_cause": "ERP migration opening balance script ran twice due to checkpoint restart after validation failure. Retained earnings opening balance doubled ($32,000 excess). Second run not detected by migration team.",
            "resolution": "Identified duplicate by cross-referencing migration run logs. Posted reversal of second load entry. Added duplicate-load check to migration validation test suite.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-026",
        "document": (
            "SUBLEDGER_ONLY on account 2001 Accounts Payable EMEA-GBP entity GBP currency. "
            "Variance $14,225 USD. GL interface validation rejected AP invoice due to inactive vendor code. "
            "AP subledger processed £11,200 vendor invoice successfully but the GL interface rejected "
            "the posting because vendor master record V10045 had been marked inactive during a vendor "
            "rationalisation exercise. Rejection logged in interface error table; no alert triggered. "
            "Resolution: reactivated vendor master and reprocessed the invoice."
        ),
        "metadata": {
            "exception_type": "SUBLEDGER_ONLY", "account_series": "2001", "currency": "GBP",
            "variance_usd": 14225, "entity": "EMEA-GBP", "category": "SYSTEM_ERROR",
            "root_cause": "GL interface validation failed: vendor V10045 marked inactive during vendor rationalisation. AP subledger posted £11,200 successfully; GL rejected silently with no operational alert.",
            "resolution": "Reactivated vendor master after approval from Procurement. Reprocessed AP batch. Added vendor-inactivation cross-check with open PO register to prevent recurrence.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-027",
        "document": (
            "GL_MISMATCH on account 4003 Revenue Licensing EMEA-EUR entity EUR currency. "
            "Variance $30,240 USD. Interface field truncation on large transaction amounts. "
            "Licensing system transmitted revenue amount as €2,800,028 but GL interface field "
            "was defined as 9 characters maximum. Amount was silently truncated to €2,800,02 "
            "producing a posting difference of €27,963 (approximately $30,240 at EUR/USD 1.08). "
            "Resolution: extended interface field width and reprocessed the affected transaction."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "4003", "currency": "EUR",
            "variance_usd": 30240, "entity": "EMEA-EUR", "category": "SYSTEM_ERROR",
            "root_cause": "GL interface amount field truncated at 9 characters. €2,800,028 licence fee silently truncated to €2,800,02. Difference €27,963 / $30,240 USD posted to wrong period accumulation.",
            "resolution": "Extended interface amount field to 15 characters. Reprocessed transaction. Added numeric truncation check to ETL validation layer. Regression tested all high-value transaction interfaces.",
            "resolution_days": 2,
        },
    },
    {
        "id": "KB-028",
        "document": (
            "GL_MISMATCH on account 6004 IT and Infrastructure AMER entity USD currency. "
            "Variance $19,500 USD. Cloud cost API feed produced duplicate posting due to retry logic. "
            "Cloud provider cost management API returned a 503 timeout at 03:00 batch run. "
            "The batch job retried without idempotency check and when the API responded successfully "
            "on the second attempt, the $19,500 cloud cost was posted to the GL twice. "
            "Subledger received only the single correct amount. "
            "Resolution: reversed duplicate GL posting and added idempotency key to API retry."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "6004", "currency": "USD",
            "variance_usd": 19500, "entity": "AMER", "category": "SYSTEM_ERROR",
            "root_cause": "Cloud cost API batch retried after 503 timeout without idempotency check. $19,500 cloud cost double-posted to GL. Subledger received single correct posting from original successful call.",
            "resolution": "Reversed duplicate GL posting. Added transaction reference as idempotency key to API retry logic. Implemented dedup check in GL interface posting layer.",
            "resolution_days": 1,
        },
    },

    # ── MANUAL_JOURNAL (4 records) ────────────────────────────────────────────
    {
        "id": "KB-029",
        "document": (
            "GL_ONLY on account 7001 Interest Expense AMER entity USD currency. "
            "Variance $32,454 USD. Manual journal posted to GL without subledger offset. "
            "Finance Director posted a manual interest expense accrual of $32,454 at month-end "
            "directly to the GL for an off-balance-sheet financing arrangement. No corresponding "
            "entry was created in the treasury subledger because the arrangement was not yet "
            "set up in the TMS. "
            "Resolution: set up the financing arrangement in TMS and created backdated subledger entry."
        ),
        "metadata": {
            "exception_type": "GL_ONLY", "account_series": "7001", "currency": "USD",
            "variance_usd": 32454, "entity": "AMER", "category": "MANUAL_JOURNAL",
            "root_cause": "Finance Director posted $32,454 interest accrual direct to GL for off-balance-sheet financing not yet configured in treasury TMS. No subledger offset exists — GL entry unsupported by operational system.",
            "resolution": "Off-balance-sheet arrangement configured in TMS. Backdated subledger entry created to match GL accrual. Policy updated to require TMS setup before GL manual entry is permitted.",
            "resolution_days": 3,
        },
    },
    {
        "id": "KB-030",
        "document": (
            "GL_ONLY on account 2300 Long-term Debt EMEA-GBP entity GBP currency. "
            "Variance $50,800 USD. Opening balance adjustment journal posted in error. "
            "During year-end close, a £40,000 loan balance adjustment was posted to the GL "
            "to correct a prior-year error. The adjustment was an auditor-requested restatement "
            "but the journal was posted to the current period instead of being reflected as a "
            "prior-period adjustment, creating a mismatch with the subledger loan schedule. "
            "Resolution: reversed current-period journal and posted as restated prior-period entry."
        ),
        "metadata": {
            "exception_type": "GL_ONLY", "account_series": "2300", "currency": "GBP",
            "variance_usd": 50800, "entity": "EMEA-GBP", "category": "MANUAL_JOURNAL",
            "root_cause": "Auditor-requested £40,000 loan restatement posted to current period instead of prior-year comparative. GL balance overstated vs subledger loan amortisation schedule by $50,800 USD.",
            "resolution": "Reversed current-period posting. Reposted as prior-period comparative restatement with appropriate disclosure. Subledger loan schedule updated to reflect restated opening balance.",
            "resolution_days": 3,
        },
    },
    {
        "id": "KB-031",
        "document": (
            "GL_MISMATCH on account 1400 Short-term Investments AMER entity USD currency. "
            "Variance $23,600 USD. Mark-to-market journal posted to wrong account series. "
            "Treasury team posted a $23,600 mark-to-market gain on equity portfolio to account "
            "1400 Short-term Investments (balance sheet) instead of the correct OCI reserve "
            "account 3100 Share Capital Other Comprehensive Income. Posting was a manual "
            "override of the automated MTM journal. "
            "Resolution: reversed misposting and reposted to correct OCI account."
        ),
        "metadata": {
            "exception_type": "GL_MISMATCH", "account_series": "1400", "currency": "USD",
            "variance_usd": 23600, "entity": "AMER", "category": "MANUAL_JOURNAL",
            "root_cause": "Manual override of automated MTM journal posted $23,600 equity portfolio gain to 1400 (Investments) instead of 3100 (OCI). Override bypassed automated account routing logic.",
            "resolution": "Reversed 1400 posting. Reposted gain to OCI reserve 3100 per IFRS 9 classification. Restricted manual override of MTM journals to require CFO approval.",
            "resolution_days": 1,
        },
    },
    {
        "id": "KB-032",
        "document": (
            "SUBLEDGER_ONLY on account 6006 Travel and Entertainment AMER entity USD currency. "
            "Variance $11,200 USD. Expense report approved in T&E system but GL interface disabled. "
            "Quarterly expense report batch for $11,200 was approved and posted in the Concur "
            "T&E subledger but the GL interface had been disabled for system maintenance and "
            "was not re-enabled after the maintenance window closed. "
            "T&E expenses accumulated in subledger for 8 days without transmitting to GL. "
            "Resolution: re-enabled interface and processed the backlog batch."
        ),
        "metadata": {
            "exception_type": "SUBLEDGER_ONLY", "account_series": "6006", "currency": "USD",
            "variance_usd": 11200, "entity": "AMER", "category": "MANUAL_JOURNAL",
            "root_cause": "Concur T&E GL interface disabled for maintenance window and not re-enabled. $11,200 of approved expense reports accumulated in subledger for 8 days without GL transmission.",
            "resolution": "Re-enabled GL interface. Processed 8-day backlog batch successfully. Added interface status to daily reconciliation dashboard with automatic escalation after 2-hour outage.",
            "resolution_days": 1,
        },
    },
]


def build(vector_store_path: str) -> None:
    chroma_client = chromadb.PersistentClient(path=vector_store_path)

    # Always rebuild fresh
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        print(f"  Dropped existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    documents = [r["document"] for r in RECORDS]
    metadatas = [r["metadata"] for r in RECORDS]
    ids = [r["id"] for r in RECORDS]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # Category breakdown
    categories = {}
    for r in RECORDS:
        cat = r["metadata"]["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"Knowledge base built: {len(RECORDS)} records in '{COLLECTION_NAME}'")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} records")
    print(f"Location: {vector_store_path}")


def main() -> None:
    base = Path(__file__).parent.parent
    vector_store_path = str(base / "data" / "vector_store")
    build(vector_store_path)


if __name__ == "__main__":
    main()
