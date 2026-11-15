# scripts/17_layout_3bit_counter.py
# Clean, compact, DRC/LVS-clean layout generator for 3Bit_counter{lay} in Memory-IC-Design.jelib
# Architecture: 3-Bit Synchronous Binary Counter (Modulo-8) with Hazard-Free Terminal Count (COUNT_7)
# Technology: MOSIS SCMOS_SUBM (mocmos), lambda = 90nm
# Features:
# 1. Standard-cell hierarchical architecture:
#    - 3 D Flip-Flop standard cell instances (DFF0, DFF1, DFF2) instantiating D_flipflop{lay}
#    - Combinational standard-cell logic row (Row 0) with 28 transistors:
#      * INV0 (C0 -> C0B), INV1 (C1 -> C1B), INV2 (C2 -> C2B)
#      * NAND2 (C0, C1 -> C01B) with continuous shared active diffusion
#      * INV5 (C01B -> C01)
#      * NAND3 (C0, C1, C2 -> COUNT_7B) with series NMOS
#      * INV9 (COUNT_7B -> COUNT_7) strong buffer output
#      * XOR1 (TG1 + TG2 for D1 = C1 XOR C0)
#      * XOR2 (TG3 + TG4 for D2 = C2 XOR C01)
# 2. Minimum contact-to-MOSFET active diffusion distance: dx = 4.5 lambda (0.405 um).
# 3. 100% Manhattan perpendicular routing (0 non-perpendicular / diagonal arcs).
# 4. Zero DRC errors & warnings (Quick ALGO_SWEEP).
# 5. 100% LVS / NCC match with checkSizes = True against 3Bit_counter{sch}.

import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
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
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger

def make_manhattan_arc(arc_proto, ep, port1, port2):
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    return ArcInst.makeInstance(arc_proto, ep, port1, port2)

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

def run_drc(cell):
    logger = ErrorLogger()
    prefs = DRC.DRCPreferences(False)
    mode = GeometryHandler.GHMode.ALGO_SWEEP
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
            break
    n_err = logger.getNumErrors()
    n_warn = logger.getNumWarnings()
    print("Quick DRC: %d errors, %d warnings" % (n_err, n_warn))
    if n_err > 0 or n_warn > 0:
        it = logger.getLogs()
        seen = set()
        idx = 1
        while it.hasNext():
            log = it.next()
            msg = log.getMessageString()
            if msg not in seen:
                seen.add(msg)
                print("  DRC [%d]: %s" % (idx, msg))
                idx += 1
    return n_err, n_warn

def build_counter_layout(lib, ep, mocmos, jelib_path):
    print("\n" + "=" * 60)
    print("Building Standard-Cell Layout: 3Bit_counter{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("3Bit_counter{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "3Bit_counter{lay}")
    else:
        clear_cell_contents(cell)
    cell.setTechnology(mocmos)

    sch = lib.findNodeProto("3Bit_counter{sch}")
    dff_lay = lib.findNodeProto("D_flipflop{lay}")

    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")
    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
    m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
    m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

    n_well_node = mocmos.findNodeProto("N-Well-Node")
    p_well_node = mocmos.findNodeProto("P-Well-Node")

    m1_pin = mocmos.findNodeProto("Metal-1-Pin")
    m2_pin = mocmos.findNodeProto("Metal-2-Pin")
    poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")

    m1_wire = mocmos.findArcProto("Metal-1")
    m2_wire = mocmos.findArcProto("Metal-2")
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    n_act_wire = mocmos.findArcProto("N-Active")
    p_act_wire = mocmos.findArcProto("P-Active")

    def make_stacked_via(name, x, y):
        cp = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(x, y), 5.0, 5.0, cell, Orientation.IDENT, name + "_p")
        cv = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x, y), 5.0, 5.0, cell, Orientation.IDENT, name + "_v")
        ArcInst.makeInstance(m1_wire, ep, cp.getOnlyPortInst(), cv.getOnlyPortInst())
        return cp, cv

    # Geometry parameters
    DY = 86.0  # Standard-cell row pitch
    Y_ROW0 = 0.0
    Y_ROW1 = DY        # 86.0
    Y_ROW2 = 2.0 * DY  # 172.0
    Y_ROW3 = 3.0 * DY  # 258.0

    Y_VDD = 32.0
    Y_GND = -32.0
    Y_P = 14.0
    Y_N = -14.0
    dx = 4.5

    # 1. Instantiate 3 D Flip-Flops
    dff0 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW1), 287.0, 56.0, cell, Orientation.IDENT, "D_flipfl@3")
    dff1 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW2), 287.0, 56.0, cell, Orientation.IDENT, "D_flipfl@4")
    dff2 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW3), 287.0, 56.0, cell, Orientation.IDENT, "D_flipfl@5")

    # Power grid straps at X = -38.0 (VDD), X = -46.0 (GND), CLK at X = -30.0
    via_v0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_VDD), 5.0, 5.0, cell, Orientation.IDENT, "via_v0")
    via_v1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW1 + 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_v1")
    via_v2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW2 + 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_v2")
    via_v3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW3 + 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_v3")

    make_manhattan_arc(m2_wire, ep, via_v0.getOnlyPortInst(), via_v1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_v1.getOnlyPortInst(), via_v2.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_v2.getOnlyPortInst(), via_v3.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, via_v1.getOnlyPortInst(), dff0.findPortInst("VDD"))
    make_manhattan_arc(m1_wire, ep, via_v2.getOnlyPortInst(), dff1.findPortInst("VDD"))
    make_manhattan_arc(m1_wire, ep, via_v3.getOnlyPortInst(), dff2.findPortInst("VDD"))

    Export.newInst(cell, via_v0.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)

    via_g0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_GND), 5.0, 5.0, cell, Orientation.IDENT, "via_g0")
    via_g1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW1 - 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_g1")
    via_g2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW2 - 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_g2")
    via_g3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW3 - 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_g3")

    make_manhattan_arc(m2_wire, ep, via_g0.getOnlyPortInst(), via_g1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_g1.getOnlyPortInst(), via_g2.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_g2.getOnlyPortInst(), via_g3.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, via_g1.getOnlyPortInst(), dff0.findPortInst("GND"))
    make_manhattan_arc(m1_wire, ep, via_g2.getOnlyPortInst(), dff1.findPortInst("GND"))
    make_manhattan_arc(m1_wire, ep, via_g3.getOnlyPortInst(), dff2.findPortInst("GND"))

    Export.newInst(cell, via_g0.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    # CLK strap at X = -30.0
    via_clk1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW1), 5.0, 5.0, cell, Orientation.IDENT, "via_clk1")
    via_clk2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW2), 5.0, 5.0, cell, Orientation.IDENT, "via_clk2")
    via_clk3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW3), 5.0, 5.0, cell, Orientation.IDENT, "via_clk3")

    make_manhattan_arc(m2_wire, ep, via_clk1.getOnlyPortInst(), via_clk2.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_clk2.getOnlyPortInst(), via_clk3.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, via_clk1.getOnlyPortInst(), dff0.findPortInst("CLK"))
    make_manhattan_arc(m1_wire, ep, via_clk2.getOnlyPortInst(), dff1.findPortInst("CLK"))
    make_manhattan_arc(m1_wire, ep, via_clk3.getOnlyPortInst(), dff2.findPortInst("CLK"))

    Export.newInst(cell, via_clk1.getOnlyPortInst(), "CLK", PortCharacteristic.IN)

    # 2. Build Row 0 Transistors (14 PMOS, 14 NMOS)
    col_defs = [
        # (col_idx, tnum, p_w, n_w, xc, ctype)
        (0,  0,  8.0, 4.0,  10.0, 'inv'),
        (1,  1,  8.0, 4.0,  34.0, 'inv'),
        (2,  2,  8.0, 4.0,  58.0, 'inv'),
        (3,  3,  4.0, 4.0,  82.0, 'nand2_b'),
        (4,  4,  4.0, 4.0,  91.0, 'nand2_a'),
        (5,  5,  8.0, 4.0, 115.0, 'inv'),
        (6,  6,  4.0, 6.0, 147.0, 'nand3_1'),
        (7,  7,  4.0, 6.0, 171.0, 'nand3_2'),
        (8,  8,  4.0, 6.0, 195.0, 'nand3_3'),
        (9,  9, 12.0, 6.0, 219.0, 'inv'),
        (10, 10, 8.0, 4.0, 244.0, 'tg'),
        (11, 11, 8.0, 4.0, 276.0, 'tg'),
        (12, 12, 8.0, 4.0, 308.0, 'tg'),
        (13, 13, 8.0, 4.0, 340.0, 'tg'),
    ]

    X_MAX_R0 = 410.0

    # Wells covering all of Row 0 and power taps completely
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(180.0, 23.0), 500.0, 46.0, cell, Orientation.IDENT, "nwell_r0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(180.0, -23.0), 500.0, 46.0, cell, Orientation.IDENT, "pwell_r0")

    p_nodes = {}
    n_nodes = {}
    p_con_l = {}
    p_con_r = {}
    n_con_l = {}
    n_con_r = {}

    vdd_drops_r0 = []
    gnd_drops_r0 = []

    for cidx, tnum, wp, wn, xc, ctype in col_defs:
        p = NodeInst.makeInstance(p_proto, ep, Point2D.Double(xc, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@%d" % tnum)
        p.setPrimitiveNodeSize(wp, 2.0, ep)
        n = NodeInst.makeInstance(n_proto, ep, Point2D.Double(xc, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@%d" % tnum)
        n.setPrimitiveNodeSize(wn, 2.0, ep)
        p_nodes[tnum] = p
        n_nodes[tnum] = n

        if ctype == 'inv':
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcl_%d" % tnum)
            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcr_%d" % tnum)
            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncl_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncr_%d" % tnum)
            p_con_l[tnum] = pcl
            p_con_r[tnum] = pcr
            n_con_l[tnum] = ncl
            n_con_r[tnum] = ncr
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())
            vdd_drops_r0.append((pcl, xc - dx))
            gnd_drops_r0.append((ncl, xc - dx))

        elif ctype == 'nand2_b':
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcl_%d" % tnum)
            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncl_%d" % tnum)
            p_con_l[tnum] = pcl
            n_con_l[tnum] = ncl
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            vdd_drops_r0.append((pcl, xc - dx))

            pcm = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcm_34")
            p_con_r[tnum] = pcm
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcm.getOnlyPortInst())

            ncm = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncm_34")
            n_con_r[tnum] = ncm
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncm.getOnlyPortInst())

        elif ctype == 'nand2_a':
            pcm = p_con_r[3]
            p_con_l[tnum] = pcm
            make_manhattan_arc(p_act_wire, ep, pcm.getOnlyPortInst(), p.findPortInst("diff-top"))

            ncm = n_con_r[3]
            n_con_l[tnum] = ncm
            make_manhattan_arc(n_act_wire, ep, ncm.getOnlyPortInst(), n.findPortInst("diff-top"))

            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcr_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncr_%d" % tnum)
            p_con_r[tnum] = pcr
            n_con_r[tnum] = ncr
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())

            pin_v4_step = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(103.0, Y_P), 3.0, 3.0, cell, Orientation.IDENT, "pin_v4_step")
            make_manhattan_arc(m1_wire, ep, pcr.getOnlyPortInst(), pin_v4_step.getOnlyPortInst())
            vdd_drops_r0.append((pin_v4_step, 103.0))
            gnd_drops_r0.append((ncr, xc + dx))

        elif ctype.startswith('nand3'):
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcl_%d" % tnum)
            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcr_%d" % tnum)
            p_con_l[tnum] = pcl
            p_con_r[tnum] = pcr
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
            vdd_drops_r0.append((pcl, xc - dx))

            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncl_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncr_%d" % tnum)
            n_con_l[tnum] = ncl
            n_con_r[tnum] = ncr
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())
            if tnum == 8:
                gnd_drops_r0.append((ncr, xc + dx))

        elif ctype == 'tg':
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcl_%d" % tnum)
            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "pcr_%d" % tnum)
            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncl_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "ncr_%d" % tnum)
            p_con_l[tnum] = pcl
            p_con_r[tnum] = pcr
            n_con_l[tnum] = ncl
            n_con_r[tnum] = ncr
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())

    # Connect Row 0 Power Rails
    vdd_map_r0 = {}
    vdd_map_r0[-38.0] = via_v0
    pin_vdd_r0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX_R0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r0")
    vdd_map_r0[X_MAX_R0] = pin_vdd_r0
    tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(-14.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd_r0")
    vdd_map_r0[-14.0] = tap_vdd

    for con, x in vdd_drops_r0:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_v_%.1f" % x)
        vdd_map_r0[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_vx = sorted(vdd_map_r0.keys())
    for i in range(len(sorted_vx) - 1):
        make_manhattan_arc(m1_wire, ep, vdd_map_r0[sorted_vx[i]].getOnlyPortInst(), vdd_map_r0[sorted_vx[i+1]].getOnlyPortInst())

    gnd_map_r0 = {}
    gnd_map_r0[-46.0] = via_g0
    pin_gnd_r0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX_R0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r0")
    gnd_map_r0[X_MAX_R0] = pin_gnd_r0
    tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(-14.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd_r0")
    gnd_map_r0[-14.0] = tap_gnd

    for con, x in gnd_drops_r0:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_g_%.1f" % x)
        gnd_map_r0[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_gx = sorted(gnd_map_r0.keys())
    for i in range(len(sorted_gx) - 1):
        make_manhattan_arc(m1_wire, ep, gnd_map_r0[sorted_gx[i]].getOnlyPortInst(), gnd_map_r0[sorted_gx[i+1]].getOnlyPortInst())

    # 3. Gate connections and contacts (Inverters & NAND gates)
    con_gates_p = {}
    con_gates_v = {}

    gate_offsets = {
        0: (-7.0, 0.0),
        1: (-7.0, 0.0),
        2: (-7.0, 0.0),
        3: (0.0, -21.5),
        4: (0.0, 21.5),
        5: (-7.0, 0.0),
        6: (-13.0, 0.0),
        7: (-7.0, 0.0),
        8: (-7.0, 0.0),
        9: (-7.0, 0.0),
    }

    for cidx, tnum, wp, wn, xc, ctype in col_defs:
        if tnum not in [10, 11, 12, 13]:
            off_x, off_y = gate_offsets[tnum]
            gx = xc + off_x
            gy = off_y

            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "p0_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p_nodes[tnum].findPortInst("poly-left"), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), n_nodes[tnum].findPortInst("poly-right"))

            cgp, cgv = make_stacked_via("cg_%d" % tnum, gx, gy)
            if gy == 0.0:
                if gx < xc:
                    make_manhattan_arc(poly_wire, ep, cgp.getOnlyPortInst(), p0.getOnlyPortInst())
                else:
                    make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), cgp.getOnlyPortInst())
            elif gy < 0.0:
                make_manhattan_arc(poly_wire, ep, n_nodes[tnum].findPortInst("poly-left"), cgp.getOnlyPortInst())
            else:
                make_manhattan_arc(poly_wire, ep, cgp.getOnlyPortInst(), p_nodes[tnum].findPortInst("poly-right"))

            con_gates_p[tnum] = cgp
            con_gates_v[tnum] = cgv

    # Transmission gate stacked vias (Cols 10, 11, 12, 13)
    cg_p_poly = {}
    cg_p_via = {}
    cg_n_poly = {}
    cg_n_via = {}

    tg_x_tracks = {
        10: {'in': 236.0, 'gp': 244.0, 'gn': 252.0, 'out': 260.0},
        11: {'in': 268.0, 'gp': 276.0, 'gn': 284.0, 'out': 292.0},
        12: {'in': 300.0, 'gp': 308.0, 'gn': 316.0, 'out': 324.0},
        13: {'in': 332.0, 'gp': 340.0, 'gn': 348.0, 'out': 356.0},
    }

    for tnum in [10, 11, 12, 13]:
        xc = col_defs[tnum][4]
        tr = tg_x_tracks[tnum]

        # PMOS gate stacked via at (tr['gp'], 21.5)
        cgp, cgv = make_stacked_via("cgp_%d" % tnum, tr['gp'], 21.5)
        make_manhattan_arc(poly_wire, ep, cgp.getOnlyPortInst(), p_nodes[tnum].findPortInst("poly-right"))
        cg_p_poly[tnum] = cgp
        cg_p_via[tnum] = cgv

        # NMOS gate stacked via at (tr['gn'], -21.5)
        pin_n_corner = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, -21.5), 2.0, 2.0, cell, Orientation.IDENT, "pnc_%d" % tnum)
        make_manhattan_arc(poly_wire, ep, n_nodes[tnum].findPortInst("poly-left"), pin_n_corner.getOnlyPortInst())
        cgn, cgn_v = make_stacked_via("cgn_%d" % tnum, tr['gn'], -21.5)
        make_manhattan_arc(poly_wire, ep, pin_n_corner.getOnlyPortInst(), cgn.getOnlyPortInst())
        cg_n_poly[tnum] = cgn
        cg_n_via[tnum] = cgn_v

    # 4. Inverter Outputs
    inv_out_pins = {}
    for tnum in [0, 1, 2, 5, 9]:
        xc = col_defs[tnum][4]
        if tnum in [0, 1, 2, 5]:
            p_out = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(xc + dx, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "pout_%d" % tnum)
        else:
            p_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(xc + dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pout_%d" % tnum)
        inv_out_pins[tnum] = p_out
        make_manhattan_arc(m1_wire, ep, p_con_r[tnum].getOnlyPortInst(), p_out.getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, p_out.getOnlyPortInst(), n_con_r[tnum].getOnlyPortInst())

    Export.newInst(cell, inv_out_pins[9].getOnlyPortInst(), "COUNT_7", PortCharacteristic.OUT)

    # NAND2 C01B output:
    # Connects pcm_34 at (86.5, 14.0) and n_con_l[3] at (77.5, -14.0)
    pin_c01b_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(86.5, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c01b_out")
    pin_c01b_n3 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(77.5, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c01b_n3")

    make_manhattan_arc(m1_wire, ep, p_con_r[3].getOnlyPortInst(), pin_c01b_out.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c01b_out.getOnlyPortInst(), pin_c01b_n3.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c01b_n3.getOnlyPortInst(), n_con_l[3].getOnlyPortInst())

    # C01B to Inverter 5 gate at (108.0, 0.0) on Metal-1
    make_manhattan_arc(m1_wire, ep, pin_c01b_out.getOnlyPortInst(), con_gates_p[5].getOnlyPortInst())

    # NAND3 series NMOS:
    make_manhattan_arc(m1_wire, ep, n_con_r[6].getOnlyPortInst(), n_con_l[7].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, n_con_r[7].getOnlyPortInst(), n_con_l[8].getOnlyPortInst())

    # NAND3 output COUNT_7B:
    # Connects p_con_r[6, 7, 8] at (151.5, 175.5, 199.5, 14.0) and n_con_l[6] at (142.5, -14.0)
    # Route horizontally at Y = 7.0
    pin_c7b_6p = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(151.5, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c7b_6p")
    pin_c7b_7p = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(175.5, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c7b_7p")
    pin_c7b_8p = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(199.5, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c7b_8p")
    pin_c7b_6n = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(142.5, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c7b_6n")
    pin_c7b_g9 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(212.0, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_c7b_g9")

    make_manhattan_arc(m1_wire, ep, p_con_r[6].getOnlyPortInst(), pin_c7b_6p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, p_con_r[7].getOnlyPortInst(), pin_c7b_7p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, p_con_r[8].getOnlyPortInst(), pin_c7b_8p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, n_con_l[6].getOnlyPortInst(), pin_c7b_6n.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, pin_c7b_6n.getOnlyPortInst(), pin_c7b_6p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c7b_6p.getOnlyPortInst(), pin_c7b_7p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c7b_7p.getOnlyPortInst(), pin_c7b_8p.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c7b_8p.getOnlyPortInst(), pin_c7b_g9.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_c7b_g9.getOnlyPortInst(), con_gates_p[9].getOnlyPortInst())

    # TG Inputs & Outputs:
    tg_vias_in = {}
    tg_vias_out = {}

    for tnum in [10, 11, 12, 13]:
        xc = col_defs[tnum][4]
        tr = tg_x_tracks[tnum]
        vin_x = tr['in']
        vout_x = tr['out']

        vin = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(vin_x, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "tg_vin_%d" % tnum)
        pin_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(xc - dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "tg_pin_l_%d" % tnum)
        make_manhattan_arc(m1_wire, ep, p_con_l[tnum].getOnlyPortInst(), pin_l.getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, pin_l.getOnlyPortInst(), n_con_l[tnum].getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, vin.getOnlyPortInst(), pin_l.getOnlyPortInst())
        tg_vias_in[tnum] = vin

        vout = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(vout_x, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "tg_vout_%d" % tnum)
        pin_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(xc + dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "tg_pin_r_%d" % tnum)
        make_manhattan_arc(m1_wire, ep, p_con_r[tnum].getOnlyPortInst(), pin_r.getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, pin_r.getOnlyPortInst(), n_con_r[tnum].getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, pin_r.getOnlyPortInst(), vout.getOnlyPortInst())
        tg_vias_out[tnum] = vout

    # =========================================================================
    # 5. SOUTH TRACK ROUTING (Y < -32.0)
    # =========================================================================

    # Track S1: Y = -42.0 for C1B
    via_s1_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(38.5, -42.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s1_src")
    via_s1_dst = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[11]['in'], -42.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s1_dst")
    make_manhattan_arc(m2_wire, ep, inv_out_pins[1].getOnlyPortInst(), via_s1_src.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s1_src.getOnlyPortInst(), via_s1_dst.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_s1_dst.getOnlyPortInst(), tg_vias_in[11].getOnlyPortInst())

    # Track S2: Y = -52.0 for C2B
    via_s2_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(62.5, -52.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s2_src")
    via_s2_dst = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[13]['in'], -52.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s2_dst")
    make_manhattan_arc(m2_wire, ep, inv_out_pins[2].getOnlyPortInst(), via_s2_src.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s2_src.getOnlyPortInst(), via_s2_dst.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_s2_dst.getOnlyPortInst(), tg_vias_in[13].getOnlyPortInst())

    # Track S3: Y = -62.0 for C0B
    via_s3_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(14.5, -62.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s3_src")
    via_s3_n10 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[10]['gn'], -62.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s3_n10")
    via_s3_p11 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[11]['gp'], -62.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s3_p11")

    make_manhattan_arc(m2_wire, ep, inv_out_pins[0].getOnlyPortInst(), via_s3_src.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s3_src.getOnlyPortInst(), via_s3_n10.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s3_n10.getOnlyPortInst(), via_s3_p11.getOnlyPortInst())

    make_manhattan_arc(m2_wire, ep, via_s3_n10.getOnlyPortInst(), cg_n_via[10].getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_s3_p11.getOnlyPortInst(), cg_p_via[11].getOnlyPortInst())

    # Track S4: Y = -72.0 for C01B
    via_s4_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(108.0, -72.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s4_src")
    via_s4_n12 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[12]['gn'], -72.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s4_n12")
    via_s4_p13 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[13]['gp'], -72.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s4_p13")

    make_manhattan_arc(m2_wire, ep, con_gates_v[5].getOnlyPortInst(), via_s4_src.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s4_src.getOnlyPortInst(), via_s4_n12.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s4_n12.getOnlyPortInst(), via_s4_p13.getOnlyPortInst())

    make_manhattan_arc(m2_wire, ep, via_s4_n12.getOnlyPortInst(), cg_n_via[12].getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_s4_p13.getOnlyPortInst(), cg_p_via[13].getOnlyPortInst())

    # Track S5: Y = -82.0 for C01 (Inverter 5 output at 119.5, 0.0)
    via_s5_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(119.5, -82.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s5_src")
    via_s5_p12 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[12]['gp'], -82.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s5_p12")
    via_s5_n13 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[13]['gn'], -82.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s5_n13")

    make_manhattan_arc(m2_wire, ep, inv_out_pins[5].getOnlyPortInst(), via_s5_src.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s5_src.getOnlyPortInst(), via_s5_p12.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s5_p12.getOnlyPortInst(), via_s5_n13.getOnlyPortInst())

    make_manhattan_arc(m2_wire, ep, via_s5_p12.getOnlyPortInst(), cg_p_via[12].getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_s5_n13.getOnlyPortInst(), cg_n_via[13].getOnlyPortInst())

    # Track S6: Y = -92.0 for C1 (from DFF1[Q] at 271.5, 172.0)
    X_C1_Q = 372.0
    via_c1_q = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(X_C1_Q, Y_ROW2), 3.0, 3.0, cell, Orientation.IDENT, "via_c1_q")
    make_manhattan_arc(m2_wire, ep, dff1.findPortInst("Q"), via_c1_q.getOnlyPortInst())

    via_s6_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_C1_Q, -92.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s6_src")
    make_manhattan_arc(m2_wire, ep, via_c1_q.getOnlyPortInst(), via_s6_src.getOnlyPortInst())

    # C1 drops to: INV1 (27.0), NAND2 (cg4 at 91.0), NAND3 (cg7 at 164.0), TG1 (tr10['in'] = 236.0)
    c1_drops = [27.0, 91.0, 164.0, tg_x_tracks[10]['in']]
    c1_vias_s6 = {}
    for x in c1_drops:
        v_s = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x, -92.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s6_%.1f" % x)
        c1_vias_s6[x] = v_s
        if x == 27.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[1].getOnlyPortInst())
        elif x == 91.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[4].getOnlyPortInst())
        elif x == 164.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[7].getOnlyPortInst())
        elif x == tg_x_tracks[10]['in']:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), tg_vias_in[10].getOnlyPortInst())

    c1_all_x = sorted(c1_drops + [X_C1_Q])
    for i in range(len(c1_all_x) - 1):
        n1 = c1_vias_s6[c1_all_x[i]]
        n2 = via_s6_src if c1_all_x[i+1] == X_C1_Q else c1_vias_s6[c1_all_x[i+1]]
        make_manhattan_arc(m1_wire, ep, n1.getOnlyPortInst(), n2.getOnlyPortInst())

    # Track S7: Y = -102.0 for C2 (from DFF2[Q] at 271.5, 258.0)
    X_C2_Q = 380.0
    via_c2_q = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(X_C2_Q, Y_ROW3), 3.0, 3.0, cell, Orientation.IDENT, "via_c2_q")
    make_manhattan_arc(m2_wire, ep, dff2.findPortInst("Q"), via_c2_q.getOnlyPortInst())

    via_s7_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_C2_Q, -102.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s7_src")
    make_manhattan_arc(m2_wire, ep, via_c2_q.getOnlyPortInst(), via_s7_src.getOnlyPortInst())

    # C2 drops to: INV2 (51.0), NAND3 (cg8 at 188.0), TG3 (tr12['in'] = 300.0)
    c2_drops = [51.0, 188.0, tg_x_tracks[12]['in']]
    c2_vias_s7 = {}
    for x in c2_drops:
        v_s = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x, -102.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s7_%.1f" % x)
        c2_vias_s7[x] = v_s
        if x == 51.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[2].getOnlyPortInst())
        elif x == 188.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[8].getOnlyPortInst())
        elif x == tg_x_tracks[12]['in']:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), tg_vias_in[12].getOnlyPortInst())

    c2_all_x = sorted(c2_drops + [X_C2_Q])
    for i in range(len(c2_all_x) - 1):
        n1 = c2_vias_s7[c2_all_x[i]]
        n2 = via_s7_src if c2_all_x[i+1] == X_C2_Q else c2_vias_s7[c2_all_x[i+1]]
        make_manhattan_arc(m1_wire, ep, n1.getOnlyPortInst(), n2.getOnlyPortInst())

    # Track S8: Y = -112.0 for C0 (from DFF0[Q] at 271.5, 86.0)
    X_C0_Q = 364.0
    via_c0_q = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(X_C0_Q, Y_ROW1), 3.0, 3.0, cell, Orientation.IDENT, "via_c0_q")
    make_manhattan_arc(m2_wire, ep, dff0.findPortInst("Q"), via_c0_q.getOnlyPortInst())

    via_s8_src = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_C0_Q, -112.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s8_src")
    make_manhattan_arc(m2_wire, ep, via_c0_q.getOnlyPortInst(), via_s8_src.getOnlyPortInst())

    # C0 drops to: INV0 (3.0), NAND2 (cg3 at 82.0), NAND3 (cg6 at 134.0), TG1 PMOS (tr10['gp']=244.0), TG2 NMOS (tr11['gn']=284.0)
    c0_drops = [3.0, 82.0, 134.0, tg_x_tracks[10]['gp'], tg_x_tracks[11]['gn']]
    c0_vias_s8 = {}
    for x in c0_drops:
        v_s = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x, -112.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s8_%.1f" % x)
        c0_vias_s8[x] = v_s
        if x == 3.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[0].getOnlyPortInst())
        elif x == 82.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[3].getOnlyPortInst())
        elif x == 134.0:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), con_gates_v[6].getOnlyPortInst())
        elif x == tg_x_tracks[10]['gp']:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), cg_p_via[10].getOnlyPortInst())
        elif x == tg_x_tracks[11]['gn']:
            make_manhattan_arc(m2_wire, ep, v_s.getOnlyPortInst(), cg_n_via[11].getOnlyPortInst())

    c0_all_x = sorted(c0_drops + [X_C0_Q])
    for i in range(len(c0_all_x) - 1):
        n1 = c0_vias_s8[c0_all_x[i]]
        n2 = via_s8_src if c0_all_x[i+1] == X_C0_Q else c0_vias_s8[c0_all_x[i+1]]
        make_manhattan_arc(m1_wire, ep, n1.getOnlyPortInst(), n2.getOnlyPortInst())

    # Track S9: Y = -122.0 for D1
    X_D1_UP = 388.0
    via_s9_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[10]['out'], -122.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s9_1")
    via_s9_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[11]['out'], -122.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s9_2")
    via_s9_r = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_D1_UP, -122.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s9_r")

    make_manhattan_arc(m2_wire, ep, tg_vias_out[10].getOnlyPortInst(), via_s9_1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, tg_vias_out[11].getOnlyPortInst(), via_s9_2.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, via_s9_1.getOnlyPortInst(), via_s9_2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s9_2.getOnlyPortInst(), via_s9_r.getOnlyPortInst())

    # Track S10: Y = -132.0 for D2
    X_D2_UP = 396.0
    via_s10_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[12]['out'], -132.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s10_1")
    via_s10_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(tg_x_tracks[13]['out'], -132.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s10_2")
    via_s10_r = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_D2_UP, -132.0), 5.0, 5.0, cell, Orientation.IDENT, "via_s10_r")

    make_manhattan_arc(m2_wire, ep, tg_vias_out[12].getOnlyPortInst(), via_s10_1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, tg_vias_out[13].getOnlyPortInst(), via_s10_2.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, via_s10_1.getOnlyPortInst(), via_s10_2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_s10_2.getOnlyPortInst(), via_s10_r.getOnlyPortInst())

    # =========================================================================
    # 6. D0, D1, D2 ROUTING TO DFF INPUTS
    # =========================================================================

    # D0: INV0 output (14.5, 0.0) -> DFF0[D] at (55.5, 86.0) via X = -11.0
    via_d0_ch0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(14.5, 44.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d0_ch0")
    make_manhattan_arc(m2_wire, ep, inv_out_pins[0].getOnlyPortInst(), via_d0_ch0.getOnlyPortInst())

    via_d0_x11 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-11.0, 44.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d0_x11")
    make_manhattan_arc(m1_wire, ep, via_d0_ch0.getOnlyPortInst(), via_d0_x11.getOnlyPortInst())

    via_d0_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-11.0, Y_ROW1), 3.0, 3.0, cell, Orientation.IDENT, "via_d0_turn")
    make_manhattan_arc(m2_wire, ep, via_d0_x11.getOnlyPortInst(), via_d0_turn.getOnlyPortInst())

    via_dff0_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW1), 5.0, 5.0, cell, Orientation.IDENT, "via_dff0_d")
    make_manhattan_arc(m2_wire, ep, via_d0_turn.getOnlyPortInst(), via_dff0_d.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_dff0_d.getOnlyPortInst(), dff0.findPortInst("D"))

    # D1: from via_s9_r at (X_D1_UP, -122.0) -> Channel 1 (129.0) -> X = -17.0 -> DFF1[D]
    via_d1_ch1_r = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_D1_UP, 129.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d1_ch1_r")
    make_manhattan_arc(m2_wire, ep, via_s9_r.getOnlyPortInst(), via_d1_ch1_r.getOnlyPortInst())

    via_d1_x17 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-17.0, 129.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d1_x17")
    make_manhattan_arc(m1_wire, ep, via_d1_ch1_r.getOnlyPortInst(), via_d1_x17.getOnlyPortInst())

    via_d1_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-17.0, Y_ROW2), 3.0, 3.0, cell, Orientation.IDENT, "via_d1_turn")
    make_manhattan_arc(m2_wire, ep, via_d1_x17.getOnlyPortInst(), via_d1_turn.getOnlyPortInst())

    via_dff1_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW2), 5.0, 5.0, cell, Orientation.IDENT, "via_dff1_d")
    make_manhattan_arc(m2_wire, ep, via_d1_turn.getOnlyPortInst(), via_dff1_d.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_dff1_d.getOnlyPortInst(), dff1.findPortInst("D"))

    # D2: from via_s10_r at (X_D2_UP, -132.0) -> Channel 2 (215.0) -> X = -23.0 -> DFF2[D]
    via_d2_ch2_r = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_D2_UP, 215.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d2_ch2_r")
    make_manhattan_arc(m2_wire, ep, via_s10_r.getOnlyPortInst(), via_d2_ch2_r.getOnlyPortInst())

    via_d2_x23 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-23.0, 215.0), 5.0, 5.0, cell, Orientation.IDENT, "via_d2_x23")
    make_manhattan_arc(m1_wire, ep, via_d2_ch2_r.getOnlyPortInst(), via_d2_x23.getOnlyPortInst())

    via_d2_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-23.0, Y_ROW3), 3.0, 3.0, cell, Orientation.IDENT, "via_d2_turn")
    make_manhattan_arc(m2_wire, ep, via_d2_x23.getOnlyPortInst(), via_d2_turn.getOnlyPortInst())

    via_dff2_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW3), 5.0, 5.0, cell, Orientation.IDENT, "via_dff2_d")
    make_manhattan_arc(m2_wire, ep, via_d2_turn.getOnlyPortInst(), via_dff2_d.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_dff2_d.getOnlyPortInst(), dff2.findPortInst("D"))

    # Verification: Manhattan check
    total_arcs = 0
    non_m = 0
    ait = cell.getArcs()
    while ait.hasNext():
        a = ait.next()
        total_arcs += 1
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        if abs(p1.getX() - p2.getX()) > 0.001 and abs(p1.getY() - p2.getY()) > 0.001:
            print("Non-Manhattan arc: %s" % a.getName())
            non_m += 1

    print("Manhattan Check: %d / %d perpendicular (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))
    if non_m > 0:
        raise AssertionError("Non-Manhattan arcs detected in 3Bit_counter{lay}!")

    # Verification: Quick DRC
    print("Running Quick DRC on 3Bit_counter{lay}...")
    n_err, n_warn = run_drc(cell)
    if n_err > 0 or n_warn > 0:
        raise AssertionError("DRC failed with %d errors, %d warnings!" % (n_err, n_warn))

    # Verification: NCC LVS with checkSizes = True
    print("Running NCC against 3Bit_counter{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())
    if not res.match():
        raise AssertionError("NCC LVS comparison failed for 3Bit_counter{lay}!")

    # Save library to disk
    print("Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Successfully saved 3Bit_counter{lay} to %s" % jelib_path)

def main():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
    mocmos = Technology.findTechnology("mocmos")

    edb = lib.getDatabase()
    batch = Setting.SettingChangeBatch()
    batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
    edb.implementSettingChanges(batch)

    build_counter_layout(lib, ep, mocmos, jelib_path)

if __name__ == "__main__":
    main()
