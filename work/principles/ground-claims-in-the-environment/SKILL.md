---
name: ground-claims-in-the-environment
description: "Apply before acting on a claim about how code, a tool, an API, or a system behaves, and before any docs lookup. Verify it in the code and the versions where the work runs, and read docs only for those versions."
disable-model-invocation: true
---

# Ground Claims in the Environment

A claim about behavior is evidence only when it comes from the code and the environment the work runs in. Memory, a subagent's report, a forum answer, and the latest docs are leads. The repository, the installed versions, and observed output are proof.

- Name where the work runs (local, CI image, container, cluster, production host) and the versions pinned there: lockfiles, manifests, Dockerfiles, CI config, provider and module pins, `--version` on the target.
- Check the environment before docs: the dependency's source, `--help`, schema, config, or one small probe.
- Query docs for that version only, and pass the version to the docs tool. A result for another version is a lead to verify.
- When environments disagree, the one the work runs in wins. Say which one you used.
- An unknown version or conflicting sources is a gap. State it and run the smallest probe that settles it.

The test: can you point each claim the work relies on at a file and line, a command and its output, or a doc page for the version where this runs? A claim whose only source is memory or unversioned docs is unverified.
