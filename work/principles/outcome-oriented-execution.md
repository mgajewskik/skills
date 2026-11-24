# Outcome-Oriented Execution

Optimize for the intended, verifiable end state rather than preserving throwaway transitional compatibility code during an owned, offline rewrite.

- **Scope boundary:** Applies only when every consumer is owned and ships together, with no live mixed-version traffic or persisted format spanning phases. Live rollouts, mixed-version contracts, and persisted data follow [Preserve Compatible Transitions](preserve-compatible-transitions.md) and [Sequence Work into Verifiable Units](sequence-verifiable-units.md).
- Prioritize end-state integrity over transitional compatibility layers that would become long-lived debt.
- Declare up front where temporary offline breakage is acceptable between internal phases, and keep it scoped and reversible in version control.
- Keep high-signal checks running on actively touched areas, and require full verification before the rewrite closes.
