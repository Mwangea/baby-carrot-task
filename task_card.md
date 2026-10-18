# Task description

A contracting officer must place the next bulk ferric chloride delivery order with one supplier. The inputs are the FY2018 through FY2025 USAspending ferric chloride transaction records, split across comma-delimited files and spreadsheets, the USAspending data dictionary and analyst guide, an office scoring standard, and a municipal invitation for the same chemical. The decision follows the scoring standard: obligations on or after the requirements vehicle's first action date, with an award kept only when each action's current total matches the obligations through that action, and with a repeated action counted once.

# Complexity justification

The rows that decide the award are split across fiscal-year comma-delimited files and spreadsheets, and those files also contain laboratory packages, repeated actions, and award-total columns. The dictionary distinguishes a transaction obligation, which can be negative, from award totals that repeat on every modification. One fiscal-year file lists the same action twice. The requirements vehicle is a run of zero-dollar modifications, and actions before its first date are history. An award drops out when an earlier action's current total does not match the obligations through that date. The single largest transaction belongs to a different supplier from the supplier with the largest net. A municipal bid document for the same chemical does not record federal obligations.

# Taxonomy tags

Analytical objectives: Data Quality, Monitoring & Alerting. Reasoning phases: explore, hypothesize, analyze, synthesize, recommend.

# Expected difficulty range

Hard. The likely miss is summing every ferric chloride obligation from FY2018 through FY2025, keeping an award whose earlier current total does not match the running obligations, or counting a repeated action a second time.

# Ground truth recommendation and rationale

Award the next order to VETERAN CHEMICALS, INC. After the scoring standard, the net federal action obligation is 461107.00 USD across 18 transactions. The requirements vehicle is W911KF20D0006 and its first action date is 2020-05-19. Awards W911KF20F0155 and W911SA22F1006 are omitted because an earlier current total does not match the obligations through that action. Award W911SA23F1000 is omitted because its deobligation does not rebuild the current total. The next supplier, MARTELLE WATER TREATMENT, INC., nets 82540.00 USD across 1 transaction, a gap of 378567.00 USD. That transaction is award W911SA25F1001. HILL BROTHERS CHEMICAL COMPANY nets 24076.92 USD. ASRC FEDERAL FACILITIES LOGISTICS, LLC nets 197.75 USD. Selecting the supplier from the single largest transaction names Martelle.

# Expected reasoning trajectory

Read the scoring standard, then the dictionary, and identify the transaction obligation field, the action date, the current award total, and the product or service code. Restrict the scan to product code 6810 and to descriptions that name ferric chloride, and keep anhydrous rows that stay on that code. Collapse rows that repeat the same award, date, and obligation. Identify the requirements vehicle as the award with the greatest number of zero-dollar actions, and keep actions on or after its first action date. Drop zero-dollar actions. Drop an award when any scored action's current total does not equal the obligations on that award through that action. Rank suppliers by the remaining net. Reject the largest-single-transaction rule because it names a different supplier. State the snapshot date as a limit on later modifications. Write one memo and the summary table from the same totals.
