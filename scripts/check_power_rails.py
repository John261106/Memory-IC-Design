# scripts/check_power_rails.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def check_power():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    vdd_exp = None
    gnd_exp = None
    for e in sch.getExports():
        if e.getName() == "VDD":
            vdd_exp = e
        elif e.getName() == "GND":
            gnd_exp = e

    print("VDD export node:", vdd_exp.getOriginalPort().getNodeInst().getName())
    print("GND export node:", gnd_exp.getOriginalPort().getNodeInst().getName())

    # Check VDD connections
    vdd_node = vdd_exp.getOriginalPort().getNodeInst()
    gnd_node = gnd_exp.getOriginalPort().getNodeInst()

    # Let's inspect all arcs in sch to see what connects to what
    ait = sch.getArcs()
    vdd_arcs = 0
    gnd_arcs = 0
    while ait.hasNext():
        a = ait.next()
        n1 = a.getHeadPortInst().getNodeInst()
        n2 = a.getTailPortInst().getNodeInst()
        name = a.getName()
        if "VDD" in name:
            vdd_arcs += 1
        if "GND" in name:
            gnd_arcs += 1

    print("Arcs with VDD in name: %d, GND in name: %d" % (vdd_arcs, gnd_arcs))

    # Also let's check electric's NCC: if we create an empty lay or dummy lay, what does NCC say?
if __name__ == "__main__":
    check_power()
