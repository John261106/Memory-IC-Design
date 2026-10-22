from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()
nodes = cell.getNodes()

count = 0

while nodes.hasNext():
    node = nodes.next()
    print(node.getName(), "|", node.getProto().getName())
    count += 1

print("Total nodes:", count)