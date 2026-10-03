# Stack examples

The playbooks are tool-neutral. This page only shows what each pattern looks like in common stacks, so the pattern is recognizable. It is not a command reference: check every flag against the target's installed version (`--help`, versioned docs) before relying on it. Facts below were checked on 2026-10-03 against Terraform 1.5.7, OpenTofu 1.11.5, kubectl 1.35.0, ansible-core 2.20.4, and systemd 262 help output, plus the vendors' current documentation for Helm, Argo CD, Flux, and Proxmox VE.

## Pattern to mechanism

| Pattern | Linux and systemd | Terraform / OpenTofu | Kubernetes, Helm, GitOps | Ansible and Proxmox VE |
| --- | --- | --- | --- | --- |
| Effective vs loaded state | `systemctl cat` shows files on disk; `systemctl show -p <Property>` shows what the manager loaded. They differ until a daemon reload. | Source vs state vs real resource; a plan compares all three. | Manifest in Git vs object in the API vs what the pod runs. | Inventory and vars vs facts gathered from the host; `qm config` / `pct config` for guest config. |
| Preview with the real engine | No general dry run for start, stop, enable, or mask; preview by listing dependents (`systemctl list-dependencies --reverse`). | `plan -out=<file>` then apply that file. | `kubectl diff` and `--dry-run=server` (server-side, runs admission); `helm diff` plugin; `argocd app diff`; `flux diff kustomization`. | `ansible-playbook --check --diff`; Proxmox has no dry run. |
| Bind approval to the exact action | The handoff fingerprint. | The saved plan file the user approved is the one applied. | A pinned manifest digest or Git revision; image by digest, not tag. | A pinned playbook revision and an explicit `--limit` host list. |
| Protection against deletion | `mask` blocks starting a unit. | `lifecycle { prevent_destroy = true }`; provider deletion-protection attributes. | Finalizers; PVC `reclaimPolicy: Retain`; `helm.sh/resource-policy: keep`; Argo CD `Prune=false` / `Delete=false`; Flux per-object prune opt-out. | Proxmox `protection` flag on guests; protected backups. |
| Reversible first | `stop` before `disable` before `mask` before removing files. | Remove from management (`removed` block in 1.7+, `state rm` before) instead of destroying, when the goal is to stop managing. | Suspend the GitOps sync, scale to zero, cordon and drain, then delete. | Stop the guest, detach a disk without deleting it, then destroy. |
| Inventory dependents | `systemctl list-dependencies --reverse`, sockets, timers. | `state list`; `plan -destroy` shows the exact delete set including dependents. | `ownerReferences`, PVCs, Ingress and Service consumers; default delete cascades in the background. | Guest disks across storages; backups referencing the VMID. |
| Verify afterwards | `systemctl is-active` plus a consumer request. | A fresh plan shows no changes for the touched addresses. | Rollout status, sync and health status, a consumer request. | A rerun reports no changes; guest state and consumer check. |

## Side effects that names hide

- `terraform plan` takes the state lock and calls provider APIs. A saved plan file and `show -json` output contain sensitive values in plain text (OpenTofu plan encryption can change that). `state pull` prints the whole state including secrets.
- `prevent_destroy` stops a plan that would destroy the object, but not once the resource block is removed from configuration.
- `-exclude` exists only in OpenTofu (1.9+); the `removed` block needs Terraform or OpenTofu 1.7+.
- `kubectl diff` and server-side dry runs need write permissions and run admission webhooks; webhooks that declare side effects reject dry runs.
- `helm ... --dry-run` prints rendered Secrets unless told to hide them; Helm stores release records as Secrets.
- `argocd app delete` cascades to the application's resources by default.
- `systemctl --dry-run` applies only to power-state verbs, not to start, stop, enable, or mask. `systemctl show` can expose `Environment=` values.
- `ansible-playbook --check` still connects to every host and gathers facts. Modules without check-mode support are skipped or partial, and a task with `check_mode: false` runs for real.
- Proxmox `qm destroy --destroy-unreferenced-disks` matches disks by VMID across all enabled storages. `vzdump` prunes older backups by default. Protected backups are guarded by Proxmox VE itself, not by the storage underneath, so direct storage access can still delete them; assume the same of the guest `protection` flag until checked.
