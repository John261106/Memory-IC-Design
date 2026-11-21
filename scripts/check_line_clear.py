# scripts/check_line_clear.py
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

def check_v_line(x, y1, y2, tol=10.0):
    print("=== Checking vertical line at X = %.1f from Y = %.1f to %.1f (tol=%.1f) ===" % (x, y1, y2, tol))
    ait = top_lay.getArcs()
    while ait.hasNext():
        a = ait.next()
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        minx = min(p1.getX(), p2.getX())
        maxx = max(p1.getX(), p2.getX())
        miny = min(p1.getY(), p2.getY())
        maxy = max(p1.getY(), p2.getY())
        if (minx <= x + tol and maxx >= x - tol) and not (maxy < y1 or miny > y2):
            print("  Arc on %-10s from (%.1f, %.1f) to (%.1f, %.1f)" % (a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    nit = top_lay.getNodes()
    while nit.hasNext():
        n = nit.next()
        b = n.getBounds()
        if (b.getX() <= x + tol and b.getX() + b.getWidth() >= x - tol) and not (b.getY() + b.getHeight() < y1 or b.getY() > y2):
            print("  Node: %-15s proto: %-15s bounds: %s" % (n.getName(), n.getProto().getName(), b))

check_v_line(75.0, -1250.0, -960.0, tol=5.0)
check_v_line(-344.5, -1250.0, -860.0, tol=5.0)
check_v_line(556.0, -1250.0, -520.0, tol=5.0)
