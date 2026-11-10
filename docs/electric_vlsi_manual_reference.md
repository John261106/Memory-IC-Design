# Electric VLSI Design System (v9.08) — Layout & Design Reference Manual

This reference manual documents the essential principles, design rules, technology specifications, verification flows, and programmatic automation APIs of the **Electric VLSI Design System (version 9.08)**, curated specifically for the **16 × 16 (256-Bit) Transistor-Level Static RAM Memory IC Design** project.

---

## 1. Electric VLSI System Architecture & Core Concepts

### 1.1 The Connectivity-Based IC Layout Paradigm
Unlike traditional polygon-pushing EDA tools (e.g., Magic, Virtuoso) that treat integrated circuit layout purely as geometric "paint" (rectangles on layers requiring subsequent flattened node extraction), **Electric treats all IC layout as a network of connected electrical nodes and arcs**:
- **Nodes:** Physical components with spatial extents and connection ports (MOS transistors, contact cuts/vias, pins, and well taps).
- **Arcs:** Connecting wires that establish electrical nets (Metal-1 to Metal-6, Polysilicon, N-Active, P-Active).
- **Ports:** Pre-defined attachment sites on nodes where arcs must connect.
- **Exports:** Ports within a subcell exposed to the exterior, making them accessible to parent cells in the hierarchy.

#### Key Advantages for Memory IC Design:
1. **Instantaneous Net Extraction:** Layout connectivity is maintained dynamically in memory. Node extraction is never an error-prone, separate extraction step.
2. **Instant LVS (NCC):** Layout-versus-schematic checks verify topology directly by comparing graphs of connected nodes.
3. **Synthesis & Scripting Friendliness:** Entire layouts can be synthesized deterministically with mathematical coordinates via the Java/Jython API.

---

### 1.2 Database Structure & Cell Views
Electric organizes designs into libraries (`.jelib` binary format or `.delib` directory format):
- **Cell Groups:** A cell group shares a base name and contains multiple **views** of the same functional block:
  - `cell{sch}`: Transistor-level schematic view.
  - `cell{ic}`: Schematic symbol (icon) view used in higher-level schematics.
  - `cell{lay}`: Physical custom layout view.
- **Naming Conventions:** Strict correspondence between `{sch}` and `{lay}` view names is required for automatic Network Consistency Checking (NCC / LVS) pairing.

---

### 1.3 Technology Scaling & Lambda ($\lambda$) Units
Electric represents all internal layout dimensions in **dimensionless integer or half-integer grid units**. These units are converted to physical distances via the technology **Scale** setting:
- **Process Technology:** TSMC 0.18 µm CMOS (`tsmc018.lib`, MOSIS `mocmos` submicron / deep submicron).
- **Scale Factor:**
  $$\lambda = 90\text{ nm} = 0.09\ \mu\text{m}$$
  $$1\text{ Electric Unit} = 1\lambda = 90\text{ nm}$$
- **Minimum Gate Length ($L_{\min}$):**
  $$L_{\min} = 2\lambda = 2 \times 90\text{ nm} = 180\text{ nm} = 0.18\ \mu\text{m}$$
- **Scale Preference Location:** `File > Preferences... > Technology > Scale` $\rightarrow$ Set `MOSIS CMOS (mocmos)` to `90` nanometers.

---

## 2. MOSIS CMOS (`mocmos`) Technology Specification

The MOSIS CMOS technology describes scalable CMOS processes fabricated through MOSIS. In this project, the technology configuration is:
- **Process:** TSMC 0.18 µm standard CMOS (1P6M — 1 Poly, 6 Metal layers).
- **Nominal Supply ($V_{\text{DD}}$):** 1.8 V.
- **Substrate:** P-type substrate (requiring N-Well for PMOS transistors and P-substrate taps for NMOS ground reference).

### 2.1 Primitive Node Types in `mocmos`
| Primitive Node Name | Category | Function / Port Attachment |
|---|---|---|
| `N-Transistor` | Active Node | 3-terminal NMOS transistor (`poly-top`, `poly-bottom`, `diff-left`, `diff-right`) |
| `P-Transistor` | Active Node | 3-terminal PMOS transistor (embedded in N-Well) |
| `Metal-1-N-Active-Con` | Contact | Connects Metal-1 to N-diffusion (active) |
| `Metal-1-P-Active-Con` | Contact | Connects Metal-1 to P-diffusion (active) |
| `Metal-1-Polysilicon-1-Con` | Contact | Connects Metal-1 to Polysilicon-1 gate line |
| `Metal-1-Metal-2-Con` | Via | Via 1: Connects Metal-1 to Metal-2 |
| `Metal-2-Metal-3-Con` | Via | Via 2: Connects Metal-2 to Metal-3 |
| `Metal-3-Metal-4-Con` | Via | Via 3: Connects Metal-3 to Metal-4 |
| `Metal-4-Metal-5-Con` | Via | Via 4: Connects Metal-4 to Metal-5 |
| `Metal-5-Metal-6-Con` | Via | Via 5: Connects Metal-5 to Metal-6 |
| `Metal-1-N-Well-Con` | Well Tap | N-Well tap contact (connected to $V_{\text{DD}}$) |
| `Metal-1-P-Well-Con` | Substrate Tap | P-Well/Substrate tap contact (connected to $\text{GND}$) |
| `Metal-1-Pin` to `Metal-6-Pin`| Routing Pin | Zero-area termination/junction pin for metal routing |
| `Polysilicon-1-Pin` | Routing Pin | Termination pin for poly routing |
| `N-Well-Node` | Pure Geometry | Solid N-Well rectangular coverage area |
| `P-Well-Node` | Pure Geometry | Solid P-Well rectangular coverage area |

---

### 2.2 Primitive Arc Types in `mocmos`
| Arc Name | Default Width | Typical Project Usage |
|---|---|---|
| `Polysilicon-1` | $2\lambda$ ($0.18\ \mu\text{m}$) | Transistor gates, short local interconnections |
| `N-Active` | $3\lambda$ ($0.27\ \mu\text{m}$) | NMOS source/drain diffusion connections |
| `P-Active` | $3\lambda$ ($0.27\ \mu\text{m}$) | PMOS source/drain diffusion connections |
| `Metal-1` | $3\lambda$ ($0.27\ \mu\text{m}$) | Internal cell routing, horizontal cell rails ($V_{\text{DD}}/\text{GND}$), Wordline tap |
| `Metal-2` | $3\lambda$ ($0.27\ \mu\text{m}$) | Vertical Bitlines (`BIT`, `BITB`), cross-coupling jumpers |
| `Metal-3` | $3\lambda$ ($0.27\ \mu\text{m}$) | Decoder outputs, horizontal bus routing, Sense Amp interconnects |
| `Metal-4` | $3\lambda$ ($0.27\ \mu\text{m}$) | Column MUX selection, vertical inter-block bus routing |
| `Metal-5` | $4\lambda$ ($0.36\ \mu\text{m}$) | Balanced clock distribution tree (`CLK`) |
| `Metal-6` | $6\lambda$–$8\lambda$ ($0.54$–$0.72\ \mu\text{m}$) | Top-metal low-resistance $V_{\text{DD}}$ and $\text{GND}$ power mesh |

---

## 3. Physical Layout Design Rules (SCMOS Deep Submicron Rules)

Electric enforces SCMOS design rules defined in $\lambda$. Adherence to these spacing, overlap, and sizing rules guarantees zero DRC errors.

### 3.1 Design Rules Quick-Reference Table

```
========================================================================================
Layer / Feature             SCMOS Rule   Lambda (λ)   Physical (0.18 µm)   Notes
========================================================================================
POLYSILICON:
  Minimum Gate Length (L)       3.1          2 λ          0.18 µm          Nominal channel length
  Poly Width (interconnect)     3.1          2 λ          0.18 µm          Minimum wire width
  Poly-to-Poly Spacing          3.2          3 λ          0.27 µm          Between independent poly
  Poly Overhang over Active     3.3          2 λ          0.18 µm          Gate extension past diffusion
  Active Overhang past Gate     3.4          2 λ          0.18 µm          Source/drain diffusion length
  Poly to Active Spacing        3.5          1 λ          0.09 µm          Unconnected poly & active
----------------------------------------------------------------------------------------
ACTIVE (DIFFUSION):
  Minimum Active Width          2.1          3 λ          0.27 µm          Minimum transistor width
  Active-to-Active Spacing      2.2          3 λ          0.27 µm          Between independent diffusions
  N+ to P+ Active Spacing       2.3          8 λ          0.72 µm          Across well boundary
----------------------------------------------------------------------------------------
CONTACTS (CUTS):
  Contact Cut Size              6.1          2 λ × 2 λ    0.18 × 0.18 µm   Exact cut dimension
  Active Overlap of Contact     6.2          1 λ          0.09 µm          Border around cut (Pad: 4×4 λ)
  Poly Overlap of Contact       6.3          1 λ          0.09 µm          Border around cut (Pad: 4×4 λ)
  Contact-to-Contact Spacing    6.4          2 λ          0.18 µm          Spacing between contacts
  Contact to Poly Gate Space    6.5          2 λ          0.18 µm          Active contact to gate poly
----------------------------------------------------------------------------------------
METAL-1:
  Minimum Width                 7.1          3 λ          0.27 µm          Minimum wire width
  Minimum Spacing               7.2          3 λ          0.27 µm          Spacing between M1 lines
  Overlap of Contact            7.3          1 λ          0.09 µm          Surround around cut
----------------------------------------------------------------------------------------
VIA-1 (METAL-1 TO METAL-2):
  Via Cut Size                  8.1          2 λ × 2 λ    0.18 × 0.18 µm   Via 1 cut dimension
  Metal-1 Overlap of Via 1      8.2          1 λ          0.09 µm          M1 surround around via
  Via-to-Via Spacing            8.3          3 λ          0.27 µm          Spacing between vias
  Metal-2 Width                 9.1          3 λ          0.27 µm          Minimum M2 width
  Metal-2 Spacing               9.2          3 λ / 4 λ    0.27 / 0.36 µm   Deep submicron requires 4 λ
  Metal-2 Overlap of Via 1      9.3          1 λ          0.09 µm          M2 surround around via
----------------------------------------------------------------------------------------
WELLS (N-WELL & P-WELL / SUBSTRATE):
  Minimum Well Width            1.1         12 λ          1.08 µm          Electric minimum well size
  Well Spacing (same potential) 1.2          6 λ          0.54 µm          Separate wells at same bias
  Well Spacing (diff potential) 1.3         18 λ          1.62 µm          Opposite potentials
  Well Overhang of Diffusion    1.4          3 λ          0.27 µm          Well enclosure of active
========================================================================================
```

---

## 4. DRC & Verification Engines

Electric features two primary checking engines: **Design Rule Checking (DRC)** and **Network Consistency Checking (NCC)**.

### 4.1 Design Rule Checking (DRC)
Electric detects 4 distinct geometric violation classes:
1. **Spacing Errors:** Geometry of different nodes/arcs placed closer than design rule minimums.
2. **Notch Errors:** Acute angles or notches on the same electrical network that violate minimum spacing.
3. **Minimum Size Errors:** Nodes or arcs whose physical width/length falls below the layer threshold.
4. **Resolution Errors:** Features smaller than the manufacturing grid resolution limit.

#### Checking Modes & Commands:
- **Hierarchical DRC (`Tools > DRC > Check Hierarchically` / shortcut `F5`):** Exhaustively checks the entire hierarchy from leaf cells upward.
- **Incremental DRC:** Runs continuously in the background during manual editing (can be toggled in `File > Preferences > Tools > DRC`).
- **Error Stepping:**
  - `>` : Advance to the next DRC violation on screen.
  - `<` : Step back to previous DRC violation.
  - Violation details appear in the **Messages Window**.
- **DRC Exclusion Nodes:** In special layout regions where intentional overlap occurs (e.g. pad interfaces), a `DRC Exclusion` node (`Components > Misc. > DRC Exclusion`) suppresses false errors.

---

### 4.2 Electrical Rule Checking (ERC): Wells & Latchup
- **Menu Command:** `Tools > ERC > Check Wells`
- **Well & Substrate Rules:**
  - Every continuous N-Well island must contain at least one `Metal-1-N-Well-Con` tied to $V_{\text{DD}}$.
  - The P-substrate surrounding NMOS transistors must contain `Metal-1-P-Well-Con` tied to $\text{GND}$.
  - **Tap Distance Rule:** The maximum distance between any MOS transistor diffusion edge and the nearest well tap contact should not exceed $20\ \mu\text{m}$–$30\ \mu\text{m}$ ($200\lambda$–$300\lambda$) to suppress CMOS SCR latch-up.
- **Coverage Implants Generator:**
  - Command: `Tools > Generation > Coverage Implants Generator`. Automatically generates pure N-Well and P-Well covering rectangles over diffusions to eliminate well boundary slits.

---

### 4.3 Network Consistency Checking (NCC / LVS)
Electric's NCC engine verifies that the layout network topology matches the transistor schematic 100%.

#### Algorithms:
1. **Local Partitioning:** Fast, highly descriptive diagnostic algorithm that locates exact mismatch locations (e.g., swapped source/drain, missing export, floating gate). Solves >95% of circuit mismatches.
2. **Gemini II:** Graph isomorphism algorithm executed after Local Partitioning to verify large-scale structural equivalence.

#### Verification Protocol:
1. **Phase 1 — Pure Topology Check:**
   - Command: `Tools > NCC > Schematic and Layout Views of Cell in Current Window`
   - Verifies all nets, nodes, and interconnections match without checking transistor dimensions.
2. **Phase 2 — Transistor Sizing Check:**
   - Configure: `File > Preferences > Tools > NCC` $\rightarrow$ Check `Check transistor sizes`.
   - Set relative tolerance (e.g., 5%) and absolute tolerance.
   - NCC verifies that:
     $$W_{\text{layout}} = W_{\text{schematic}} \quad \text{and} \quad L_{\text{layout}} = L_{\text{schematic}}$$
3. **Series & Parallel Reductions:**
   - When NCC encounters parallel transistors with identical $L$, it sums their widths:
     $$W_{\text{eff}} = \sum W_i$$
   - When NCC encounters series transistors with identical $W$, it computes equivalent series channel lengths.

---

## 5. Physical Layout Disciplines for Memory IC Design

### 5.1 Strictly Manhattan (Perpendicular) Routing
- **Rule:** IC fabrication masks require purely rectilinear Manhattan geometry.
- **Electric Implementation:** All arcs must be strictly horizontal ($\Delta Y = 0$) or vertical ($\Delta X = 0$). Diagonal arcs cause DRC off-grid geometry errors.
- **Validation Command:** `Edit > Cleanup Cell > Show Nonmanhattan` highlights any slanted wires.

### 5.2 Arc Constraint Types & Behavioral Modes
Electric provides powerful physical constraint propagation on arcs (`Chapter 5`):
1. **Rigid Arcs:** Constant length and orientation. When one node moves, the connected node moves identically.
2. **Fixed-Angle Arcs:** Arcs are constrained to remain strictly horizontal or vertical ($0^\circ$, $90^\circ$, $180^\circ$, $270^\circ$). Moving one endpoint stretches the arc along its axis without skewing.
3. **Slidable Arcs:** Arc endpoints can slide freely across the face of a wide port (such as a power rail or wide contact) without moving the target node.
4. **Arc End Extension:** Arcs automatically extend past their center endpoint by:
   $$\text{Extension} = \frac{1}{2} \times \text{Width}$$
   Ensures flush, gapless junctions at ports.

---

### 5.3 Active Diffusion Sharing
To achieve maximum packing density in SRAM peripherals and decoders:
- **Abutment:** Connect adjacent transistors with a continuous diffusion arc of length $0\lambda$ to $3\lambda$, or place diffusion contacts directly on shared nodes.
- **NAND Decoder Series Stack:** NMOS pull-down transistors share source/drain diffusions directly, eliminating intermediate contact resistance and parasitic capacitance.
- **Inverter PMOS / NMOS Fingers:** Parallel PMOS transistors share $V_{\text{DD}}$ contacts and output drains in a folded layout configuration.

---

### 5.4 Standard Cell Architecture & Snapping
To allow standard logic gates (Inverters, NAND, AND, Decoders) and 6T memory cells to tile seamlessly:
- **Standard Cell Height:** Fixed rail-to-rail distance (e.g., $V_{\text{DD}}$ at $Y = +38$, $\text{GND}$ at $Y = -38$; center-to-center pitch = $76\lambda$).
- **Rail Overhang:** Power and ground rails extend $2\lambda$ beyond cell bounding boxes on left and right edges.
  - When two cells are abutted side-by-side, their rails overlap by $4\lambda$, ensuring continuous conduction without DRC notch violations.
- **Transistor Placement:**
  - Pull-up PMOS network resides strictly in the upper half ($Y > 0$, N-Well).
  - Pull-down NMOS network resides strictly in the lower half ($Y < 0$, P-substrate).

---

## 6. Memory Array Generation (16 × 16 SRAM Core)

Building the 256-bit memory array requires systematic replication of the `6T_cell{lay}`.

### 6.1 Array Generation Methods

#### Method A: GUI Array Command (`Edit > Array...`)
- Select the `6T_cell{lay}` instance.
- Enter $X = 16$ (columns) and $Y = 16$ (rows).
- **Spacing Modes:**
  - *Edge overlap:* Negative value for overlapping rail boundaries.
  - *Centerline distance:* Exact $X$-pitch ($\Delta X$) and $Y$-pitch ($\Delta Y$).
- **Mirroring / Staggering:**
  - Check *Flip alternate rows* to share common $V_{\text{DD}}$ and $\text{GND}$ rails between adjacent cell rows.
  - Check *Flip alternate columns* to share vertical bitline tracks (`BIT` and `BITB`) and well taps.

#### Method B: Programmatic Generation via Jython (Recommended)
```python
# Programmatic 16x16 Array Instantiation
cell_proto = lib.findNodeProto("6T_cell{lay}")
pitch_x = 176.0  # Cell width in lambda
pitch_y = 110.0  # Cell height in lambda

for row in range(16):
    for col in range(16):
        pos_x = col * pitch_x
        pos_y = row * pitch_y
        # Flip alternating rows to share supply rails
        orient = Orientation.MY if (row % 2 == 1) else Orientation.IDENT
        inst = NodeInst.makeInstance(cell_proto, Point2D.Double(pos_x, pos_y),
                                     cell_proto.getDefWidth(), cell_proto.getDefHeight(),
                                     array_cell, orient, "cell_%d_%d" % (row, col))
```

---

### 6.2 Top-Metal Power, Ground & Clock Distribution
Per the project engineering requirements:
1. **Core Power ($V_{\text{DD}}$) & Ground ($\text{GND}$):**
   - Local rails on Metal-1 are strapped up to **Metal-6** using stacked via columns (`M1-M2-Con` $\rightarrow$ `M2-M3-Con` $\rightarrow$ `M3-M4-Con` $\rightarrow$ `M4-M5-Con` $\rightarrow$ `M5-M6-Con`).
   - Top Metal-6 runs as a low-resistance horizontal and vertical grid across the chip, eliminating IR drop and electromigration during simultaneous 16-bit row precharge.
2. **Balanced Clock Tree (`CLK`):**
   - Master clock input from the packaging pad is routed symmetrically using an H-Tree topology on **Metal-5**.
   - Equal path lengths to row decoders, column decoders, address registers, and sense amplifier latch enables eliminate clock skew.

---

## 7. Parasitic Extraction (PEX) & SPICE Deck Generation

To verify read static noise margin (SNM), write margin, access time, and maximum operating frequency ($F_{\max}$):

### 7.1 Parasitic Parameters Setup
Configure layer parasitics in `File > Preferences > Tools > Parasitic`:
- **Sheet Resistances ($R_\square$):**
  - Polysilicon: $\sim 8.0\ \Omega/\square$
  - Metal-1: $\sim 0.08\ \Omega/\square$
  - Metal-2 to Metal-5: $\sim 0.05\ \Omega/\square$
  - Metal-6 (Thick Top Metal): $\sim 0.02\ \Omega/\square$
- **Capacitance Models:**
  - Area Capacitance ($C_{\text{area}}$, $\text{aF}/\mu\text{m}^2$)
  - Fringe/Edge Capacitance ($C_{\text{perim}}$, $\text{aF}/\mu\text{m}$)
- **Max Series Resistance:** Set threshold to break long continuous bitline and wordline arcs into distributed $\Pi$ or T-lumped RC ladder segments.

---

### 7.2 Generating Post-Layout SPICE Netlists
- **Menu Command:** `Tools > Simulation (Spice) > Write Spice Deck...`
- **Settings:**
  - Set *Spice Engine* to `Spice3`, `LTspice`, or `HSPICE`.
  - Include Parasitic Capacitances: `Yes`.
  - Include Parasitic Resistors: `Yes`.
  - Level of Extraction: Full parasitic extraction.
- **Generated Netlist:** Produces exact transistor instances with geometric lengths ($L$), widths ($W$), source/drain areas ($AS, AD$), and perimeters ($PS, PD$), alongside parasitic node capacitors ($C$) and series resistors ($R$).

---

## 8. I/O Pad Frame & Chip Packaging Architecture

The SRAM communicates externally via strictly **5 signal pins** (plus $V_{\text{DD}}$ and $\text{GND}$):
1. `CLK` (Master Clock)
2. `CTRL` (Read / Write Control)
3. `ADDR_IN` (1-bit Serial Address)
4. `DIN` (1-bit Serial Data In)
5. `DOUT` (1-bit Serial Read Data Out)

### 8.1 Pad Frame Generator Specification (`Chapter 9-8-1`)
Electric generates complete pad rings from an ASCII specification deck (`padframe.txt`):
```text
celllibrary pad_library.jelib copy
cell padframe{lay}
views lay sch
core memory_core_top{lay}
align pad_bidir p_left p_right

; North Pad Ring
place pad_vdd
place pad_gnd
place pad_in tap=clk_pad export io=CLK
place pad_in tap=ctrl_pad export io=CTRL

rotate CCW
; West Pad Ring
place pad_in tap=addr_pad export io=ADDR_IN
place pad_in tap=din_pad export io=DIN

rotate CCW
; South Pad Ring
place pad_out tap=dout_pad export io=DOUT
place pad_vdd
place pad_gnd

rotate CCW
; East Pad Ring (Power strapping)
place pad_vdd
place pad_gnd
```

### 8.2 Packaging Parasitics Model
All 5 external signal pins and power rails must include the packaging RLC equivalent circuit:
```
           L_bond (1.5 nH)       R_bond (0.1 Ω)
Pad Pin o---UUUUUUU---------------/\/\/\/\-------+---> On-Chip Core Port
                                                 |
                                               ----- C_pad (0.8 pF)
                                               -----
                                                 |
                                                GND
```

---

## 9. Jython & Java Scripting Automation Reference

Electric VLSI 9.08 exposes its complete object model to Jython and BeanShell via Java packages under `com.sun.electric.*`.

### 9.1 Essential Java Class Map
| Fully-Qualified Java Class | Purpose & Role |
|---|---|
| `com.sun.electric.tool.Job` | UI control, thread management, getting current cell (`Job.getUserInterface().getCurrentCell()`) |
| `com.sun.electric.technology.Technology` | Technology database (`Technology.findTechnology("mocmos")`) |
| `com.sun.electric.technology.PrimitiveNode` | Primitive node prototype factory (`mocmos.findNodeProto("N-Transistor")`) |
| `com.sun.electric.technology.ArcProto` | Primitive arc prototype factory (`mocmos.findArcProto("Metal-1")`) |
| `com.sun.electric.database.hierarchy.Cell` | Cell container for schematics and layouts (`Cell.makeInstance(...)`) |
| `com.sun.electric.database.hierarchy.Library`| Jelib library database manager (`LibraryFiles.readEntireLibrary(...)`) |
| `com.sun.electric.database.topology.NodeInst`| Placed instance of a primitive or subcell (`NodeInst.makeInstance(...)`) |
| `com.sun.electric.database.topology.ArcInst` | Physical wire connecting two `PortInst` ports (`ArcInst.makeInstance(...)`) |
| `com.sun.electric.database.topology.PortInst`| Port instance on a specific placed `NodeInst` (`node.findPortInst("diff-left")`) |
| `com.sun.electric.database.hierarchy.Export` | Hierarchical interface pin (`Export.newInst(cell, portInst, name, characteristic)`) |
| `com.sun.electric.database.prototype.PortCharacteristic`| Port directional types (`PortCharacteristic.IN`, `OUT`, `BIDIR`, `PWR`, `GND`) |
| `com.sun.electric.util.math.Orientation` | Geometric transformations (`Orientation.IDENT`, `R90`, `R180`, `R270`, `MX`, `MY`) |
| `com.sun.electric.tool.ncc.Ncc` | Headless execution of Network Consistency Checking / LVS |
| `com.sun.electric.tool.drc.DRC` | Headless execution of hierarchical DRC engine |

---

### 9.2 Complete Jython Headless Automation Template
Below is the validated template for creating headless layout generators:

```python
import sys
import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric import Main
from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, Library
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.id import IdManager
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import DRC

def init_electric_headless():
    """Initializes Electric's headless UI dummy and ID manager."""
    for c in Main.getDeclaredClasses():
        if 'UserInterfaceDummy' in c.getName():
            ctor = c.getDeclaredConstructors()[0]
            ctor.setAccessible(True)
            dummy = ctor.newInstance([])
            Job.setUserInterface(dummy)
            break
    IdManager()

def build_manhattan_arc(arc_proto, ep, port_a, port_b):
    """Enforces 100% perpendicular routing (zero diagonal skew)."""
    pt_a = port_a.getCenter()
    pt_b = port_b.getCenter()
    dx = abs(pt_a.getX() - pt_b.getX())
    dy = abs(pt_a.getY() - pt_b.getY())
    if dx > 0.001 and dy > 0.001:
        raise ValueError("Non-Manhattan arc prohibited between (%.1f, %.1f) and (%.1f, %.1f)" % 
                         (pt_a.getX(), pt_a.getY(), pt_b.getX(), pt_b.getY()))
    return ArcInst.makeInstance(arc_proto, ep, port_a, port_b)

def run_headless_verification(cell_lay, cell_sch):
    """Runs automated hierarchical DRC and NCC (LVS)."""
    print("Running DRC on %s..." % cell_lay.getName())
    drc_errors = DRC.checkHierarchical(cell_lay)
    print("DRC Error Count: %d" % drc_errors)
    
    if cell_sch is not None:
        print("Running NCC (LVS) between %s and %s..." % (cell_lay.getName(), cell_sch.getName()))
        ncc_opts = NccOptions()
        ncc_opts.checkTransistorSizes = True
        ncc_res = Ncc.compare(cell_lay, cell_sch, ncc_opts)
        print("NCC Result: %s" % ("MATCH CLEAN" if ncc_res.isMatch() else "MISMATCH"))
```

---

## 10. Electric VLSI Keyboard & Mouse Cheat Sheet

| Keystroke / Action | Tool Function | Operational Meaning |
|---|---|---|
| **Left Click** | Select | Selects node, arc, or export under mouse |
| **Right Click** | Wire / Connect | Creates connecting arc from highlighted port to target port |
| **Ctrl + Click** | Cycle Select | Cycles through overlapping geometry under cursor |
| **Shift + Click** | Multi-Select | Toggles object into current selection set |
| `Ctrl + G` | Grid Toggle | Shows / hides the layout alignment grid dots |
| `Ctrl + I` | Object Properties | Opens dialog for transistor sizing ($W, L$), arc widths, or cell properties |
| `Ctrl + J` | Rotate 90° CCW | Rotates selected node counter-clockwise by 90 degrees |
| `Ctrl + M` | Duplicate | Duplicates highlighted components at cursor location |
| `Ctrl + B` | Interactive Resize | Resizes selected node (e.g. well cover rectangles) interactively |
| `Ctrl + E` | Create Export | Opens export dialog to define input/output/power port |
| `Ctrl + D` | Down Hierarchy | Descends into the highlighted subcell instance for inspection |
| `Ctrl + U` | Up Hierarchy | Returns to parent cell in the hierarchy |
| `F5` | Hierarchical DRC | Executes full design rule check across all hierarchical levels |
| `>` / `<` | Step DRC Errors | Steps forward / backward through reported DRC error markers |
| `F2` | Auto-Stitch | Auto-connects touching or overlapping ports with appropriate arcs |
| `Delete` / `Backspace`| Delete | Removes highlighted nodes or arcs from current cell |
| `f` / `h` | Grid Pitch Scale | Makes alignment grid coarser (`f`) or finer (`h`) |

---

## 11. Layout Checklist for Subcell Sign-Off

Before any layout view is stamped verified for integration into higher-level memory blocks:
- [ ] **100% Manhattan Geometry:** Zero diagonal wires (`Show Nonmanhattan` reports clean).
- [ ] **Exact Transistor Sizing:** Layout $W$ and $L$ match transistor schematics identically.
- [ ] **Diffusion Sharing:** Series stacks and parallel pairs share source/drain diffusions.
- [ ] **Substrate & Well Taps:** Every PMOS island has $V_{\text{DD}}$ N-well tap; every NMOS island has $\text{GND}$ substrate tap within $200\lambda$.
- [ ] **Well Coverage:** Solid N-Well / P-Well coverage eliminates boundary DRC notches during abutment.
- [ ] **Standard Cell Pitch:** Power/ground rails align horizontally with $2\lambda$ boundary extension.
- [ ] **DRC Clean:** `0` errors reported by `Check Hierarchically (F5)`.
- [ ] **NCC (LVS) Clean:** Topology and transistor sizes match schematic view with zero discrepancies.
- [ ] **Export Verification:** All required hierarchical ports are exported with proper directionality (`IN`, `OUT`, `PWR`, `GND`).
