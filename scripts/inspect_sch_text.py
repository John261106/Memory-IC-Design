from com.sun.electric.database.hierarchy import Cell, View
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

print("=== NODES IN TOP{SCH} ===")
for ni in cell_sch.getNodes():
    proto = ni.getProto()
    name = ni.getName()
    vars_list = []
    it = ni.getVariables()
    while it.hasNext():
        v = it.next()
        vars_list.append("%s=%s" % (v.getName(), v.getObject()))
    
    # Check if proto is primitive or cell
    pname = proto.getName() if proto else "None"
    # Print if node has name or variables or is primitive pin
    if name or vars_list:
        print("Node: proto=%s, name=%s, vars=%s, pos=(%s, %s)" % (pname, name, vars_list, ni.getTrueCenterX(), ni.getTrueCenterY()))

print("\n=== ARCS IN TOP{SCH} ===")
for ai in cell_sch.getArcs():
    name = ai.getName()
    vars_list = []
    it = ai.getVariables()
    while it.hasNext():
        v = it.next()
        vars_list.append("%s=%s" % (v.getName(), v.getObject()))
    if name or vars_list:
        print("Arc: name=%s, vars=%s, head=(%s,%s), tail=(%s,%s)" % (name, vars_list, ai.getHeadLocation().getX(), ai.getHeadLocation().getY(), ai.getTailLocation().getX(), ai.getTailLocation().getY()))

print("\n=== EXPORTS IN TOP{SCH} ===")
eit = cell_sch.getExports()
while eit.hasNext():
    exp = eit.next()
    print("Export: name=%s, port=%s, char=%s" % (exp.getName(), exp.getOriginalPort(), exp.getCharacteristic()))
