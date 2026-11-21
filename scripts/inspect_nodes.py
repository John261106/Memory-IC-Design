from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, 'Memory-IC-Design', FileType.JELIB, False)

top_pkg = lib.findNodeProto('Top_package{sch}')
nit = top_pkg.getNodes()
while nit.hasNext():
    ni = nit.next()
    x = ni.getTrueCenterX()
    y = ni.getTrueCenterY()
    print('Node: %s (%s) at (%.1f, %.1f)' % (ni.getName(), ni.getProto().getName(), x, y))
