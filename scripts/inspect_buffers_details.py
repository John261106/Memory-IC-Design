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

for name in ['input_buffer{lay}', 'output_buffer{lay}']:
    cell = lib.findNodeProto(name)
    print('=== %s ===' % name)
    print('Bounds: %s' % cell.getBounds())
    eit = cell.getExports()
    while eit.hasNext():
        exp = eit.next()
        p = exp.getOriginalPort()
        node = p.getNodeInst()
        print('  Export: %s, layer: %s, pt: (%f, %f)' % (exp.getName(), node.getProto().getName(), p.getCenter().getX(), p.getCenter().getY()))
