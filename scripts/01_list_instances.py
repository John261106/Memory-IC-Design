
# Electric VLSI 9.08 - List all instances

from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Open a schematic first.")

nodes = cell.getNodes()
counts = {}
total = 0

while nodes.hasNext():
    node = nodes.next()
    instance_name = str(node.getName())
    prototype_name = str(node.getProto().getName())

    print(instance_name, "|", prototype_name)

    counts[prototype_name] = counts.get(prototype_name, 0) + 1
    total += 1

print("\n========== SUMMARY ==========")

for name in sorted(counts.keys()):
    print(name, ":", counts[name])

print("Total nodes:", total)
