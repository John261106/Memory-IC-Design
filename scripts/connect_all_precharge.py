
# Electric VLSI 9.08 - Precharge circuit wiring
# Assumes 16 Precharge_ckt instances already exist
# Exports: PCB, VDD, BIT0-BIT15, BITB0-BITB15

from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

cell = Job.getUserInterface().getCurrentCell()

tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

# Find all precharge instances
instances = []
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    if node.getProto().getName() == "Precharge_ckt":
        instances.append(node)

if len(instances) != 16:
    print("ERROR: Expected 16 Precharge_ckt instances.")
    print("Found:", len(instances))

else:
    # Sort by position for predictable ordering
    instances.sort(
        key=lambda n: (
            -n.getAnchorCenter().getY(),
            n.getAnchorCenter().getX()
        )
    )

    print("Found 16 precharge instances.")

    # Connect all PCB pins together
    for i in range(15):
        p0 = instances[i].findPortInst("PCB")
        p1 = instances[i + 1].findPortInst("PCB")
        ArcInst.makeInstance(wire, p0, p1)

    # Connect all VDD pins together
    for i in range(15):
        p0 = instances[i].findPortInst("VDD")
        p1 = instances[i + 1].findPortInst("VDD")
        ArcInst.makeInstance(wire, p0, p1)

    print("Connected PCB pins.")
    print("Connected VDD pins.")

    # Export shared PCB control
    if cell.findExport("PCB") is None:
        Export.newInst(
            cell,
            instances[0].findPortInst("PCB"),
            "PCB",
            PortCharacteristic.IN
        )

    # Export shared VDD supply
    if cell.findExport("VDD") is None:
        Export.newInst(
            cell,
            instances[0].findPortInst("VDD"),
            "VDD",
            PortCharacteristic.PWR
        )

    # Export individual BIT and BITB pins
    created = 0

    for i in range(16):
        bit_name = "BIT" + str(i)
        bitb_name = "BITB" + str(i)

        if cell.findExport(bit_name) is None:
            Export.newInst(
                cell,
                instances[i].findPortInst("BIT"),
                bit_name,
                PortCharacteristic.BIDIR
            )
            created += 1

        if cell.findExport(bitb_name) is None:
            Export.newInst(
                cell,
                instances[i].findPortInst("BITB"),
                bitb_name,
                PortCharacteristic.BIDIR
            )
            created += 1

    print("Created individual bitline exports:", created)
    print("DONE. Inspect the schematic and run DRC.")
