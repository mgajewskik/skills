---
name: ground-claims-in-the-environment
description: "Apply before acting on a claim about how code, a tool, an API, or a system behaves, and before any docs lookup. Verify it in the code and the versions where the work runs, and read docs only for those versions."
disable-model-invocation: true
---

# Ground Claims in the Environment

A claim about behavior is evidence only when it comes from the code and the environment the work runs in. Memory, a subagent's report, a forum answer, and the latest docs are leads; the repository, the installed versions, and observed output are proof.

**Why:** Flags, defaults, APIs, and config keys change between versions. Docs for the wrong version read as authoritative and yield code that looks right and fails where it runs. That place is often not this machine: CI images, containers, clusters, and production hosts pin their own versions.

**Pattern:**
- Name where the work runs (local, CI image, container, cluster, production host) and the versions pinned there: lockfiles, manifests, Dockerfiles, CI config, provider and module pins, `--version` on the target
- Check the environment before docs: the dependency's source, `--help`, schema, config, or one small probe
- Query docs for that version only. Pass the version to the docs tool (a versioned library ID, a versioned docs URL, the docs shipped in the package); a result for another version is a lead to verify, not an answer
- When environments disagree (local 1.8, CI 1.6), the one the work runs in wins; say which one you used
- An unknown version or conflicting sources is a gap: state it and run the smallest probe that settles it
- Cite each claim's source: file and line, command and output, or versioned doc page

**The test:** for each claim the work relies on, can you point at the file, the command output, or the doc page for the version where this runs? A claim whose only source is memory or unversioned docs is unverified.
