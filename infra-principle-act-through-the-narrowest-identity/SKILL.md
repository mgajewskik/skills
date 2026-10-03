---
name: infra-principle-act-through-the-narrowest-identity
description: Apply before the first live command of a task, and again right before any apply, destroy, or bulk change. Name the acting identity and the resolved target, use the narrowest identity that can do the step, and rely on guards the platform enforces over care the agent promises.
disable-model-invocation: true
user-invocable: false
---

# Act through the narrowest identity

Part of `work-mode`; follow its `references/contract.md` (in this catalog: `../work-mode/references/contract.md`). If that file cannot be found, stop operational work and say so. Identifying the identity and target is read-only. Requesting, assuming, or creating a different role or credential is an access change the user makes.

The contract decides what the agent may do; the credentials decide what it can do. A wrong target reached through a broad identity turns one mistaken command into a production outage. Name both before acting, keep the identity as narrow as the step, and let the platform refuse what the agent should never do.

## Why

AWS Well-Architected wants environments separated by identity ("You use separate AWS accounts to isolate developers from production environments") and lists "By default, you grant users administrator permissions" as an anti-pattern ([SEC03-BP02](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_permissions_least_privileges.html)). It also names emergency access used because "they find it easier to make changes directly than submit changes through a pipeline" as an anti-pattern ([SEC03-BP03](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_permissions_emergency_process.html)). OWASP's mitigation for excessive agency is to "Implement authorization in downstream systems rather than relying on an LLM to decide if an action is allowed or not" ([LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)). In a reported 2026 incident, an agent unpacked an old Terraform state file over the current one, so `terraform destroy` removed production; the database had no deletion protection and its snapshots went with it ([author's account](https://aishippingblog.com/p/how-i-dropped-our-production-database)).

## Pattern

1. Before the first live command, record the acting identity and the resolved target: account and role, project, region, kube context and namespace, IaC backend and workspace, host. Read them from the tool's own whoami, context, or backend output, never from file names, shell history, or memory.
2. Match the identity to the step: a read-only identity for diagnosis and inventory, a scoped one for a single change. When only a broad identity (administrator, root, cluster-admin, break-glass) is available, say so and let the user choose to narrow it, proceed, or take the step over.
3. Prefer guards the platform enforces: deletion protection, `prevent_destroy`, retention policies, disruption budgets, resource locks, organization policies. A stateful target without one is a finding to report before the change, per `infra-principle-design-recovery-first`.
4. Right before any apply, destroy, or bulk change, resolve the target again and compare it with step 1 and with the preview: same account, context, backend, workspace, and state lineage. Any difference stops the step.
5. Write the identity and the resolved target into the journal entry or the handoff's `## Targets`, so the reader sees exactly where the command lands and as whom.

The test: if the state file, kube context, or profile had switched to production a minute ago, which check in your next step would catch it?

You skipped this when a journal entry or handoff names a target but not the identity it runs as, or an apply runs against a target last resolved at the start of the session.

## Stop and limit

Halt when the identity cannot be determined, when two reads of the target disagree, or when the only identity available is break-glass outside an emergency. Find the identity from whoami output, never by reading credential files, tokens, or environment dumps. A narrow identity limits damage; it neither makes an action safe nor authorizes it, and the contract still decides who executes.
