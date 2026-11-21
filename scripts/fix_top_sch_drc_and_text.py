# -*- coding: utf-8 -*-
# scripts/fix_top_sch_drc_and_text.py

from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, View
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
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
sch_tech = Technology.findTechnology("schematic")
wire_arc = sch_tech.findArcProto("wire")

def reconnect_node_arcs(node):
    arcs_to_reconnect = []
    for ai in top_sch.getArcs():
        h = ai.getHeadPortInst().getNodeInst()
        t = ai.getTailPortInst().getNodeInst()
        if h == node or t == node:
            arcs_to_reconnect.append((ai, ai.getHeadPortInst(), ai.getTailPortInst(), ai.getName()))
    for ai, p1, p2, name in arcs_to_reconnect:
        ai.kill()
        new_ai = ArcInst.makeInstance(wire_arc, ep, p1, p2)
        if name:
            new_ai.setName(name, ep)

print("=== 1. Fixing DRC Spacing in Top{sch} ===")

# 1. Fix CLK Branch 1 (s1, s2)
s1 = top_sch.findNode("pin_clk_s1")
s2 = top_sch.findNode("pin_clk_s2")
if s1 and s2:
    s1.move(0.0, -6.0)
    s2.move(0.0, -6.0)
    reconnect_node_arcs(s1)
    reconnect_node_arcs(s2)
    print("Fixed CLK branch 1: s1, s2 at Y=56.0")

# 2. Fix CLK Branch 3 (cnt1, cnt2)
cnt1 = top_sch.findNode("pin_clk_cnt1")
cnt2 = top_sch.findNode("pin_clk_cnt2")
if cnt1 and cnt2:
    cnt1.move(0.0, -4.0)
    cnt2.move(0.0, -4.0)
    reconnect_node_arcs(cnt1)
    reconnect_node_arcs(cnt2)
    print("Fixed CLK branch 3: cnt1, cnt2 at Y=3.0")

# 3. Fix 14 pairs of WL_driver GND and VDD stubs
for col_base in [0, 8]:
    for i in range(7):
        inst_idx = col_base + i
        next_idx = inst_idx + 1
        
        wl_curr = top_sch.findNode("WL_drive@%d" % inst_idx)
        wl_next = top_sch.findNode("WL_drive@%d" % next_idx)
        cy_curr = wl_curr.getTrueCenterY()
        cy_next = wl_next.getTrueCenterY()
        cx = wl_curr.getTrueCenterX()
        
        gnd_y_old = cy_curr - 11.0
        vdd_y_old = cy_next + 11.0
        
        for ni in top_sch.getNodes():
            if abs(ni.getTrueCenterX() - cx) < 0.1:
                if abs(ni.getTrueCenterY() - gnd_y_old) < 0.1:
                    ni.move(0.0, 2.0)
                    reconnect_node_arcs(ni)
                elif abs(ni.getTrueCenterY() - vdd_y_old) < 0.1:
                    ni.move(0.0, -2.0)
                    reconnect_node_arcs(ni)
print("Fixed all 14 pairs of WL_driver GND and VDD pins.")

print("\n=== 2. Hiding Text for Internal Nodes and Arcs in All Schematic Cells ===")
cit = lib.getCells()
while cit.hasNext():
    c = cit.next()
    if c.getView() != View.SCHEMATIC:
        continue
    cname = c.getName()
    
    hidden_nodes = 0
    nit = c.getNodes()
    while nit.hasNext():
        ni = nit.next()
        td = ni.getTextDescriptor(NodeInst.NODE_NAME)
        if td is not None and td.isDisplay():
            ni.setTextDescriptor(NodeInst.NODE_NAME, td.withDisplay(False))
            hidden_nodes += 1
            
    hidden_arcs = 0
    ait = c.getArcs()
    while ait.hasNext():
        ai = ait.next()
        td = ai.getTextDescriptor(ArcInst.ARC_NAME)
        if td is not None and td.isDisplay():
            ai.setTextDescriptor(ArcInst.ARC_NAME, td.withDisplay(False))
            hidden_arcs += 1
            
    # Ensure all exports remain visible
    eit = c.getExports()
    exp_count = 0
    while eit.hasNext():
        exp = eit.next()
        exp_count += 1
        exp_td = exp.getTextDescriptor(Export.EXPORT_NAME)
        if exp_td is not None and not exp_td.isDisplay():
            exp.setTextDescriptor(Export.EXPORT_NAME, exp_td.withDisplay(True))
            
    if hidden_nodes > 0 or hidden_arcs > 0:
        print("Cell %-20s: hidden %4d node labels, %4d arc labels, preserved %2d export labels" % (
            cname + "{sch}", hidden_nodes, hidden_arcs, exp_count))

print("\n=== 3. Verification & Validation ===")
# 1. Schematic DRC Check
logger_sch = ErrorLogger()
prefs = DRC.DRCPreferences(False)
sch_drc = Schematic()
sch_drc.doCheck(logger_sch, top_sch, None, prefs)
print("Schematic DRC Errors: %d, Warnings: %d" % (logger_sch.getNumErrors(), logger_sch.getNumWarnings()))

# 2. Manhattan Check
total_arcs = 0
non_m = 0
ait = top_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    total_arcs += 1
    p1 = a.getHeadPortInst().getCenter()
    p2 = a.getTailPortInst().getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        non_m += 1
print("Top{sch} Manhattan Check: %d / %d perpendicular (non-Manhattan: %d)" % (
    total_arcs - non_m, total_arcs, non_m))

# 3. Hierarchical NCC Check
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print("Hierarchical NCC (checkSizes=True): match = %s" % res.match())

# 4. Layout DRC Check
logger_lay = ErrorLogger()
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger_lay, top_lay, None, None, None, None, prefs, mode, False])
        break
print("Top{lay} Quick DRC Errors: %d" % logger_lay.getNumErrors())
errs = ArrayList()
DRC.checkDRCHierarchically(prefs, top_lay, errs, None, mode, False)
print("Top{lay} Hierarchical DRC Errors: %d" % len(errs))

if logger_sch.getNumErrors() == 0 and res.match() and non_m == 0 and logger_lay.getNumErrors() == 0 and len(errs) == 0:
    print("\nAll checks PASSED! Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library successfully updated and saved.")
else:
    print("\nVerification FAILED! Library was not saved.")
    java.lang.System.exit(1)

java.lang.System.exit(0)
