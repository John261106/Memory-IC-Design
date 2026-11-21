from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database.topology import NodeInst
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_sch = lib.findNodeProto('Top{sch}')
nit = top_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    proto = n.getProto()
    if isinstance(proto, Cell):
        print('Instance: %s of cell: %s' % (n.getName(), proto.getName()))

print('=== Top{sch} Exports ===')
eit = top_sch.getExports()
while eit.hasNext():
    e = eit.next()
    p = e.getOriginalPort()
    print('  Export: %s, on node: %s, port: %s' % (e.getName(), p.getNodeInst().getName(), p.getPortProto().getName()))
