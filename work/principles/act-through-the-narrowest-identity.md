# Act Through the Narrowest Identity

Before acting on live infrastructure, name who you act as and exactly where the command lands. The identity decides what a mistake can reach.

- Read identity and target from the tool itself (`whoami`, current context, backend and workspace), never from file names, shell history, or memory.
- Diagnose with a read-only identity and change with one scoped to the step. Say so before using admin or break-glass.
- Prefer platform guards over care: deletion protection, retention policies, disruption budgets, resource locks. Terraform's `prevent_destroy` stops guarding once its resource block is removed. A stateful target without a guard is a finding.
- Resolve the target again right before apply or destroy and compare it with the plan. Any difference stops the step.

The test: if the context or profile had switched to production a minute ago, which check in your next step would catch it?
