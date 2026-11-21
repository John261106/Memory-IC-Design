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

wd = lib.findNodeProto('Write_driver{lay}')
eit = wd.getExports()
while eit.hasNext():
    e = eit.next()
    p = e.getOriginalPort()
    print('wd export %-10s: layer %-15s at (%f, %f)' % (e.getName(), p.getNodeInst().getProto().getName(), p.getCenter().getX(), p.getCenter().getY()))
