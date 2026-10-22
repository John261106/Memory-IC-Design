from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()

it = cell.getNodes()
while it.hasNext():
    node = it.next()

    if node.getProto().getName() != "6T_cell":
        continue

    print("\nINSTANCE:", node.getName())

    for name in ["WL", "BIT", "BITB", "VDD", "GND"]:
        pi = node.findPortInst(name)
        if pi is not None:
            print(name, "->", pi.getCenter())