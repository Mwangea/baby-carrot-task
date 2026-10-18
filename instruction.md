# Next bulk ferric chloride order

You are advising the contracting officer who buys bulk ferric chloride for a federal installation.

The office will place the next delivery order with one supplier. The incumbents and the other sellers show up in the transaction records. A municipal invitation for the same chemical is in the folder as well. Laboratory reagent packages that merely share the chemical name are outside this requirement.

The data dictionary is `/workspace/data/reference/Data_Dictionary_Crosswalk.xlsx`. The analyst guide is `/workspace/data/reference/analyst-guide-download.pdf`. The office scoring standard is `/workspace/data/reference/scoring-standard.txt`. The municipal invitation is `/workspace/data/correspondence/19000-016.0-bid-document.pdf`. The contract transaction records are the FY2018 through FY2025 files under `/workspace/data/transactions`, in `.csv` and `.xlsx`. PDF and Excel reading is installed in this environment: run `python /workspace/tools/read_records.py` on a `.pdf` or `.xlsx` file. The packages `pypdf` and `openpyxl` are installed as well.

Using those records:

1. Decide which supplier should receive the next bulk ferric chloride delivery order. The scoring standard decides which transactions count and which dollar field measures what the government actually obligated. The municipal invitation does not record those obligations.
2. Take one position. Support it with figures you calculated from the records.

Write these files under `/workspace/output/`:

- `recommendation.md` — a decision memo for the contracting officer, in Markdown. Use these headings, in this order: `Recommendation`, `Evidence`, `Risks`. The Recommendation section names exactly one supplier, that supplier's net obligation in USD to the cent, and the gap versus the next supplier in USD to the cent. Use each supplier's name as it appears in the transaction records. State amounts in USD. A dollar sign or a thousands separator is acceptable. Do not write a second memo.
- `analysis/summary.csv` — a comma-delimited table. The first line is the header, with no blank line before it. The columns are exactly `offeror`, `net_obligation_usd`, `transaction_count`, `largest_transaction_usd`. Include one row for every supplier that sold bulk ferric chloride in the transaction records. `net_obligation_usd` and `largest_transaction_usd` are decimal numbers with two digits after the decimal point. Sort the rows by `net_obligation_usd` from largest to smallest.

Do not leave placeholder or debug text in either file.
