# Electric VLSI & Jython Automation Reference

## 1. Environment & Design Database
- **Tool:** Electric VLSI Design System version 9.08.
- **Library File:** [`src/Memory-IC-Design.jelib`](file:///d:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib)
- **Technology:** `mocmos` (MOSIS CMOS), submicron rules, scalable.
- **Scripting Language:** **Jython 2.7** (Python running on Java JVM inside Electric VLSI).

---

## 2. Cell Hierarchy in `Memory-IC-Design.jelib`

| Cell Name | View | Function |
|---|---|---|
| `6T_cell` | `{sch}`, `{lay}` | Single 6T SRAM bitcell. Ports: `WL`, `BIT`, `BITB`, `VDD`, `GND`. |
| `Precharge_ckt` | `{sch}`, `{lay}` | Precharge and equalization unit. Ports: `BIT`, `BITB`, `PCB`, `VDD`. |
| `Sense_amp` | `{sch}`, `{lay}` | Differential latch sense amplifier. Ports: `BIT`, `BITB`, `READ_EN`, `SENSE`, `VDD`, `GND`. |
| `Write_driver` | `{sch}`, `{lay}` | Tri-state write driver. Ports: `BIT`, `BITB`, `DATA`, `WRITE_EN`, `VDD`, `GND`. |
| `16bit_array` | `{sch}` | Sub-array row/column slice. |
| `256bit_SRAM` / `Top_SRAM` | `{sch}`, `{lay}` | Full $16 \times 16$ integrated memory with decoders, peripheral circuits, clock tree, and pads. |

---

## 3. Automation Scripts Overview (`scripts/`)

| Script | Purpose |
|---|---|
| `01_list_instances.py` | Inspects currently active cell in Electric and prints all instance names and prototype cells. |
| `02_inspect_cell_pins.py` | Prints exported ports and pins of all instances in the current schematic. |
| `03_list_exports.py` | Lists top-level exported ports/pins of the current cell. |
| `04_connect_sram_top.py` | Fully automates wiring between 256 `6T_cell` instances, 16 `Precharge_ckt`, 16 `Write_driver`, and 16 `Sense_amp` instances. |
| `05_connect_decoder.py` | Automates schematic wiring for 4-to-16 static address decoders. |
| `06_layout_6t_cell.py` | Programmatically generates, places, and wires traditional `6T_cell{lay}` in `Memory-IC-Design.jelib`, verifying 100% perpendicular (Manhattan) arcs, zero DRC collisions/violations, and 100% LVS/NCC topology & sizing match. |
| `07_layout_not_and_nand.py` | Generates compact physical layout views for `Not{lay}` and `Nand{lay}` in `Memory-IC-Design.jelib`, with 100% Manhattan perpendicular lines, 0 DRC violations, and 100% LVS/NCC topology & sizing match. |
| `Electric_VLSI_Jython_Automation_README.md` | Comprehensive developer guide to Electric's Java/Jython API. |

---

## 4. Key Jython API Patterns for Electric VLSI

```python
from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

# 1. Get active cell
cell = Job.getUserInterface().getCurrentCell()

# 2. Find schematic wire prototype
tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

# 3. Find named port on an instance
port_inst = node.findPortInst("WL")

# 4. Wire two ports together
ArcInst.makeInstance(wire, port1, port2, True)

# 5. Export a pin to make it visible hierarchically
Export.newInstance(cell, port_inst, "PIN_NAME", PortCharacteristic.BIDIRECTIONAL)
```

## 5. Netlist Generation & Simulation Export
- Inside Electric VLSI: `Tools -> Simulation (SPICE) -> Write SPICE Deck...`
- Outputs `.spi` deck incorporating MOSIS submicron models and subcircuit declarations.
- Verify simulation outputs in `spice/` directory.

---

## 6. SCMOS / `mocmos` DRC Rules & Safe Compact Layout Guidelines
Discovered through Electric's built-in Quick DRC engine (`ALGO_SWEEP`):

### Contact Primitive Sizing Rules
| Primitive Node | Default / Required Size | DRC Rule Triggered if Sized Down |
|---|---|---|
| `Metal-1-N-Active-Con` | $17.0\lambda \times 17.0\lambda$ | Rule 6.2, 7.3 (`Minimum size error on Y axis ... LESS THAN -7 IN SIZE`) |
| `Metal-1-P-Active-Con` | $17.0\lambda \times 17.0\lambda$ | Rule 6.2, 7.3 (`Minimum size error on Y axis ... LESS THAN -7 IN SIZE`) |
| `Metal-1-N-Well-Con` | $17.0\lambda \times 17.0\lambda$ | Rule 6.2, 7.3 (`Minimum size error on Y axis ... LESS THAN -7 IN SIZE`) |
| `Metal-1-P-Well-Con` | $17.0\lambda \times 17.0\lambda$ | Rule 6.2, 7.3 (`Minimum size error on Y axis ... LESS THAN -7 IN SIZE`) |
| `Metal-1-Polysilicon-1-Con`| $5.0\lambda \times 5.0\lambda$ | Safe at $5.0\lambda \times 5.0\lambda$ or default |
| `Metal-1-Pin` | $3.0\lambda \times 3.0\lambda$ | Safe at $3.0\lambda \times 3.0\lambda$ |

### Placement Spacing & Notch Boundaries
1. **Rule 4.4 Select Notch Spacing ($X_{\text{con}} \ge 13.0\lambda$):**
   - Transistors in `Orientation.R` have active diffusion extending horizontally by $3.75\lambda$ from center.
   - Active contacts placed at $|X| < 13.0\lambda$ cause their Select layer boundary to come within $1.5\lambda$ of the transistor channel edge, violating rule 4.4 (`Notch layer Select LESS THAN 2`).
   - Hence, minimum contact horizontal offset is $X_{\text{con}} = 13.0\lambda$.

2. **Rule 2.5 Well Tap Spacing ($Y_{\text{rail}} \ge 28.0\lambda$ for $Y_{\text{MOS}} = 16.0\lambda$):**
   - Well tap contact `Metal-1-N-Well-Con` (N-Active) must be $\ge 4.0\lambda$ away from PMOS P-Active.
   - For PMOS at $Y_P = 16.0\lambda$ (diffusion extends to $Y = 20.0\lambda$), VDD tap must be at $Y_{\text{VDD}} \ge 28.0\lambda$ to satisfy $28.0 - 17.0/2 = 19.5$ tap edge clearance against well boundary.

3. **Optimal Validated Standard Inverter Dimensions (`Not{lay}`):**
   - `X_CON = 13.0`, `Y_P = 16.0`, `Y_N = -16.0`
   - `Y_VDD = 28.0`, `Y_GND = -28.0`, `X_EDGE = 22.0`
   - Overall cell bounding box: Width = $44.0\lambda$ ($3.96\ \mu\text{m}$), Height = $56.0\lambda$ ($5.04\ \mu\text{m}$), Area = $2464\ \lambda^2$ (42.1% reduction vs original $56\lambda \times 76\lambda$).
   - Electric Quick DRC: **0 Errors, 0 Warnings**. NCC/LVS: **100% Match**.

---

## 7. Headless Batch Execution & DRC Check in Jython
When running scripts outside the interactive UI, GUI calls (such as progress dialogs) throw `NullPointerException`. Always use Electric batch mode with BeanShell launcher:

```powershell
java -jar "C:\Users\USER\OneDrive\Desktop\electricBinaryFull-9.08.jar" -batch -s scripts\run_script.bsh
```

Where `scripts/run_script.bsh` contains:
```java
org.python.util.PythonInterpreter pi = new org.python.util.PythonInterpreter();
pi.execfile("scripts/07_layout_not_and_nand.py");
System.exit(0);
```

### Direct Programmatic DRC Check via Reflection:
```python
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

m_chk = None
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m_chk = m
        m_chk.setAccessible(True)
        break

if m_chk is not None:
    m_chk.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
    errors = logger.getNumErrors()
    warnings = logger.getNumWarnings()
```
