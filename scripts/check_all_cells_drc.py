from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import DRC, Quick
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.util import ArrayList

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

cit = lib.getCells()
while cit.hasNext():
    cell = cit.next()
    cname = cell.getName()
    vname = str(cell.getView())
    
    # Check Quick DRC
    logger = ErrorLogger()
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
            break
    q_err = logger.getNumErrors()
    q_warn = logger.getNumWarnings()
    
    # Check Hierarchical DRC
    errs = ArrayList()
    DRC.checkDRCHierarchically(prefs, cell, errs, None, mode, False)
    h_err = len(errs)
    
    if q_err > 0 or q_warn > 0 or h_err > 0:
        print("CELL %s (view: %s): Quick DRC (%d err, %d warn), Hier DRC (%d err)" % (cname, vname, q_err, q_warn, h_err))
        for e in errs:
            print("   hier err:", e)

print("Finished checking all cells!")
