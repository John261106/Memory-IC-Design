from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
dec = lib.findNodeProto("Decoder{lay}")

print("Decoder OUT0..3 exports:")
eit = dec.getExports()
while eit.hasNext():
    e = eit.next()
    if e.getName().startswith("OUT"):
        pi = e.getOriginalPort()
        print("  %s @ (%.1f, %.1f) on %s" % (e.getName(), pi.getCenter().getX(), pi.getCenter().getY(), pi.getNodeInst().getName()))
