# scripts/find_empty_regions.py
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

def count_in_box(x1, y1, x2, y2):
    cnt = 0
    nit = top_lay.getNodes()
    while nit.hasNext():
        b = nit.next().getBounds()
        if not (b.getX() + b.getWidth() < x1 or b.getX() > x2 or b.getY() + b.getHeight() < y1 or b.getY() > y2):
            cnt += 1
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
            cnt += 1
    return cnt

candidates = [
    # (name, x1, y1, x2, y2)
    ("East near wd: [700, 850] x [-560, -460]", 700.0, -560.0, 850.0, -460.0),
    ("East near dff: [1000, 1150] x [-560, -460]", 1000.0, -560.0, 1150.0, -460.0),
    ("South West 1: [-800, -650] x [-1300, -1180]", -800.0, -1300.0, -650.0, -1180.0),
    ("South West 2: [-600, -450] x [-1300, -1180]", -600.0, -1300.0, -450.0, -1180.0),
    ("South Mid 1:  [-400, -250] x [-1300, -1180]", -400.0, -1300.0, -250.0, -1180.0),
    ("South Mid 2:  [-200, -50]  x [-1300, -1180]", -200.0, -1300.0, -50.0,  -1180.0),
    ("South East:   [50, 200]    x [-1300, -1180]", 50.0,   -1300.0, 200.0,  -1180.0),
    ("West 1: [-1250, -1050] x [-950, -800]", -1250.0, -950.0, -1050.0, -800.0),
    ("West 2: [-1250, -1050] x [-1150, -1000]", -1250.0, -1150.0, -1050.0, -1000.0),
]

for name, x1, y1, x2, y2 in candidates:
    cnt = count_in_box(x1, y1, x2, y2)
    print("%-45s : %d objects" % (name, cnt))
