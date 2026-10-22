
from com.sun.electric.tool import Job
from com.sun.electric.database.hierarchy import Export
from com.sun.electric.database.prototype import PortCharacteristic

cell = Job.getUserInterface().getCurrentCell()

instances = {}
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    name = node.getName()

    if name.startswith("6T_cell@"):
        index = int(name.split("@")[1])
        instances[index] = node

if len(instances) != 16:
    print("ERROR: Expected 16 cells, found", len(instances))
else:
    created = 0

    for i in range(16):
        for pin, prefix in [("BIT", "BIT"), ("BITB", "BITB")]:
            export_name = prefix + str(i)

            # Skip exports that already exist
            if cell.findExport(export_name) is not None:
                print("Already exists:", export_name)
                continue

            port = instances[i].findPortInst(pin)

            exp = Export.newInst(cell, port, export_name, PortCharacteristic.BIDIR)

            if exp is None:
                print("FAILED:", export_name)
            else:
                created += 1

    print("Finished. New exports created:", created)
