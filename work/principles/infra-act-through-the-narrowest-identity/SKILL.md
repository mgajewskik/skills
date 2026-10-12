---
name: infra-act-through-the-narrowest-identity
description: "Apply before the first live command of a task, and again right before any apply, destroy, or bulk change. Name the acting identity and the resolved target, act with the least privilege the step needs, and lean on guards the platform enforces."
disable-model-invocation: true
---

# Act Through the Narrowest Identity

Before acting on live infrastructure, name who you act as and exactly where the command lands. Use the least privilege that can do the step, and let the platform refuse what you should never do.

**Why:** Credentials decide what a mistake can reach. A wrong target behind an admin identity turns one bad command into an outage: a switched kube context, a stale state file, a production profile left in the shell.

**Pattern:**
- Read identity and target from the tool itself (`whoami`, current context, backend and workspace), never from file names, shell history, or memory
- Diagnose with a read-only identity; change with one scoped to the step. When only admin or break-glass is available, say so before using it
- Prefer platform guards over care: deletion protection, retention policies, disruption budgets, resource locks. Terraform's `prevent_destroy` is weaker, since it stops guarding once its resource block is removed. A stateful target without a guard is a finding
- Resolve the target again right before apply or destroy and compare it with the plan. Any difference stops the step

**The test:** if the context or profile had switched to production a minute ago, which check in your next step would catch it?
