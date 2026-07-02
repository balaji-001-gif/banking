# Bizaxl Banking — ERPNext Banking Module

A comprehensive banking module for **ERPNext v15+ / Frappe Framework v15** that covers the full lifecycle of retail banking operations — from customer onboarding and KYC, through deposits and payments, to lending, NPA management, fraud detection, dispute resolution, and regulatory reporting.

**Total: 28 DocTypes** (19 Master, 2 Child Tables, 7 Supporting) + **8 Integration Modules** + **12 Report Scripts** + **10 Scheduler Jobs**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Data Model](#architecture--data-model)
3. [DocTypes at a Glance](#doctypes-at-a-glance)
4. [New Doctypes (v2.0)](#new-doctypes-v20)
5. [Schema Enhancements (v2.0)](#schema-enhancements-v20)
6. [Feature Modules & Business Logic](#feature-modules--business-logic)
7. [New Features (v2.0)](#new-features-v20)
8. [Scheduler Jobs (Automated Tasks)](#scheduler-jobs-automated-tasks)
9. [Roles & Permissions](#roles--permissions)
10. [End-User SOP (Step-by-Step Workflows)](#end-user-sop-step-by-step-workflows)
11. [Installation Guide (Developer)](#installation-guide-developer)
12. [Developer Guide](#developer-guide)
13. [API Reference](#api-reference)
14. [Roadmap](#roadmap)

---

## Overview

Bizaxl Banking is a **full-featured banking operations module** built as a Frappe/ERPNext custom app. It provides:

- **28 DocTypes** covering the complete banking domain including 7 new in v2.0
- **8 External Integration Modules** — NPCI/UPI Rails, Aadhaar eKYC, PAN Verification, Credit Bureau, NACH Mandates, Sanctions Screening, SMS/Email/WhatsApp, and e-Sign/DigiLocker — all configurable via a single Settings doctype with stub-to-live fallback
- **8 Custom Roles** with granular permission matrices
- **Full business logic in all controllers** — validation, auto-numbering, interest calculation, EMI processing, NPA classification, fraud detection, prepayment, and more
- **10 scheduled jobs** for daily, weekly, and monthly automation
- **12 Report scripts** for operations and regulatory compliance
- **Reconciliation engine** for daily balance matching
- **Bulk payment processing** with CSV upload
- **CRM lead pipeline** with lead-to-customer conversion
- **Fraud detection** with 5 alert types (Velocity Breach, Unusual Geography, Account Takeover, Positive Pay Mismatch, Manual)

All integrations follow a **stub-to-live pattern**: they work immediately in simulated mode (no credentials needed), and automatically switch to live API calls as soon as you configure the API keys in *Banking Integration Settings*.

The module follows Indian banking regulations and RBI guidelines for:
- KYC norms (Aadhaar/PAN/Video KYC)
- NPA classification (SMA-0 → SMA-1 → SMA-2 → Sub-standard → Doubtful → Loss)
- Payment rail limits (UPI/IMPS/NEFT/RTGS)
- AML screening and fraud detection
- Priority Sector Lending (PSL) reporting
- SLA-based dispute resolution (T+5 UPI, T+30 others)

---

## Architecture & Data Model

### Entity-Relationship Diagram

```
                           ┌──────────────────────────────────────┐
                           │     Banking Integration Settings      │
                           │  (Single — API Keys & Endpoints)     │
                           └──┬────┬────┬────┬────┬────┬───┬───┬──┘
                              │    │    │    │    │    │   │   │
          ┌───────────────────┘    │    │    │    │    │   │   └──────────────────┐
          │                        │    │    │    │    │   └──────────┐           │
          ▼                        ▼    ▼    ▼    ▼    ▼              ▼           ▼
   ┌────────────┐          ┌──────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
   │ NPCI/UPI   │          │ Aadhaar  │ │ PAN    │ │ Credit   │ │ NACH    │ │ e-Sign / │
   │ Rails      │          │ eKYC     │ │ Verif. │ │ Bureau   │ │ Mandate │ │ DigiLocker│
   └─────┬──────┘          └────┬─────┘ └───┬────┘ └────┬─────┘ └────┬────┘ └────┬─────┘
         │                      │           │           │           │           │
         ▼                      ▼           ▼           ▼           ▼           ▼
   ┌──────────┐           ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Payment  │           │ KYC      │ │ Customer │ │ Loan     │ │ NACH     │ │ Agreement│
   │ Orders   │           │ Documents│ │ Profiles │ │ Applic.  │ │ Mandates │ │ Signing  │
   └──────────┘           └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

   ┌──────────────┐    ┌────────────────────┐
   │ Sanctions    │    │ SMS / Email /      │
   │ Screening    │    │ WhatsApp           │
   └──────┬───────┘    └────────┬───────────┘
          │                     │
          ▼                     ▼
   ┌──────────────┐    ┌────────────────────┐
   │ AML Logs /   │    │ Customer Alerts /  │
   │ Fraud Alerts │    │ Transaction Notifs │
   └──────────────┘    └────────────────────┘


                               ┌─────────────────────────┐
                               │ Banking Configuration    │
                               │ (Singleton — Bank Admin) │
                               └─────────┬───────────────┘
                                         │
┌────────────────────────────────────────┼───────────────────────────────┐
│                                        │                               │
▼                                        ▼                               ▼
┌──────────────────┐           ┌──────────────────────┐      ┌──────────────────────┐
│ Banking State      │◄──────────│ Banking Branch        │      │ Banking Interest      │
│ (Master — 28       │           │ (IFSC, Manager,      │      │ Rate Schedule         │
│  Indian states)    │           │  Address, Type)       │      │ (Slab-based rates)    │
└──────────────────┘           └──────────┬───────────┘      └──────────────────────┘
                                          │
                                          ▼
                          ┌──────────────────────────────┐
                          │ Banking Customer               │
                          │ (Individual/Company/Trust/...) │
                          │ PAN validation, AML log       │
                          └──┬───────────────┬───────────┘
                             │               │
              ┌──────────────┘               └──────────────┐
              ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────────┐
│ Banking KYC Document      │              │ Banking Customer Lead        │
│ (Aadhaar/PAN/Passport)    │              │ (CRM — Lead → Customer      │
│ Expiry tracking          │              │  conversion pipeline)        │
└──────────────────────────┘              └──────────────────────────────┘

                          ┌──────────────────────────────────────────────────┐
                          │                  Banking Account                  │
                          │  (Savings/Current/Salary/NRE/NRO/CC/OD)         │
                          │  Joint Holders (child) · Nominee · Balance      │
                          └──┬────────────────┬──────────────┬──────────────┘
                             │                │              │
                             ▼                ▼              ▼
              ┌─────────────────────┐  ┌──────────────┐  ┌──────────────────┐
              │ Banking Account     │  │ Banking NACH │  │ Banking Service  │
              │ Entitlement         │  │ Mandate      │  │ Charge Rule      │
              │ (Multi-user access) │  │ (Auto-debit) │  │ (Fee config)     │
              └─────────────────────┘  └──────────────┘  └──────────────────┘

              ┌──────────────────────────────────────────────────────────────┐
              │                  Banking Payment Order                        │
              │  Maker → Checker → Submitted → Settled                      │
              │  UPI/IMPS/NEFT/RTGS/Cheque                                  │
              │  UTR auto-generation · Balance check                        │
              └──┬───────────────────────────────────────────────────────────┘
                 │
                 ▼
              ┌──────────────────────────────────────────────────────────────┐
              │              Banking Transaction Ledger                       │
              │  Double-entry · Running balance · Dynamic Link to source     │
              │  Transaction types: Debit/Credit/Interest/Fee/Penalty        │
              └──────────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────────────────┐
              │                  Banking Standing Instruction                 │
              │  Recurring payments — Utility/EMI/Investment/Sweep/Custom    │
              │  Daily/Weekly/Monthly/Quarterly/Annual                       │
              └──────────────────────────────────────────────────────────────┘

                        ┌───────────────────────────────────┐
                        │       Lending Module               │
                        ├───────────────────────────────────┤
                        ▼                                   ▼
        ┌──────────────────────────┐    ┌──────────────────────────┐
        │ Banking Loan Application │    │ Banking Loan Account      │
        │ Risk grading A1→D       │◄───│ EMI · Interest · NPA     │
        │ Bureau score · FOIR     │    │ Prepayment · Rate update  │
        │ Co-applicants (child)   │    │ Linked Mandate            │
        └──────────────────────────┘    └────────┬─────────────────┘
                                                  │
                          ┌───────────────────────┼───────────────────┐
                          ▼                       ▼                   ▼
              ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐
              │ Banking Collateral   │  │ Banking NPA      │  │ Banking Bulk │
              │ (Property/FD/Gold)  │  │ Tracker          │  │ Payment      │
              └──────────────────────┘  │ SMA-0→Loss      │  │ (CSV batch)  │
                                        │ Provision %     │  └──────────────┘
                                        └──────────────────┘

                        ┌───────────────────────────────────┐
                        │    Fraud & Compliance Module       │
                        ├───────────────────────────────────┤
                        ▼               ▼               ▼
        ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
        │ Banking Fraud    │  │ Banking AML      │  │ Banking Dispute  │
        │ Alert            │  │ Screening Log    │  │ Case             │
        │ 5 alert types    │  │ ONSC/OFAC/PEP    │  │ SLA · Reversal   │
        │ Auto-hold        │  │ Match detection  │  │ Escalation       │
        └──────────────────┘  └──────────────────┘  └──────────────────┘

        ┌──────────────────────────────────────────────────────────────┐
        │              Banking Regulatory Report                        │
        │  CTR · STR · CRILC · NPA Return · Priority Sector           │
        │  Auto-generation · Weekly/Monthly/Quarterly                 │
        └──────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────────────────────────┐
        │              Banking Positive Pay Record                      │
        │  Check fraud prevention — pre-submit cheque details         │
        │  System matches presented cheques against submitted data    │
        └──────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────────────────────────┐
        │              Reports (12 Scripts)                            │
        │  Portfolio Summary · Transaction Log · KYC Pending          │
        │  Fraud Dashboard · NPA Register · EMI Dues                 │
        │  Payment Reconciliation · AML Summary · Interest Accrual   │
        │  RBI NPA Return · Priority Sector · CTR/STR Export         │
        └──────────────────────────────────────────────────────────────┘
```

---

## DocTypes at a Glance

### Foundation Layer

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 1 | Banking Configuration | Single | Bank-level settings (RBI license, IFSC prefix, AML threshold) | IFSC prefix validation, AML threshold validation |
| 2 | Banking State | Master | Indian states with RBI zone mapping | Master data (28 states) |
| 3 | Banking Branch | Master | Branch details, IFSC code | Link → State, IFSC format validation |
| 4 | Banking Interest Rate Schedule | Master | Slab-based interest rate configuration | Slab rate lookup, interest calculation |

### Onboarding & KYC

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 5 | Banking Customer Lead | Master | CRM lead pipeline | Lead-to-customer conversion, auto-RM assignment |
| 6 | Banking Customer | Master | Customer profile (Individual/Company/Trust etc.) | Auto-numbering, PAN validation, mobile validation, AML log, risk scoring |
| 7 | Banking KYC Document | Master | KYC documents (Aadhaar/PAN/Passport etc.) | Expiry tracking, re-KYC trigger, auto-freeze on 90+ days expired |
| 8 | Banking Account Entitlement | Master | Multi-user access for business accounts | Owner/Accountant/Auditor levels, duplicate user check |

### Deposits

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 9 | Banking Deposit Product | Master | Product catalog (Savings/FD/RD/PPF/SSY) | Interest rate validation, tenure validation |
| 10 | Banking Account | Master | Deposit accounts (Savings/Current/Salary/NRE/NRO/CC/OD) | Auto-numbering, balance management, joint holders, dormant classification, closure validation |
| 11 | Banking Account Joint Holder | **Child Table** | Joint account holders with operating mode | Operating mode: Either or Survivor/Jointly/Former or Survivor/Anyone or Survivor |
| 12 | Banking Service Charge Rule | Master | Bank fee configuration | Account maintenance, ATM, cheque return, SMS charges |

### Payments

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 13 | Banking Payment Order | Master | Payment instructions (UPI/IMPS/NEFT/RTGS/Cheque) | Maker-Checker, balance check, rail limits, UTR generation |
| 14 | Banking Transaction Ledger | Master | Double-entry transaction log | Running balance, Dynamic Link to source, account sync |
| 15 | Banking Standing Instruction | Master | Recurring payments (EMI/Utility/SIP) | Auto-execution, balance check, pause on failure |
| 16 | Banking NACH Mandate | Master | NACH auto-debit mandates | Amount validation |
| 17 | Banking Bulk Payment | Master | Batch payment processing | CSV upload, batch processing, auto-creates Payment Orders |
| 18 | Banking Bulk Payment Entry | **Child Table** | Individual beneficiary in bulk payment | Status tracking, UTR capture, error messages |

### Lending

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 19 | Banking Loan Application | Master | Loan applications (Personal/MSME/Home/Vehicle/Gold/Agri/Microfinance) | Risk grading (A1→D), FOIR validation, auto-create Loan Account |
| 20 | Banking Loan Co-applicant | **Child Table** | Loan co-applicants | Linked via Table field |
| 21 | Banking Loan Account | Master | Sanctioned loans with EMI schedules | Daily reducing balance interest, EMI processing, prepayment, floating rate update, NPA tracker |
| 22 | Banking Collateral | Master | Collateral against loans (Property/FD/Gold/Stocks) | Lien validation (lien ≤ market value) |
| 23 | Banking NPA Tracker | Master | NPA classification & provisioning | Auto-classification (SMA-0→Loss), provision calculation |

### Risk & Compliance

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 24 | Banking Fraud Alert | Master | Fraud alerts & case management | 5 alert types, auto-detection, auto-hold |
| 25 | Banking Positive Pay Record | Master | Check fraud prevention | Pre-submit cheque details, match against presented cheques |
| 26 | Banking AML Screening Log | Master | AML/sanctions screening records | Match-disposition validation |
| 27 | Banking Dispute Case | Master | Customer dispute resolution | SLA deadline (T+5 UPI, T+30 others), auto-escalation, auto-reversal |
| 28 | Banking Regulatory Report | Master | Regulatory submissions (CTR/STR/CRILC/NPA/PSL) | Auto-generation, generate_scheduled_reports() weekly |

### Integrations

| # | Doctype/Module | Type | Purpose | Key Functions |
|---|---------------|------|---------|---------------|
| 29 | **Banking Integration Settings** | **Single** | **Central API key management for all 8 external integrations** | **Enable/disable toggles, test connection buttons** |

### Reports (12 Scripts)

| # | Report | Purpose | Frequency |
|---|--------|---------|-----------|
| R1 | Portfolio Summary | Total deposits, advances, NPA%, CD ratio by branch | Daily |
| R2 | Transaction Log | All posted debits/credits with UTR, rail, settlement | Daily |
| R3 | KYC Pending Tracker | Customers with pending/rejected/re-KYC status | Daily |
| R4 | Fraud Alert Dashboard | Open alerts by type, risk score, SLA breach | Real-time |
| R5 | NPA Register | All NPA accounts: DPD bucket, outstanding, provision | Weekly |
| R6 | EMI Dues & Collections | EMIs due next 7 days, collected vs pending | Daily |
| R7 | Payment Reconciliation | System-settled vs ledger-posted, unmatched flagged | Daily |
| R8 | AML Screening Summary | Total screened, matches, false positives, STRs | Weekly |
| R9 | Interest Income Accrual | Accrued interest by product, FD maturity, TDS | Monthly |
| R10 | RBI NPA Return | Prescribed RBI format: Sub-standard, Doubtful, Loss split | Quarterly |
| R11 | Priority Sector Lending | PSL achievement vs target: Agri, MSME, Weaker Section | Quarterly |
| R12 | CTR/STR Export | FIU-IND prescribed export ready for submission | On demand |

---

## New Doctypes (v2.0)

### Banking State
**Purpose:** Master data for Indian states with RBI zone mapping for jurisdiction-based reporting.

| Field | Type | Description |
|-------|------|-------------|
| state_name | Data | Full state name (e.g., Maharashtra) |
| state_code | Data | ISO state code (e.g., MH) |
| region | Select | North/South/East/West/Central/North-East |
| rbi_zone | Select | RBI zone (Mumbai/New Delhi/Chennai/Kolkata etc.) |

### Banking Interest Rate Schedule
**Purpose:** Configure slab-based interest rates for deposit products.

| Field | Type | Description |
|-------|------|-------------|
| product_type | Select | Savings/Current/FD/RD/PPF/SSY |
| deposit_product | Link → Banking Deposit Product | Optional product link |
| min_amount | Currency | Lower bound of slab (inclusive) |
| max_amount | Currency | Upper bound of slab (inclusive) |
| interest_rate | Percent | Annual interest rate for this slab |
| min_tenure_days | Int | Minimum tenure in days |
| max_tenure_days | Int | Maximum tenure in days |
| is_active | Check | Enable/disable this slab |

**Key Methods:**
- `get_applicable_rate(amount, tenure_days)` — Find matching rate for given amount
- `calculate_interest(principal, tenure_days)` — Calculate interest using slab rate

### Banking Service Charge Rule
**Purpose:** Define bank charges — account maintenance, ATM fees, cheque return, SMS alerts, etc.

| Field | Type | Description |
|-------|------|-------------|
| charge_type | Select | Account Maintenance/ATM Fee/Cheque Return/SMS Alert/DD/RTGS-NEFT/Debit Card/Overdraft Interest |
| account_type | Select | All/Savings/Current/Salary/NRE/NRO/Cash Credit/Overdraft |
| charge_amount | Currency | Fixed fee amount |
| charge_percentage | Percent | Optional % of transaction value |
| min_charge | Currency | Floor for percentage-based charges |
| max_charge | Currency | Cap for percentage-based charges |
| frequency | Select | One-time/Monthly/Quarterly/Annual/Per Transaction |
| applicable_if_balance_below | Currency | Only charge if balance below this threshold |

### Banking Customer Lead
**Purpose:** CRM-style lead pipeline — capture prospects before they become customers.

| Field | Type | Description |
|-------|------|-------------|
| full_name | Data | Prospect name |
| customer_type | Select | Individual/Proprietary/Partnership/Company/Trust/Co-op Society |
| mobile | Data | 10-digit Indian mobile (validated) |
| lead_source | Select | Walk-in/Referral/Website/Campaign/Agent/Branch/Partner/Other |
| lead_status | Select | New/Contacted/Qualified/Proposal/Converted/Lost |
| branch | Link → Banking Branch | Assigned branch |
| assigned_rm | Link → User | Auto-assigned Relationship Manager |
| product_interest | Select | Savings/Current/FD/RD/Personal Loan/Home Loan/etc. |
| converted_to_customer | Link → Banking Customer | Auto-set on conversion |

**Key Methods:**
- `convert_to_customer()` — Creates Banking Customer record, updates lead status to "Converted"
- `before_save()` — Auto-assigns RM from branch if not set

### Banking Account Entitlement
**Purpose:** Multi-user access levels for business accounts — Owner/Accountant/Auditor.

| Field | Type | Description |
|-------|------|-------------|
| account | Link → Banking Account | Target account |
| user | Link → User | Entitled user |
| access_level | Select | Owner (full)/Accountant (payments)/Auditor (read-only)/Viewer |
| can_initiate_payments | Check | Payment creation permission |
| can_approve_payments | Check | Payment approval permission |
| can_view_statements | Check | Statement access |

### Banking Bulk Payment
**Purpose:** Batch payment processing — upload CSV of beneficiaries, process in bulk with consolidated approval.

| Field | Type | Description |
|-------|------|-------------|
| batch_reference | Data | Batch identifier |
| from_account | Link → Banking Account | Debit account |
| total_amount | Currency | Auto-calculated sum of all entries |
| total_entries | Int | Auto-calculated entry count |
| status | Select | Draft/Pending Approval/Approved/Processing/Completed/Partially Completed/Failed |
| uploaded_csv | Attach | CSV file input |
| entries | Table (Banking Bulk Payment Entry) | Beneficiary list |

**Key Methods:**
- `load_csv()` — Parse uploaded CSV (columns: beneficiary_name, to_account_no, to_ifsc, payment_rail, amount)
- `process_batch()` — Create individual Payment Orders for each entry, track status

### Banking Bulk Payment Entry (Child Table)

| Field | Type | Description |
|-------|------|-------------|
| beneficiary_name | Data | Payee name |
| to_account_no | Data | Beneficiary account number |
| to_ifsc | Data | Beneficiary IFSC code |
| payment_rail | Select | UPI/IMPS/NEFT/RTGS/Internal |
| amount | Currency | Payment amount |
| status | Select | Pending/Settled/Failed (read-only) |
| utr_number | Data | Auto-populated on settlement |
| error_message | Small Text | Failure reason |
| payment_order_ref | Data | Link to created Payment Order |

---

## Schema Enhancements (v2.0)

### 1. Banking Branch → State Field
- **Before:** `state` was a plain `Data` field
- **After:** `state` is now `Link → Banking State` — enables RBI zone filtering and state-level reporting

### 2. Banking Account Joint Holder → Operating Mode
- **New field:** `operating_mode` (Select)
- **Options:** Either or Survivor / Jointly / Former or Survivor / Anyone or Survivor
- Required for compliance with joint account operating instructions

### 3. Banking Transaction Ledger → Dynamic Link
- **Before:** `source_doctype` and `source_docname` were separate `Data` fields
- **After:**
  - `source_doctype` is now `Link → DocType`
  - `source_docname` is now `Dynamic Link (options: source_doctype)`
- Enables native Frappe linking with proper referential integrity and UI navigation

---

## Banking Integration Settings (New Single Doctype)

The **Banking Integration Settings** doctype serves as the central configuration hub for all 8 external integrations. Each integration has its own section with:

- **Enable toggle** — Turn integration on/off without losing saved credentials
- **Mode selector** — Switch between Sandbox (testing) and Live (production)
- **API Key & Secret** — Password fields encrypted at rest by Frappe
- **Endpoint URLs** — Separate fields for sandbox and live endpoints (with sensible defaults pre-filled)
- **Provider selector** — Choose between providers (e.g., CIBIL/Experian/CRIF for bureau, MSG91/Twilio for SMS)
- **Test Connection button** — Whitelisted method to verify credentials without leaving the UI

**Permissions:** Only System Manager and Banking System Admin can view/edit. Banking Auditor gets read-only access.

### Configuration Flow

```
1. Navigate to: Banking Integration Settings
2. Find the integration you want to configure (NPCI, Aadhaar, PAN, etc.)
3. Check "Enable [Integration]"
4. Enter API Key and API Secret (provided by the service provider)
5. Set Mode: Sandbox (for testing) or Live (for production)
6. Verify endpoints (defaults are pre-filled)
7. Click "Test [Integration] Connection" to verify credentials
8. Save — Integrations activate automatically
```

> **Stub-to-Live Pattern:** All integrations work immediately in "simulated" mode without any API keys. In simulated mode, they return realistic mock data so the entire application can be developed and tested without external dependencies. The moment you enter real API keys, they switch to live mode transparently.

---

## External Integration Modules

### 1. NPCI / UPI Rails (`payment_gateways/npci.py`)

**Purpose:** Execute UPI, IMPS, NEFT, and RTGS payments against NPCI infrastructure.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `execute_payment(payment_order)` | Submit payment to NPCI for execution | Simulated: generates fake UTR |
| `verify_transaction_status(utr)` | Check settlement status by UTR | Simulated: returns "settled" |

**Wired Into:** `BankingPaymentOrder.process_payment()` → On submit, calls NPCI, uses returned UTR, sends transaction alert via messaging.

**Settings Required:** NPCI API Key, NPCI API Secret, Merchant Code, Terminal ID, Encryption Key

### 2. UIDAI / Aadhaar eKYC (`kyc/aadhaar.py`)

**Purpose:** Aadhaar OTP-based eKYC verification and Offline XML verification.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `verify_aadhaar_otp(aadhaar, otp, txn_id)` | Generate OTP + verify with KYC data retrieval | Simulated: returns mock KYC data |
| `verify_offline_xml(xml, ref_id)` | Parse and verify Aadhaar Offline XML | Works without API (XML parsing) |

**Settings Required:** Aadhaar API Key, License Key (AUA/KUA), Org ID (ASA)

### 3. NSDL / PAN Verification (`kyc/pan.py`)

**Purpose:** Real-time PAN validation with name and DOB matching.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `verify_pan(pan, name, dob)` | Validate PAN, match name/DOB against NSDL database | Simulated: returns valid with name/DOB match |

**Wired Into:** `BankingCustomer.on_update()` → Runs silently on KYC verification. Warns if PAN name doesn't match customer-provided name.

**Settings Required:** PAN API Key, Merchant Code

### 4. CIBIL / Experian / CRIF (`bureau/cibil.py`)

**Purpose:** Credit score pull, full credit report, bureau-based loan eligibility.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `fetch_credit_score(pan, name, mobile)` | Pull credit score and report from configured bureau | Simulated: returns score 750 with realistic report |
| `evaluate_loan_eligibility(pan, amount, income, obligations)` | Calculate max eligible amount and FOIR based on score | Works in simulated mode with score 750 |

**Wired Into:** `BankingLoanApplication.validate()` → Auto-fills bureau_score if empty. Uses configured provider (CIBIL/Experian/CRIF).

**Settings Required:** Bureau API Key, Provider (CIBIL/Experian/CRIF), Member ID, Password

### 5. NACH Mandate (NPCI) (`payment_gateways/nach.py`)

**Purpose:** Register, execute, and cancel NACH mandates with sponsor bank.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `register_mandate(mandate)` | Register mandate with sponsor bank | Simulated: returns fake sponsor ref |
| `execute_auto_debit(mandate, amount)` | Execute auto-debit against registered mandate | Simulated: returns fake UTR |
| `cancel_mandate(ref)` | Cancel an existing mandate | Simulated: returns cancelled |

**Wired Into:** `BankingNachMandate.before_submit()` → Automatically registers with sponsor bank on submit.

**Settings Required:** NACH API Key, Sponsor Bank Code, Member ID

### 6. FIU-IND / Sanction Lists (`compliance/sanctions.py`)

**Purpose:** Screen customers and transactions against OFAC, UN, PEP, MHA designated lists.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `screen_customer(name, pan, full_name, dob)` | Full sanctions/PEP screening | Simulated: returns "Clear" |
| `screen_transaction(payment_order)` | Transaction-level sanctions check | Simulated: no match found |

**Wired Into:** `BankingCustomer.on_update()` → Runs silently on KYC verification. Creates AML Screening Log if match found.

**Settings Required:** Sanctions API Key, Provider (FIU-IND/UN/OFAC/World-Check), Check Frequency

### 7. SMS / Email / WhatsApp (`notifications/messaging.py`)

**Purpose:** Multi-channel customer notifications — transaction alerts, EMI reminders, KYC reminders, OTP delivery.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `send_sms(mobile, message, template)` | Send SMS via MSG91/Twilio/AWS SNS/Exotel | Simulated: logs message |
| `send_email(to, subject, message)` | Send email via Frappe's built-in mail | Works if Frappe email is configured |
| `send_whatsapp(mobile, message, template)` | Send WhatsApp via Business API | Simulated: logs message |
| `send_transaction_alert(customer, account, payment)` | Multi-channel alert for debits | Combines SMS + WhatsApp + Email |
| `send_emi_reminder(customer, loan, amount, date)` | EMI due reminder | Sends SMS if configured |
| `send_kyc_reminder(customer, days_remaining)` | KYC re-verification reminder | Sends SMS if configured |

**Wired Into:** `BankingPaymentOrder.process_payment()` → Sends transaction alert on settlement.

**Settings Required:** SMS Provider, API Key, Sender ID; Email API Key, From Address; WhatsApp API Key, Business Phone

### 8. e-Sign / DigiLocker (`kyc/esign.py`)

**Purpose:** Aadhaar-based digital signing of agreements, DigiLocker document retrieval.

| Function | Description | Status Without API Key |
|----------|-------------|----------------------|
| `send_for_esign(doc_path, aadhaar, name, type)` | Send document for e-Sign | Simulated: marks as signed |
| `esign_callback()` | Webhook endpoint for e-Sign provider | Always available |
| `fetch_digilocker_document(uid, doc_type)` | Fetch verified document from DigiLocker | Simulated: returns verified |

**Settings Required:** e-Sign API Key, Provider (eSign CDAC/DigiLocker/SignDesk), Certificate ID

### Integration Wiring Summary

| Integration | Triggers When | Business Impact |
|-------------|---------------|-----------------|
| NPCI/UPI Rails | Payment Order submitted | Executes live payment, returns UTR, sends alert |
| Aadhaar eKYC | KYC Document verified | Retrieves name/DOB/address from UIDAI |
| PAN Verification | Customer KYC verified | Validates PAN, warns on name mismatch |
| Credit Bureau | Loan Application saved | Auto-fills bureau score and FOIR if empty |
| NACH Mandate | NACH Mandate submitted | Registers with sponsor bank for auto-debit |
| Sanctions Screening | Customer KYC verified | Creates AML Log if match found |
| SMS/Email/WhatsApp | Payment Order settled | Sends multi-channel transaction alert |
| e-Sign/DigiLocker | API call only | Signs agreements, retrieves DigiLocker docs |

---

## Feature Modules & Business Logic

### 1. Customer Onboarding & KYC

```
Banking Customer Lead → Banking Customer → Banking KYC Document → AML Screening
       │                       │                     │                    │
       │  CRM pipeline         │  PAN/Mobile         │  Expiry tracking  │  Match detection
       │  Lead→Customer        │  validation         │  Re-KYC trigger   │  Disposition check
       │  Auto-RM              │  Risk scoring       │  90d→auto-freeze  │
       └───────────────────────┴─────────────────────┴───────────────────┘
```

**Validations:**
- PAN format: `ABCDE1234F` (10 characters, regex validated)
- Mobile: 10-digit Indian mobile (starts with 6-9)
- Customer auto-numbering: `CUST-YYYY-MM-XXXXX`
- Lead auto-conversion: Qualified leads can be converted to full customers
- KYC expiry: Documents expiring → Customer status "Re-KYC Due"; 90+ days expired → Account frozen

### 2. Account Management

```
Banking Customer → Banking Account → Banking Transaction Ledger
                        │
                    ├── Joint Holders (child table with operating mode)
                    ├── Nominee
                    ├── Entitlements (multi-user access)
                    └── Dormant classification (12 months inactivity)
```

**Validations:**
- Account auto-numbering: `ACC-YYYYMM-XXXXX`
- Available balance ≤ Current balance
- Date Opened defaults to today
- Balance auto-updates on every Transaction Ledger submission
- **Dormant classification**: Accounts with no transactions for 12+ months auto-classified as "Dormant"
- **Closure validation**: Zero balance check, no active standing instructions, no NACH mandates, no pending payments

### 3. Payments (Maker-Checker Workflow)

```
Banking Payment Order
    │
    ├── Draft → Pending Approval → Approved → Submitted → Settled
    │                                                          │
    │  Maker: creates                               UTR auto-generated
    │  Checker: approves                            Balance deducted
    │  Rules: Maker ≠ Checker                       Transaction Ledger entry
    │
    └── Payment Rails: UPI (≤₹1L), IMPS (24×7), NEFT (batch), RTGS (min ₹2L)

Banking Bulk Payment
    │
    ├── CSV Upload → Validation → Approval
    ├── Batch processing → Individual Payment Orders
    └── Status: Completed / Partially Completed / Failed
```

**Business Rules:**
- Maker and Checker must be different users
- Checker is required before submission
- Sufficient balance checked before settlement
- Payment rail limits enforced:
  - RTGS: Minimum ₹2,00,000
  - NEFT: Maximum ₹50,00,000
  - UPI: Maximum ₹1,00,000
- UTR number auto-generated: `UTR{YYYYMMDDHHMMSS}{random}`
- Settlement creates Transaction Ledger entry and debits account

### 4. Loan Lifecycle

```
Loan Application → Approval → Loan Account → EMI Schedule → NPA Tracking
      │                                                           │
      │  Risk grading (A1-D)                         SMA-0 (0-30 DPD)
      │  Bureau score (300-900)                      SMA-1 (31-60 DPD)
      │  FOIR validation (≤70%)                      SMA-2 (61-90 DPD)
      │  Co-applicants (child table)                 Sub-standard (91-180)
      │  Auto-create Loan Account on approval        Doubtful (181-365)
      └── Loan Products: Personal/MSME/Home/Vehicle  Loss (365+ DPD)
                          Gold/Agri/Microfinance
```

**Interest Calculation (Daily Reducing Balance):**
```
Interest = Outstanding Principal × Rate% ÷ 100 ÷ 365 × Days
Monthly Interest = Outstanding Principal × Rate% ÷ 1200
```

**EMI Processing:**
- Scheduled daily: processes loans where `emi_date` matches today's date
- Posts EMI credit to Transaction Ledger
- Reduces outstanding principal
- Creates NPA Tracker entry for monitoring
- Auto-closes loan when final EMI is processed

**Prepayment:**
- `process_prepayment(amount)` — Reduce outstanding, recalculate EMI
- Partial prepayment → EMI recalculation using amortization formula
- Full prepayment → Account status "Prepaid"

**Floating Rate Updates:**
- `update_interest_rate(new_rate)` — For MCLR-linked loans
- Recalculates EMI based on new rate
- Logs rate change

**NPA Classification (RBI Guidelines):**

| DPD | Classification | Provision % |
|-----|---------------|-------------|
| 0-30 | SMA-0 (Special Mention) | 0% |
| 31-60 | SMA-1 | 5% |
| 61-90 | SMA-2 | 10% |
| 91-180 | Sub-standard | 15% |
| 181-365 | Doubtful | 40% |
| 365+ | Loss | 100% |

### 5. Fraud Detection

**5 Alert Types:**

| Alert Type | Detection Rule | Risk Score | Auto-Hold Threshold |
|------------|---------------|------------|---------------------|
| Velocity Breach | ≥5 payments in 1 hour OR single payment ≥₹10L | 65-75 | ≥80 |
| Unusual Geography | Beneficiary IFSC prefix differs from branch IFSC prefix | 60 | ≥80 |
| Account Takeover | ≥3 failed/draft payments in 1 hour OR ≥3 cancelled in 24h | 80 | ≥80 |
| Positive Pay Mismatch | Presented cheque details don't match Positive Pay Record | 85 | Yes |
| Manual | Created by compliance officer | User-defined | Configurable |

**Auto-Hold Behavior:**
- Risk score ≥ 80 → Account frozen (`account_status = "Frozen"`)
- Deduplication: Same account/alerts within 24 hours don't duplicate

### 6. Standing Instructions

- **Types:** Utility, Loan EMI, Investment, Sweep, Custom
- **Frequencies:** Daily, Weekly, Monthly, Quarterly, Annual
- **Auto-execution:** Runs daily for due instructions
  - Sufficient balance → executes payment
  - Insufficient balance → status = "Paused", error logged
  - End date reached → status = "Completed"

### 7. Dispute Management

- **SLA deadlines:** T+5 for UPI disputes, T+30 for other transaction types
- **SLA auto-escalation:** Daily job escalates disputes past their deadline
- **Auto-reversal:** When dispute is resolved "Upheld" with "Reversal" action → auto-creates reversal Transaction Ledger entry
- **Status flow:** Open → Under Investigation → Resolved - Upheld / Resolved - Rejected / Escalated

### 8. Reconciliation

**Daily Reconciliation (`run_daily_reconciliation()`):**
- For each active account, compare settled payments vs ledger entries
- Flag discrepancies with ₹1+ difference as Fraud Alerts

**CSV Upload (`upload_statement_csv()`):**
- Upload bank statement CSV with columns: txn_date, narration, debit, credit, reference
- Matches against Transaction Ledger entries
- Returns matched/unmatched/error counts

---

## New Features (v2.0)

### Bulk Payment Processing
- Upload CSV of multiple beneficiaries → creates individual Payment Orders
- Consolidated approval workflow
- Per-entry status tracking (Settled/Failed) with UTR capture
- Scheduler: `process_pending_bulk_payments()` — auto-processes approved batches

### Loan Prepayment
- Partial or full prepayment with EMI recalculation
- Amortization formula: `EMI = P × r × (1+r)^n / ((1+r)^n - 1)`
- Full prepayment → Account status "Prepaid"

### CRM Lead Workflow
- Full lead pipeline: New → Contacted → Qualified → Proposal → Converted → Lost
- `convert_to_customer()` — single-click conversion with KYC defaults
- Auto-RM assignment based on branch

### 12 Banking Reports
Runnable via Frappe Report Builder. Each report supports filters (date range, branch, status, etc.).

### Positive Pay System
- Pre-submit cheque details (number, date, amount, payee)
- System matches presented cheques against submitted records
- Mismatch → Fraud Alert (Positive Pay Mismatch, Risk Score: 85)

---

## Scheduler Jobs (Automated Tasks)

### Daily Tasks (`daily_long`) — 10 Jobs

| Function | Purpose | When |
|----------|---------|------|
| `auto_classify_npa()` | Calculate DPD for all loans, classify SMA-0→Loss | Every day |
| `process_due_instructions()` | Execute standing instructions due today | Every day |
| `auto_detect_fraud()` | Check for velocity breaches, geography mismatches, ATO, Positive Pay | Every day |
| `process_all_emis()` | Process EMIs for loans where today matches emi_date | Every day |
| `auto_escalate_overdue_disputes()` | Escalate disputes past their SLA deadline | Every day |
| `check_kyc_reverification_due()` | Flag customers with expired KYC docs, freeze 90+ days | Every day |
| `auto_classify_dormant_accounts()` | Mark accounts with 12 months inactivity as Dormant | Every day |
| `recalculate_customer_risk_scores()` | Upgrade risk based on transaction volumes | Every day |
| `process_pending_bulk_payments()` | Auto-process approved bulk payment batches | Every day |
| `run_daily_reconciliation()` | Match settled payments vs ledger, flag discrepancies | Every day |

### Weekly Tasks (`weekly_long`) — 1 Job

| Function | Purpose | When |
|----------|---------|------|
| `generate_scheduled_reports()` | Auto-generate NPA Return and Priority Sector reports | Weekly |

### Monthly Tasks (`monthly_long`) — 1 Job

| Function | Purpose | When |
|----------|---------|------|
| `post_all_interest()` | Post monthly interest on active/NPA loan accounts | 1st of month |

---

## Roles & Permissions

| Role | Access Scope | Key Permissions |
|------|-------------|-----------------|
| **Banking System Admin** | Full system | Read/Write/Create/Delete on all 27 doctypes |
| **Banking Branch Manager** | Branch-wide | Full CRUD on customers, accounts, loans (branch scope); approve payments |
| **Banking Relationship Manager** | Own customers | Create/Edit own records; initiate payments; read-only on others |
| **Banking Credit Officer** | Loan processing | Full CRUD on loan applications, loan accounts, collateral |
| **Banking Recovery Officer** | NPA management | Full CRUD on NPA trackers, recovery actions; read-only accounts |
| **Banking Compliance Officer** | Regulatory | Full CRUD on AML logs, fraud alerts, regulatory reports; verify KYC |
| **Banking Teller** | Cash counter | Create payment orders; own-branch customers; initiate payments |
| **Banking Auditor** | Read-only | Read-only access to all transactions and reports |

---

## End-User SOP (Step-by-Step Workflows)

### Workflow 1: Lead-to-Customer Onboarding

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                        LEAD-TO-CUSTOMER ONBOARDING SOP                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Step 1: Capture Lead                                                               │
│  └── RM creates Banking Customer Lead (Walk-in/Referral/Website/Campaign)          │
│  └── Enter: Full Name, Customer Type, Mobile, Lead Source, Product Interest        │
│  └── System auto-assigns RM based on branch                                        │
│                                                                                     │
│  Step 2: Qualify Lead                                                               │
│  └── Contact prospect, collect KYC documents                                       │
│  └── Update Lead Status → "Qualified"                                              │
│                                                                                     │
│  Step 3: Convert to Customer                                                        │
│  └── Click "Convert to Customer" button                                            │
│  └── System auto-creates Banking Customer with:                                    │
│      ├── Customer ID: CUST-YYYY-MM-XXXXX                                           │
│      ├── KYC Status: Pending                                                       │
│      ├── Risk Category: Auto-calculated                                            │
│      ├── AML Screening Log: Created                                                │
│      └── Lead Status: "Converted"                                                  │
│                                                                                     │
│  Step 4: KYC Verification                                                           │
│  └── Upload Aadhaar/PAN/Passport as Banking KYC Document                           │
│  └── Select verification method: eKYC/Video/Physical                               │
│  └── On verification → Customer KYC status = "Verified"                            │
│  └── KYC docs tracked for expiry → Re-KYC trigger at expiry                        │
│                                                                                     │
│  Step 5: Open Account                                                               │
│  └── Create Banking Account                                                         │
│  └── Select account type: Savings/Current/Salary                                   │
│  └── Link deposit product, add joint holders (with operating mode)                 │
│  └── Set nominee, configure entitlements for business accounts                     │
│  └── System auto-generates: ACC-YYYYMM-XXXXX                                       │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow 2: Payment Processing (Maker-Checker)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT PROCESSING SOP                                      │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Step 1: Maker Creates Payment Order                                                │
│  └── Select From Account (must have sufficient balance)                            │
│  └── Enter To Account No, To IFSC                                                  │
│  └── Select Payment Rail: UPI/IMPS/NEFT/RTGS/Internal/Cheque                      │
│  └── Enter Amount, Narration (optional)                                            │
│  └── Set yourself as Maker                                                          │
│  └── Status: Draft                                                                  │
│                                                                                     │
│  Step 2: Submit for Approval                                                        │
│  └── Set Checker (different user)                                                   │
│  └── Submit → Status: Pending Approval                                              │
│                                                                                     │
│  Step 3: Checker Reviews & Approves                                                 │
│  └── Checker logs in, verifies payment details                                     │
│  └── System validates:                                                             │
│      ├── Maker ≠ Checker                                                           │
│      ├── Sufficient balance                                                         │
│      ├── Rail limits (UPI ≤₹1L, RTGS ≥₹2L, etc.)                                  │
│  └── Approves → Status: Submitted                                                   │
│  └── System auto-processes:                                                        │
│      ├── Generates UTR: UTR{timestamp}{random}                                     │
│      ├── Debits account balance                                                     │
│      ├── Creates Transaction Ledger entry                                           │
│      └── Status: Settled                                                            │
│                                                                                     │
│  Step 4: Bulk Payment (Alternative)                                                 │
│  └── Upload CSV with columns: beneficiary_name, to_account_no, to_ifsc,           │
│       payment_rail, amount                                                          │
│  └── System validates and loads entries                                             │
│  └── Set Maker, Checker → Submit                                                   │
│  └── Batch processed: individual Payment Orders created for each entry             │
│  └── Status: Completed / Partially Completed                                       │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow 3: Loan Origination & Prepayment

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       LOAN ORIGINATION & PREPAYMENT SOP                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Step 1: Loan Application                                                           │
│  └── Credit Officer creates loan application                                       │
│  └── Link Applicant (Banking Customer)                                              │
│  └── Select Loan Product: Personal/MSME/Home/Vehicle/Gold/Agri/Microfinance        │
│  └── Enter Amount, Tenure, Purpose                                                  │
│  └── Add Co-applicants (child table) if applicable                                  │
│  └── Enter Bureau Score (300-900)                                                   │
│  └── Enter FOIR % (must be ≤ 70%)                                                  │
│  └── System auto-calculates Risk Grade:                                             │
│      ├── ≥750: A1  │ ≥700: A2  │ ≥650: B1  │ ≥600: B2  │ ≥500: C  │ <500: D     │
│                                                                                     │
│  Step 2: Credit Assessment & Approval                                               │
│  └── Review application details, risk grade                                        │
│  └── Set Decision: Approved/Referred/Rejected                                      │
│  └── Submit                                                                         │
│                                                                                     │
│  Step 3: Loan Account Creation (automatic)                                          │
│  └── If Approved → System auto-creates Loan Account                                │
│  └── Fields auto-populated:                                                        │
│      ├── Loan Account No: LOAN-YYYYMM-XXXXX                                        │
│      ├── Sanctioned Amount = Requested Amount                                      │
│      ├── Interest Rate = 12% (configurable)                                        │
│      ├── Rate Type: Fixed or Floating (MCLR-linked)                                │
│      ├── EMI = Calculated via amortization formula                                  │
│      ├── EMI Date = 5th of month (default)                                          │
│      └── Status: Active                                                             │
│                                                                                     │
│  Step 4: Collateral (if applicable)                                                 │
│  └── Create Banking Collateral record                                              │
│  └── Link to Loan Account                                                           │
│  └── Set Market Value, Valuation Date, Lien Amount                                 │
│  └── Validation: Lien Amount ≤ Market Value                                        │
│                                                                                     │
│  Step 5: Prepayment (if needed)                                                     │
│  └── Use process_prepayment(amount) method                                         │
│  └── Partial prepayment:                                                           │
│      ├── Outstanding reduced                                                        │
│      ├── EMI recalculated using amortization formula                                │
│      └── Transaction posted to ledger                                               │
│  └── Full prepayment:                                                               │
│      └── Account status → "Prepaid"                                                 │
│                                                                                     │
│  Step 6: Interest Rate Change (Floating Rate Loans)                                 │
│  └── Use update_interest_rate(new_rate) method                                     │
│  └── Only for rate_type = "Floating (MCLR-linked)"                                  │
│  └── EMI recalculated, change logged                                                │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow 4: NPA Management

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          NPA MANAGEMENT SOP                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Daily (automated by scheduler):                                                    │
│  └── System calculates DPD for all active loans                                    │
│  └── Classifies based on DPD:                                                      │
│      ├── 0-30 DPD: SMA-0                                                            │
│      ├── 31-60 DPD: SMA-1                                                           │
│      ├── 61-90 DPD: SMA-2                                                           │
│      ├── 91-180: Sub-standard                                                       │
│      ├── 181-365: Doubtful                                                          │
│      └── 365+: Loss                                                                 │
│  └── Updates Loan Account status to "NPA" if DPD > 90                              │
│  └── Calculates provision amount:                                                   │
│      ├── SMA-0: 0.25% of outstanding                                               │
│      ├── SMA-1: 5%                                                                 │
│      ├── SMA-2: 10%                                                                │
│      ├── Sub-standard: 15%                                                          │
│      ├── Doubtful: 25% (secured) / 40% (unsecured)                                │
│      └── Loss: 100%                                                                │
│                                                                                     │
│  Manual Actions (Recovery Officer):                                                │
│  └── Monitor NPA Tracker for overdue accounts                                       │
│  └── Set Recovery Stage: Notice Sent / Legal Filed / Lok Adalat /                  │
│       SARFAESI / DRT / Written Off                                                  │
│  └── Assign to recovery team member                                                 │
│  └── Update provision amounts as needed                                             │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow 5: Fraud Detection & Dispute Resolution

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    FRAUD DETECTION & DISPUTE RESOLUTION SOP                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Automatic Detection (scheduled daily):                                             │
│  └── Velocity Breach: ≥5 payments in 1 hour OR single payment ≥₹10L               │
│  └── Unusual Geography: Beneficiary IFSC prefix ≠ Branch IFSC prefix               │
│  └── Account Takeover: ≥3 failed payments in 1 hour OR ≥3 cancelled in 24h         │
│  └── Positive Pay Mismatch: Cheque presented without matching Positive Pay Record  │
│  └── If risk score ≥ 80 → Account auto-frozen                                      │
│                                                                                     │
│  Manual Review (Compliance Officer):                                                │
│  └── Review open fraud alerts by type and risk score                               │
│  └── Investigate → Update status:                                                   │
│      ├── Confirmed Fraud → File STR, take recovery action                          │
│      ├── False Positive → Close alert, unfreeze account                            │
│      └── Closed (manual action taken)                                               │
│                                                                                     │
│  Customer Dispute:                                                                  │
│  └── Customer raises dispute (portal/manual)                                       │
│  └── Create Banking Dispute Case                                                    │
│  └── SLA timer starts:                                                             │
│      ├── UPI dispute: T+5 days                                                      │
│      └── Other disputes: T+30 days                                                  │
│  └── Investigate → Update status:                                                   │
│      ├── Resolved - Upheld → Auto-reversal of transaction                          │
│      └── Resolved - Rejected → Close case                                          │
│  └── If SLA deadline passes → Auto-escalated to management                         │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow 6: Regulatory Reporting

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         REGULATORY REPORTING SOP                                     │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Step 1: Create Regulatory Report                                                   │
│  └── Compliance Officer creates report                                              │
│  └── Select Report Type: CTR / STR / CRILC / NPA Return / Priority Sector          │
│  └── Set Period From / Period To                                                    │
│                                                                                     │
│  Step 2: Generate Report                                                             │
│  └── System queries relevant data:                                                  │
│      ├── CTR: Transactions > ₹10L/day from Transaction Ledger                       │
│      ├── STR: Confirmed fraud alerts / Under Review                                 │
│      ├── CRILC: Loans with sanction ≥ ₹5Cr                                          │
│      ├── NPA Return: Sub-standard/Doubtful/Loss accounts with provisions            │
│      └── PSL: Agri/MSME/Microfinance loan portfolio vs targets                       │
│  └── Status: Generated                                                              │
│                                                                                     │
│  Step 3: Weekly Auto-Generation                                                     │
│  └── Scheduler runs generate_scheduled_reports() weekly                             │
│  └── Auto-generates NPA Return and Priority Sector reports                         │
│  └── No duplicate generation for same period                                        │
│                                                                                     │
│  Step 4: Submit to Regulator                                                        │
│  └── Submitted By: Compliance Officer                                               │
│  └── Status: Submitted → Acknowledged                                              │
│                                                                                     │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation Guide (Developer)

### Prerequisites

- ERPNext v15+ / Frappe Framework v15+
- Python 3.10+
- Node.js 18+
- MariaDB 10.6+

### Setup Steps

```bash
# 1. Initialize Frappe Bench (if not already done)
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# 2. Get ERPNext
bench get-app erpnext --branch version-15

# 3. Create a new site
bench new-site banking.local

# 4. Install ERPNext
bench --site banking.local install-app erpnext

# 5. Get the Banking app
# Option A: From GitHub
bench get-app bizaxl_banking https://github.com/balaji-001-gif/banking

# Option B: From local path
bench get-app bizaxl_banking /path/to/banking

# 6. Install the Banking app
bench --site banking.local install-app bizaxl_banking

# 7. Migrate (apply schema changes)
bench --site banking.local migrate

# 8. Start the development server
bench start
```

### Initial Configuration

After installation, log in as **System Manager** and:

1. **Create State Master**: Go to `Banking State` → Add applicable Indian states with RBI zones
2. **Create Bank Configuration**: Go to `Banking Configuration` → Set Bank Name, License Type, RBI License No, IFSC Prefix, AML Threshold
3. **Create Branches**: Go to `Banking Branch` → Add branches with IFSC codes, link to State
4. **Create Deposit Products**: Go to `Banking Deposit Product` → Add Savings, Current, FD, RD, PPF, SSY products
5. **Create Interest Rate Schedules**: Go to `Banking Interest Rate Schedule` → Configure slab-based rates
6. **Assign Roles**: Go to `User` → Assign `Banking Branch Manager`, `Banking Relationship Manager`, `Banking Teller`, `Banking Credit Officer`, `Banking Compliance Officer`, `Banking Auditor` roles

### Configuring External Integrations

All 8 integrations work out of the box in **simulated mode** (zero configuration needed for development/testing). When you're ready to connect to live services:

1. **Open Banking Integration Settings**: Single doctype accessible via Frappe Awesome Bar or module list
2. **Enable the integration**: Check the enable checkbox for each service you need
3. **Enter credentials**: API keys, secrets, and endpoints from your service provider
4. **Set mode**: Choose Sandbox (test) or Live (production)
5. **Test connection**: Click the "Test" button to verify credentials before saving
6. **Save**: Integrations activate immediately — all wired business logic switches from simulated to live automatically

No code changes or restarts needed. The stub-to-live pattern means you can configure integrations one at a time without affecting others.

---

## Developer Guide

### Adding New Business Logic

Each DocType controller is in its own Python file. To add new logic:

1. Open the appropriate `.py` file in `bizaxl_banking/banking/doctype/<doctype>/`
2. Add new methods to the Document class
3. Common hooks:

```python
class BankingX(Document):
    def autoname(self):          # Auto-naming logic
    def validate(self):          # Validation before save
    def before_submit(self):     # Before submission
    def on_submit(self):         # After submission
    def on_cancel(self):         # After cancellation
    def on_update(self):         # After any save
    def before_save(self):       # Before save
```

### Adding Scheduled Tasks

Edit `hooks.py` and add to `scheduler_events`:

```python
scheduler_events = {
    "daily_long": [
        "bizaxl_banking.banking.doctype.your_doctype.your_module.your_function"
    ],
    "hourly": [...],
    "weekly_long": [...],
    "monthly_long": [...]
}
```

### Adding New Reports

Create a new `.py` file in `bizaxl_banking/banking/reports/` with the standard Frappe report interface:

```python
def execute(filters=None):
    columns = [...]
    data = [...]
    return columns, data
```

The report will auto-register when you run `bench migrate`.

### Naming Series

Custom naming is configured in class `autoname()` methods:

- Banking Customer: `CUST-YYYY-MM-XXXXX`
- Banking Account: `ACC-YYYYMM-XXXXX`
- Banking Payment Order: `PAY-YYYYMM-XXXXX`
- Banking Loan Account: `LOAN-YYYYMM-XXXXX`
- Banking Customer Lead: `LEAD-YYYYMM-XXXXX`
- Banking Bulk Payment: `BULK-YYYYMM-XXXXX`

### Extending Permissions

Permissions are defined in each DocType's `.json` file under the `permissions` array.

### Adding Child Tables

1. Create a new doctype directory with `istable: 1` in JSON
2. Define fields in the child table
3. In the parent doctype JSON, add a field with `fieldtype: "Table"` and `options: "Your Child Table"`
4. Run `bench migrate` to apply schema changes

---

## API Reference

All DocTypes are accessible via Frappe's standard REST API:

### Authentication

```bash
POST /api/method/login
{"usr": "administrator", "pwd": "password"}
```

### Customer APIs

```bash
# Create Customer
POST /api/resource/Banking Customer
{
    "customer_type": "Individual",
    "full_name": "Rahul Sharma",
    "date_of_birth": "1990-01-15",
    "pan_number": "ABCDE1234F",
    "mobile": "9876543210",
    "kyc_status": "Pending",
    "risk_category": "Medium",
    "fatca_status": "Compliant",
    "branch": "MAH-0001"
}

# Get Customer
GET /api/resource/Banking Customer/{name}

# List Customers
GET /api/resource/Banking Customer?filters=[["status","=","Active"]]
```

### Account APIs

```bash
# Create Account
POST /api/resource/Banking Account
{
    "account_number": "ACC-202607-00001",
    "customer": "CUST-2026-07-00001",
    "account_type": "Savings",
    "deposit_product": "Regular Savings",
    "branch": "MAH-0001",
    "current_balance": 10000,
    "available_balance": 10000,
    "account_status": "Active"
}

# Get Balance
GET /api/resource/Banking Account/{name}
```

### Payment APIs

```bash
# Create Payment Order
POST /api/resource/Banking Payment Order
{
    "from_account": "ACC-202607-00001",
    "to_account_no": "1234567890",
    "to_ifsc": "HDFC0001234",
    "payment_rail": "NEFT",
    "amount": 50000,
    "maker": "user@bank.com",
    "checker": "manager@bank.com"
}

# Bulk Payment Upload
POST /api/resource/Banking Bulk Payment
{
    "from_account": "ACC-202607-00001",
    "payment_date": "2026-07-02",
    "uploaded_csv": "/files/bulk_salary.csv"
}
```

### Loan APIs

```bash
# Create Loan Application
POST /api/resource/Banking Loan Application
{
    "applicant": "CUST-2026-07-00001",
    "loan_product": "Personal",
    "requested_amount": 500000,
    "requested_tenure_months": 60,
    "purpose": "Home Renovation",
    "bureau_score": 750,
    "foir": 40,
    "decision": "Approved"
}

# Process Prepayment
POST /api/method/bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.process_prepayment
{
    "prepayment_amount": 50000
}
```

### Lead APIs

```bash
# Create Lead
POST /api/resource/Banking Customer Lead
{
    "full_name": "Priya Patel",
    "customer_type": "Individual",
    "mobile": "9876543210",
    "lead_source": "Referral",
    "product_interest": "Savings Account"
}

# Convert Lead to Customer
POST /api/method/bizaxl_banking.banking.doctype.banking_customer_lead.banking_customer_lead.convert_to_customer
```

### Running Reports

```bash
# Portfolio Summary
GET /api/method/bizaxl_banking.banking.reports.portfolio_summary.execute

# Fraud Dashboard
GET /api/method/bizaxl_banking.banking.reports.fraud_alert_dashboard.execute?filters={"status":"Open"}

# FIU XML Export
GET /api/method/bizaxl_banking.banking.reports.ctr_str_export.generate_fiu_xml
```

### Triggering Scheduler Jobs Manually

```bash
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_npa_tracker.banking_npa_tracker.auto_classify_npa
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.process_all_emis
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_fraud_alert.banking_fraud_alert.auto_detect_fraud
bench --site banking.local execute bizaxl_banking.banking.reconciliation.run_daily_reconciliation
```

---

## Roadmap

### Phase 1: Core Operations (✅ Implemented)
- [x] Foundation: Configuration, Branch, State, Interest Rate Schedules, Service Charges
- [x] CRM: Customer Lead → Customer → KYC → Account
- [x] Payments: Payment Orders (5 rails), Transaction Ledger, Standing Instructions, NACH Mandates
- [x] Lending: Loan Application → Loan Account → EMI → NPA → Collateral
- [x] Risk: Fraud Detection (5 types), AML Screening, Dispute Management, Positive Pay
- [x] Reporting: 12 Report scripts, Regulatory Reports (CTR/STR/CRILC/NPA/PSL)
- [x] Business Logic: Interest calculation, prepayment, floating rate updates, dormant classification
- [x] Automation: 10 daily, 1 weekly, 1 monthly scheduler jobs
- [x] Bulk Operations: Bulk Payment with CSV upload, batch processing
- [x] Reconciliation: Daily balance matching, statement CSV upload

### Phase 2: External Integrations (✅ Implemented)
- [x] NPCI/UPI Rails — `payment_gateways/npci.py` (execute_payment, verify_status)
- [x] Aadhaar eKYC — `kyc/aadhaar.py` (OTP-based eKYC, Offline XML)
- [x] PAN Verification — `kyc/pan.py` (NSDL integration with name/DOB match)
- [x] Credit Bureau — `bureau/cibil.py` (CIBIL/Experian/CRIF score pull & eligibility)
- [x] NACH Mandates — `payment_gateways/nach.py` (register, execute, cancel)
- [x] Sanctions Screening — `compliance/sanctions.py` (OFAC/UN/PEP/FIU-IND)
- [x] SMS/Email/WhatsApp — `notifications/messaging.py` (alerts, reminders, OTP)
- [x] e-Sign/DigiLocker — `kyc/esign.py` (digital signing, document retrieval)
- [x] Central API Key Management — `Banking Integration Settings` (Single doctype, stub-to-live pattern)

### Phase 3: Advanced (Future)
- [ ] Core Banking Integration (T24/Finacle)
- [ ] Mobile banking API
- [ ] Interest rate change engine (MCLR-linked automated updates)
- [ ] Automated provisioning & NPA write-offs
- [ ] Internal credit scoring engine
- [ ] Audit trail & data retention compliance
- [ ] Customer portal (self-service)

---

## License

MIT

---

*For support, contact: you@example.com*
