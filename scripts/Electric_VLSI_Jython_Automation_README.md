# Electric VLSI Jython Automation — Quick Reference

A black-box-level reference for the Electric VLSI functions used to automate the `16bit_array{sch}` SRAM schematic.

The scripts use **Jython** (Python syntax running on the Java platform), not JavaScript. Electric provides the underlying objects and APIs; the script calls those APIs to inspect cells, find pins, create wires, add exports, and verify connectivity.

## 1. Workflow at a glance

1. Get the currently active schematic.
2. Find its node instances.
3. Identify the required instances by name.
4. Find pins on those instances by exported pin name.
5. Create wires between the selected ports.
6. Create parent-level exports for pins that must be accessible hierarchically.
7. Inspect the netlist and run DRC.

## 2. Core functions

### `Job.getUserInterface().getCurrentCell()`

**Purpose:** Gets the cell currently open/active in Electric.

**Arguments:** None.

**Returns:** The current `Cell` object.

**Typical use:**
```python
from com.sun.electric.tool import Job
cell = Job.getUserInterface().getCurrentCell()
```

**Black-box view:** “Give me the schematic I am editing.”

---

### `cell.getNodes()`

**Purpose:** Provides an iterator over the nodes/instances in the current cell.

**Arguments:** None.

**Returns:** An iterator-like object. Use `hasNext()` and `next()` to traverse it.

**Typical use:**
```python
nodes = cell.getNodes()
while nodes.hasNext():
    node = nodes.next()
```

**Black-box view:** “List the objects placed in this schematic.”

---

### `node.getName()`

**Purpose:** Gets the name of a node/instance.

**Arguments:** None.

**Returns:** A string, such as `6T_cell@3`.

**Black-box view:** “What is this instance called?”

---

### `node.getProto()`

**Purpose:** Gets the prototype associated with the node, such as the reusable `6T_cell` cell.

**Arguments:** None.

**Returns:** The prototype object.

**Black-box view:** “Which reusable cell or primitive is this instance based on?”

**Terminology:** `6T_cell@3` is an instance; `6T_cell` is its prototype.

---

### `node.findPortInst(port_name)`

**Purpose:** Finds a named port instance on a particular node/instance.

**Arguments:**
- `port_name` — string containing the port name, e.g. `"WL"`, `"BIT"`, `"BITB"`, `"VDD"`, or `"GND"`.

**Returns:** The matching port instance, if found.

**Typical use:**
```python
wl_pin = node.findPortInst("WL")
bit_pin = node.findPortInst("BIT")
```

**Black-box view:** “On this specific SRAM instance, find the pin with this name.”

**Important:** This means coordinates do not need to be manually looked up for ordinary port-to-port connections. You still need the correct instance and pin name.

---

### `port.getCenter()`

**Purpose:** Retrieves the center location of a port.

**Arguments:** None.

**Returns:** A point/coordinate object.

**Typical use:**
```python
position = node.findPortInst("WL").getCenter()
```

**Black-box view:** “Where is this pin located in the schematic?”

**When useful:** Debugging geometry or tasks that genuinely need coordinates. It was not required for the SRAM pin-to-pin wires in this workflow.

---

### `Technology.findTechnology(technology_name)`

**Purpose:** Finds a technology by name.

**Arguments:**
- `technology_name` — string; `"schematic"` was used here.

**Returns:** The technology object, if found.

**Typical use:**
```python
from com.sun.electric.technology import Technology
tech = Technology.findTechnology("schematic")
```

**Black-box view:** “Get Electric's schematic drawing rules and object types.”

---

### `tech.findArcProto(arc_name)`

**Purpose:** Finds an arc prototype (wire type) in the selected technology.

**Arguments:**
- `arc_name` — string; `"wire"` was used for ordinary schematic wires.

**Returns:** The arc prototype.

**Typical use:**
```python
wire = tech.findArcProto("wire")
```

**Black-box view:** “Select the type of connection to create.”

---

### `ArcInst.makeInstance(arc_proto, port_a, port_b)`

**Purpose:** Creates an arc/wire connecting two port instances.

**Arguments:**
- `arc_proto` — wire/arc type, such as the schematic `"wire"` prototype.
- `port_a` — first endpoint port instance.
- `port_b` — second endpoint port instance.

**Returns:** The created arc object, or potentially `None` if creation fails.

**Typical use:**
```python
from com.sun.electric.database.topology import ArcInst

arc = ArcInst.makeInstance(
    wire,
    instances[0].findPortInst("WL"),
    instances[1].findPortInst("WL")
)
```

**Black-box view:** “Draw a wire between these two actual pins.”

**Important:** It connects the selected ports; it does not automatically connect every pin with the same name. A loop was used to connect consecutive SRAM instances, making the whole chain one electrical net.

---

### `Export.newInst(parent_cell, internal_port, export_name, characteristic)`

**Purpose:** Creates a port/export on the parent cell that exposes an internal instance port to higher levels of the design hierarchy.

**Arguments:**
- `parent_cell` — the cell receiving the export.
- `internal_port` — the port instance inside that cell to expose.
- `export_name` — name visible on the parent cell, e.g. `"BIT7"`.
- `characteristic` — port characteristic, e.g. `PortCharacteristic.BIDIR` for a bidirectional bitline.

**Returns:** The created export object, depending on API behavior.

**Typical use:**
```python
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

Export.newInst(
    cell,
    instances[7].findPortInst("BIT"),
    "BIT7",
    PortCharacteristic.BIDIR
)
```

**Black-box view:** “Expose this internal pin as a named port on the parent schematic.”

**Version note:** In the Electric environment used for this project, `Export.newInstance(...)` with these four arguments raised `TypeError: newInstance(): expected 0 args; got 4`. The working call used `Export.newInst(...)`.

---

### `PortCharacteristic.BIDIR`

**Purpose:** Marks an export as bidirectional.

**Arguments:** None; this is an enum-like constant.

**Typical use:** Used for SRAM bitlines that can be driven during writes and observed/sensed during reads.

**Other characteristics observed in this environment:** `IN`, `OUT`, `PWR`, `GND`, and `UNKNOWN` were present. Choose characteristics according to the intended interface and the Electric API.

---

### `cell.getNetlist()`

**Purpose:** Retrieves the cell's electrical netlist representation.

**Arguments:** None.

**Returns:** A netlist object.

**Typical use:**
```python
netlist = cell.getNetlist()
```

**Black-box view:** “Give me Electric's interpretation of the circuit connectivity.”

---

### `netlist.getNetwork(port_instance)`

**Purpose:** Gets the electrical network containing a given port instance.

**Arguments:**
- `port_instance` — a port instance, such as `node.findPortInst("WL")`.

**Returns:** A network object.

**Typical use:**
```python
netlist = cell.getNetlist()
wl_net = netlist.getNetwork(node.findPortInst("WL"))
vdd_net = netlist.getNetwork(node.findPortInst("VDD"))
```

**Black-box view:** “Which electrical net does this pin belong to?”

**Use:** Compare the networks of pins to check whether two ports are on the same net. This was used to verify that WL, VDD, and GND remained separate.

---

## 3. Common pattern: connect a named signal across instances

This example connects the same named port across 16 instances in a chain. It assumes `instances` is a dictionary mapping indices `0` through `15` to the corresponding node objects, and `wire` has already been found.

```python
for i in range(15):
    p0 = instances[i].findPortInst("WL")
    p1 = instances[i + 1].findPortInst("WL")
    arc = ArcInst.makeInstance(wire, p0, p1)
```

The same pattern was used for `"VDD"` and `"GND"`.

**Why a chain works:** connecting instance 0 to 1, 1 to 2, and so on puts all 16 pins on the same connected net. It is not necessary to draw 15 separate wires from every pin to a single central point.

## 4. Instance indexing pattern

Electric instance names in this design follow the pattern `6T_cell@0`, `6T_cell@1`, ..., `6T_cell@15`.

```python
instances = {}
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    name = node.getName()
    if name.startswith("6T_cell@"):
        index = int(name.split("@")[1])
        instances[index] = node
```

**Black-box view:** scan the schematic objects, select those belonging to the SRAM-cell instances, extract the index from each name, and store each instance for easy access.

The script should check that 16 expected instances were found before making connections.

## 5. What each stage changes

- **Finding objects and ports:** reads/inspects the design; does not itself wire anything.
- **`ArcInst.makeInstance(...)`:** changes the schematic by creating a wire.
- **`Export.newInst(...)`:** changes the cell interface by adding a parent-level export.
- **`getNetlist()` / `getNetwork(...)`:** queries the circuit's interpreted connectivity.
- **DRC:** checks design-rule violations; it does not replace a functional connectivity review.

## 6. Practical cautions

1. **Names must match exactly.** `findPortInst("BITB")` needs a port actually named `BITB` on that instance.
2. **Instance and prototype are different.** The instance identifies a placement; the prototype describes the reusable cell definition.
3. **A wire function does not infer design intent.** The script must decide which two pins should connect.
4. **Check for duplicate wires/exports when rerunning scripts.** Re-running a script can create duplicates unless it checks existing objects first.
5. **DRC-clean does not necessarily mean functionally correct.** Verify the netlist and, where appropriate, simulate read/write behavior.
6. **Hierarchy matters.** Export only the pins needed by the next level of the design.
7. **Array topology matters.** For a conventional SRAM, word lines are shared across columns within a row, while bitline pairs are shared vertically down columns. Make higher-level connections according to the intended array architecture.

## 7. Minimal mental model

Think of Electric as exposing a few kinds of objects:

- **Cell:** the schematic/design block.
- **Node:** an instance or other placed schematic object.
- **Port instance:** a pin on a particular instance.
- **Arc:** a wire/connection between ports.
- **Export:** a port exposed at the cell boundary.
- **Netlist/network:** Electric's interpreted electrical connectivity.

The automation script finds the correct objects, selects named pins, asks Electric to create wires or exports, and then checks the result. You do not need to understand Java internals to use this workflow effectively.
