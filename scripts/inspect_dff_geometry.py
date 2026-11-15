# scripts/inspect_dff_geometry.py
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

dff_lay = lib.findNodeProto("D_flipflop{lay}")
nit = dff_lay.getNodes()
min_x = 999999
max_x = -999999
min_y = 999999
max_y = -999999
while nit.hasNext():
    n = nit.next()
    pt = n.getCenter()
    if pt.getX() < min_x: min_x = pt.getX()
    if pt.getX() > max_x: max_x = pt.getX()
    if pt.getY() < min_y: min_y = pt.getY()
    if pt.getY() > max_y: max_y = pt.getY()

print("D_flipflop{lay} node bounds: X: [%f, %f], Y: [%f, %f]" % (min_x, max_x, min_y, max_y))
print("Total width = %f, height = %f" % (max_x - min_x, max_y - min_y))
