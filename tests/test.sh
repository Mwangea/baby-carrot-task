#!/usr/bin/env bash
set -uo pipefail

# Verifier entry point — A DETERMINISM GATE, NOT THE GRADED REWARD.
#
# Read this before tuning the formula below. Grading on this platform is
# RUBRIC-ONLY: the number your task is scored on comes from the rubric judge,
# which runs on-platform against your final output files. The float this
# script writes is NOT that number and never enters it.
#
# What it IS for: proving the package is deterministic. The platform runs your
# package twice with no model involved —
#
#   oracle  applies solution/solve.sh first, then runs this script.
#           It must produce EXACTLY 1.0. Anything less means your own gold
#           solution does not satisfy your own checks.
#   nop     does nothing at all, then runs this script.
#           It must produce EXACTLY 0.0. Anything more means doing nothing
#           already scores, which is a task defect.
#
# A MISSING reward file is not a low score — it is a broken PACKAGE, and it
# fails both arms at once. So this script's job is to write a reward every
# time it can honestly compute one, and to fail loudly (no reward file) only
# when it genuinely cannot.
#
# The file contract, pinned by the platform:
#
#   - /logs/verifier/reward.json  {"reward": <float>} — the trial's score.
#     Partial credit is real signal; never round a fraction to 0 or 1.
#   - /logs/verifier/ctrf.json    per-check CTRF results, so a reviewer sees
#     WHICH checks failed, not just the total.
#
# Grade FINAL OUTPUT FILES only. The verifier never reads how the model
# worked, only what it produced.
#
# NO NETWORK. The verifier phase runs with networking denied, so everything
# this script calls must already be in the environment image. pytest and the
# CTRF plugin are installed by environment/Dockerfile for exactly that reason;
# do not reintroduce a fetch-at-run-time tool such as uvx here.
#
# Note the missing `-e`: it is deliberate. pytest exits 1 when a check fails,
# and a failing check is an ORDINARY outcome this script must go on to score.
# Each failure mode below is therefore handled explicitly.

mkdir -p /logs/verifier

python3 -m pytest --ctrf /logs/verifier/ctrf.json -rA /tests/test_outputs.py
pytest_status=$?

# pytest exit codes: 0 = every check passed, 1 = some check failed. Both are a
# real RUN with a real verdict, and both must be scored. Anything above 1
# (2 interrupted, 3 internal error, 4 usage error, 5 nothing collected) means
# the suite never expressed a verdict at all — scoring that as 0.0 would tell
# the platform "the model earned nothing" when the truth is "the verifier did
# not run". Leave reward.json unwritten so the run is reported as a broken
# package, and say why on stderr.
if [ "${pytest_status}" -gt 1 ]; then
  echo "test.sh: pytest exited ${pytest_status} — the suite never produced a verdict" \
       "(2=interrupted, 3=internal, 4=usage, 5=nothing collected). No reward written." >&2
  exit "${pytest_status}"
fi

if [ ! -s /logs/verifier/ctrf.json ]; then
  echo "test.sh: pytest exited ${pytest_status} but wrote no CTRF report at" \
       "/logs/verifier/ctrf.json. The pytest-json-ctrf plugin is missing from the" \
       "environment image, or --ctrf was rejected. No reward written." >&2
  exit 1
fi

# Stub scoring: equal weight per check, as a float fraction. Replace with the
# weighting your checks deserve — the shape (a float written to reward.json)
# is the contract, the formula is yours. Whatever you write it as, keep the
# two endpoints exact: all checks passing must give 1.0, none passing 0.0.
python3 - <<'PY'
import json
import sys

CTRF = "/logs/verifier/ctrf.json"
REWARD = "/logs/verifier/reward.json"

try:
    with open(CTRF) as fh:
        summary = json.load(fh)["results"]["summary"]
except (OSError, ValueError, KeyError, TypeError) as exc:
    sys.exit(f"test.sh: {CTRF} is not a readable CTRF report ({exc!r}). No reward written.")

total = summary.get("tests")
passed = summary.get("passed")
if not isinstance(total, int) or not isinstance(passed, int):
    sys.exit(
        f"test.sh: {CTRF} summary is missing integer 'tests'/'passed' "
        f"(got tests={total!r}, passed={passed!r}). No reward written."
    )
if total <= 0:
    # Not a zero — an empty suite. Scoring it 0.0 would blame the model for a
    # verifier that collected nothing, and would make the nop arm pass for the
    # wrong reason.
    sys.exit(f"test.sh: {CTRF} reports {total} tests collected. No reward written.")

reward = passed / total
with open(REWARD, "w") as fh:
    json.dump({"reward": round(reward, 6)}, fh)
print(f"test.sh: {passed}/{total} checks passed -> reward {reward}")
PY
