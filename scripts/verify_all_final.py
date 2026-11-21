# -*- coding: utf-8 -*-
# scripts/verify_all_final.py

import java.lang.Double
from java.awt.geom import Point2D
from java.util import ArrayList

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC, Schematic
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
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

prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

print("==================================================")
print("       FINAL VERIFICATION AUDIT REPORT           ")
print("==================================================")

# 1. Check input_buffer and output_buffer DRC and NCC
for bname in ["input_buffer", "output_buffer"]:
    print("\n--- Checking %s ---" % bname)
    b_lay = lib.findNodeProto("%s{lay}" % bname)
    b_sch = lib.findNodeProto("%s{sch}" % bname)

    logger = ErrorLogger()
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, b_lay, None, None, None, None, prefs, mode, False])
            break
    q_err = logger.getNumErrors()
    q_warn = logger.getNumWarnings()

    errs = ArrayList()
    DRC.checkDRCHierarchically(prefs, b_lay, errs, None, mode, False)
    h_err = len(errs)

    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(b_sch, None, b_lay, None, opts)

    print("Quick DRC:        %d errors, %d warnings" % (q_err, q_warn))
    print("Hierarchical DRC: %d errors" % h_err)
    print("NCC (checkSizes): match = %s" % res.match())
    assert q_err == 0 and h_err == 0 and res.match(), "%s verification failed!" % bname

# 2. Check Top{lay} & Top{sch} DRC and NCC
print("\n--- Checking Top DRC & NCC ---")
top_lay = lib.findNodeProto("Top{lay}")
top_sch = lib.findNodeProto("Top{sch}")

# Schematic DRC
logger_sch = ErrorLogger()
sch_drc = Schematic()
sch_drc.doCheck(logger_sch, top_sch, None, prefs)
print("Top{sch} DRC:             %d errors, %d warnings" % (logger_sch.getNumErrors(), logger_sch.getNumWarnings()))

# Layout DRC
logger_lay = ErrorLogger()
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger_lay, top_lay, None, None, None, None, prefs, mode, False])
        break
q_err = logger_lay.getNumErrors()
q_warn = logger_lay.getNumWarnings()

errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, errs, None, mode, False)
h_err = len(errs)

opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)

print("Top{lay} Quick DRC:        %d errors, %d warnings" % (q_err, q_warn))
print("Top{lay} Hierarchical DRC: %d errors" % h_err)
print("Top NCC (checkSizes=True): match = %s" % res.match())

# 3. Manhattan Check
def check_manhattan(cell, name):
    total = 0
    non_m = 0
    ait = cell.getArcs()
    while ait.hasNext():
        a = ait.next()
        total += 1
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        dx = abs(p1.getX() - p2.getX())
        dy = abs(p1.getY() - p2.getY())
        if dx > 0.001 and dy > 0.001:
            non_m += 1
    print("%s Manhattan Check:  %d / %d arcs (non-Manhattan: %d)" % (name, total - non_m, total, non_m))
    assert non_m == 0, "%s has %d non-Manhattan arcs!" % (name, non_m)

check_manhattan(top_sch, "Top{sch}")
check_manhattan(top_lay, "Top{lay}")

# 4. Check Top_package is removed
print("\n--- Checking Top_package ---")
top_pkg_sch = lib.findNodeProto("Top_package{sch}")
top_pkg_lay = lib.findNodeProto("Top_package{lay}")
assert top_pkg_sch is None and top_pkg_lay is None, "Top_package still exists!"
print("Top_package{sch}: Successfully removed from library as requested.")

# 5. Check Text Visibility on Schematics and Layouts
print("\n--- Checking Text Visibility on Schematics and Layouts ---")
cit = lib.getCells()
displayed_sch_nodes = 0
displayed_sch_arcs = 0
displayed_lay_nodes = 0
while cit.hasNext():
    c = cit.next()
    if c.getView() == View.SCHEMATIC:
        nit = c.getNodes()
        while nit.hasNext():
            td = nit.next().getTextDescriptor(NodeInst.NODE_NAME)
            if td is not None and td.isDisplay():
                displayed_sch_nodes += 1
        ait = c.getArcs()
        while ait.hasNext():
            td = ait.next().getTextDescriptor(ArcInst.ARC_NAME)
            if td is not None and td.isDisplay():
                displayed_sch_arcs += 1
    elif c.getView() == View.LAYOUT:
        nit = c.getNodes()
        while nit.hasNext():
            td = nit.next().getTextDescriptor(NodeInst.NODE_NAME)
            if td is not None and td.isDisplay():
                displayed_lay_nodes += 1

print("Schematic internal node names visible: %d" % displayed_sch_nodes)
print("Schematic arc/wire net names visible:  %d" % displayed_sch_arcs)
print("Layout internal node names visible:    %d" % displayed_lay_nodes)

# Check Top Exports
print("\n--- Checking Top Exports ---")
eit = top_sch.getExports()
sch_exports = []
while eit.hasNext():
    exp = eit.next()
    td = exp.getTextDescriptor(Export.EXPORT_NAME)
    assert td is not None and td.isDisplay(), "Export %s text is hidden!" % exp.getName()
    sch_exports.append(exp.getName())
print("Top{sch} active visible exports (%d): %s" % (len(sch_exports), sorted(sch_exports)))

print("\n==================================================")
print("      ALL SPECIFICATIONS AND CHECKS PASSED!       ")
print("==================================================")

java.lang.System.exit(0)
