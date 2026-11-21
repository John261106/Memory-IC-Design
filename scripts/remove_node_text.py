# -*- coding: utf-8 -*-
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View
from com.sun.electric.database.variable import TextDescriptor
from com.sun.electric.technology import Technology
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger
from java.util import ArrayList
import java.lang.Double
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

print("=== Hiding Node Text Descriptors in All Layout Cells ===")
cit = lib.getCells()
hidden_counts = {}
while cit.hasNext():
    c = cit.next()
    if c.getView() != View.LAYOUT:
        continue
    c_name = c.getName()
    hidden_in_cell = 0
    nit = c.getNodes()
    while nit.hasNext():
        ni = nit.next()
        td = ni.getTextDescriptor(NodeInst.NODE_NAME)
        if td is not None and td.isDisplay():
            ni.setTextDescriptor(NodeInst.NODE_NAME, td.withDisplay(False))
            hidden_in_cell += 1
    
    # Ensure all exports remain visible
    eit = c.getExports()
    exp_count = 0
    while eit.hasNext():
        exp = eit.next()
        exp_count += 1
        exp_td = exp.getTextDescriptor(Export.EXPORT_NAME)
        if exp_td is not None and not exp_td.isDisplay():
            exp.setTextDescriptor(Export.EXPORT_NAME, exp_td.withDisplay(True))
            
    hidden_counts[c_name] = (hidden_in_cell, exp_count)
    print("Cell %-20s: hidden %4d node labels, preserved %2d export labels" % (
        c_name, hidden_in_cell, exp_count))

print("\n=== Running Verification on Top{lay} ===")
top_lay = lib.findNodeProto("Top{lay}")
top_sch = lib.findNodeProto("Top{sch}")

# 1. Manhattan check
total_arcs = 0
non_m = 0
ait = top_lay.getArcs()
while ait.hasNext():
    a = ait.next()
    total_arcs += 1
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        non_m += 1
print("Manhattan Check: %d / %d perpendicular (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

# 2. Quick DRC
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, top_lay, None, None, None, None, prefs, mode, False])
        break
print("Quick DRC: errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))

# 3. Hierarchical DRC
errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, errs, None, mode, False)
print("Hierarchical DRC: errors=%d" % len(errs))

# 4. Hierarchical NCC with checkSizes = True
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print("Hierarchical NCC (with checkSizes=True): match = %s" % res.match())

if logger.getNumErrors() == 0 and len(errs) == 0 and res.match() and non_m == 0:
    print("\nAll checks PASSED! Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library successfully updated and saved.")
else:
    print("\nVerification FAILED! Library was not saved.")

java.lang.System.exit(0)
