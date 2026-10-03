# Eval

**You own the experiment design. Plan, blind, run, synthesize.**

**Non-negotiables for blinding:**

- No `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, or `arena` in any directory, file, or prompt the candidate sees.
- The candidate prompt looks like an organic user request. State the goal, not the meta.
- No chain-eliciting cues. Don't ask the candidate to list which skills, principles, or files they applied. Ask for design notes generally and grade chain-following from the work's shape, not self-report.
- Sanitize directory and slug names. Use project-shaped names a user might pick.
- Don't tell the candidate other candidates exist.
- The judge can know it's judging but sees outputs by sanitized label only, never by model or variant name.
- Comparing two variants: one judge scores both sets in a single pass on one scale, blind to which set each came from.
- Candidates never touch a live system. Fixtures stand in for targets; a candidate that would act on a live system is graded on what it says it would do.

**Steps:**

1. **Frame.** State what variant is under test and what behavior counts as success. Write the rubric (3-6 concrete criteria) for the judge only. Hold it back from candidates.
2. **Set up sanitized environments.** A per-candidate working directory under a temp root, with the variant in place. Plant any context an organic task would have: a project skeleton, the skills the candidate would naturally read.
3. **Author one organic prompt.** What a user would type. No leakage of what's being measured.
4. **Spawn N parallel candidates** as local subagents per the **arena** skill's Phase B (fan out), with models from [Model routing](../../references/host-notes.md#model-routing). Each works in its own sanitized directory. Same prompt to each.
5. **Spawn one blinded judge** with its model from [Model routing](../../references/host-notes.md#model-routing), per the **arena** skill's Phase C (cross-judge). The judge sees outputs by sanitized label and the rubric, never a model name.
6. **Verify the chain from transcripts, not self-report.** Read each candidate's transcript (the subagent's returned trace, or this project's session transcript per the host notes). Never glob across other projects' transcripts. Look at which files each candidate actually opened. Grade chain-following from the files it really read plus the shape of the work, never from the candidate's own claims.
7. **Read every candidate output yourself** end to end. Compare to the judge's verdict. Disagreement means a model is biased or the rubric is ambiguous. Synthesize.

**Reply.** Variant under test, rubric, per-candidate notes, judge's verdict, your synthesis, and a recommendation for whether to promote the variant.
