# Bizaxl Banking

Schema-level Frappe custom app scaffold, generated from a Banking App Module
spec, targeting **ERPNext v15+ / Frappe Framework v15**.

## What this IS

- 18 DocTypes with fields, types, and required flags transcribed from the spec.
- All custom doctypes are prefixed `Banking ` to avoid name collisions with
  ERPNext's own core doctypes (ERPNext already ships `Customer`,
  `Bank Account`, `Payment Order`, and `Loan Application` -- using those
  names as-is would break `bench migrate`).
- 8 custom Roles matching the spec's permission matrix, exported as a
  fixture (`fixtures/role.json`).
- A role-based permission matrix applied to the 8 doctypes the spec's
  permission table covers (Customer, KYC Document, Account, Payment Order,
  Loan Application, Loan Account, Fraud Alert, Regulatory Report). All other
  doctypes default to System Manager only -- add roles as you see fit.
- Controller stubs (`class X(Document): pass`) for every doctype, ready for
  you to add validation/business logic.

## What this is NOT

- **No payment rail integration.** UPI/IMPS/NEFT/RTGS execution against
  NPCI or a sponsor bank API is not implemented -- `payment_rail` and
  `status` are just Select fields you update yourself or via code you add.
- **No credit bureau integration** (CIBIL/Experian/CRIF). `bureau_score`
  is a plain Int field.
- **No eKYC/UIDAI, DigiLocker, or e-Sign integration.**
- **No NACH mandate registration with a sponsor bank** -- `Banking NACH
  Mandate` just stores a reference number.
- **No interest accrual, EMI calculation, or NPA auto-classification
  logic.** These need scheduled jobs (`hooks.py` -> `scheduler_events`)
  that this scaffold does not include.
- **No maker-checker workflow engine.** `maker`/`checker` fields exist on
  `Banking Payment Order`, but there's no enforced approval workflow --
  add a Frappe Workflow or server-side validation for that.
- **No AML/sanctions-list screening logic** -- `Banking AML Screening Log`
  is a log table you'd populate from your own screening job/API.
- Child tables (joint holders, co-applicants) were flattened to a
  `Small Text` notes field to keep this scaffold simple. If you need real
  child tables, create separate `istable: 1` doctypes and swap the field
  type to `Table`.
- Doctype JSONs reference ERPNext core `Currency`, `Bank`, and `User` as
  Link targets, so this app expects **ERPNext installed alongside it**
  (see `required_apps` in `hooks.py`). If you're on plain Frappe without
  ERPNext, edit those Link options.

## DocTypes included

- **Banking Configuration**
- **Banking Branch**
- **Banking Customer**
- **Banking KYC Document**
- **Banking Account**
- **Banking Deposit Product**
- **Banking Payment Order**
- **Banking Transaction Ledger**
- **Banking Standing Instruction**
- **Banking NACH Mandate**
- **Banking Loan Application**
- **Banking Loan Account**
- **Banking Collateral**
- **Banking NPA Tracker**
- **Banking Fraud Alert**
- **Banking AML Screening Log**
- **Banking Dispute Case**
- **Banking Regulatory Report**

## Install (ERPNext v15+, using `bench`)

```bash
# from your bench directory
bench get-app bizaxl_banking /path/to/unzipped/bizaxl_banking
bench --site your-site.local install-app bizaxl_banking
bench --site your-site.local migrate
```

If you're not using an existing bench, initialise one first:

```bash
bench init frappe-bench --frappe-branch version-15
cd frappe-bench
bench get-app erpnext --branch version-15
bench new-site your-site.local
bench --site your-site.local install-app erpnext
bench get-app bizaxl_banking /path/to/unzipped/bizaxl_banking
bench --site your-site.local install-app bizaxl_banking
```

## Suggested next steps, roughly in order

1. Review every DocType JSON against your actual regulatory/product
   requirements -- this is a transcription of a spec document, not a
   reviewed banking data model.
2. Add real child tables for joint holders / co-applicants if needed.
3. Add a Frappe Workflow (or server-side hooks) for the Payment Order
   maker-checker flow.
4. Add scheduled jobs for interest accrual, EMI posting, and NPA
   reclassification (`hooks.py` -> `scheduler_events`).
5. Wire up whichever payment rail / bureau / eKYC / AML integrations you
   actually have credentials and agreements for -- one at a time, tested
   against sandbox endpoints before anything touches real money.
6. Get this reviewed by someone who has shipped a regulated banking
   product before you go anywhere near production data.
