# scripts/inspect_pins.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
target_pin_names = ["pin@387", "pin@388", "pin@389", "pin@390", "pin@391", "pin@392", "pin_ren_not", "pin_vdd_out", "pin_gnd_out"]

ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst()
    t = a.getTailPortInst()
    hn = h.getNodeInst()
    tn = t.getNodeInst()
    if hn.getName() in target_pin_names or tn.getName() in target_pin_names:
        print("Arc '%s' (%s): %s['%s'](%.1f, %.1f) <---> %s['%s'](%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(),
            hn.getProto().getName(), hn.getName(), h.getCenter().getX(), h.getCenter().getY(),
            tn.getProto().getName(), tn.getName(), t.getCenter().getX(), t.getCenter().getY()
        ))
