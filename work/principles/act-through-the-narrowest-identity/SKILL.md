---
name: act-through-the-narrowest-identity
description: "Apply before the first live command of a task, and again right before any apply, destroy, or bulk change. Name the identity and resolved target, act with least privilege, lean on platform guards."
disable-model-invocation: true
---

# Act Through the Narrowest Identity

Before acting on live infrastructure, name who you act as and exactly where the command lands. Credentials decide what a mistake can reach. Behind an admin identity, a switched kube context, a stale state file, or a production profile left in the shell turns one bad command into an outage.

- Read identity and target from the tool itself (`whoami`, current context, backend and workspace), never from file names, shell history, or memory.
- Diagnose with a read-only identity; change with one scoped to the step. When only admin or break-glass is available, say so before using it.
- Prefer platform guards over care: deletion protection, retention policies, disruption budgets, resource locks. Terraform's `prevent_destroy` is weaker, since it stops guarding once its resource block is removed. A stateful target without a guard is a finding.
- Resolve the target again right before apply or destroy and compare it with the plan. Any difference stops the step.

**The test:** if the context or profile had switched to production a minute ago, which check in your next step would catch it?
