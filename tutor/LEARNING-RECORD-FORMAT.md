# Learning Record Format

Learning records live in `./learning-records/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc. Create the directory lazily: only when the first record is written.

They capture decision-grade insights that steer future sessions: non-obvious lessons, stated prior knowledge, and corrections. They are not the status dashboard; `LEARNING.md` owns current unit, hint stage, and `attempted` / `demonstrated` / `retained`.

## Template

```md
# {Short title of what was learned or established}

{1-3 sentences: what was learned (or what prior knowledge was established), and why it matters for future sessions.}
```

That is the whole format. A learning record can be a single paragraph. The value is recording _that_ this is now known and _why_ it changes what to teach next, not in filling out sections.

## Optional sections

Only include these when they add genuine value. Most records will not need them.

- **Status** (`active` or `superseded by LR-NNNN`): when an earlier understanding turns out to be wrong and is replaced.
- **Evidence**: how the user showed it (inspectable work, a teach-back explanation in chat, prior experience cited), the concept name, and the status in `LEARNING.md` after this event. Use this when the claim might be revisited. Do not treat the record as the status source of truth.
- **Implications**: what this unlocks, skips, or rules out for the next unit.

## Numbering

Scan `./learning-records/` for the highest existing number and increment by one.

## When to write a learning record

Write one when any of these is true:

1. **The user demonstrated genuine understanding of something non-trivial**: not exposure, but evidence they can use the concept correctly. This sets a new floor for what to teach next.
2. **The user disclosed prior knowledge**: "I already know X." Record it so future sessions do not re-teach it. Record the depth claimed.
3. **A misconception was corrected**: the user previously believed something wrong and now sees why. These predict future stumbling blocks for related topics.
4. **The mission shifted in response to learning**: the user discovered they cared about something different than they thought. Update `MISSION.md` (after confirming with the user) and cross-link it from the record.

### What does not qualify

- Material that was merely covered. Coverage is not learning. Wait for evidence.
- The user's full teach-back essay. Quote only the decision-grade insight; the writing in chat is the performance, not a file to keep.
- Session-by-session activity logs. Learning records are not a journal.
- Status, hint stage, or current unit. Those stay in `LEARNING.md`.

## Supersession

When a later record contradicts an earlier one, mark the old record `Status: superseded by LR-NNNN` rather than deleting it. The history of how understanding evolved is itself useful signal.
