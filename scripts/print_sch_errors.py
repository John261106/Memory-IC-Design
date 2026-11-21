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
sch_drc = Schematic()
sch_drc.doCheck(logger, cell_sch, None, prefs)

print("=== ALL SCHEMATIC DRC MESSAGES (%d) ===" % logger.getNumLogs())
for i in range(logger.getNumLogs()):
    log = logger.getLog(i)
    print("[%02d] %s" % (i, log.getMessage()))
