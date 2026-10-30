# ============================================================
# Electric VLSI 9.08 - 4-to-16 DECODER AUTOMATION SCRIPT
# Reuses verified patterns from scripts/04_connect_sram_top.py
#
# Connects:
#   - 4 Input Inverters (Not@0..3) for A0..A3 true & complement
#   - 16 4-input NAND gates (Nand@0..15) for minterms m0..m15
#   - 16 Output Inverters (Not@4..19) to create active-high outputs
#   - All VDD and GND pins across all 36 gates
#
# Hierarchical Exports Created:
#   - Inputs: A0, A1, A2, A3
#   - Outputs: OUT0..OUT15 (clean, buffered active-high select lines)
#   - Note: Complementary gate enable is generated locally inside/beside
#           the transmission gate block to avoid routing 32 global wires.
#   - Supplies: VDD, GND
# ============================================================

from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

# ------------------------------------------------------------
# 1. SETUP & CURRENT CELL VALIDATION
# ------------------------------------------------------------

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Please open the 4-to-16 Decoder schematic first in Electric VLSI.")

print("Connecting Decoder in cell: %s" % cell.getName())

tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

if wire is None:
    raise Exception("Cannot find schematic wire prototype.")

# ------------------------------------------------------------
# 2. COLLECT INSTANCES
# ------------------------------------------------------------

not_gates = {}
nand_gates = {}

nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    name = str(node.getName())
    proto_name = str(node.getProto().getName()).lower()

    # Identify NOT / Inverter instances
    if "@" in name and any(k in name.lower() for k in ["not", "inv"]):
        try:
            idx = int(name.split("@")[1])
            not_gates[idx] = node
        except ValueError:
            pass

    # Identify NAND instances
    elif "@" in name and "nand" in name.lower():
        try:
            idx = int(name.split("@")[1])
            nand_gates[idx] = node
        except ValueError:
            pass

print("Found %d NOT gates and %d NAND gates." % (len(not_gates), len(nand_gates)))

if len(not_gates) < 20:
    raise Exception("Expected at least 20 NOT gates (Not@0..19), but found %d." % len(not_gates))

if len(nand_gates) < 16:
    raise Exception("Expected 16 NAND gates (Nand@0..15), but found %d." % len(nand_gates))

for i in range(20):
    if i not in not_gates:
        raise Exception("Missing NOT gate instance: Not@%d" % i)

for i in range(16):
    if i not in nand_gates:
        raise Exception("Missing NAND gate instance: Nand@%d" % i)

print("Instance validation successful: Not@0..19 and Nand@0..15 present.")

# ------------------------------------------------------------
# 3. HELPER FUNCTIONS FOR ROBUST PIN LOOKUP & WIRING
# ------------------------------------------------------------

def pin(node, names):
    """Finds a port instance trying a list of common alias names."""
    if isinstance(names, str):
        names = [names]
    for n in names:
        p = node.findPortInst(n)
        if p is not None:
            return p
    # If not found by name, try case-insensitive search
    ports = node.getProto().getPorts()
    while ports.hasNext():
        port = ports.next()
        pname = str(port.getName())
        for n in names:
            if pname.lower() == n.lower():
                return node.findPortInst(pname)
    raise Exception("Missing pin %s on instance %s" % (names, node.getName()))

def connect(a, b):
    """Connects two ports with a wire if not already on the same electrical net."""
    netlist = cell.getNetlist()
    na = netlist.getNetwork(a)
    nb = netlist.getNetwork(b)

    if na is not None and nb is not None and na == nb:
        return

    arc = ArcInst.makeInstance(wire, a, b)
    if arc is None:
        print("WARNING: ArcInst creation returned None between %s and %s" % (a, b))

def connect_chain(port_list):
    """Chains a sequence of ports together into a single continuous net."""
    for i in range(len(port_list) - 1):
        connect(port_list[i], port_list[i + 1])

def export_if_missing(p, name, characteristic):
    """Exports a port to the parent cell interface if not already exported."""
    exports = cell.getPorts()
    while exports.hasNext():
        exp = exports.next()
        if str(exp.getName()) == name:
            print("Export '%s' already exists; skipping." % name)
            return

    Export.newInst(cell, p, name, characteristic)
    print("Exported port: %s" % name)

# ------------------------------------------------------------
# 4. PIN ALIAS DEFINITIONS
# ------------------------------------------------------------

NOT_IN  = ["IN", "in", "A", "a"]
NOT_OUT = ["OUT", "out", "Y", "y"]

NAND_A   = ["A", "a", "in-1", "IN1", "in1"]
NAND_B   = ["B", "b", "in-2", "IN2", "in2"]
NAND_C   = ["C", "c", "in-3", "IN3", "in3"]
NAND_D   = ["D", "d", "in-4", "IN4", "in4"]
NAND_OUT = ["OUT", "out", "Y", "y"]

VDD_NAMES = ["VDD", "vdd", "Vdd", "Pwr", "PWR"]
GND_NAMES = ["GND", "gnd", "Gnd", "VSS", "vss"]

# ------------------------------------------------------------
# 5. INPUT INVERTERS & ADDRESS BIT MAPPING
# Mapping:
#   Not@0 -> Bit 0 (LSB, A0)
#   Not@1 -> Bit 1 (A1)
#   Not@2 -> Bit 2 (A2)
#   Not@3 -> Bit 3 (MSB, A3)
# ------------------------------------------------------------

print("Connecting Address Inputs A0..A3...")

addr_true_pins = []
addr_comp_pins = []

for bit in range(4):
    in_pin  = pin(not_gates[bit], NOT_IN)
    out_pin = pin(not_gates[bit], NOT_OUT)

    addr_true_pins.append(in_pin)
    addr_comp_pins.append(out_pin)

    # Export inputs A0..A3
    export_if_missing(in_pin, "A%d" % bit, PortCharacteristic.IN)

# ------------------------------------------------------------
# 6. CONNECT NAND GATES (16 MINTERMS)
#
# Minterm k = (b3, b2, b1, b0) where:
#   b3 is A3 (NAND input A)
#   b2 is A2 (NAND input B)
#   b1 is A1 (NAND input C)
#   b0 is A0 (NAND input D)
# ------------------------------------------------------------

print("Connecting 16 NAND minterms...")

for k in range(16):
    nand_node = nand_gates[k]

    b0 = (k >> 0) & 1
    b1 = (k >> 1) & 1
    b2 = (k >> 2) & 1
    b3 = (k >> 3) & 1

    # Connect A3 / A3_B to input A
    src_3 = addr_true_pins[3] if b3 == 1 else addr_comp_pins[3]
    connect(pin(nand_node, NAND_A), src_3)

    # Connect A2 / A2_B to input B
    src_2 = addr_true_pins[2] if b2 == 1 else addr_comp_pins[2]
    connect(pin(nand_node, NAND_B), src_2)

    # Connect A1 / A1_B to input C
    src_1 = addr_true_pins[1] if b1 == 1 else addr_comp_pins[1]
    connect(pin(nand_node, NAND_C), src_1)

    # Connect A0 / A0_B to input D
    src_0 = addr_true_pins[0] if b0 == 1 else addr_comp_pins[0]
    connect(pin(nand_node, NAND_D), src_0)

# ------------------------------------------------------------
# 7. CONNECT OUTPUT INVERTERS & EXPORT DECODER OUTPUTS
#
# Nand@k.OUT connects to Not@(k + 4).IN
# Not@(k + 4).OUT is active-high output OUTk
# Local inverters inside/beside transmission gates generate the PMOS gate enable
# ------------------------------------------------------------

print("Connecting Output Inverters and Exports...")

for k in range(16):
    nand_out_pin = pin(nand_gates[k], NAND_OUT)
    inv_in_pin   = pin(not_gates[k + 4], NOT_IN)
    inv_out_pin  = pin(not_gates[k + 4], NOT_OUT)

    # Connect NAND output to Inverter input
    connect(nand_out_pin, inv_in_pin)

    # Export clean, buffered active-high output (AND result)
    export_if_missing(inv_out_pin, "OUT%d" % k, PortCharacteristic.OUT)

# ------------------------------------------------------------
# 8. COMMON VDD AND GND DISTRIBUTION ACROSS ALL 36 GATES
# ------------------------------------------------------------

print("Routing VDD and GND nets across all 36 gates...")

all_nodes = [not_gates[i] for i in range(20)] + [nand_gates[i] for i in range(16)]

vdd_pins = []
gnd_pins = []

for node in all_nodes:
    try:
        vdd_pins.append(pin(node, VDD_NAMES))
    except Exception:
        pass
    try:
        gnd_pins.append(pin(node, GND_NAMES))
    except Exception:
        pass

if len(vdd_pins) > 0:
    connect_chain(vdd_pins)
    export_if_missing(vdd_pins[0], "VDD", PortCharacteristic.PWR)
    print("VDD routed across %d nodes." % len(vdd_pins))

if len(gnd_pins) > 0:
    connect_chain(gnd_pins)
    export_if_missing(gnd_pins[0], "GND", PortCharacteristic.GND)
    print("GND routed across %d nodes." % len(gnd_pins))

print("\n============================================================")
print("SUCCESS: 4-to-16 Decoder completely connected and exported!")
print("============================================================")
