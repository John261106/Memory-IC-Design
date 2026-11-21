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

top_sch = lib.findNodeProto('Top{sch}')
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getName() in ['DL', 'DLB']:
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        n1 = a.getHeadPortInst().getNodeInst().getName()
        n2 = a.getTailPortInst().getNodeInst().getName()
        print('Net %-4s from %-15s (%.1f, %.1f) to %-15s (%.1f, %.1f)' % (
            a.getName(), n1, p1.getX(), p1.getY(), n2, p2.getX(), p2.getY()))
