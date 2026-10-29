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
