from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

cell = Job.getUserInterface().getCurrentCell()
tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

# --------------------------------------------------
# 1. Sort instances by physical position
#    Top-to-bottom, left-to-right
# --------------------------------------------------

items = []
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    if node.getName().startswith("6T_cell@"):
        pos = node.getAnchorCenter()
        items.append((pos.getY(), pos.getX(), node))

if len(items) != 256:
    print("ERROR: Expected 256 cells, found", len(items))
else:
    items.sort(key=lambda item: (-item[0], item[1]))

    # array[row][col] gives the cell at that position
    array = []
    for row in range(16):
        array.append([])
        for col in range(16):
            array[row].append(items[row * 16 + col][2])

    # --------------------------------------------------
    # 2. Connect word lines horizontally
    # --------------------------------------------------

    for row in range(16):
        for col in range(15):
            p0 = array[row][col].findPortInst("WL")
            p1 = array[row][col + 1].findPortInst("WL")
            ArcInst.makeInstance(wire, p0, p1)

    print("Connected 16 word lines.")

    # --------------------------------------------------
    # 3. Connect bitlines vertically
    # --------------------------------------------------

    for col in range(16):
        for row in range(15):
            p0 = array[row][col].findPortInst("BIT")
            p1 = array[row + 1][col].findPortInst("BIT")
            ArcInst.makeInstance(wire, p0, p1)

            p0b = array[row][col].findPortInst("BITB")
            p1b = array[row + 1][col].findPortInst("BITB")
            ArcInst.makeInstance(wire, p0b, p1b)

    print("Connected 16 BL and 16 BLB columns.")

    # --------------------------------------------------
    # 4. Connect VDD and GND
    #    Horizontal chains plus one vertical chain
    # --------------------------------------------------

    for signal in ["VDD", "GND"]:
        for row in range(16):
            for col in range(15):
                p0 = array[row][col].findPortInst(signal)
                p1 = array[row][col + 1].findPortInst(signal)
                ArcInst.makeInstance(wire, p0, p1)

        for row in range(15):
            p0 = array[row][0].findPortInst(signal)
            p1 = array[row + 1][0].findPortInst(signal)
            ArcInst.makeInstance(wire, p0, p1)

    print("Connected VDD and GND.")

    # --------------------------------------------------
    # 5. Export word lines
    # --------------------------------------------------

    created = 0

    for row in range(16):
        name = "WL" + str(row)
        port = array[row][0].findPortInst("WL")

        if cell.findExport(name) is None:
            Export.newInst(cell, port, name, PortCharacteristic.IN)
            created += 1

    # --------------------------------------------------
    # 6. Export bitlines and complementary bitlines
    # --------------------------------------------------

    for col in range(16):
        bl_name = "BL" + str(col)
        blb_name = "BLB" + str(col)

        if cell.findExport(bl_name) is None:
            Export.newInst(
                cell, array[0][col].findPortInst("BIT"),
                bl_name, PortCharacteristic.BIDIR
            )
            created += 1

        if cell.findExport(blb_name) is None:
            Export.newInst(
                cell, array[0][col].findPortInst("BITB"),
                blb_name, PortCharacteristic.BIDIR
            )
            created += 1

    # --------------------------------------------------
    # 7. Export power pins
    # --------------------------------------------------

    if cell.findExport("VDD") is None:
        Export.newInst(
            cell, array[0][0].findPortInst("VDD"),
            "VDD", PortCharacteristic.PWR
        )
        created += 1

    if cell.findExport("GND") is None:
        Export.newInst(
            cell, array[0][0].findPortInst("GND"),
            "GND", PortCharacteristic.GND
        )
        created += 1

    print("Created exports:", created)
    print("DONE. Inspect the schematic and run DRC.")