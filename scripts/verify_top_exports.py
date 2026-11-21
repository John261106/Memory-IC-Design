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

for vname in ['Top{sch}', 'Top{lay}']:
    c = lib.findNodeProto(vname)
    print('=== %s Exports ===' % vname)
    eit = c.getExports()
    while eit.hasNext():
        e = eit.next()
        p = e.getOriginalPort()
        print('  Export: %-10s char: %-6s node: %s' % (e.getName(), e.getCharacteristic().name(), p.getNodeInst().getName()))
