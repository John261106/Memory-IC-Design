from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
sch = lib.findNodeProto("3Bit_counter{sch}")

net_map = {}
ait = sch.getArcs()
while ait.hasNext():
    a = ait.next()
    net = a.getNet()
    net_name = net.getName() if net else "anon"
    if net_name not in net_map:
        net_map[net_name] = set()
    hp = a.getHeadPortInst()
    tp = a.getTailPortInst()
    net_map[net_name].add("%s[%s]" % (hp.getNodeInst().getName(), hp.getPortProto().getName()))
    net_map[net_name].add("%s[%s]" % (tp.getNodeInst().getName(), tp.getPortProto().getName()))

for net_name in sorted(net_map.keys()):
    print("Net %s: %s" % (net_name, ", ".join(sorted(net_map[net_name]))))
