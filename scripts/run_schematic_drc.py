from com.sun.electric.tool.drc import Schematic, DRC
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.user import ErrorLogger

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
# Schematic.doCheck(ErrorLogger, Cell, Geometric[], DRCPreferences)
sch_drc = Schematic()
sch_drc.doCheck(logger, cell_sch, None, prefs)

print("Schematic DRC Errors:", logger.getNumErrors())
print("Schematic DRC Warnings:", logger.getNumWarnings())

# Let's see how to read errors from ErrorLogger
for m in logger.getClass().getMethods():
    if "error" in m.getName().lower() or "list" in m.getName().lower() or "get" in m.getName().lower():
        print(" logger method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
