# Autonomous Agent Operational Rules & Protocol

> [!IMPORTANT]
> **MANDATORY POLICY FOR ALL AI AGENTS WORKING ON THIS REPOSITORY**
> 
> You must follow this continuous synchronization protocol during every conversation and task. You do not need the user to remind you.

---

## 1. Living Design Report Protocol (`docs/design_report.md`)

The user requires a comprehensive end-of-project report. To eliminate the need for massive context recall at the end, **the engineering report must be continuously updated as design choices happen**:

1. **Design Decisions & Trade-Offs:**
   - Whenever a circuit design choice or trade-off is discussed and selected (e.g., transistor sizing choices, column multiplexing, decoder schemes, routing methods, buffer insertions), immediately add a new entry to **Section 3: Design Decisions & Architectural Evolution Log** in [`docs/design_report.md`](file:///d:/Projects/Memory-IC-Design/docs/design_report.md).
   - Each entry must record: *Date, Context, Alternatives Considered, Decision, and Engineering Rationale*.

2. **Simulation & Characterization Results:**
   - Whenever SPICE simulations (transient, power, timing, noise margins) or layout measurements (area, DRC/LVS) are performed, immediately populate the corresponding row in **Section 6: Simulation & Characterization Metrics** in [`docs/design_report.md`](file:///d:/Projects/Memory-IC-Design/docs/design_report.md).

---

## 2. Agent Knowledge Base Synchronization (`agent/`)

Whenever changes occur in the codebase or design architecture, keep the token-dense agent files in sync:

1. **`agent/status_and_tasks.md`:** Check off completed tasks and update the active sprint phase.
2. **`agent/architecture.md`:** Update block diagrams, pinouts, or circuit topology notes if the hardware architecture changes.
3. **`agent/specs.md`:** Keep electrical specifications aligned with latest project targets.

---

## 3. Git Hygiene
- Stage and commit documentation updates alongside corresponding scripts and design files.
- Keep commit messages concise, descriptive, and aligned with standard conventional commit practices.
