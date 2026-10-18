"""Determinism checks over the final output files.

Oracle (solution applied) must pass every test. Nop (no files) must fail every test.
"""

import csv
import re
from decimal import Decimal
from pathlib import Path

_CONTAINER_OUTPUT_DIR = Path("/workspace/output")
_STAGED_OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR = _CONTAINER_OUTPUT_DIR if _CONTAINER_OUTPUT_DIR.is_dir() else _STAGED_OUTPUT_DIR

RECOMMENDATION_MD = OUTPUT_DIR / "recommendation.md"
SUMMARY_CSV = OUTPUT_DIR / "analysis" / "summary.csv"

EXPECTED_ROWS = [
    ("VETERAN CHEMICALS, INC.", "461107.00", "18", "34559.00"),
    ("MARTELLE WATER TREATMENT, INC.", "82540.00", "1", "82540.00"),
    ("HILL BROTHERS CHEMICAL COMPANY", "24076.92", "1", "24076.92"),
    ("ASRC FEDERAL FACILITIES LOGISTICS, LLC", "197.75", "1", "197.75"),
]
TWO_DECIMALS = re.compile(r"^-?\d+\.\d{2}$")
HEADINGS = ("Recommendation", "Evidence", "Risks")


def _heading_at(text: str, name: str) -> int:
    match = re.search(rf"(?m)^#{{1,6}}[ \t]+{re.escape(name)}[ \t]*$", text)
    assert match is not None
    return match.start()


def _amount_in_text(text: str, raw: str) -> None:
    target = f"{Decimal(raw).quantize(Decimal('0.01')):.2f}"
    compact = text.replace("$", "").replace(",", "").replace(" ", "")
    assert target in compact


def test_memo_names_the_leader_and_the_gap() -> None:
    """The Recommendation section names one supplier and states the net and the gap in USD."""
    assert RECOMMENDATION_MD.is_file(), f"no memo at {RECOMMENDATION_MD}"
    assert SUMMARY_CSV.is_file(), f"no summary at {SUMMARY_CSV}"
    text = RECOMMENDATION_MD.read_text(encoding="utf-8")
    starts = [_heading_at(text, name) for name in HEADINGS]
    assert starts == sorted(starts)
    recommendation = text[starts[0] : starts[1]]
    with SUMMARY_CSV.open(encoding="utf-8", newline="") as handle:
        body = list(csv.reader(handle))[1:]
    winner = body[0][0]
    assert winner in recommendation
    for row in body[1:]:
        assert row[0] not in recommendation
    assert "USD" in recommendation or "$" in recommendation
    _amount_in_text(recommendation, body[0][1])
    gap = Decimal(body[0][1]) - Decimal(body[1][1])
    _amount_in_text(recommendation, format(gap, "f"))
    net = f"{Decimal(body[0][1]).quantize(Decimal('0.01')):.2f}"
    paragraphs = [block for block in recommendation.split("\n\n") if block.strip()]
    assert any(
        winner in block and net in block.replace("$", "").replace(",", "").replace(" ", "")
        for block in paragraphs
    )


def test_summary_lists_the_scored_suppliers() -> None:
    """The summary table matches the net obligations from the scoring standard."""
    assert SUMMARY_CSV.is_file(), f"no summary at {SUMMARY_CSV}"
    with SUMMARY_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows
    assert rows[0] == [
        "offeror",
        "net_obligation_usd",
        "transaction_count",
        "largest_transaction_usd",
    ]
    body = rows[1:]
    assert len(body) == len(EXPECTED_ROWS)
    for got, expected in zip(body, EXPECTED_ROWS):
        assert tuple(got) == expected
        assert TWO_DECIMALS.match(got[1])
        assert TWO_DECIMALS.match(got[3])
    nets = [Decimal(row[1]) for row in body]
    assert nets == sorted(nets, reverse=True)
