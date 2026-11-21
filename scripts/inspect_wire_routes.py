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

print('=== Checking arcs in X in [-800, -450] and Y < -500 ===')
ait = top_lay.getArcs()
while ait.hasNext():
    a = ait.next()
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    minx = min(p1.getX(), p2.getX())
    maxx = max(p1.getX(), p2.getX())
    miny = min(p1.getY(), p2.getY())
    maxy = max(p1.getY(), p2.getY())
    if maxx >= -800 and minx <= -450 and miny <= -500:
        print('Arc on %s from (%.1f, %.1f) to (%.1f, %.1f)' % (a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
