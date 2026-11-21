from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst
from com.sun.electric.util.math import Orientation
from java.awt.geom import Point2D

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")
cell = lib.findNodeProto("buffer{lay}")
n_well_node = mocmos.findNodeProto("N-Well-Node")

nw = NodeInst.makeInstance(n_well_node, ep, Point2D.Double(50.0, 18.0), 100.0, 30.0, cell, Orientation.IDENT, "nw_test")
print("Before setPrimitiveNodeSize: xSize=%.1f, ySize=%.1f, bounds=%s" % (nw.getXSize(), nw.getYSize(), nw.getBounds()))
nw.setPrimitiveNodeSize(100.0, 30.0, ep)
print("After setPrimitiveNodeSize: xSize=%.1f, ySize=%.1f, bounds=%s" % (nw.getXSize(), nw.getYSize(), nw.getBounds()))
