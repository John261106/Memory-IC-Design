from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.erc import ERC
from com.sun.electric.tool.user import ErrorLogger

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

print("--- Testing DRC.checkNetworks on Top{sch} ---")
logger = ErrorLogger()
DRC.checkNetworks(logger, cell_sch, False)
print("Errors:", logger.getNumErrors())
print("Warnings:", logger.getNumWarnings())
# Let's inspect methods of logger
for m in ErrorLogger.getDeclaredMethods():
    if "err" in m.getName().lower() or "log" in m.getName().lower() or "list" in m.getName().lower():
        print(" logger method:", m.getName())

print("--- Testing ERC ---")
erc_tool = ERC.getERCTool()
print("ERC Tool:", erc_tool)
for m in erc_tool.getClass().getDeclaredMethods():
    print(" erc method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
