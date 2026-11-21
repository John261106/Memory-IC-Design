from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.ncc import Ncc, NccOptions

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
top_lay = lib.findNodeProto("Top{lay}")

# Clear arc names on Top{sch}
cleared = 0
for ai in top_sch.getArcs():
    if ai.isUsernamed():
        ai.setName("", ep)
        cleared += 1

print("Cleared %d arc names in Top{sch}" % cleared)

# Check NCC
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print("NCC after clearing arc names: match = %s" % res.match())
