# scripts/diagnose_buffer.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

cell = lib.findNodeProto("buffer{lay}")
print "=== Cells in library ==="
print "buffer{lay}:", cell

print "\n=== Nodes in buffer{lay} ==="
nit = cell.getNodes()
while nit.hasNext():
    n = nit.next()
    print "%s ['%s'] at (%.1f, %.1f), size (%.1f, %.1f), bounds: %s" % (
        n.getProto().getName(), n.getName(),
        n.getAnchorCenterX(), n.getAnchorCenterY(),
        n.getXSize(), n.getYSize(),
        n.getBounds()
    )

print "\n=== Running Quick DRC ==="
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break

print "DRC Errors: %d, Warnings: %d" % (logger.getNumErrors(), logger.getNumWarnings())
it = logger.getLogs()
while it.hasNext():
    log = it.next()
    print "  LOG:", log.getMessageString()
    print "    geom:", log.getGeom()
    print "    node1:", log.getNode1(), "node2:", log.getNode2()
