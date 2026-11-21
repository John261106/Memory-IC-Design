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
nodes = ['8Bit_shi@0', '3Bit_cou@0', 'Control_@0', 'in_buf_addr', 'in_buf_clk', 'in_buf_ctrl']

for nname in nodes:
    n = top_sch.findNode(nname)
    if n:
        print('=== %s (%s) ===' % (nname, n.getProto().getName()))
        print('  Bounds: %s' % n.getBounds())
        pit = n.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            print('  Port %-10s at (%.1f, %.1f)' % (pi.getPortProto().getName(), pi.getCenter().getX(), pi.getCenter().getY()))

print('\n=== Arcs connected to these nodes ===')
for nname in nodes:
    n = top_sch.findNode(nname)
    if not n: continue
    pit = n.getPortInsts()
    while pit.hasNext():
        pi = pit.next()
        pname = pi.getPortProto().getName()
        ait = top_sch.getArcs()
        while ait.hasNext():
            a = ait.next()
            if a.getHeadPortInst() == pi or a.getTailPortInst() == pi:
                other = a.getTailPortInst() if a.getHeadPortInst() == pi else a.getHeadPortInst()
                other_n = other.getNodeInst()
                print('  %s.%s -> %s.%s (arc name: %s, from (%.1f, %.1f) to (%.1f, %.1f))' % (
                    nname, pname, other_n.getName(), other.getPortProto().getName(), a.getName() or '',
                    a.getHeadPortInst().getCenter().getX(), a.getHeadPortInst().getCenter().getY(),
                    a.getTailPortInst().getCenter().getX(), a.getTailPortInst().getCenter().getY()))
