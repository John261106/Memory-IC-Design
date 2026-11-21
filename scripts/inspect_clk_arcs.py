# scripts/inspect_clk_arcs.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getName() == "CLK":
        h = a.getHeadPortInst()
        t = a.getTailPortInst()
        print("Arc 'CLK': %s.%s <---> %s.%s" % (
            h.getNodeInst().getName(), h.getPortProto().getName(),
            t.getNodeInst().getName(), t.getPortProto().getName()))
