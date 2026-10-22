
from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import ArcInst

cell = Job.getUserInterface().getCurrentCell()
tech = Technology.findTechnology("schematic")
wire = tech.findArcProto("wire")

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
    for signal in ["VDD", "GND"]:
        for i in range(15):
            p0 = instances[i].findPortInst(signal)
            p1 = instances[i + 1].findPortInst(signal)

            arc = ArcInst.makeInstance(wire, p0, p1)

            if arc is None:
                print("ERROR:", signal, i, "to", i + 1)
                break
        else:
            print("SUCCESS: Connected all", signal, "pins")
