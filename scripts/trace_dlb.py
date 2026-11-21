# scripts/trace_dlb.py
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
    if a.getName() in ["DL", "DLB"]:
        h = a.getHeadPortInst()
        t = a.getTailPortInst()
        hn = h.getNodeInst()
        tn = t.getNodeInst()
        print("Arc '%s': %s['%s'](%.1f, %.1f) <---> %s['%s'](%.1f, %.1f)" % (
            a.getName(), hn.getProto().getName(), hn.getName(), h.getCenter().getX(), h.getCenter().getY(),
            tn.getProto().getName(), tn.getName(), t.getCenter().getX(), t.getCenter().getY()
        ))
