from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
top = lib.findNodeProto("Top{lay}")

nit = top.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() in ["Not@0", "3Bit_cou@0", "D_flipfl@0", "Control_@0"]:
        b = n.getBounds()
        print("%s bounds: x=[%.1f, %.1f] y=[%.1f, %.1f]" % (n.getName(), b.getMinX(), b.getMaxX(), b.getMinY(), b.getMaxY()))
