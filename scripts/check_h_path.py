# scripts/check_h_path.py
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

def check_h_line(y, x1, x2, tol=10.0):
    print("=== Checking horizontal line at Y = %.1f from X = %.1f to %.1f (tol=%.1f) ===" % (y, x1, x2, tol))
    ait = top_lay.getArcs()
    while ait.hasNext():
        a = ait.next()
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        minx = min(p1.getX(), p2.getX())
        maxx = max(p1.getX(), p2.getX())
        miny = min(p1.getY(), p2.getY())
        maxy = max(p1.getY(), p2.getY())
        if (miny <= y + tol and maxy >= y - tol) and not (maxx < x1 or minx > x2):
            print("  Arc on %-10s from (%.1f, %.1f) to (%.1f, %.1f)" % (a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    nit = top_lay.getNodes()
    while nit.hasNext():
        n = nit.next()
        b = n.getBounds()
        if (b.getY() <= y + tol and b.getY() + b.getHeight() >= y - tol) and not (b.getX() + b.getWidth() < x1 or b.getX() > x2):
            print("  Node: %-15s proto: %-15s bounds: %s" % (n.getName(), n.getProto().getName(), b))

check_h_line(-520.0, 556.0, 1100.0, tol=5.0)
check_h_line(-500.0, 556.0, 1100.0, tol=5.0)
check_h_line(-480.0, 556.0, 1100.0, tol=5.0)
