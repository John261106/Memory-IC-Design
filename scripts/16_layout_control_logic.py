# scripts/16_layout_control_logic.py
# Clean, compact, DRC/LVS-clean layout generator for Control_logic{lay} in Memory-IC-Design.jelib
# Rules: MOSIS SCMOS_SUBM (mocmos), lambda = 90nm
# Features:
# 1. Minimum contact-to-MOSFET active diffusion distance: dx = 4.5 lambda (0.405 um) across all 42 transistors.
# 2. Continuous shared active diffusion regions for all 3 NAND pairs:
#    - WL_EN NAND pair (pmos@11 & pmos@12, nmos@11 & nmos@12)
#    - WRITE_EN NAND pair (pmos@5 & pmos@6, nmos@5 & nmos@6)
#    - READ_EN NAND pair (pmos@8 & pmos@9, nmos@8 & nmos@9)
# 3. Standard cell height = 56.0 lambda (Y_VDD = +28.0, Y_GND = -28.0).
# 4. Straight, low-resistance vertical Metal-1 lines, horizontal Metal-2 routing tracks, and power rails.
# 5. 100% Manhattan perpendicular routing (0 non-perpendicular arcs).
# 6. Zero DRC errors & warnings (Quick ALGO_SWEEP).
# 7. 100% LVS / NCC match with checkSizes = True against Control_logic{sch}.

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
    while eit.hasNext():
        exp_kill.append(eit.next())
    for e in exp_kill:
        e.kill()

    ait = cell.getArcs()
    arc_kill = []
    while ait.hasNext():
        arc_kill.append(ait.next())
    for a in arc_kill:
        a.kill()

    nit = cell.getNodes()
    node_kill = []
    while nit.hasNext():
        node_kill.append(nit.next())
    for n in node_kill:
        n.kill()

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
        while it.hasNext():
            msg = it.next().getMessageString()
            if msg not in seen:
                seen.add(msg)
                print("   DRC:", msg)
    return n_err, n_warn

def build_control_logic_layout(lib, ep, mocmos, jelib_path):
    sch = lib.findNodeProto("Control_logic{sch}")
    if not sch:
        raise AssertionError("Control_logic{sch} not found in library!")

    cell = lib.findNodeProto("Control_logic{lay}")
    if not cell:
        cell = Cell.makeInstance(lib, "Control_logic{lay}")
    else:
        clear_cell_contents(cell)
    cell.setTechnology(mocmos)

    # Node prototypes
    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")
    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
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

    Y_VDD = 28.0
    Y_GND = -28.0
    Y_P = 14.0
    Y_N = -14.0
    dx = 4.5

    # 21 columns
    # col_defs: (idx, tnum, wp, wn, is_nand_b, is_nand_a)
    col_defs = [
        (0,  0,  8.0, 4.0, False, False), # Col 0: CLK Inv
        (1,  2,  8.0, 4.0, False, False), # Col 1: CLKB Buf
        (2,  3, 12.0, 6.0, False, False), # Col 2: PCB Buf (12/6)
        (3,  4,  8.0, 4.0, False, False), # Col 3: CTRL Inv
        (4, 12,  4.0, 4.0, True,  False), # Col 4: WL_EN NAND B (4/4)
        (5, 11,  4.0, 4.0, False, True),  # Col 5: WL_EN NAND A (4/4)
        (6, 13, 12.0, 6.0, False, False), # Col 6: WL_EN Buf (12/6)
        (7,  6,  4.0, 4.0, True,  False), # Col 7: WRITE_EN NAND B (4/4)
        (8,  5,  4.0, 4.0, False, True),  # Col 8: WRITE_EN NAND A (4/4)
        (9,  7, 12.0, 6.0, False, False), # Col 9: WRITE_EN Buf (12/6)
        (10, 9,  4.0, 4.0, True,  False), # Col 10: READ_EN NAND B (4/4)
        (11, 8,  4.0, 4.0, False, True),  # Col 11: READ_EN NAND A (4/4)
        (12, 10, 8.0, 4.0, False, False), # Col 12: ren_d0 Inv
        (13, 14, 8.0, 4.0, False, False), # Col 13: ren_d1 Inv
        (14, 15, 8.0, 4.0, False, False), # Col 14: ren_d2 Inv
        (15, 16, 8.0, 4.0, False, False), # Col 15: ren_d3 Inv
        (16, 17, 8.0, 4.0, False, False), # Col 16: ren_d4 Inv
        (17, 18, 8.0, 4.0, False, False), # Col 17: ren_d5 Inv
        (18, 19, 8.0, 4.0, False, False), # Col 18: ren_d6 Inv
        (19, 20, 8.0, 4.0, False, False), # Col 19: ren_d7 Inv
        (20, 21, 12.0, 6.0, False, False),# Col 20: READ_EN Buf (12/6)
    ]

    # Calculate X_COLS with pitch 24.0 and NAND pitch 9.0
    X_COLS = {}
    curr_x = 10.0
    for idx, tnum, wp, wn, is_nb, is_na in col_defs:
        X_COLS[idx] = curr_x
        if is_nb:
            curr_x += 9.0
        else:
            curr_x += 24.0
    X_MAX = curr_x

    print("Total columns: %d, X_MAX = %.1f" % (len(col_defs), X_MAX))

    # N-well & P-well
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(X_MAX / 2.0, 19.0), X_MAX + 16.0, 32.0, cell, Orientation.IDENT, "nwell_core")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(X_MAX / 2.0, -19.0), X_MAX + 16.0, 32.0, cell, Orientation.IDENT, "pwell_core")

    # Step 1: Place Transistors & Active Contacts
    p_nodes = {}
    n_nodes = {}
    p_con_l = {}
    p_con_r = {}
    n_con_l = {}
    n_con_r = {}
    p_con_mid = {}
    n_con_mid = {}

    vdd_drops = []
    gnd_drops = []

    for idx, tnum, wp, wn, is_nb, is_na in col_defs:
        xc = X_COLS[idx]
        p = NodeInst.makeInstance(p_proto, ep, Point2D.Double(xc, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@%d" % tnum)
        p.setPrimitiveNodeSize(wp, 2.0, ep)
        p_nodes[tnum] = p

        n = NodeInst.makeInstance(n_proto, ep, Point2D.Double(xc, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@%d" % tnum)
        n.setPrimitiveNodeSize(wn, 2.0, ep)
        n_nodes[tnum] = n

        if is_nb:
            # NAND B (left transistor):
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_l_%d" % tnum)
            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_l_%d" % tnum)
            p_con_l[tnum] = pcl
            n_con_l[tnum] = ncl
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            vdd_drops.append((pcl, xc - dx))
            gnd_drops.append((ncl, xc - dx))

            # Middle shared contact between NAND B and NAND A
            mid_x = xc + dx
            pcm = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(mid_x, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_mid_%d" % tnum)
            ncm = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(mid_x, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_mid_%d" % tnum)
            p_con_mid[tnum] = pcm
            n_con_mid[tnum] = ncm
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcm.getOnlyPortInst())
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncm.getOnlyPortInst())

        elif is_na:
            # NAND A (right transistor):
            pair_b_tnum = col_defs[idx - 1][1]
            pcm = p_con_mid[pair_b_tnum]
            ncm = n_con_mid[pair_b_tnum]
            make_manhattan_arc(p_act_wire, ep, pcm.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, ncm.getOnlyPortInst(), n.findPortInst("diff-top"))

            # Right contact: VDD (PMOS) and NAND_OUT (NMOS)
            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_r_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_r_%d" % tnum)
            p_con_r[tnum] = pcr
            n_con_r[tnum] = ncr
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())
            vdd_drops.append((pcr, xc + dx))

        else:
            # Standard Inverter column
            pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_l_%d" % tnum)
            pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_r_%d" % tnum)
            p_con_l[tnum] = pcl
            p_con_r[tnum] = pcr
            make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
            make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())

            ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_l_%d" % tnum)
            ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_r_%d" % tnum)
            n_con_l[tnum] = ncl
            n_con_r[tnum] = ncr
            make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
            make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())

            vdd_drops.append((pcl, xc - dx))
            gnd_drops.append((ncl, xc - dx))

    # Step 2: VDD and GND Power Rails
    vdd_map = {}
    tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(-2.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd")
    vdd_map[-2.0] = tap_vdd
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")
    vdd_map[X_MAX] = pin_vdd_r

    for con, x in vdd_drops:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_v_%.1f" % x)
        vdd_map[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_vdd_x = sorted(vdd_map.keys())
    for i in range(len(sorted_vdd_x) - 1):
        make_manhattan_arc(m1_wire, ep, vdd_map[sorted_vdd_x[i]].getOnlyPortInst(), vdd_map[sorted_vdd_x[i+1]].getOnlyPortInst())

    gnd_map = {}
    tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(-2.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd")
    gnd_map[-2.0] = tap_gnd
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")
    gnd_map[X_MAX] = pin_gnd_r

    for con, x in gnd_drops:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_g_%.1f" % x)
        gnd_map[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_gnd_x = sorted(gnd_map.keys())
    for i in range(len(sorted_gnd_x) - 1):
        make_manhattan_arc(m1_wire, ep, gnd_map[sorted_gnd_x[i]].getOnlyPortInst(), gnd_map[sorted_gnd_x[i+1]].getOnlyPortInst())

    Export.newInst(cell, tap_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, tap_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    # Step 3: Poly gates and Inverter Outputs
    gate_tap_pins = {}
    inv_out_pins = {}

    for idx, tnum, wp, wn, is_nb, is_na in col_defs:
        xc = X_COLS[idx]
        p = p_nodes[tnum]
        n = n_nodes[tnum]

        if tnum in [12, 6, 9]: # NAND B gates (tap at Y = -7.0)
            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "ppin0_%d" % tnum)
            ptap = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, -7.0), 2.0, 2.0, cell, Orientation.IDENT, "ptap_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p.findPortInst("poly-left"), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), ptap.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, ptap.getOnlyPortInst(), n.findPortInst("poly-right"))
            gate_tap_pins[tnum] = ptap

        elif tnum == 8: # Col 11 (READ_ENB NAND A) tap at Y = +7.0
            ptap = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 7.0), 2.0, 2.0, cell, Orientation.IDENT, "ptap_%d" % tnum)
            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "ppin0_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p.findPortInst("poly-left"), ptap.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, ptap.getOnlyPortInst(), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), n.findPortInst("poly-right"))
            gate_tap_pins[tnum] = ptap

        elif tnum in [5, 11]: # NAND A gates (tap below NMOS at Y = -21.0)
            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "ppin0_%d" % tnum)
            ptap = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, -21.0), 2.0, 2.0, cell, Orientation.IDENT, "ptap_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p.findPortInst("poly-left"), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), n.findPortInst("poly-right"))
            make_manhattan_arc(poly_wire, ep, n.findPortInst("poly-left"), ptap.getOnlyPortInst())
            gate_tap_pins[tnum] = ptap

        else:
            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "ppin0_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p.findPortInst("poly-left"), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), n.findPortInst("poly-right"))
            gate_tap_pins[tnum] = p0

        if not is_nb and not is_na:
            opin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(xc + dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "opin_%d" % tnum)
            inv_out_pins[tnum] = opin
            make_manhattan_arc(m1_wire, ep, p_con_r[tnum].getOnlyPortInst(), opin.getOnlyPortInst())
            make_manhattan_arc(m1_wire, ep, opin.getOnlyPortInst(), n_con_r[tnum].getOnlyPortInst())

    # NAND internal output connections:
    nand_out_pins = {}
    for b_tnum, a_tnum, name in [(12, 11, "WL_ENB"), (6, 5, "WRITE_ENB"), (9, 8, "READ_ENB")]:
        mid_pcon = p_con_mid[b_tnum] # at mid_x, Y_P
        r_ncon = n_con_r[a_tnum]     # at a_xc + dx, Y_N
        mid_x = mid_pcon.getOnlyPortInst().getCenter().getX()
        r_x = r_ncon.getOnlyPortInst().getCenter().getX()

        pin_pm = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(mid_x, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_pm_%s" % name)
        pin_nm = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(r_x, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_nm_%s" % name)
        make_manhattan_arc(m1_wire, ep, mid_pcon.getOnlyPortInst(), pin_pm.getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, r_ncon.getOnlyPortInst(), pin_nm.getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, pin_pm.getOnlyPortInst(), pin_nm.getOnlyPortInst())
        nand_out_pins[name] = pin_nm

    # Step 4: Inter-Gate Routing & Exports
    
    # 1. CLK Input: at Col 0 (X_COLS[0] = 10.0)
    con_clk = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(0.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_clk")
    make_manhattan_arc(poly_wire, ep, con_clk.getOnlyPortInst(), gate_tap_pins[0].getOnlyPortInst())
    Export.newInst(cell, con_clk.getOnlyPortInst(), "CLK", PortCharacteristic.IN)

    # 2. CLKB: Col 0 output (inv_out_pins[0] at 14.5, 0.0)
    # Feeds Col 1 gate at X_COLS[1] = 34.0:
    con_g_2 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[1] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_2")
    make_manhattan_arc(poly_wire, ep, con_g_2.getOnlyPortInst(), gate_tap_pins[2].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, inv_out_pins[0].getOnlyPortInst(), con_g_2.getOnlyPortInst())

    # Co-locate via_clkb_1 with con_g_2 at (27.0, 0.0), then Metal-2 down to (27.0, -7.0) and to Col 4 at (99.0, -7.0):
    via_clkb_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[1] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "via_clkb_1")
    make_manhattan_arc(m1_wire, ep, con_g_2.getOnlyPortInst(), via_clkb_1.getOnlyPortInst())
    pin_clkb_m2 = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(X_COLS[1] - 7.0, -7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_clkb_m2")
    make_manhattan_arc(m2_wire, ep, via_clkb_1.getOnlyPortInst(), pin_clkb_m2.getOnlyPortInst())

    # Destination at Col 4: stack m1_m2_con and m1_poly_con at (X_COLS[4] - 7.0, -7.0) = (99.0, -7.0)
    via_clkb_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[4] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "via_clkb_2")
    con_g_12 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[4] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_12")
    make_manhattan_arc(m1_wire, ep, via_clkb_2.getOnlyPortInst(), con_g_12.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, pin_clkb_m2.getOnlyPortInst(), via_clkb_2.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_g_12.getOnlyPortInst(), gate_tap_pins[12].getOnlyPortInst())

    # 3. CLK_buf: Col 1 output (inv_out_pins[2] at X_COLS[1]+4.5, 0.0) -> Col 2 gate (at X_COLS[2] = 58.0)
    con_g_3 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[2] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_3")
    make_manhattan_arc(poly_wire, ep, con_g_3.getOnlyPortInst(), gate_tap_pins[3].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, inv_out_pins[2].getOnlyPortInst(), con_g_3.getOnlyPortInst())

    # 4. PCB Export: Col 2 output
    Export.newInst(cell, inv_out_pins[3].getOnlyPortInst(), "PCB", PortCharacteristic.OUT)

    # 5. CTRL Input: feeds Col 3 (X_COLS[3] = 82.0) and Col 11 (X_COLS[11] = 229.0)
    # Contact at (X_COLS[3] - 7.0, 0.0) = (75.0, 0.0):
    con_ctrl = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[3] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_ctrl")
    via_ctrl_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[3] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "via_ctrl_1")
    make_manhattan_arc(m1_wire, ep, con_ctrl.getOnlyPortInst(), via_ctrl_1.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_ctrl.getOnlyPortInst(), gate_tap_pins[4].getOnlyPortInst())
    Export.newInst(cell, con_ctrl.getOnlyPortInst(), "CTRL", PortCharacteristic.IN)

    # Turn up to Y = +7.0 in Metal-2:
    pin_ctrl_m2 = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(X_COLS[3] - 7.0, 7.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_ctrl_m2")
    make_manhattan_arc(m2_wire, ep, via_ctrl_1.getOnlyPortInst(), pin_ctrl_m2.getOnlyPortInst())

    # Route CTRL to Col 11 (p8/n8 at 229.0) via Metal-2 track at Y = +7.0:
    via_ctrl_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(238.0, 7.0), 5.0, 5.0, cell, Orientation.IDENT, "via_ctrl_2")
    con_g_8 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(238.0, 7.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_8")
    make_manhattan_arc(m1_wire, ep, via_ctrl_2.getOnlyPortInst(), con_g_8.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, pin_ctrl_m2.getOnlyPortInst(), via_ctrl_2.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_g_8.getOnlyPortInst(), gate_tap_pins[8].getOnlyPortInst())

    # 6. CTRLB: output of Col 3 (inv_out_pins[4] at X_COLS[3]+4.5 = 86.5, 0.0) -> feeds Col 8 (at X_COLS[8] = 172.0)
    via_ctrlb_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[3] + 4.5, -21.0), 5.0, 5.0, cell, Orientation.IDENT, "via_ctrlb_1")
    make_manhattan_arc(m1_wire, ep, inv_out_pins[4].getOnlyPortInst(), via_ctrlb_1.getOnlyPortInst())

    # Horizontal Metal-2 wire from (86.5, -21.0) to (172.0, -21.0):
    via_ctrlb_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[8], -21.0), 5.0, 5.0, cell, Orientation.IDENT, "via_ctrlb_2")
    con_g_5 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[8], -21.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_5")
    make_manhattan_arc(m1_wire, ep, via_ctrlb_2.getOnlyPortInst(), con_g_5.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_ctrlb_1.getOnlyPortInst(), via_ctrlb_2.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_g_5.getOnlyPortInst(), gate_tap_pins[5].getOnlyPortInst())

    # 7. COUNT_7 Input: feeds Col 5 (at X_COLS[5] = 115.0)
    # Place below NMOS at Y = -21.0:
    con_count7 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[5], -21.0), 5.0, 5.0, cell, Orientation.IDENT, "con_count7")
    make_manhattan_arc(poly_wire, ep, gate_tap_pins[11].getOnlyPortInst(), con_count7.getOnlyPortInst())
    Export.newInst(cell, con_count7.getOnlyPortInst(), "COUNT_7", PortCharacteristic.IN)

    # 8. WL_ENB: output of NAND (nand_out_pins["WL_ENB"]) -> Col 6 gate (at X_COLS[6] = 139.0)
    con_g_13 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[6] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_13")
    make_manhattan_arc(poly_wire, ep, con_g_13.getOnlyPortInst(), gate_tap_pins[13].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, nand_out_pins["WL_ENB"].getOnlyPortInst(), con_g_13.getOnlyPortInst())

    # 9. WL_EN: output of Col 6 (inv_out_pins[13] at X_COLS[6]+4.5 = 143.5, 0.0)
    # Feeds: Export WL_EN, Col 7 gate (at X_COLS[7] = 163.0), and Col 10 gate (at X_COLS[10] = 220.0)
    Export.newInst(cell, inv_out_pins[13].getOnlyPortInst(), "WL_EN", PortCharacteristic.OUT)

    # Route WL_EN to Col 7 and Col 10:
    via_wlen_1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[6] + 4.5, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "via_wlen_1")
    make_manhattan_arc(m1_wire, ep, inv_out_pins[13].getOnlyPortInst(), via_wlen_1.getOnlyPortInst())
    
    # Col 7 gate contact at X_COLS[7] - 7.0 = 156.0:
    via_wlen_2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[7] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "via_wlen_2")
    con_g_6 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[7] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_6")
    make_manhattan_arc(m1_wire, ep, via_wlen_2.getOnlyPortInst(), con_g_6.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_wlen_1.getOnlyPortInst(), via_wlen_2.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_g_6.getOnlyPortInst(), gate_tap_pins[6].getOnlyPortInst())

    # Col 10 gate contact at X_COLS[10] - 7.0 = 213.0:
    via_wlen_3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_COLS[10] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "via_wlen_3")
    con_g_9 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[10] - 7.0, -7.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_9")
    make_manhattan_arc(m1_wire, ep, via_wlen_3.getOnlyPortInst(), con_g_9.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_wlen_2.getOnlyPortInst(), via_wlen_3.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_g_9.getOnlyPortInst(), gate_tap_pins[9].getOnlyPortInst())

    # 10. WRITE_ENB: output of NAND (nand_out_pins["WRITE_ENB"]) -> Col 9 gate (at X_COLS[9] = 196.0)
    con_g_7 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[9] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_7")
    make_manhattan_arc(poly_wire, ep, con_g_7.getOnlyPortInst(), gate_tap_pins[7].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, nand_out_pins["WRITE_ENB"].getOnlyPortInst(), con_g_7.getOnlyPortInst())

    # 11. WRITE_EN Export: Col 9 output
    Export.newInst(cell, inv_out_pins[7].getOnlyPortInst(), "WRITE_EN", PortCharacteristic.OUT)

    # 12. READ_ENB: output of NAND (nand_out_pins["READ_ENB"]) -> Col 12 gate (at X_COLS[12] = 253.0)
    con_g_10 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X_COLS[12] - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_10")
    make_manhattan_arc(poly_wire, ep, con_g_10.getOnlyPortInst(), gate_tap_pins[10].getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, nand_out_pins["READ_ENB"].getOnlyPortInst(), con_g_10.getOnlyPortInst())

    # 13. Delay line chain:
    chain_pairs = [
        (10, 14, 13),
        (14, 15, 14),
        (15, 16, 15),
        (16, 17, 16),
        (17, 18, 17),
        (18, 19, 18),
        (19, 20, 19),
        (20, 21, 20),
    ]

    for src_tnum, dst_tnum, dst_col_idx in chain_pairs:
        dst_xc = X_COLS[dst_col_idx]
        cg = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(dst_xc - 7.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_g_%d" % dst_tnum)
        make_manhattan_arc(poly_wire, ep, cg.getOnlyPortInst(), gate_tap_pins[dst_tnum].getOnlyPortInst())
        make_manhattan_arc(m1_wire, ep, inv_out_pins[src_tnum].getOnlyPortInst(), cg.getOnlyPortInst())

    # 14. READ_EN Export: Col 20 output
    Export.newInst(cell, inv_out_pins[21].getOnlyPortInst(), "READ_EN", PortCharacteristic.OUT)

    # Verification: Manhattan check
    ait = cell.getArcs()
    non_m = 0
    tot_arcs = 0
    while ait.hasNext():
        a = ait.next()
        tot_arcs += 1
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        if abs(p1.getX() - p2.getX()) > 0.001 and abs(p1.getY() - p2.getY()) > 0.001:
            print("Non-manhattan arc: %s" % a.getName())
            non_m += 1
    print("Manhattan check: %d / %d perpendicular" % (tot_arcs - non_m, tot_arcs))
    if non_m > 0:
        raise AssertionError("Non-manhattan arcs detected in Control_logic{lay}!")

    # Verification: Quick DRC
    print("Running Quick DRC on Control_logic{lay}...")
    n_err, n_warn = run_drc(cell)
    if n_err > 0 or n_warn > 0:
        raise AssertionError("DRC failed with %d errors, %d warnings!" % (n_err, n_warn))

    # Verification: NCC LVS with checkSizes = True
    print("Running NCC against Control_logic{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())
    if not res.match():
        raise AssertionError("NCC LVS comparison failed for Control_logic{lay}!")

    # Save library to disk
    print("Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Successfully saved Control_logic{lay} to %s" % jelib_path)

def main():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
    mocmos = Technology.findTechnology("mocmos")

    build_control_logic_layout(lib, ep, mocmos, jelib_path)

if __name__ == "__main__":
    main()
