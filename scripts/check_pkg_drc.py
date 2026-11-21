from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Schematic, DRC
from com.sun.electric.tool.user import ErrorLogger

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, 'Memory-IC-Design', FileType.JELIB, False)

top_pkg = lib.findNodeProto('Top_package{sch}')
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
sch_drc = Schematic()
sch_drc.doCheck(logger, top_pkg, None, prefs)
print("Top_package DRC Errors: %d, Warnings: %d" % (logger.getNumErrors(), logger.getNumWarnings()))
for i in range(logger.getNumLogs()):
    print("  ", logger.getLog(i).getMessage())
