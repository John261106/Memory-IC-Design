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
    if a.getName() in ["net@14653", "net@14672", "net@14735", "net@14787"]:
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        print("%s from (%.1f, %.1f) to (%.1f, %.1f) W=%.1f" % (
            a.getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY(), a.getLambdaBaseWidth()))
