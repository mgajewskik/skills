# Trace forensics

**You own the diagnosis from the artifact. Load it, shape it, narrow to the cause, attribute to source.**

Distinct from Runtime forensics, which instruments a running process. Here the capture already exists: a `perf.data` or other profile, a trace, a core dump, a heap snapshot, a pcap, or a log bundle. The artifact is a fixed dataset; read it, don't re-run it. Use the generic tool for its format (`perf report`/`perf script`, `gdb` or `lldb`, `tshark`, a trace or heap parser, plain text tools for logs). Artifacts can hold secrets and customer data: select fields, never paste raw dumps.

1. Identify the format and load it with the right tool. Parse large artifacts in a subagent (**principle-guard-the-context-window**) and keep the reduced finding in the main thread.
2. Transform the raw artifact into a form you can query. Dump samples, frames, packets, or log lines into sqlite, one row each. Reach the queryable shape before you read.
3. Narrow to the cause. Query for the frames that hold the most time and walk the call tree to the hot path. For a leak, follow the retainer chain from the leaked object to a root. For a core dump, the faulting thread's stack and the state it read. For a pcap, the first request whose response diverges. For logs, the first event that differs between a failing and a succeeding run.
4. Attribute to source. Map the hot frame to file, symbol, and line via the artifact's own symbols. A frame with no source mapping is not yet a diagnosis. Resolve the symbols, or say plainly the artifact does not carry them.
5. Confirm against a paired capture when you have one. Diff a before and after artifact. Without one, mark the finding as the strongest hypothesis the artifact supports, not a confirmed cause.
6. Hand back a cited diagnosis, no fix unless asked. Route to Bug fix or Perf issue once the cause is known. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only forensics`.

**Reply.** The artifact and format, the reduced finding, the source location, the artifact and sqlite paths, and whether a paired capture confirmed it.
