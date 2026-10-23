
# ============================================================
# Electric VLSI 9.08 - 16 x 16 SRAM TOP-LEVEL CONNECTIONS
# Uses existing instances. Does NOT create new instances.
#
# Assumed instance indexing:
#   6T_cell@0..255       -> row-major: index = row*16 + col
#   Precharg@0..15       -> column 0..15
#   Write_dr@0..15       -> column 0..15
#   Sense_am@0..15       -> column 0..15
#
# Shared: VDD, GND, DATA, PCB
# Individual: WL0..WL15, WE0..WE15, RE0..RE15
# Sense outputs: SENSE0..SENSE15
# ============================================================

from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

N = 16
TOTAL_CELLS = N * N

# ------------------------------------------------------------
# GET CURRENT CELL AND WIRE PROTOTYPE
# ------------------------------------------------------------

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Open the SRAM top-level schematic first.")

tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

if wire is None:
    raise Exception("Cannot find schematic wire prototype.")

print("Top-level cell:", cell.getName())

# ------------------------------------------------------------
# COLLECT INSTANCES USING THEIR INSTANCE NAMES
# ------------------------------------------------------------

cells = {}
precharges = {}
write_drivers = {}
sense_amps = {}

nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    name = str(node.getName())
    proto = str(node.getProto().getName())

    if name.startswith("6T_cell@") and proto == "6T_cell":
        idx = int(name.split("@")[1])
        cells[idx] = node

    elif name.startswith("Precharg@") and proto == "Precharge_ckt":
        idx = int(name.split("@")[1])
        precharges[idx] = node

    elif name.startswith("Write_dr@") and proto == "Write_driver":
        idx = int(name.split("@")[1])
        write_drivers[idx] = node

    elif name.startswith("Sense_am@") and proto == "Sense_amp":
        idx = int(name.split("@")[1])
        sense_amps[idx] = node

# Validate all expected instances before modifying the schematic.
if len(cells) != TOTAL_CELLS:
    raise Exception("Expected 256 cells; found %d" % len(cells))

if len(precharges) != N:
    raise Exception("Expected 16 precharges; found %d" % len(precharges))

if len(write_drivers) != N:
    raise Exception("Expected 16 write drivers; found %d" % len(write_drivers))

if len(sense_amps) != N:
    raise Exception("Expected 16 sense amplifiers; found %d" % len(sense_amps))

for i in range(TOTAL_CELLS):
    if i not in cells:
        raise Exception("Missing 6T_cell index %d" % i)

for i in range(N):
    if i not in precharges or i not in write_drivers or i not in sense_amps:
        raise Exception("Missing peripheral instance index %d" % i)

print("Validated: 256 cells, 16 precharges, 16 drivers, 16 sense amps.")

# ------------------------------------------------------------
# PIN LOOKUP
# ------------------------------------------------------------

def pin(node, name):
    p = node.findPortInst(name)
    if p is None:
        raise Exception(
            "Missing pin %s on instance %s" % (name, node.getName())
        )
    return p

# ------------------------------------------------------------
# CONNECTION HELPER
# Avoid adding a wire if pins already share a network.
# ------------------------------------------------------------

def connect(a, b):
    netlist = cell.getNetlist()
    na = netlist.getNetwork(a)
    nb = netlist.getNetwork(b)

    if na is not None and nb is not None and na == nb:
        return

    arc = ArcInst.makeInstance(wire, a, b)

    if arc is None:
        print("WARNING: wire creation returned None.")

def connect_chain(port_list):
    # Connecting adjacent ports makes one continuous net.
    for i in range(len(port_list) - 1):
        connect(port_list[i], port_list[i + 1])

# ------------------------------------------------------------
# EXPORT HELPER - Electric 9.08 API: Export.newInst()
# ------------------------------------------------------------

def export_if_missing(p, name, characteristic):
    exports = cell.getPorts()

    while exports.hasNext():
        exp = exports.next()
        if str(exp.getName()) == name:
            print("Export exists; skipped:", name)
            return

    Export.newInst(cell, p, name, characteristic)
    print("Exported:", name)

# ------------------------------------------------------------
# 1. WORD LINES: 16 ROWS
# ------------------------------------------------------------

print("Connecting word lines...")

for row in range(N):
    row_pins = []

    for col in range(N):
        idx = row * N + col
        row_pins.append(pin(cells[idx], "WL"))

    connect_chain(row_pins)

    export_if_missing(
        row_pins[0], "WL%d" % row, PortCharacteristic.IN
    )

# ------------------------------------------------------------
# 2. BIT LINES: 16 COLUMNS, EACH WITH BIT AND BITB
# Connect all 16 SRAM cells, precharge, driver, and sense amp
# on the corresponding column.
# ------------------------------------------------------------

print("Connecting differential bit lines...")

for col in range(N):
    bit_pins = []
    bitb_pins = []

    for row in range(N):
        idx = row * N + col
        bit_pins.append(pin(cells[idx], "BIT"))
        bitb_pins.append(pin(cells[idx], "BITB"))

    # Add peripheral pins to the same column nets.
    bit_pins.append(pin(precharges[col], "BIT"))
    bit_pins.append(pin(write_drivers[col], "BIT"))
    bit_pins.append(pin(sense_amps[col], "BIT"))

    bitb_pins.append(pin(precharges[col], "BITB"))
    bitb_pins.append(pin(write_drivers[col], "BITB"))
    bitb_pins.append(pin(sense_amps[col], "BITB"))

    connect_chain(bit_pins)
    connect_chain(bitb_pins)

# ------------------------------------------------------------
# 3. COMMON POWER AND GROUND
# ------------------------------------------------------------

print("Connecting VDD and GND...")

vdd_pins = []
gnd_pins = []

for idx in range(TOTAL_CELLS):
    vdd_pins.append(pin(cells[idx], "VDD"))
    gnd_pins.append(pin(cells[idx], "GND"))

for col in range(N):
    vdd_pins.append(pin(precharges[col], "VDD"))
    vdd_pins.append(pin(write_drivers[col], "VDD"))
    vdd_pins.append(pin(sense_amps[col], "VDD"))
    gnd_pins.append(pin(write_drivers[col], "GND"))
    gnd_pins.append(pin(sense_amps[col], "GND"))

connect_chain(vdd_pins)
connect_chain(gnd_pins)

export_if_missing(
    vdd_pins[0], "VDD", PortCharacteristic.PWR
)
export_if_missing(
    gnd_pins[0], "GND", PortCharacteristic.GND
)

# ------------------------------------------------------------
# 4. SHARED WRITE DATA
# All drivers receive the same data input.
# Separate WE signals determine which driver is enabled.
# ------------------------------------------------------------

print("Connecting write data...")

data_pins = []

for col in range(N):
    data_pins.append(pin(write_drivers[col], "DATA"))

connect_chain(data_pins)

export_if_missing(
    data_pins[0], "DATA", PortCharacteristic.IN
)

# ------------------------------------------------------------
# 5. INDIVIDUAL WRITE ENABLES
# ------------------------------------------------------------

print("Exporting individual write enables...")

for col in range(N):
    we_pin = pin(write_drivers[col], "WRITE_EN")

    export_if_missing(
        we_pin, "WE%d" % col, PortCharacteristic.IN
    )

# ------------------------------------------------------------
# 6. PRECHARGE CONTROL
# Common PCB control shared by all 16 precharge circuits.
# ------------------------------------------------------------

print("Connecting precharge control...")

pcb_pins = []

for col in range(N):
    pcb_pins.append(pin(precharges[col], "PCB"))

connect_chain(pcb_pins)

export_if_missing(
    pcb_pins[0], "PCB", PortCharacteristic.IN
)

# ------------------------------------------------------------
# 7. INDIVIDUAL SENSE AMPLIFIER READ ENABLES
# RE0..RE15 remain independent.
# ------------------------------------------------------------

print("Exporting individual read enables and sense outputs...")

for col in range(N):
    re_pin = pin(sense_amps[col], "READ_EN")
    sense_pin = pin(sense_amps[col], "SENSE")

    export_if_missing(
        re_pin, "RE%d" % col, PortCharacteristic.IN
    )

    export_if_missing(
        sense_pin, "SENSE%d" % col, PortCharacteristic.OUT
    )

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("")
print("============================================")
print("SRAM TOP-LEVEL CONNECTION PASS COMPLETE")
print("============================================")
print("Memory cells       : 256")
print("Word lines         : WL0..WL15")
print("Bit-line pairs     : BIT0..BIT15 and BITB0..BITB15")
print("Precharge circuits : 16, common PCB")
print("Write drivers      : 16, common DATA")
print("Write enables      : WE0..WE15")
print("Sense amplifiers   : 16")
print("Read enables       : RE0..RE15 (individual)")
print("Sense outputs      : SENSE0..SENSE15")
print("Power exports      : VDD, GND")
print("============================================")
print("NOTE: Row/column decoders and output MUX")
print("are not instantiated by this script.")
print("Verify connectivity and simulate before layout.")
print("============================================")
