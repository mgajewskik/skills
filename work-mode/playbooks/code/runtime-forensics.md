# Runtime forensics

**You own the diagnosis. Instrument the running process, don't theorize from source.** The deliverable is a cited diagnosis, not a fix.

Attaching to a running process is an observation with effects: `perf`, `strace`, `gdb`, and eBPF tools need privileges, add overhead, and can pause the target. On a local or development process, go ahead. On anything shared or production, treat attaching as a live change under [the contract](../../references/contract.md).

1. Capture the live signal: `perf record` or `perf top` for a spinning process, `strace -f -T` for syscalls and waits, `/proc/<pid>/` (`status`, `stack`, `fd`, `smaps_rollup`) for state and memory, a heap snapshot or the runtime's own profiler for a leak, eBPF tools (`bpftrace`, `bcc`) when they are installed. Check which of these exist and their versions first; installing one needs the user's approval. A real artifact, not a guess.
2. Reduce the artifact to the smoking gun: the function on the hot path, the retainer chain from the leaked object to a root, the loop firing without input, the syscall that blocks. Parse large artifacts in a subagent (**principle-guard-the-context-window**) and keep the reduced finding in the main thread.
3. Prove the mechanism before believing it. Confirm the hypothesis cheaply with added instrumentation: a log line, a probe, a debugger breakpoint, a local rebuild. A live hotfix to confirm it is a live change: outside production, journal it as a reversible change and revert it after the confirmation; in production it is user-executed.
4. Map the finding back to source: file, symbol, the line that allocates, schedules, or blocks.
5. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only forensics`.

**Reply.** The signal captured, the reduced finding, how you proved the mechanism, the source location, artifact paths, and any journal entries made. No fix unless asked. Hand back to Bug fix or Perf issue once the cause is known.
