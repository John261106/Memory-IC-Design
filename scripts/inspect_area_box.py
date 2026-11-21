# scripts/inspect_area_box.py
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

def check_box(x1, y1, x2, y2, desc):
    print("=== Checking box %s: [%.1f, %.1f] x [%.1f, %.1f] ===" % (desc, x1, x2, y1, y2))
    nit = top_lay.getNodes()
    while nit.hasNext():
        n = nit.next()
        b = n.getBounds()
        if not (b.getX() + b.getWidth() < x1 or b.getX() > x2 or b.getY() + b.getHeight() < y1 or b.getY() > y2):
            print("  Node: %-15s proto: %-15s bounds: %s" % (n.getName(), n.getProto().getName(), b))
    ait = top_lay.getArcs()
    while ait.hasNext():
        a = ait.next()
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        minx = min(p1.getX(), p2.getX())
        maxx = max(p1.getX(), p2.getX())
        miny = min(p1.getY(), p2.getY())
        maxy = max(p1.getY(), p2.getY())
        if not (maxx < x1 or minx > x2 or maxy < y1 or miny > y2):
            print("  Arc on %-10s from (%.1f, %.1f) to (%.1f, %.1f)" % (a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))

check_box(380.0, -460.0, 520.0, -370.0, "Candidate in_buf_din area")
check_box(-650.0, -920.0, -480.0, -800.0, "Candidate in_buf_addr area")
check_box(-450.0, -1080.0, -280.0, -950.0, "Candidate in_buf_clk area")
check_box(-250.0, -1020.0, -80.0, -900.0, "Candidate in_buf_ctrl area")
