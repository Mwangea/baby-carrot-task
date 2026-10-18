#!/usr/bin/env python3
"""Print the text of a PDF or the rows of an xlsx workbook."""

from __future__ import annotations

import csv
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _column_index(cell_ref: str) -> int:
    letters = "".join(character for character in cell_ref if character.isalpha())
    index = 0
    for character in letters:
        index = index * 26 + ord(character.upper()) - 64
    return max(index - 1, 0)


def _pdf_text(path: Path) -> None:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    for page in reader.pages:
        print(page.extract_text() or "")


def _xlsx_rows(path: Path) -> None:
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{_NS}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{_NS}t")))
        sheets = sorted(name for name in book.namelist() if name.startswith("xl/worksheets/sheet"))
        writer = csv.writer(sys.stdout, lineterminator="\n")
        for sheet_name in sheets:
            root = ET.fromstring(book.read(sheet_name))
            for row in root.findall(f"{_NS}sheetData/{_NS}row"):
                values: list[str] = []
                for cell in row.findall(f"{_NS}c"):
                    index = _column_index(cell.attrib.get("r", ""))
                    while len(values) <= index:
                        values.append("")
                    kind = cell.attrib.get("t")
                    if kind == "inlineStr":
                        values[index] = "".join(node.text or "" for node in cell.iter(f"{_NS}t"))
                        continue
                    value = cell.find(f"{_NS}v")
                    if value is None or value.text is None:
                        values[index] = ""
                    elif kind == "s":
                        values[index] = shared[int(value.text)]
                    else:
                        values[index] = value.text
                writer.writerow(values)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: read_records.py <file.pdf|file.xlsx>")
    path = Path(sys.argv[1])
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        _pdf_text(path)
    elif suffix == ".xlsx":
        _xlsx_rows(path)
    else:
        raise SystemExit("pass a .pdf or .xlsx file")


if __name__ == "__main__":
    main()
