"""Copy ferric-chloride rows out of the contract zips into one CSV per fiscal year."""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path

ROOT = Path(r"c:\Users\MUSA\PROJECTS\Baby Crarrot\baby-carrot-task")
SOURCE = ROOT / "environment" / "data" / "usaspending"
DEST = ROOT / "environment" / "data" / "transactions"
KEEP = [
    "recipient_name",
    "federal_action_obligation", 
    "current_total_value_of_award",
    "potential_total_value_of_award",
    "transaction_description",
    "product_or_service_code",
    "award_id_piid",
    "piid",
    "award_id",
    "action_date",
]


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    writers: dict[str, csv.writer] = {}
    handles: dict[str, object] = {}
    counts: dict[str, int] = {}
    psc_counts: dict[str, int] = {}
    for path in sorted(SOURCE.glob("FY*_All_Contracts_Full_*.zip")):
        fiscal = path.name.split("_", 1)[0]
        print(f"scanning {path.name}", flush=True)
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.lower().endswith(".csv"):
                    continue
                with archive.open(member) as raw:
                    harvest(raw, fiscal, writers, handles, counts, psc_counts)
    for handle in handles.values():
        handle.close()
    print("rows", counts, flush=True)
    print("psc", psc_counts, flush=True)


def harvest(raw, fiscal, writers, handles, counts, psc_counts) -> None:
    header_line = raw.readline()
    if not header_line:
        return
    header = next(csv.reader([header_line.decode("utf-8-sig")]))
    index = {name: pos for pos, name in enumerate(header)}
    description_at = index.get("transaction_description")
    psc_at = index.get("product_or_service_code")
    if description_at is None or psc_at is None:
        return
    kept = [name for name in KEEP if name in index]
    if fiscal not in writers:
        handle = (DEST / f"{fiscal}_ferric_rows.csv").open("w", encoding="utf-8", newline="")
        handles[fiscal] = handle
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(kept)
        writers[fiscal] = writer
        counts[fiscal] = 0
    writer = writers[fiscal]
    positions = [index[name] for name in kept]
    tail = b""

    def take(block: bytes, final: bool) -> None:
        nonlocal tail
        data = tail + block
        if not final:
            split = data.rfind(b"\n")
            if split < 0:
                tail = data[-80:]
                return
            tail = data[split + 1 :]
            data = data[:split]
        else:
            tail = b""
        if b"FERRIC" not in data and b"ferric" not in data and b"Ferric" not in data:
            return
        for line in data.splitlines():
            if b"FERRIC" not in line and b"ferric" not in line and b"Ferric" not in line:
                continue
            accept(line)

    def accept(line: bytes) -> None:
        fields = next(csv.reader([line.decode("utf-8")]))
        if len(fields) <= description_at:
            return
        if "FERRIC CHLORIDE" not in fields[description_at].upper():
            return
        psc = fields[psc_at].strip() if psc_at < len(fields) else ""
        psc_counts[psc] = psc_counts.get(psc, 0) + 1
        writer.writerow([(fields[pos] if pos < len(fields) else "") for pos in positions])
        counts[fiscal] += 1

    while True:
        chunk = raw.read(8 << 20)
        if not chunk:
            take(b"", True)
            break
        take(chunk, False)


if __name__ == "__main__":
    main()
