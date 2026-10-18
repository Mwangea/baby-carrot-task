# Before you submit

Two lists. The first is what you can genuinely check yourself. The second is
what you cannot, and must not assume.

## 1. Checks you CAN run locally — and that predict our pipeline

No model, no API key, no platform account. Install
[harbor](https://harborframework.com/docs) (`uv tool install harbor`) and
Docker first; the platform grades with harbor 0.18.0.

- [ ] `docker build environment/` succeeds.
      The template ships a REAL pinned digest on the FROM line, so this passes
      unmodified. If you change the base image, pin the replacement by
      `@sha256:` digest too — a tag is rejected at intake.
- [ ] `harbor run -p . -a nop` reports EXACTLY 0.0.
      A missing reward is not a zero — it is reported as a broken package.
- [ ] `harbor run -p . -a oracle` reports EXACTLY 1.0.
      Below 1.0 means your gold solution fails your own checks.
- [ ] `python -m pytest tests/test_outputs.py` passes against the gold output
      tree staged as `tests/output/`.
      This mirrors the grading runner's own invocation, which never executes
      `tests/test.sh`.

### Rubric numbers to verify in rubrics.json

Every one of these is enforced at finalize. A rubric that misses any of them
is refused, naming the rule.

- [ ] At least 25 criteria. The MAXIMUM is an admin-configured bound, not a
      number you can read off documentation — the rubric editor reports the
      live value, and it is the only authority. Do not author against a
      ceiling copied from anywhere, this file included.
- [ ] At least 3 criteria carry `category: "recommend"`.
- [ ] Positive weights sum to EXACTLY 100.
- [ ] No single criterion carries more than 20% of the pooled positive weight
      (the pool includes the positive weights in tests/test_weights.json).
- [ ] At least 3 positive-weight recommend criteria carry 30 to 50 of those 100 points, and none carries more than 20.
- [ ] instruction_following criteria carry 1-10 positive points.
- [ ] Every penalty weight is between -8 and -2, and the penalties together
      sum to -30 or higher.
- [ ] Criterion text is 20-250 characters.
- [ ] Every criterion names at least one `grades_output_files` glob. The judge
      sees only final output files, so a criterion that names none grades
      nothing.
- [ ] The positive weights in tests/test_weights.json carry at most 10% of the
      pooled positive weight. With the rubric pinned to exactly 100, that caps
      this file at 11 positive points.
- [ ] No criterion asks the judge to consult something it cannot see — a
      ground truth, a reference answer, the task card, the prompt. The judge
      reads the output files and nothing else.
- [ ] No criterion is a matter of degree. Each states one fact that is
      present or absent.

The decision-pool SHARE the rubric editor displays is a reported statistic. It
gates nothing; the two rules that do are the decision-criteria count and the
recommend-category point budget above.

## 2. What you CANNOT check locally

These run only after you submit. Nothing above validates any of them, and a
package that passes every box above can still be returned by any one:

- rubric judging — the actual graded reward, which is rubric-only;
- task quality review;
- similarity against the existing task set and against your own earlier tasks;
- the automated audit;
- instruction-following coverage;
- the model sweeps.

The verifier float in `tests/test.sh` is a determinism gate for the nop and
oracle arms. It is NOT the graded reward and never enters it.
