# Prove It Works

Verify every output by checking the real artifact directly: offline tests, rendered outputs, and diffs for Code playbooks; live state and consumer signals for Ops playbooks. Proxies (file mtimes, self-reports, cached output, "it compiles") do not count. When a check fails, suspect the observation method before the system.

Script the check when you can. A deterministic script that reruns the comparison beats a one-time look. Record the command and observed result in the work log (attaching long output as an artifact), and commit a check script only when it belongs in the repository's permanent suite.
