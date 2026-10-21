#!/usr/bin/env python3
"""Net PSC 6810 ferric chloride obligations from the fiscal-year transaction files."""

from __future__ import annotations

import csv
import io
import os
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

OUT_DIR = Path(os.environ.get("FERRIC_OUT_DIR", "/workspace/output"))
NEEDLE = "FERRIC CHLORIDE"
PSC = "6810"
CENT = Decimal("0.01")
COLUMNS = {
    "recipient_name": ("recipient_name", "Recipient Name"),
    "federal_action_obligation": (
        "federal_action_obligation",
        "Federal Action Obligation",
    ),
    "transaction_description": (
        "transaction_description",
        "Transaction Description",
    ),
    "product_or_service_code": (
        "product_or_service_code",
        "Product or Service Code",
    ),
    "award_id": ("award_id_piid", "Award ID", "piid", "award_id"),
}


def money(value: Decimal) -> str:
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def blank_supplier() -> dict:
    return {
        "net": Decimal("0"),
        "positive": Decimal("0"),
        "count": 0,
        "largest": None,
        "largest_award": "",
        "negatives": [],
    }


def field(row: dict[str, str], key: str) -> str:
    for name in COLUMNS[key]:
        if name in row and row[name] is not None:
            return str(row[name]).strip()
    return ""


def transaction_roots() -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("FERRIC_DATA_DIR")
    if override:
        roots.append(Path(override))
    roots.append(Path("/workspace/data/transactions"))
    roots.append(Path(__file__).resolve().parents[1] / "environment" / "data" / "transactions")
    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        found.append(root)
    if not found:
        raise SystemExit("no transaction files under /workspace/data/transactions")
    return found


def transaction_paths() -> list[Path]:
    found: dict[str, Path] = {}
    for root in transaction_roots():
        for pattern in ("*.csv", "*.xlsx"):
            for path in root.rglob(pattern):
                found.setdefault(path.name, path)
    if not found:
        raise SystemExit("no transaction files under /workspace/data/transactions")
    return [found[name] for name in sorted(found)]


def rows_from_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _column_index(cell_ref: str) -> int:
    letters = "".join(character for character in cell_ref if character.isalpha())
    index = 0
    for character in letters:
        index = index * 26 + ord(character.upper()) - 64
    return index - 1


def _shared_strings(book: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in book.namelist():
        return []
    root = ET.fromstring(book.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall(f"{_XLSX_NS}si"):
        parts = [node.text or "" for node in item.iter(f"{_XLSX_NS}t")]
        strings.append("".join(parts))
    return strings


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        parts = [node.text or "" for node in cell.iter(f"{_XLSX_NS}t")]
        return "".join(parts)
    value = cell.find(f"{_XLSX_NS}v")
    if value is None or value.text is None:
        return ""
    if kind == "s":
        return shared[int(value.text)]
    return value.text


def rows_from_xlsx(path: Path):
    with zipfile.ZipFile(path) as book:
        shared = _shared_strings(book)
        sheets = sorted(name for name in book.namelist() if name.startswith("xl/worksheets/sheet"))
        for sheet_name in sheets:
            root = ET.fromstring(book.read(sheet_name))
            table: list[list[str]] = []
            for row in root.findall(f"{_XLSX_NS}sheetData/{_XLSX_NS}row"):
                values: list[str] = []
                for cell in row.findall(f"{_XLSX_NS}c"):
                    index = _column_index(cell.attrib.get("r", ""))
                    while len(values) <= index:
                        values.append("")
                    values[index] = _cell_text(cell, shared)
                table.append(values)
            if not table:
                continue
            header = [cell.strip() for cell in table[0]]
            if not any(name in header for name in COLUMNS["federal_action_obligation"]):
                continue
            for values in table[1:]:
                row = {
                    name: values[index] if index < len(values) else ""
                    for index, name in enumerate(header)
                    if name
                }
                yield row


def raw_amount(row: dict[str, str]) -> str:
    return field(row, "federal_action_obligation")


def action_date(row: dict[str, str]) -> str:
    return (row.get("action_date") or row.get("Action Date") or "").strip()


def current_total(row: dict[str, str]) -> Decimal | None:
    raw = (
        row.get("current_total_value_of_award")
        or row.get("Current Total Value of Award")
        or ""
    ).strip()
    if raw == "":
        return None
    return Decimal(raw)


def is_bulk(row: dict[str, str]) -> bool:
    if NEEDLE not in field(row, "transaction_description").upper():
        return False
    return field(row, "product_or_service_code") == PSC


def load_rows() -> tuple[list[str], list[dict[str, str]]]:
    paths = transaction_paths()
    rows: list[dict[str, str]] = []
    for path in paths:
        print(f"reading {path.name}", flush=True)
        reader = rows_from_csv(path) if path.suffix.lower() == ".csv" else rows_from_xlsx(path)
        rows.extend(row for row in reader if is_bulk(row) and raw_amount(row) != "")
    return [path.name for path in paths], rows


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    kept: list[dict[str, str]] = []
    for row in rows:
        key = (field(row, "award_id"), action_date(row), money(Decimal(raw_amount(row))))
        if key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept


def requirements_vehicle(rows: list[dict[str, str]]) -> str:
    zeros: dict[str, int] = {}
    for row in rows:
        if Decimal(raw_amount(row)) != 0:
            continue
        award = field(row, "award_id")
        zeros[award] = zeros.get(award, 0) + 1
    if not zeros:
        raise SystemExit("no requirements vehicle")
    return max(zeros, key=lambda award: (zeros[award], award))


def kept_rows(rows: list[dict[str, str]]) -> tuple[str, str, list[str], list[dict[str, str]]]:
    rows = dedupe(rows)
    vehicle = requirements_vehicle(rows)
    start = min(action_date(row) for row in rows if field(row, "award_id") == vehicle)
    candidates = [
        row
        for row in rows
        if field(row, "award_id") != vehicle
        and action_date(row) >= start
        and Decimal(raw_amount(row)) != 0
    ]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in candidates:
        grouped.setdefault(field(row, "award_id"), []).append(row)
    omitted: list[str] = []
    kept: list[dict[str, str]] = []
    for award, group in grouped.items():
        running = Decimal("0")
        reconciled = True
        for row in sorted(group, key=action_date):
            running += Decimal(raw_amount(row))
            balance = current_total(row)
            if balance is None or running != balance:
                reconciled = False
                break
        if not reconciled:
            omitted.append(award)
            continue
        kept.extend(group)
    return vehicle, start, sorted(omitted), kept


def accept(row: dict[str, str], suppliers: dict[str, dict]) -> None:
    amount = Decimal(raw_amount(row))
    supplier = field(row, "recipient_name")
    award = field(row, "award_id")
    slot = suppliers.setdefault(supplier, blank_supplier())
    slot["net"] += amount
    slot["count"] += 1
    if amount > 0:
        slot["positive"] += amount
    elif amount < 0:
        slot["negatives"].append((amount, award))
    if slot["largest"] is None or amount > slot["largest"]:
        slot["largest"] = amount
        slot["largest_award"] = award


def recurring_level(rows: list[dict[str, str]]) -> Decimal:
    counts: dict[str, int] = {}
    for row in rows:
        key = money(Decimal(raw_amount(row)))
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        raise SystemExit("no kept actions")
    chosen = max(counts, key=lambda key: (counts[key], Decimal(key)))
    return Decimal(chosen)


def scan() -> tuple[list[str], str, str, list[str], Decimal, dict[str, str], dict[str, dict]]:
    archives, rows = load_rows()
    vehicle, start, omitted, kept = kept_rows(rows)
    level = recurring_level(kept)
    scored = [row for row in kept if Decimal(raw_amount(row)) <= level]
    outlier = max(kept, key=lambda row: Decimal(raw_amount(row)))
    suppliers: dict[str, dict] = {}
    for row in scored:
        accept(row, suppliers)
    return archives, vehicle, start, omitted, level, outlier, suppliers


def render(
    archives: list[str],
    vehicle: str,
    start: str,
    omitted: list[str],
    level: Decimal,
    outlier: dict[str, str],
    suppliers: dict[str, dict],
) -> tuple[str, str]:
    ranked = sorted(suppliers, key=lambda name: suppliers[name]["net"], reverse=True)
    if len(ranked) < 2:
        raise SystemExit("fewer than two suppliers")
    winner = ranked[0]
    runner = ranked[1]
    win = suppliers[winner]
    run = suppliers[runner]
    gap = win["net"] - run["net"]
    positive_rank = sorted(suppliers, key=lambda name: suppliers[name]["positive"], reverse=True)
    still_winner = positive_rank[0] == winner
    peak_name = field(outlier, "recipient_name")
    peak_amount = Decimal(raw_amount(outlier))
    peak_award = field(outlier, "award_id")

    lines = [
        "# Ferric chloride supply recommendation",
        "",
        "## Recommendation",
        "",
        (
            f"Place the next bulk ferric chloride delivery order with {winner}, "
            f"whose net federal obligation is {money(win['net'])} USD, "
            f"{money(gap)} USD ahead of the next supplier."
        ),
        "",
        "## Evidence",
        "",
        "The contract transaction files that this memo uses are:",
    ]
    for name in archives:
        lines.append(f"- {name}")
    lines.extend(
        [
            "",
            (
                "Those files are the USAspending contract transaction records for "
                "FY2018 through FY2025, snapshot date 2026-09-06."
            ),
            (
                "Bulk ferric chloride is the product whose product or service code "
                "is PSC 6810. Laboratory reagent packages that merely share the "
                "chemical name are outside this requirement. Anhydrous ferric "
                "chloride under PSC 6810 remains in the score."
            ),
            (
                "The dollar measure is federal_action_obligation. A deobligation "
                "is stored as a negative amount and is omitted when the award "
                "current total cannot be rebuilt from the ferric chloride actions."
            ),
            (
                f"The requirements vehicle is {vehicle}. Scored actions begin on "
                f"the first action date of that vehicle, {start}. Zero-dollar "
                "actions are omitted."
            ),
            (
                "The same action can appear twice. Each action is scored once, "
                "matched on award identifier, action date, and federal action obligation."
            ),
            (
                "These awards are left out because an action's current total does "
                "not equal the scored obligations through that action: "
                + ", ".join(omitted)
                + "."
            ),
            (
                f"The recurring order level is {money(level)} USD, the obligation "
                "amount on the greatest number of kept actions. An action above "
                "that level is omitted."
            ),
            "",
            "Suppliers, net obligation in USD, transaction count, and largest transaction:",
            "",
        ]
    )
    for name in ranked:
        slot = suppliers[name]
        lines.append(
            f"- {name}: net {money(slot['net'])} USD, transaction count {slot['count']}; "
            f"largest transaction {money(slot['largest'])} USD"
            + (f" on award {slot['largest_award']}" if slot["largest_award"] else "")
            + "."
        )
    lines.extend(
        [
            "",
            (
                f"The largest single transaction in the set is {money(peak_amount)} USD "
                f"to {peak_name} on award {peak_award}. "
                f"Selecting the supplier from that single transaction would name {peak_name.rstrip('.')}."
            ),
            (
                f"That reading is rejected because {winner} has a net obligation of "
                f"{money(win['net'])} USD and {runner} has a net obligation of "
                f"{money(run['net'])} USD."
            ),
            "",
            "## Risks",
            "",
            (
                "The municipal invitation does not record those obligations."
            ),
            (
                "The archives are the 2026-09-06 USAspending snapshot. "
                "An obligation signed after that date is not in these files."
            ),
            (
                "Dropping the negative obligations would "
                + (
                    f"not replace {winner.rstrip('.')}. The positive-only totals still rank {winner} first."
                    if still_winner
                    else f"replace {winner} with {positive_rank[0]}."
                )
            ),
            "",
        ]
    )
    memo = "\n".join(lines)

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        ["offeror", "net_obligation_usd", "transaction_count", "largest_transaction_usd"]
    )
    for name in ranked:
        slot = suppliers[name]
        writer.writerow([name, money(slot["net"]), str(slot["count"]), money(slot["largest"])])
    return memo, buffer.getvalue()


def main() -> None:
    archives, vehicle, start, omitted, level, outlier, suppliers = scan()
    memo, table = render(archives, vehicle, start, omitted, level, outlier, suppliers)
    destination = OUT_DIR / "analysis"
    destination.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "recommendation.md").write_text(memo, encoding="utf-8")
    (destination / "summary.csv").write_text(table, encoding="utf-8")


if __name__ == "__main__":
    main()
