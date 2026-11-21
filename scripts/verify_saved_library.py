# -*- coding: utf-8 -*-
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC, Schematic
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.util import ArrayList
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_sch = lib.findNodeProto("Top{sch}")
top_lay = lib.findNodeProto("Top{lay}")
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

# 1. Schematic DRC
logger_sch = ErrorLogger()
sch_drc = Schematic()
sch_drc.doCheck(logger_sch, top_sch, None, prefs)
print("Top{sch} DRC Errors: %d" % logger_sch.getNumErrors())

# 2. Layout DRC
logger_lay = ErrorLogger()
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger_lay, top_lay, None, None, None, None, prefs, mode, False])
        break
print("Top{lay} Quick DRC Errors: %d" % logger_lay.getNumErrors())

errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, errs, None, mode, False)
print("Top{lay} Hierarchical DRC Errors: %d" % len(errs))

# 3. NCC
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print("Top NCC (checkSizes=True): match = %s" % res.match())

# 4. Exports
eit = top_sch.getExports()
exps = []
while eit.hasNext():
    exps.append(eit.next().getName())
print("Top{sch} Exports: %s" % sorted(exps))
