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
sa = top_sch.findNode('Sense_am@0')
wd = top_sch.findNode('Write_dr@0')

print('Sense_amp ports and connected arcs:')
pit = sa.getPortInsts()
while pit.hasNext():
    pi = pit.next()
    pname = pi.getPortProto().getName()
    if pname in ['BIT', 'BITB']:
        ait = top_sch.getArcs()
        while ait.hasNext():
            a = ait.next()
            if a.getHeadPortInst() == pi or a.getTailPortInst() == pi:
                print('  sa port %s connected to arc: name=%s, head=(%.1f, %.1f), tail=(%.1f, %.1f)' % (
                    pname, a.getName(), a.getHeadPortInst().getCenter().getX(), a.getHeadPortInst().getCenter().getY(),
                    a.getTailPortInst().getCenter().getX(), a.getTailPortInst().getCenter().getY()))

print('Write_driver ports and connected arcs:')
pit = wd.getPortInsts()
while pit.hasNext():
    pi = pit.next()
    pname = pi.getPortProto().getName()
    if pname in ['BIT', 'BITB']:
        ait = top_sch.getArcs()
        while ait.hasNext():
            a = ait.next()
            if a.getHeadPortInst() == pi or a.getTailPortInst() == pi:
                print('  wd port %s connected to arc: name=%s, head=(%.1f, %.1f), tail=(%.1f, %.1f)' % (
                    pname, a.getName(), a.getHeadPortInst().getCenter().getX(), a.getHeadPortInst().getCenter().getY(),
                    a.getTailPortInst().getCenter().getX(), a.getTailPortInst().getCenter().getY()))
