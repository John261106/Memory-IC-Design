from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

for p_name in ["pin@75", "pin@79", "pin@80", "pin@84"]:
    for ni in cell_sch.getNodes():
        if ni.getName() == p_name:
            print("Pin %s at (%s, %s)" % (p_name, ni.getTrueCenterX(), ni.getTrueCenterY()))

# Let's see what arcs are connected to WL_driver@0..15 or around X=10 and X=50
for ai in cell_sch.getArcs():
    h = ai.getHeadPortInst().getNodeInst().getName()
    t = ai.getTailPortInst().getNodeInst().getName()
    if "WL_drive" in h or "WL_drive" in t or "pin@7" in h or "pin@7" in t or "pin@8" in h or "pin@8" in t:
        if ai.getName() in ["VDD", "GND"]:
            print("Arc %s: %s (%s) to %s (%s)" % (ai.getName(), h, ai.getHeadLocation(), t, ai.getTailLocation()))
