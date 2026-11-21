from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

for i in range(16):
    wl_inst = cell_sch.findNode("WL_drive@%d" % i)
    cx = wl_inst.getTrueCenterX()
    cy = wl_inst.getTrueCenterY()
    
    # find VDD and GND arcs
    vdd_arc = None
    gnd_arc = None
    for ai in cell_sch.getArcs():
        h = ai.getHeadPortInst().getNodeInst()
        t = ai.getTailPortInst().getNodeInst()
        if h == wl_inst or t == wl_inst:
            if ai.getName() == "VDD":
                vdd_arc = ai
            elif ai.getName() == "GND":
                gnd_arc = ai
    
    v_other = vdd_arc.getHeadPortInst().getNodeInst() if vdd_arc.getTailPortInst().getNodeInst() == wl_inst else vdd_arc.getTailPortInst().getNodeInst()
    g_other = gnd_arc.getHeadPortInst().getNodeInst() if gnd_arc.getTailPortInst().getNodeInst() == wl_inst else gnd_arc.getTailPortInst().getNodeInst()
    print("WL_drive@%d at (%.1f, %.1f): VDD pin=%s at (%.1f, %.1f), GND pin=%s at (%.1f, %.1f)" % (
        i, cx, cy, v_other.getName(), v_other.getTrueCenterX(), v_other.getTrueCenterY(),
        g_other.getName(), g_other.getTrueCenterX(), g_other.getTrueCenterY()))
