# Opening a PR

Run at the end of a code playbook when the change is meant for review. Opening a PR notifies people, so the user executes it: you prepare the branch, the commits, and the description, and hand over one exact command.

**Branch.** Work on the user's working branch, or a branch the user named. Dirty tree with unrelated work: leave that work alone and commit only your files. If the change needs a new branch, create it locally; pushing it is the user's (the contract lets you push only the user's working branch).

**Commits.** Commit liberally while working. Before handing over, rebase your unpushed commits into small, ordered commits. Each commit is landable and ordered to tell the story. Amend when the fix belongs in a just-made commit; new commit when separable. Never rewrite commits that are already pushed. The **commit** skill writes every commit message.

**Before review.** Run the **no-comments** skill over the diff. Write the PR title and description with the **technical-writing** skill (every layer except Diátaxis), then apply **unslop**. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works. Follow the repository's own PR conventions when it has them; they win over this page.

**Titles.** Without a repository convention, use Conventional Commits: `type(scope): subject`, with `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`, the changed area as scope, a short imperative subject, a real symbol when one carries the change, and no trailing period.

**Description.** The PR body is a briefing, not the lab notebook. A reviewer who has the diff should learn why the change exists, what it leaves out, what it could break, and how you proved it works, in under a minute. Short, simple sentences with few identifiers. Keep it under about 40 lines. Use these `##` sections in order, and drop a section that has nothing to say:

- `## Why`: the problem and the approach in one to three short sentences.
- `## What changed`: one to three short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename.
- `## Scope`: what the PR covers and what it deliberately leaves out. Always present.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about.
- `## Blast radius`: one or two sentences on who or what the change touches and why that is safe or risky.
- `## Verification`: one to three bullets, each a real run path and its outcome. For a performance change, one primary number with its unit as `before -> after`.

Attach screenshots or recordings when they prove a claim. No full SHAs, lane recitals, file-by-file checklists, or "CLEAN" verdicts in the body.

**Size and stacks.** Prefer several narrow PRs to one large one. A stack is a base-branch chain: the root PR targets trunk, each child targets its parent branch.

**Hand over.** Write the body to `.work-mode/pr-<slug>.md`. Push the branch if it is the user's working branch; otherwise give the push command. Then give the exact create command, for example `gh pr create --base <base> --head <branch> --title "<title>" --body-file .work-mode/pr-<slug>.md`, or `--base <parent-branch>` for a stacked child. Without `gh` or GitHub, report the pushed branch and the body path.

**After.** Opening a PR does not start a babysit. Keep building; run Babysit only when the user asks.

**Reply.** The branch and its commits, push status, the PR title, the body path, and the exact command for the user.
