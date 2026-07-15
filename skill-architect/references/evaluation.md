# Evaluation

Use this reference for audits, trigger tuning, functional tests, version comparisons, and evidence-based refinement.

## Define the claim first

State the criteria the evaluation must prove and at least one anti-criterion that catches a false positive or regression. Choose the lightest procedure that can credibly test those claims; do not build a benchmark system merely because the skill may be reused.

Evaluate three separate layers:

1. **Structure:** the package and frontmatter are valid for the target runtime.
2. **Triggering:** the skill loads for intended requests and stays quiet for near-misses.
3. **Function:** the workflow produces the required result, respects guardrails, and fails safely.

Structural validation does not prove good triggering or behavior.

## Validate structure

Check directly:

- `SKILL.md` exists with valid frontmatter and a non-empty body
- required fields, types, syntax, and limits match the target runtime
- referenced files exist and instructions do not advertise deleted interfaces
- scripts parse and execute against representative safe inputs
- generated artifacts contain no placeholders, dead links, or speculative files

Use the bundled validator for the portable core when PyYAML is already available:

```bash
uv run skill-architect/scripts/quick_validate.py <skill-directory>
```

Then use the target runtime's own validator or observed loading behavior for extensions the portable validator intentionally rejects.

## Test trigger boundaries

Use realistic prompts from each category:

- obvious request using expected language
- paraphrased request using different language
- indirect request where the need is present but the skill is not named
- ambiguous boundary case
- competitive near-miss sharing vocabulary but requiring another workflow

Description tuning must improve intent recognition, not memorize the test set. Watch for both undertriggering and overtriggering. Hold out at least one paraphrase or near-miss when iterating so a keyword-heavy description cannot appear successful by overfitting.

## Test representative behavior

Include:

- a normal functional request
- a meaningful edge case
- a failure path such as missing input, unavailable tool, invalid artifact, or unsafe action
- a safety or preservation case when the skill transforms facts or can change state

Inspect the resulting files, command output, tool behavior, and visible result. Do not accept a transcript's claim that an artifact is correct without opening or validating it. Assertions must discriminate success from superficial compliance; a file existing or a keyword appearing is rarely enough.

Use human review for taste, clarity, pedagogy, strategy, and other subjective outcomes. A fixed numeric rubric is useful only when its dimensions are meaningful to this task and reviewers can apply them consistently.

## Choose an honest baseline

| Change | Baseline |
|---|---|
| New skill | Identical request with no skill |
| Skill refactor | Prior version of the skill |
| Description-only change | Prior description |
| Runtime adapter | Portable core without the adapter |

Run both sides with identical prompts, inputs, permissions, and relevant model/runtime settings in fresh contexts. Keep the old artifact unchanged for the comparison. If those conditions cannot be controlled, label the result as directional rather than definitive.

Compare outcomes that matter to the stated claim, such as:

- requirement and safety coverage
- false positive and false negative triggers
- correctness of produced artifacts
- unnecessary questions, tool calls, or files
- irrelevant reference loading and ritual steps
- unsupported claims or invented runtime behavior
- user corrections required

Blind the reviewer to version labels when subjective outputs are close and doing so is practical.

## Diagnose before editing

Classify each observed failure:

- **Routing:** description misses intent or competes with a neighboring skill.
- **Instruction:** the core workflow is absent, ambiguous, or over-constrained.
- **Placement:** required guidance is hidden in an unloaded reference, or branch-specific detail bloats every run.
- **Tooling:** a deterministic step is unreliable, unavailable, or insufficiently validated.
- **Evaluation:** the prompt, assertion, or baseline does not test the actual claim.

Make the smallest change likely to fix the class of failure. Generalize from the cause, not the exact wording of one prompt. Re-run the failed case plus a near-miss and an unaffected regression case.

## Stop and report

Stop when all required criteria pass, anti-criteria do not occur, and another change is unlikely to produce meaningful improvement. Do not keep adding rules because an outcome could theoretically be better.

Report:

- criteria and anti-criteria with pass, fail, or unverified status
- prompts and baselines used
- inspected artifacts and executed checks
- observed regressions and improvements
- subjective judgments separately from objective checks
- runtime assumptions, uncontrolled variables, and skipped cases

Never claim a benchmark, packaging format, trigger rate, or behavioral improvement that was not actually executed and observed.
