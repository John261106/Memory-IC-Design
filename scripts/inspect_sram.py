
from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    print("ERROR: No schematic is open.")
else:
    print("Current cell:", cell.getName())
    print("---- Cell instances ----")

    nodes = cell.getNodes()

    while nodes.hasNext():
        node = nodes.next()
        proto = node.getProto()

        print(
            "Instance:", node.getName(),
            "| Prototype:", proto.getName()
        )

        ports = proto.getPorts()

        while ports.hasNext():
            port = ports.next()
            print("    Port:", port.getName())
