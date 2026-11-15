from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

sch = lib.findNodeProto("Write_driver{sch}")
lay = lib.findNodeProto("Write_driver{lay}")
icon = lib.findNodeProto("Write_driver{ic}")

print("Write_driver{sch}:", sch)
print("Write_driver{lay}:", lay)
print("Write_driver{ic}:", icon)

if sch:
    print("\n--- SCHEMATIC PINS DETAILS ---")
    for pin_name in ['pin@29', 'pin@30', 'pin@3', 'pin@33', 'pin@32']:
        node = sch.findNode(pin_name)
        if node:
            print("Pin %s at (%.1f, %.1f):" % (pin_name, node.getTrueCenter().getX(), node.getTrueCenter().getY()))
            for p in node.getPortInsts():
                for c in p.getConnections():
                    print("   conn arc: %s" % c.getArc().getName())



