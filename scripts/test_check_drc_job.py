from com.sun.electric.tool.drc import DRC
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.Job import Priority

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

for c in DRC.getDeclaredClasses():
    if "CheckDRCJob" in c.getName():
        job_cls = c
        break

dp = DRC.DRCPreferences(False)
cons = job_cls.getDeclaredConstructor([Cell, DRC.DRCCheckLogging if False else java.lang.Object, Priority, DRC.DRCPreferences, java.lang.Boolean.TYPE])
# let's find the constructor dynamically
for cons in job_cls.getDeclaredConstructors():
    print("cons params:", [p.getName() for p in cons.getParameterTypes()])
