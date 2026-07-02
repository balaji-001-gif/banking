# Bizaxl Banking — ERPNext Banking Module

A comprehensive banking module for **ERPNext v15+ / Frappe Framework v15** that covers the full lifecycle of retail banking operations — from customer onboarding and KYC, through deposits and payments, to lending, NPA management, fraud detection, and regulatory reporting.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Data Model](#architecture--data-model)
3. [Installation Guide (Developer)](#installation-guide-developer)
4. [Feature Modules & Business Logic](#feature-modules--business-logic)
5. [Scheduler Jobs (Automated Tasks)](#scheduler-jobs-automated-tasks)
6. [Roles & Permissions](#roles--permissions)
7. [End-User SOP (Step-by-Step Workflows)](#end-user-sop-step-by-step-workflows)
8. [Developer Guide](#developer-guide)
9. [API Reference](#api-reference)
10. [Customization & Extending](#customization--extending)
11. [Roadmap](#roadmap)

---

## Overview

Bizaxl Banking is a **full-featured banking operations module** built as a Frappe/ERPNext custom app. It provides:

- **18 Master DocTypes** covering the complete banking domain
- **2 Child Table DocTypes** for joint account holders and loan co-applicants
- **8 Custom Roles** with granular permission matrices
- **Business logic in all controllers** — validation, auto-numbering, interest calculation, EMI processing, NPA classification, fraud detection, and more
- **Scheduled jobs** for daily and monthly automation
- **Regulatory report generation** (CTR, STR, CRILC, NPA Return, Priority Sector)

The module follows Indian banking regulations and RBI guidelines for:
- KYC norms (Aadhaar/PAN/Video KYC)
- NPA classification (SMA-0 → SMA-1 → SMA-2 → Sub-standard → Doubtful → Loss)
- Payment rail limits (UPI/IMPS/NEFT/RTGS)
- AML screening and fraud detection
- Priority Sector Lending (PSL) reporting

---

## Architecture & Data Model

### Entity-Relationship Diagram

```
Banking Configuration (Singleton)
         │
         ▼
Banking Branch ─────────────────────┐
         │                          │
         ▼                          ▼
Banking Customer ◄──── Banking Account
         │                   │       │
         │                   │       ├── Banking Account Joint Holder (child)
         │                   │       │
         ▼                   ▼       └── Banking NACH Mandate
Banking KYC Document    Banking Transaction Ledger
                                │
                                ▼
Banking Payment Order ──── Banking Transaction Ledger
         │
         ├── Maker / Checker (User links)
         └── UTR Number (auto-generated)
                               
Banking Deposit Product ──── Banking Account (product link)

Banking Loan Application ◄──── Banking Customer
         │                      │
         ├── Co-applicants (child table)
         │                      │
         ▼                      ▼
Banking Loan Account ──── Banking NPA Tracker
         │                      │
         ├── Banking Collateral │
         ├── Banking NACH Mandate
         └── EMI → Transaction Ledger

Banking Fraud Alert ──── Banking Account
Banking Dispute Case ──── Banking Customer / Payment Order
Banking AML Screening Log ──── Banking Customer
Banking Regulatory Report (CTR/STR/CRILC/NPA/PSL)
```

### DocTypes at a Glance

| # | DocType | Type | Purpose | Key Logic |
|---|---------|------|---------|-----------|
| 1 | Banking Configuration | Single | Bank-level settings (RBI license, IFSC prefix, AML threshold) | IFSC prefix validation, AML threshold validation |
| 2 | Banking Branch | Master | Branch details, IFSC code | IFSC format validation (4 letters + 0 + 6 alphanumeric) |
| 3 | Banking Customer | Master | Customer profile (Individual/Company/Trust etc.) | Auto-numbering (CUST-YYYY-MM-XXXXX), PAN validation, mobile validation, AML log creation |
| 4 | Banking KYC Document | Master | KYC documents (Aadhaar/PAN/Passport etc.) | Expiry tracking, auto-update customer KYC status on verification |
| 5 | Banking Account | Master | Deposit accounts (Savings/Current/Salary/NRE/NRO/CC/OD) | Auto-numbering (ACC-YYYYMM-XXXXX), balance management, transaction ledger integration |
| 6 | Banking Account Joint Holder | **Child Table** | Joint account holders | Linked to Banking Account via Table field |
| 7 | Banking Deposit Product | Master | Product catalog (Savings/FD/RD/PPF/SSY) | Interest rate validation (0-25%), tenure validation |
| 8 | Banking Payment Order | Master | Payment instructions (UPI/IMPS/NEFT/RTGS/Cheque) | Maker-Checker enforcement, balance check, payment rail limits, UTR generation |
| 9 | Banking Transaction Ledger | Master | Double-entry transaction log | Running balance calculation, account balance sync |
| 10 | Banking Standing Instruction | Master | Recurring payments (EMI/Utility/SIP) | Auto-execution, balance check, pause on failure |
| 11 | Banking NACH Mandate | Master | NACH auto-debit mandates | Amount validation |
| 12 | Banking Loan Application | Master | Loan applications (Personal/MSME/Home/Vehicle/Gold/Agri/Microfinance) | Risk grading (A1→D), FOIR validation, auto-create Loan Account on approval |
| 13 | Banking Loan Co-applicant | **Child Table** | Loan co-applicants | Linked to Banking Loan Application via Table field |
| 14 | Banking Loan Account | Master | Sanctioned loans with EMI schedules | Daily reducing balance interest, EMI processing, NPA tracker creation |
| 15 | Banking Collateral | Master | Collateral against loans (Property/FD/Gold/Stocks etc.) | Lien validation (lien ≤ market value) |
| 16 | Banking NPA Tracker | Master | NPA classification & provisioning | Auto-classification (RBI guidelines), provision calculation |
| 17 | Banking Fraud Alert | Master | Fraud alerts & case management | Auto-detection (velocity breach, high-value), auto-hold |
| 18 | Banking AML Screening Log | Master | AML/sanctions screening records | Match-disposition validation |
| 19 | Banking Dispute Case | Master | Customer dispute resolution | SLA deadline tracking, resolution enforcement |
| 20 | Banking Regulatory Report | Master | Regulatory submissions (CTR/STR/CRILC/NPA/PSL) | Auto-generation from transaction data |

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

1. **Create Bank Configuration**: Go to `Banking Configuration` → Set Bank Name, License Type, RBI License No, IFSC Prefix, AML Threshold
2. **Create Branches**: Go to `Banking Branch` → Add at least one branch with IFSC code
3. **Create Deposit Products**: Go to `Banking Deposit Product` → Add Savings, Current, FD, RD products with interest rates
4. **Assign Roles**: Go to `User` → Assign `Banking Branch Manager`, `Banking Relationship Manager`, `Banking Teller`, `Banking Credit Officer`, `Banking Compliance Officer`, `Banking Auditor` roles to appropriate users

---

## Feature Modules & Business Logic

### 1. Customer Onboarding & KYC

```
Banking Customer ──► Banking KYC Document ──► AML Screening
     │                        │                      │
     │  PAN validation        │  Expiry tracking     │  Match detection
     │  Mobile validation     │  Auto-verify KYC     │  Disposition check
     └────────────────────────┴──────────────────────┘
```

**Validations:**
- PAN format: `ABCDE1234F` (10 characters)
- Mobile: 10-digit Indian mobile (starts with 6-9)
- Auto-numbering: `CUST-YYYY-MM-XXXXX`
- On KYC document verification → auto-updates Customer KYC status to "Verified"
- On KYC verification → creates AML Screening Log with type "Onboarding"

### 2. Account Management

```
Banking Customer ──► Banking Account ──► Banking Transaction Ledger
                         │
                         ├── Joint Holders (child table)
                         └── Nominee
```

**Validations:**
- Auto-numbering: `ACC-YYYYMM-XXXXX`
- Available balance ≤ Current balance
- Date Opened defaults to today
- Balance auto-updates on every Transaction Ledger submission

### 3. Payments (Maker-Checker Workflow)

```
Banking Payment Order
    │
    ├── Draft ──► Pending Approval ──► Approved ──► Submitted ──► Settled
    │                                                              │
    │  Maker: creates                                   UTR auto-generated
    │  Checker: approves                                Balance deducted
    │  Rules: Maker ≠ Checker                           Transaction Ledger entry
    │
    └── Payment Rails: UPI (₹1L), IMPS (₹5L), NEFT (₹50L), RTGS (min ₹2L)
```

**Business Rules:**
- Maker and Checker must be different users
- Checker is required before submission
- Sufficient balance checked before settlement
- Payment rail limits enforced:
  - RTGS: Minimum ₹2,00,000
  - NEFT: Maximum ₹50,00,000
  - UPI: Maximum ₹1,00,000
- UTR number auto-generated on settlement: `UTR{YYYYMMDDHHMMSS}{random}`
- Settlement creates Transaction Ledger entry and debits account

### 4. Loan Lifecycle

```
Loan Application ──► Approval ──► Loan Account ──► EMI Schedule ──► NPA Tracking
      │                                                                 │
      │  Risk grading (A1-D)                              SMA-0 (0-30 DPD)
      │  Bureau score (300-900)                            SMA-1 (31-60 DPD)
      │  FOIR validation (≤70%)                            SMA-2 (61-90 DPD)
      │  Co-applicants (child table)                       Sub-standard (91-180)
      │  Auto-create Loan Account on approval              Doubtful (181-365)
      └── Loan Products: Personal/MSME/Home/Vehicle        Loss (365+ DPD)
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

**Auto-Detection Rules (scheduled daily):**
1. **High-value transactions**: Any Payment Order ≥ ₹10,00,000 triggers a Velocity Breach alert (Risk Score: 65)
2. **Rapid payment attempts**: ≥5 payments from the same account within 1 hour triggers a Velocity Breach alert (Risk Score: 75)
3. **Auto-hold**: If risk score ≥ 80, the account is automatically frozen (status → "Frozen")

### 6. Standing Instructions

- Supports Utility, Loan EMI, Investment, Sweep, and Custom types
- Frequencies: Daily, Weekly, Monthly, Quarterly, Annual
- Auto-executes on due date if sufficient balance
- If insufficient balance → status changes to "Paused" and error is logged
- Auto-completes when end date is reached

### 7. Regulatory Reports

| Report | Source Data | Purpose |
|--------|-------------|---------|
| CTR (Cash Transaction Report) | Transaction Ledger | Cash transactions > ₹10L/day |
| STR (Suspicious Transaction Report) | Fraud Alerts | Confirmed fraud cases |
| CRILC | Loan Accounts ≥ ₹5Cr | Large credit data to RBI |
| NPA Return | NPA Tracker | Sub-standard/Doubtful/Loss accounts |
| Priority Sector | Agri/MSME/Microfinance loans | PSL compliance |

---

## Scheduler Jobs (Automated Tasks)

### Daily Tasks (`daily_long`)

| Function | Purpose | When |
|----------|---------|------|
| `auto_classify_npa()` | Calculate DPD for all loans, classify SMA-0→Loss | Every day |
| `process_due_instructions()` | Execute standing instructions due today | Every day |
| `auto_detect_fraud()` | Check for high-value payments, rapid payment attempts | Every day |
| `process_all_emis()` | Process EMIs for loans where today matches emi_date | Every day |

### Monthly Tasks (`monthly_long`)

| Function | Purpose | When |
|----------|---------|------|
| `post_all_interest()` | Post monthly interest on active/NPA loan accounts | 1st of month |

---

## Roles & Permissions

| Role | Access Scope | Key Permissions |
|------|-------------|-----------------|
| **Banking System Admin** | Full system | Read/Write/Create/Delete on all doctypes |
| **Banking Branch Manager** | Branch-wide | Full CRUD on customers, accounts, loans (branch scope) |
| **Banking Relationship Manager** | Own customers | Create/Edit own records, read-only on others |
| **Banking Credit Officer** | Loan processing | Full CRUD on loan applications, loan accounts |
| **Banking Recovery Officer** | NPA management | Full CRUD on NPA trackers, recovery actions |
| **Banking Compliance Officer** | Regulatory | Full CRUD on AML logs, fraud alerts, regulatory reports |
| **Banking Teller** | Cash counter | Create payment orders, read-only customer data |
| **Banking Auditor** | Read-only | Read-only access to all transactions and reports |

---

## End-User SOP (Step-by-Step Workflows)

### Workflow 1: Customer Onboarding

```
┌─────────────────────────────────────────────────────────────────┐
│                   CUSTOMER ONBOARDING SOP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Banking Configuration                                  │
│  └── Admin sets up bank settings (license, IFSC, AML threshold) │
│                                                                  │
│  Step 2: Banking Branch                                         │
│  └── Admin creates branch(es) with IFSC codes                   │
│                                                                  │
│  Step 3: Banking Customer                                       │
│  └── Relationship Manager creates customer profile              │
│  └── Enters: Full Name, DOB, PAN, Aadhaar, Mobile              │
│  └── Selects: Customer Type, Branch, Risk Category             │
│  └── System auto-generates: CUST-YYYY-MM-XXXXX                 │
│  └── System validates: PAN format, Mobile format               │
│                                                                  │
│  Step 4: Banking KYC Document                                   │
│  └── Upload Aadhaar/PAN/Passport/etc.                          │
│  └── Select verification method: eKYC/Video/Physical           │
│  └── On verification → Customer KYC status = "Verified"        │
│  └── System creates AML Screening Log entry                    │
│                                                                  │
│  Step 5: Banking Account                                        │
│  └── Teller/Relationship Manager creates account               │
│  └── Select account type: Savings/Current/Salary               │
│  └── Link deposit product, add joint holders (child table)     │
│  └── Set nominee                                               │
│  └── System auto-generates: ACC-YYYYMM-XXXXX                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow 2: Payment Processing (Maker-Checker)

```
┌─────────────────────────────────────────────────────────────────┐
│                   PAYMENT PROCESSING SOP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Maker Creates Payment Order                            │
│  └── Select From Account (must have sufficient balance)         │
│  └── Enter To Account No, To IFSC                              │
│  └── Select Payment Rail: UPI/IMPS/NEFT/RTGS/Internal/Cheque   │
│  └── Enter Amount, Narration (optional)                        │
│  └── Set yourself as Maker                                      │
│  └── Status: Draft                                               │
│                                                                  │
│  Step 2: Submit for Approval                                    │
│  └── Set Checker (different user)                               │
│  └── Submit → Status: Pending Approval                          │
│                                                                  │
│  Step 3: Checker Reviews & Approves                             │
│  └── Checker logs in, verifies payment details                 │
│  └── Approves → Status: Submitted                               │
│  └── System auto-processes:                                    │
│      ├── Validates balance                                      │
│      ├── Validates payment rail limits                          │
│      ├── Generates UTR: UTR{timestamp}{random}                  │
│      ├── Dedits account balance                                 │
│      ├── Creates Transaction Ledger entry                       │
│      └── Status: Settled                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow 3: Loan Origination

```
┌─────────────────────────────────────────────────────────────────┐
│                   LOAN ORIGINATION SOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Loan Application                                       │
│  └── Credit Officer creates loan application                   │
│  └── Link Applicant (Banking Customer)                          │
│  └── Select Loan Product: Personal/MSME/Home/Vehicle/Gold/...  │
│  └── Enter Amount, Tenure, Purpose                              │
│  └── Add Co-applicants (child table) if applicable              │
│  └── Enter Bureau Score (300-900)                               │
│  └── Enter FOIR % (must be ≤ 70%)                              │
│  └── System auto-calculates Risk Grade:                         │
│      ├── ≥750: A1 │ ≥700: A2 │ ≥650: B1                       │
│      ├── ≥600: B2 │ ≥500: C  │ <500: D                        │
│                                                                  │
│  Step 2: Credit Assessment                                      │
│  └── Review application details, risk grade                    │
│  └── Set Decision: Approved/Referred/Rejected                  │
│  └── Submit                                                     │
│                                                                  │
│  Step 3: Loan Account Creation (automatic)                     │
│  └── If Approved → System auto-creates Loan Account            │
│  └── Fields auto-populated:                                    │
│      ├── Loan Account No: LOAN-YYYYMM-XXXXX                    │
│      ├── Sanctioned Amount = Requested Amount                   │
│      ├── Interest Rate = 12% (configurable)                     │
│      ├── EMI = Calculated via amortization formula              │
│      ├── EMI Date = 5th of month (default)                      │
│      └── Status: Active                                         │
│                                                                  │
│  Step 4: Collateral (if applicable)                             │
│  └── Create Banking Collateral record                          │
│  └── Link to Loan Account                                       │
│  └── Set Market Value, Valuation Date, Lien Amount             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow 4: NPA Management

```
┌─────────────────────────────────────────────────────────────────┐
│                   NPA MANAGEMENT SOP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Daily (automated by scheduler):                                │
│  └── System calculates DPD for all active loans                │
│  └── Classifies based on DPD:                                   │
│      ├── 0-30 DPD: SMA-0                                        │
│      ├── 31-60 DPD: SMA-1                                       │
│      ├── 61-90 DPD: SMA-2                                       │
│      ├── 91-180: Sub-standard                                   │
│      ├── 181-365: Doubtful                                      │
│      └── 365+: Loss                                              │
│  └── Updates Loan Account status to "NPA" if DPD > 90          │
│  └── Calculates provision amount                                 │
│                                                                  │
│  Manual Actions (Recovery Officer):                             │
│  └── Monitor NPA Tracker for overdue accounts                   │
│  └── Set Recovery Stage: Notice/Legal/Lok Adalat/SARFAESI/DRT   │
│  └── Assign to recovery team member                              │
│  └── Update provision amounts as needed                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow 5: Regulatory Reporting

```
┌─────────────────────────────────────────────────────────────────┐
│                   REGULATORY REPORTING SOP                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Create Regulatory Report                               │
│  └── Compliance Officer creates report                          │
│  └── Select Report Type: CTR/STR/CRILC/NPA Return/PSL          │
│  └── Set Period From / Period To                                │
│                                                                  │
│  Step 2: Generate Report                                        │
│  └── Click "Generate" button                                    │
│  └── System queries relevant data:                              │
│      ├── CTR: Transactions > ₹10L/day from Transaction Ledger   │
│      ├── STR: Confirmed fraud alerts                            │
│      ├── CRILC: Loans with sanction ≥ ₹5Cr                      │
│      ├── NPA Return: Sub-standard/Doubtful/Loss accounts        │
│      └── PSL: Agri/MSME/Microfinance loan portfolio             │
│  └── Status: Generated                                           │
│  └── Download report file                                        │
│                                                                  │
│  Step 3: Submit to Regulator                                    │
│  └── Submitted By: Compliance Officer                           │
│  └── Status: Submitted                                           │
│  └── On regulator acknowledgment: Status → Acknowledged         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

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
    "weekly": [...],
    "monthly_long": [...]
}
```

### Naming Series

Custom naming is configured in hooks.py and class `autoname()` methods:

```python
naming_series = {
    "Banking Customer": "CUST-.YYYY.-.MM.-.#####",
    "Banking Account": "ACC-.YYYYMM.-.#####",
    "Banking Payment Order": "PAY-.YYYYMM.-.#####",
}
```

### Extending Permissions

Permissions are defined in each DocType's `.json` file under the `permissions` array. Add new role entries:

```json
{
    "role": "Banking Custom Role",
    "read": 1,
    "write": 1,
    "create": 1,
    "delete": 0,
    "if_owner": 1,
    "print": 1,
    "email": 1
}
```

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
# Login
POST /api/method/login
{
    "usr": "administrator",
    "pwd": "password"
}
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
    "branch": "BRN-00001"
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
    "branch": "BRN-00001",
    "current_balance": 10000,
    "available_balance": 10000,
    "account_status": "Active"
}

# Get Balance
GET /api/resource/Banking Account/{name}
# Returns: current_balance, available_balance
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
```

### Running Reports

```bash
# Generate Regulatory Report
POST /api/resource/Banking Regulatory Report
{
    "report_type": "CRILC",
    "period_from": "2026-04-01",
    "period_to": "2026-06-30"
}
```

### Triggering Scheduler Jobs Manually

```bash
# Run NPA classification
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_npa_tracker.banking_npa_tracker.auto_classify_npa

# Run EMI processing
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.process_all_emis

# Run fraud detection
bench --site banking.local execute bizaxl_banking.banking.doctype.banking_fraud_alert.banking_fraud_alert.auto_detect_fraud
```

---

## Customization & Extending

### Adding Payment Rail Integrations

The current implementation validates limits and generates UTRs but does not execute against real payment rails (NPCI, sponsor bank). To add real integration:

1. Create a new Python module: `bizaxl_banking/payment_gateways/`
2. Implement API calls for each payment rail (UPI/IMPS/NEFT/RTGS)
3. Call from `BankingPaymentOrder.process_payment()` after validation
4. Update status based on API response

### Adding Credit Bureau Integration

1. Create `bizaxl_banking/bureau/` module
2. Implement CIBIL/Experian/CRIF API calls
3. Call from `BankingLoanApplication.validate()` or a separate API endpoint
4. Update `bureau_score` field with retrieved score

### Adding eKYC Integration

1. Create `bizaxl_banking/kyc/` module
2. Implement UIDAI Aadhaar eKYC or DigiLocker API
3. Call from `BankingKYCDocument` on verification
4. Auto-update verification status based on API response

### Adding Mobile/Email Notifications

1. Edit `hooks.py` and add `doc_events` for relevant triggers
2. Implement notification functions using Frappe's email/SMS integration
3. Example: Send SMS on payment settlement, email on NPA classification

---

## Roadmap

### Phase 1: Core Operations (✅ Implemented)
- [x] Customer onboarding & KYC
- [x] Account management with joint holders
- [x] Payment processing with Maker-Checker
- [x] Loan origination & EMI processing
- [x] NPA classification & provisioning
- [x] Fraud detection & auto-hold
- [x] Standing instruction automation
- [x] Regulatory report generation
- [x] Role-based permissions (8 roles)

### Phase 2: Integrations (Future)
- [ ] Payment rail integration (UPI/IMPS/NEFT/RTGS APIs)
- [ ] Credit bureau integration (CIBIL/Experian)
- [ ] Aadhaar eKYC / DigiLocker integration
- [ ] NACH mandate registration with sponsor bank
- [ ] Email/SMS notifications
- [ ] Account statements (PDF generation)

### Phase 3: Advanced (Future)
- [ ] Interest rate change engine (MCLR-linked)
- [ ] Automated provisioning & NPA write-offs
- [ ] Credit scoring engine (internal scorecard)
- [ ] Mobile banking API
- [ ] Core Banking Integration (T24/Finacle)
- [ ] Audit trail & data retention compliance

---

## License

MIT

---

*For support, contact: you@example.com*
