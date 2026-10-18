# Gold solution

`solve.sh` runs `analyze.py`, which reads the FY2018–FY2025 transaction files and writes the memo and summary. `gold.patch` is the diff of those files and must match what `solve.sh` writes.

- `gold.patch` — unified diff (git diff format) from the fresh workspace to
  the solved state. This is the artifact reviewers read; keep it exactly in
  sync with what `solve.sh` produces.
- `solve.sh` — deterministic script that materializes the gold outputs in a
  fresh environment. The oracle run executes it and must earn exactly 1.0
  from `tests/test.sh`; the nop run (no action taken) must earn exactly 0.0.

Requirements:

- The final recommendation is DETERMINISTIC: anyone re-running the analysis
  on the input data reaches the same figures and the same position.
- Produce every output file the instruction asks for, at the exact paths the
  verifier and rubric grade.
- Nothing under `solution/` may be visible to the model: never COPY this
  directory into the environment image.

## The local check ladder

Run these from the task directory, in order. Each rung tells you something the
next one assumes, so a failure low down makes everything above it meaningless.
No model and no API key is involved in any of them.

Install the CLI first — [harbor](https://harborframework.com/docs)
(`uv tool install harbor`) and Docker. The platform grades with harbor 0.18.0;
pin the same version locally if your results and ours disagree.

1. `docker build environment/`
   The FROM line ships a REAL `python:3.12-slim` digest, so the unmodified
   template builds as-is. Keep the digest pinned: swap the base image only by
   pasting another real `@sha256:` digest, never a tag. Nothing below can run
   before this passes.

2. `harbor run -p . -a nop`
   Must report EXACTLY 0.0. Any other number — including a missing reward,
   which is reported as a broken package rather than as a score — is a defect
   in the package, not a low score.

3. `harbor run -p . -a oracle`
   Must report EXACTLY 1.0. Less than 1.0 means your own gold solution does
   not satisfy your own checks in `tests/test_outputs.py`.

4. `python -m pytest tests/test_outputs.py`, with the gold output tree staged
   beside it as `tests/output/`.
   This is the exact invocation the platform's grading runner makes, and it
   runs the checks WITHOUT `tests/test.sh`. A suite that only works through
   test.sh will not work there.

5. Re-read `tests/README.md` and confirm every rubric number it lists.

## What these checks do NOT tell you

They are a package-integrity gate. They say the package builds, is
deterministic, and has a gold solution that satisfies its own checks. They say
NOTHING about whether the task will be accepted.

Grading is RUBRIC-ONLY: the score your task earns comes from a judge reading
your rubric against the final output files, on-platform, after you submit. The
float in step 2 and step 3 never enters it.

Everything below runs only after submission and cannot be reproduced locally:
rubric judging, task quality review, similarity against the existing task set,
the automated audit, instruction-following coverage, and the model sweeps. A
package that passes every rung above can still be returned by any one of them.
