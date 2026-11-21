# scripts/inspect_top_sch_io.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")

print("=== Top{sch} Target Pins & Arcs ===")
pin_names = ["pin@0", "pin@18", "pin@19", "pin@385", "pin@391"]
nit = top_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() in pin_names:
        print("Pin '%s' at (%.1f, %.1f)" % (n.getName(), n.getAnchorCenterX(), n.getAnchorCenterY()))

ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    hn = a.getHeadPortInst().getNodeInst().getName()
    tn = a.getTailPortInst().getNodeInst().getName()
    if any(p in [hn, tn] for p in pin_names):
        print("Arc '%s' (%s): %s.%s (%.1f, %.1f) <---> %s.%s (%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(),
            hn, a.getHeadPortInst().getPortProto().getName(), a.getHeadPortInst().getCenter().getX(), a.getHeadPortInst().getCenter().getY(),
            tn, a.getTailPortInst().getPortProto().getName(), a.getTailPortInst().getCenter().getX(), a.getTailPortInst().getCenter().getY()
        ))
