
# ============================================================
# Electric VLSI 9.08 - Jython
# 16 Write Driver Connections and Exports
# ============================================================

from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

DRIVER_CELL_NAME = "Write_driver"
EXPECTED_DRIVERS = 16

PIN_NAMES = {
    "vdd":  ["VDD", "vdd"],
    "gnd":  ["GND", "gnd"],
    "data": ["DATA", "data", "DIN", "Din"],
    "we":   ["WRITE_EN", "Write_EN", "WE", "we"],
    "bit":  ["BIT", "bit"],
    "bitb": ["BITB", "BITb", "bitb", "BIT_BAR"]
}

# ------------------------------------------------------------
# GET CURRENT CELL AND WIRE TYPE
# ------------------------------------------------------------

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Open the parent schematic first.")

tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

if wire is None:
    raise Exception("Could not find schematic wire prototype.")

# ------------------------------------------------------------
# FIND ALL WRITE DRIVER INSTANCES
# ------------------------------------------------------------

drivers = []
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    proto_name = str(node.getProto().getName())

    if proto_name.split("{")[0] == DRIVER_CELL_NAME:
        drivers.append(node)

if len(drivers) != EXPECTED_DRIVERS:
    raise Exception(
        "Expected 16 Write_driver instances, found %d"
        % len(drivers)
    )

# Sort left-to-right for predictable WE0 ... WE15 naming
drivers.sort(key=lambda n: n.getAnchorCenterX())

print("Found all 16 write drivers.")

# ------------------------------------------------------------
# HELPER: FIND A PIN
# ------------------------------------------------------------

def get_pin(node, candidates):
    for name in candidates:
        port = node.findPortInst(name)
        if port is not None:
            return port

    print("Instance:", node.getName())
    print("Candidate pins:", candidates)
    raise Exception("Required pin not found.")

# ------------------------------------------------------------
# HELPER: CHECK EXISTING EXPORTS
# ------------------------------------------------------------

def export_if_missing(port, name, characteristic):
    exports = cell.getPorts()

    while exports.hasNext():
        exp = exports.next()

        if str(exp.getName()) == name:
            print("Export already exists; skipped:", name)
            return

    # Correct API for this Electric environment
    Export.newInst(cell, port, name, characteristic)
    print("Exported:", name)

# ------------------------------------------------------------
# HELPER: CHECK CONNECTIVITY BEFORE WIRING
# ------------------------------------------------------------

def connect_if_needed(pin_a, pin_b):
    # Compare electrical networks to avoid adding a wire
    # when both pins are already electrically connected.
    netlist = cell.getNetlist()

    net_a = netlist.getNetwork(pin_a)
    net_b = netlist.getNetwork(pin_b)

    if net_a is not None and net_b is not None and net_a == net_b:
        return

    ArcInst.makeInstance(wire, pin_a, pin_b)

# ------------------------------------------------------------
# COLLECT ALL DRIVER PINS
# ------------------------------------------------------------

pins = []

for i, driver in enumerate(drivers):
    pins.append({
        "vdd":  get_pin(driver, PIN_NAMES["vdd"]),
        "gnd":  get_pin(driver, PIN_NAMES["gnd"]),
        "data": get_pin(driver, PIN_NAMES["data"]),
        "we":   get_pin(driver, PIN_NAMES["we"]),
        "bit":  get_pin(driver, PIN_NAMES["bit"]),
        "bitb": get_pin(driver, PIN_NAMES["bitb"])
    })

print("All required pins found.")

# ------------------------------------------------------------
# CONNECT SHARED VDD, GND AND DATA
# ------------------------------------------------------------

for key in ["vdd", "gnd", "data"]:
    for i in range(EXPECTED_DRIVERS - 1):
        connect_if_needed(pins[i][key], pins[i + 1][key])

print("Shared VDD, GND and DATA connections checked.")

# ------------------------------------------------------------
# EXPORT SHARED SIGNALS
# ------------------------------------------------------------

export_if_missing(
    pins[0]["vdd"], "VDD", PortCharacteristic.PWR
)

export_if_missing(
    pins[0]["gnd"], "GND", PortCharacteristic.GND
)

export_if_missing(
    pins[0]["data"], "DATA", PortCharacteristic.IN
)

# ------------------------------------------------------------
# EXPORT WRITE ENABLES AND BIT LINES
# ------------------------------------------------------------

for i in range(EXPECTED_DRIVERS):

    # Individual write enable for each column
    export_if_missing(
        pins[i]["we"],
        "WE%d" % i,
        PortCharacteristic.IN
    )

    # Bit line and complementary bit line
    export_if_missing(
        pins[i]["bit"],
        "BIT%d" % i,
        PortCharacteristic.BIDIR
    )

    export_if_missing(
        pins[i]["bitb"],
        "BITB%d" % i,
        PortCharacteristic.BIDIR
    )

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("")
print("========================================")
print("WRITE DRIVER SETUP COMPLETE")
print("========================================")
print("Drivers found: 16")
print("Shared exports: VDD, GND, DATA")
print("Write enables: WE0 to WE15")
print("Bit lines: BIT0 to BIT15")
print("Complementary lines: BITB0 to BITB15")
print("Expected total exports: 51")
print("========================================")
