# -*- coding: utf-8 -*-
# scripts/build_buffer_layout.py
# Layout generator for buffer{lay} matching buffer{sch}

import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.util import ArrayList

def make_manhattan_arc(arc_proto, ep, port1, port2, width=None):
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    arc = ArcInst.makeInstance(arc_proto, ep, port1, port2)
    if width is not None:
        arc.setLambdaBaseWidth(width)
    return arc

def clear_cell_contents(cell):
    eit = cell.getExports()
    exp_kill = []
    while eit.hasNext(): exp_kill.append(eit.next())
    for e in exp_kill: e.kill()

    ait = cell.getArcs()
    arc_kill = []
    while ait.hasNext(): arc_kill.append(ait.next())
    for a in arc_kill: a.kill()

    nit = cell.getNodes()
    node_kill = []
    while nit.hasNext():
        n = nit.next()
        if "Facet-Center" not in n.getProto().getName():
            node_kill.append(n)
    for n in node_kill: n.kill()

def build_buffer(lib, ep, mocmos):
    print("Building buffer{lay}...")
    cell = lib.findNodeProto("buffer{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "buffer{lay}")
    cell.setTechnology(mocmos)
    clear_cell_contents(cell)

    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")

    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
    m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

    n_well_node = mocmos.findNodeProto("N-Well-Node")
    p_well_node = mocmos.findNodeProto("P-Well-Node")

    m1_pin = mocmos.findNodeProto("Metal-1-Pin")
    poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")

    m1_wire = mocmos.findArcProto("Metal-1")
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    n_act_wire = mocmos.findArcProto("N-Active")
    p_act_wire = mocmos.findArcProto("P-Active")

    # Layout Parameters
    Y_P = 24.0
    Y_N = -16.0
    Y_VDD = 50.0
    Y_GND = -34.0
    dx = 4.5

    # 4 Inverters:
    # Inv 1: PMOS W=4, NMOS W=2  @ X1 = 14.0
    # Inv 2: PMOS W=8, NMOS W=4  @ X2 = 30.0
    # Inv 3: PMOS W=16, NMOS W=8 @ X3 = 46.0
    # Inv 4: PMOS W=32, NMOS W=16 @ X4 = 62.0
    stages = [
        {"x": 14.0, "wp": 4.0,  "wn": 2.0,  "p_name": "pmos@0", "n_name": "nmos@1"},
        {"x": 30.0, "wp": 8.0,  "wn": 4.0,  "p_name": "pmos@1", "n_name": "nmos@2"},
        {"x": 46.0, "wp": 16.0, "wn": 8.0,  "p_name": "pmos@4", "n_name": "nmos@5"},
        {"x": 62.0, "wp": 32.0, "wn": 16.0, "p_name": "pmos@5", "n_name": "nmos@6"}
    ]

    X_LEFT = 0.0
    X_RIGHT = 74.0

    # N-well and P-well coverage
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double((X_LEFT + X_RIGHT)/2.0, 26.0),
                          (X_RIGHT - X_LEFT) + 16.0, 56.0, cell, Orientation.IDENT, None)
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double((X_LEFT + X_RIGHT)/2.0, -20.0),
                          (X_RIGHT - X_LEFT) + 16.0, 44.0, cell, Orientation.IDENT, None)

    # Input contact at X = 5.0, Y = 0.0
    con_in = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(5.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)

    vdd_pins = []
    gnd_pins = []

    # Leftmost rail pins
    p_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_LEFT, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
    p_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_LEFT, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
    vdd_pins.append(p_vdd_l)
    gnd_pins.append(p_gnd_l)

    # Well taps at X = 5.0
    tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(5.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, None)
    tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(5.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, None)
    vdd_pins.append(tap_vdd)
    gnd_pins.append(tap_gnd)

    prev_out_node = None

    for idx, st in enumerate(stages):
        x = st["x"]
        wp = st["wp"]
        wn = st["wn"]

        # PMOS & NMOS
        pmos = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x, Y_P), 22.0, 15.0, cell, Orientation.R, None)
        pmos.setPrimitiveNodeSize(wp, 2.0, ep)

        nmos = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x, Y_N), 22.0, 15.0, cell, Orientation.R, None)
        nmos.setPrimitiveNodeSize(wn, 2.0, ep)

        # Gate midpoint at (x, 0.0)
        pin_g_mid = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(poly_wire, ep, pmos.findPortInst("poly-left"), pin_g_mid.getOnlyPortInst())
        make_manhattan_arc(poly_wire, ep, pin_g_mid.getOnlyPortInst(), nmos.findPortInst("poly-right"))

        # Connect input to gate
        if idx == 0:
            make_manhattan_arc(poly_wire, ep, con_in.getOnlyPortInst(), pin_g_mid.getOnlyPortInst())
        else:
            make_manhattan_arc(poly_wire, ep, prev_out_node.getOnlyPortInst(), pin_g_mid.getOnlyPortInst())

        # Source contacts at x - dx
        c_p_src = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(p_act_wire, ep, c_p_src.getOnlyPortInst(), pmos.findPortInst("diff-top"))

        p_vdd_st = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x - dx, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(m1_wire, ep, c_p_src.getOnlyPortInst(), p_vdd_st.getOnlyPortInst())
        vdd_pins.append(p_vdd_st)

        c_n_src = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(n_act_wire, ep, c_n_src.getOnlyPortInst(), nmos.findPortInst("diff-top"))

        p_gnd_st = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x - dx, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(m1_wire, ep, c_n_src.getOnlyPortInst(), p_gnd_st.getOnlyPortInst())
        gnd_pins.append(p_gnd_st)

        # Drain contacts at x + dx
        c_p_drn = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(p_act_wire, ep, pmos.findPortInst("diff-bottom"), c_p_drn.getOnlyPortInst())

        c_n_drn = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, None)
        make_manhattan_arc(n_act_wire, ep, nmos.findPortInst("diff-bottom"), c_n_drn.getOnlyPortInst())

        if idx < len(stages) - 1:
            # Internal stage output connects to M1-Poly contact at (x + dx, 0.0)
            con_out_st = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(x + dx, 0.0), 5.0, 5.0, cell, Orientation.IDENT, None)
            make_manhattan_arc(m1_wire, ep, c_p_drn.getOnlyPortInst(), con_out_st.getOnlyPortInst())
            make_manhattan_arc(m1_wire, ep, con_out_st.getOnlyPortInst(), c_n_drn.getOnlyPortInst())
            prev_out_node = con_out_st
        else:
            # Final stage output connects to pin_out at (x + dx, 0.0)
            pin_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x + dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, None)
            make_manhattan_arc(m1_wire, ep, c_p_drn.getOnlyPortInst(), pin_out.getOnlyPortInst())
            make_manhattan_arc(m1_wire, ep, pin_out.getOnlyPortInst(), c_n_drn.getOnlyPortInst())
            prev_out_node = pin_out

    # Rightmost rail pins
    p_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_RIGHT, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, None)
    p_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_RIGHT, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, None)
    vdd_pins.append(p_vdd_r)
    gnd_pins.append(p_gnd_r)

    # Sort and stitch VDD rail
    vdd_pins.sort(key=lambda p: p.getAnchorCenterX())
    for i in range(len(vdd_pins) - 1):
        make_manhattan_arc(m1_wire, ep, vdd_pins[i].getOnlyPortInst(), vdd_pins[i+1].getOnlyPortInst())

    # Sort and stitch GND rail
    gnd_pins.sort(key=lambda p: p.getAnchorCenterX())
    for i in range(len(gnd_pins) - 1):
        make_manhattan_arc(m1_wire, ep, gnd_pins[i].getOnlyPortInst(), gnd_pins[i+1].getOnlyPortInst())

    # Exports
    Export.newInst(cell, con_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
    Export.newInst(cell, prev_out_node.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
    Export.newInst(cell, p_vdd_r.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, p_gnd_r.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    print("buffer{lay} generated: Width=%.1f lambda (%.2f um), Height=%.1f lambda (%.2f um)" % (
        X_RIGHT - X_LEFT, (X_RIGHT - X_LEFT) * 0.09, Y_VDD - Y_GND, (Y_VDD - Y_GND) * 0.09))
    return cell

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

cell = build_buffer(lib, ep, mocmos)

# Verification
print("\n=== Verifying buffer{lay} ===")
# 1. Manhattan
total_arcs = 0
non_m = 0
ait = cell.getArcs()
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
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break
print("Quick DRC: errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))
it = logger.getLogs()
while it.hasNext():
    print("  DRC Log: %s" % it.next().getMessageString())

# 3. Hierarchical DRC
errs = ArrayList()
DRC.checkDRCHierarchically(prefs, cell, errs, None, mode, False)
print("Hierarchical DRC: errors=%d" % len(errs))
for e in errs:
    print("  Hier DRC Error: %s" % e)

# 4. NCC against buffer{sch}
buf_sch = lib.findNodeProto("buffer{sch}")
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(buf_sch, None, cell, None, opts)
print("Hierarchical NCC (checkSizes=True): match = %s" % res.match())

if logger.getNumErrors() == 0 and len(errs) == 0 and res.match() and non_m == 0:
    print("\nAll checks PASSED! Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library successfully updated and saved.")
else:
    print("\nVerification FAILED! Library was not saved.")

java.lang.System.exit(0)
