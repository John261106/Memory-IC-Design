# scripts/test_instantiate_dff.py
import java.lang.Double
from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

test_cell = Cell.newInst(lib, "Test_Cell{lay}")
test_cell.setTechnology(mocmos)

dff_lay = lib.findNodeProto("D_flipflop{lay}")
dff_inst = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, 0.0), 287.0, 56.0, test_cell, Orientation.IDENT, "dff0")

print("dff_inst ports:")
pit = dff_inst.getPortInsts()
while pit.hasNext():
    pi = pit.next()
    print("  Port: %s, at %s" % (pi.getPortProto().getName(), str(pi.getCenter())))

# Clean up
test_cell.kill()
print("Success!")
