
# Electric VLSI 9.08 - Inspect pins of each prototype

from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Open a schematic first.")

seen = set()
nodes = cell.getNodes()

while nodes.hasNext():
    node = nodes.next()
    proto = node.getProto()
    proto_name = str(proto.getName())

    if proto_name in seen:
        continue

    seen.add(proto_name)

    print("\nPrototype:", proto_name)
    print("Example instance:", node.getName())

    ports = proto.getPorts()

    while ports.hasNext():
        port = ports.next()
        print("  Pin:", port.getName())

print("\nPin inspection complete.")
