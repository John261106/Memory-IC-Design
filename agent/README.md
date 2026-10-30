# Agent Quick-Start & Navigation Guide

This folder contains token-optimized reference documentation for AI agents working on the **16 × 16 (256-Bit) SRAM IC** design.

## Purpose & Token Efficiency
- Large SPICE raw files (`.raw`), log files (`.log`), and massive netlists consume thousands of tokens unnecessarily.
- **Do NOT read `.raw` or `.op.raw` files directly.** Use targeted analysis scripts or reference these concise agent guides.
- When an agent is invoked for a specific task, refer to the table below to read only the relevant file(s).

## Agent File Index

| File | Focus / Information Covered | When to Read |
|---|---|---|
| [`agent/rules.md`](file:///d:/Projects/Memory-IC-Design/agent/rules.md) | **MANDATORY RULES:** Autonomous protocol to continuously update `docs/design_report.md` on every design choice | MUST read before making or recording any design change |
| [`agent/specs.md`](file:///d:/Projects/Memory-IC-Design/agent/specs.md) | Condensed technical specifications, pin list, operating constraints, target metrics | Starting any new task or checking electrical constraints |
| [`agent/architecture.md`](file:///d:/Projects/Memory-IC-Design/agent/architecture.md) | Transistor-level block breakdown, subcell schematics, decoders, sense amp, write driver, clock tree, bond wire/pad model, top-metal grid | Modifying or designing schematics / layout |
| [`agent/pinout_and_interface.md`](file:///d:/Projects/Memory-IC-Design/agent/pinout_and_interface.md) | 5-pin external interface, serial addressing protocol, read/write timing diagrams | Designing I/O pads, testbenches, or addressing circuits |
| [`agent/cad_and_jython.md`](file:///d:/Projects/Memory-IC-Design/agent/cad_and_jython.md) | Electric VLSI 9.08 Python/Jython automation API, cell hierarchy, scripting patterns | Automating schematic connections, DRC, or layout generation |
| [`agent/simulation_guide.md`](file:///d:/Projects/Memory-IC-Design/agent/simulation_guide.md) | SPICE / LTspice / ngspice testbench templates, TSMC 0.18µm model usage, power/energy/Fmax formulas | Running circuit simulations or characterizing power/timing |
| [`agent/status_and_tasks.md`](file:///d:/Projects/Memory-IC-Design/agent/status_and_tasks.md) | Project status, completed components, active sprint, prioritized task list | Planning next steps or reporting progress |

## Project Root Reference
- Top-level project description: [`project.md`](file:///d:/Projects/Memory-IC-Design/project.md) / [`docs/project.md`](file:///d:/Projects/Memory-IC-Design/docs/project.md)
- TSMC 0.18 µm model cards: [`lib/tsmc018.lib`](file:///d:/Projects/Memory-IC-Design/lib/tsmc018.lib)
- Electric VLSI binary library: [`src/Memory-IC-Design.jelib`](file:///d:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib)
- Jython scripts: [`scripts/`](file:///d:/Projects/Memory-IC-Design/scripts/)
- SPICE deck netlists: [`spice/`](file:///d:/Projects/Memory-IC-Design/spice/)
