from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_lay = lib.findNodeProto('Top{lay}')

print('=== Nodes with Center Y <= -890 ===')
nit = top_lay.getNodes()
while nit.hasNext():
    n = nit.next()
    b = n.getBounds()
    if b.getY() <= -890:
        print('Node: %-15s proto: %-15s bounds: %s' % (n.getName(), n.getProto().getName(), b))

print('=== Arcs with Y <= -890 ===')
ait = top_lay.getArcs()
while ait.hasNext():
    a = ait.next()
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    if min(p1.getY(), p2.getY()) <= -890:
        print('Arc on %-10s from (%.1f, %.1f) to (%.1f, %.1f)' % (a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
