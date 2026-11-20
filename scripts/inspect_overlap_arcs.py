from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
top = lib.findNodeProto("Top{lay}")

ait = top.getArcs()
while ait.hasNext():
    a = ait.next()
    if a.getName() in ["net@11788", "net@11796", "net@11797", "net@11805", "net@11806", "net@11814", "net@11779", "net@11787", "net@11683"]:
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        print("%s (%s) from (%.1f, %.1f) to (%.1f, %.1f)" % (
            a.getName(), a.getProto().getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
