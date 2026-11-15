# ==============================================================================
# Electric VLSI 9.08 - Shared-Diffusion 6T SRAM Bitcell Layout Generator
#
# Generates the highly optimized physical layout view:
#   6T_cell{lay} in 'Memory-IC-Design.jelib'
#
# Optimization Achievements:
#   - Width:  45.0 lambda (4.05 um)   [reduced from 72.0 lambda, 37.5% reduction]
#   - Height: 72.0 lambda (6.48 um)   [reduced from 90.0 lambda, 20.0% reduction]
#   - Silicon Area: 3,240 lambda^2 (26.24 um^2)
#       -> 50.0% Area Reduction vs previous compact layout (6,480 lambda^2)
#       -> 89.88% Area Reduction vs original baseline (32,000 lambda^2)
#
# Shared-Diffusion Architecture:
#   1. Continuous Shared N-Active Diffusion Row:
#      All 4 NMOS transistors share ONE continuous horizontal active diffusion row:
#      - Left access (nmos@2) and left driver (nmos@0) share the Node Q diffusion & contact.
#      - Left driver (nmos@0) and right driver (nmos@1) share the GND diffusion & contact.
#      - Right driver (nmos@1) and right access (nmos@3) share the Node QB diffusion & contact.
#      No separate row of access transistors needed!
#   2. Continuous Shared P-Active Diffusion Row:
#      Both pull-up PMOS transistors (pmos@0, pmos@1) share ONE continuous active diffusion row,
#      sharing the central VDD diffusion & contact.
#   3. Minimum contact-to-MOSFET active diffusion distance: dx = 4.5 lambda (0.405 um)
#      for every single transistor on both source and drain sides!
#   4. 100% Manhattan / Perpendicular routing (41 arcs, zero diagonal segments)
#   5. Zero DRC violations / warnings in Electric's native ALGO_SWEEP engine
#   6. 100% LVS / NCC clean: exact topology, exports, and transistor sizing:
#        - Pull-Down Drivers (nmos@0, nmos@1): W = 7.0 lambda, L = 2.0 lambda
#        - Access Transistors (nmos@2, nmos@3): W = 4.0 lambda, L = 2.0 lambda
#        - Pull-Up Loads (pmos@0, pmos@1):     W = 3.0 lambda, L = 2.0 lambda
#   7. Substrate / Well Tap Grounding:
#        - P-well is grounded at the horizontal GND rail via tap_gnd (Metal-1-P-Well-Con).
#        - N-well is tied to VDD rail via tap_vdd (Metal-1-N-Well-Con).
# ==============================================================================

import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, Library
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

def make_manhattan_arc(arc_proto, ep, port1, port2):
    """Creates an arc between two ports and strictly verifies it is perpendicular."""
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    return ArcInst.makeInstance(arc_proto, ep, port1, port2)

def clear_cell_contents(cell):
    """Removes existing nodes, arcs, and exports from a cell to ensure a clean build."""
    eit = cell.getExports()
    exp_kill = []
    while eit.hasNext():
        exp_kill.append(eit.next())
    for e in exp_kill:
        e.kill()

    nit = cell.getNodes()
    to_kill = []
    while nit.hasNext():
        n = nit.next()
        if "Facet-Center" not in n.getProto().getName():
            to_kill.append(n)
    for n in to_kill:
        n.kill()

def build_shared_diffusion_6t_cell(lib, ep, mocmos):
    """Builds the ultra-compact 45x72 lambda shared-diffusion 6T SRAM cell layout view in mocmos."""
    print("\n" + "=" * 60)
    print("Building Shared-Diffusion 6T SRAM Cell (6T_cell{lay})...")
    print("=" * 60)

    cell = lib.findNodeProto("6T_cell{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "6T_cell{lay}")
    cell.setTechnology(mocmos)
    clear_cell_contents(cell)

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

    # Shared-Diffusion Coordinates with contact distance dx = 4.5 lambda:
    # Width = 2 * 22.5 = 45.0 lambda (4.05 um)
    # Height = 48.0 - (-24.0) = 72.0 lambda (6.48 um)
    # Area = 3,240 lambda^2 (26.24 um^2)
    x_drv = 6.5
    dx    = 4.5
    x_gnd = 0.0
    x_d0  = -x_drv           # -6.5 lambda (Left Pull-Down Driver)
    x_q   = x_d0 - dx        # -11.0 lambda (Shared Q Contact)
    x_a0  = x_q - dx         # -15.5 lambda (Left Access Transistor)
    x_bl  = x_a0 - dx        # -20.0 lambda (Bitline Contact)

    x_d1  = x_drv            # +6.5 lambda (Right Pull-Down Driver)
    x_qb  = x_d1 + dx        # +11.0 lambda (Shared QB Contact)
    x_a1  = x_qb + dx        # +15.5 lambda (Right Access Transistor)
    x_blb = x_a1 + dx        # +20.0 lambda (Bitline B Contact)

    x_edge = abs(x_bl) + 2.5 # 22.5 lambda (Cell Boundary)

    y_wl       = -24.0       # Horizontal Poly Wordline Rail
    y_gnd      = -14.0       # Horizontal Metal-1 Ground Rail
    y_nmos     = 0.0         # Continuous Shared NMOS Active Row
    y_via_bl   = 8.0         # Bitline Metal-1 to Metal-2 Via
    y_cross_q  = 13.0        # Node Q cross-coupling level
    y_cross_qb = 21.0        # Node QB cross-coupling level
    y_pmos     = 34.0        # Continuous Shared PMOS Active Row
    y_vdd      = 48.0        # Horizontal Metal-1 VDD Rail

    # 1. NMOS Row (Continuous Shared N-Active Diffusion)
    # Pull-down drivers: W=7.0, L=2.0; Access transistors: W=4.0, L=2.0
    nmos0 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_d0, y_nmos), 22.0, 15.0, cell, Orientation.R, "nmos@0")
    nmos0.setPrimitiveNodeSize(7.0, 2.0, ep)
    nmos1 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_d1, y_nmos), 22.0, 15.0, cell, Orientation.R, "nmos@1")
    nmos1.setPrimitiveNodeSize(7.0, 2.0, ep)

    nmos2 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_a0, y_nmos), 22.0, 15.0, cell, Orientation.R, "nmos@2")
    nmos2.setPrimitiveNodeSize(4.0, 2.0, ep)
    nmos3 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(x_a1, y_nmos), 22.0, 15.0, cell, Orientation.R, "nmos@3")
    nmos3.setPrimitiveNodeSize(4.0, 2.0, ep)

    # 2. NMOS Active Contacts (at exact minimum distance dx = 4.5 lambda)
    con_bit        = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_bl, y_nmos), 17.0, 17.0, cell, Orientation.IDENT, "con_bit")
    con_q_nmos     = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_q, y_nmos), 17.0, 17.0, cell, Orientation.IDENT, "con_q_nmos")
    con_gnd_shared = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_gnd, y_nmos), 17.0, 17.0, cell, Orientation.IDENT, "con_gnd_shared")
    con_qb_nmos    = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_qb, y_nmos), 17.0, 17.0, cell, Orientation.IDENT, "con_qb_nmos")
    con_bitb       = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(x_blb, y_nmos), 17.0, 17.0, cell, Orientation.IDENT, "con_bitb")

    # Connect continuous N-Active diffusion row across all 4 transistors
    make_manhattan_arc(n_act_wire, ep, con_bit.getOnlyPortInst(), nmos2.findPortInst("diff-top"))
    make_manhattan_arc(n_act_wire, ep, nmos2.findPortInst("diff-bottom"), con_q_nmos.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, con_q_nmos.getOnlyPortInst(), nmos0.findPortInst("diff-top"))

    a_gnd0 = make_manhattan_arc(n_act_wire, ep, nmos0.findPortInst("diff-bottom"), con_gnd_shared.getOnlyPortInst())
    a_gnd0.setLambdaBaseWidth(7.0)
    a_gnd1 = make_manhattan_arc(n_act_wire, ep, con_gnd_shared.getOnlyPortInst(), nmos1.findPortInst("diff-top"))
    a_gnd1.setLambdaBaseWidth(7.0)

    make_manhattan_arc(n_act_wire, ep, nmos1.findPortInst("diff-bottom"), con_qb_nmos.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, con_qb_nmos.getOnlyPortInst(), nmos3.findPortInst("diff-top"))
    make_manhattan_arc(n_act_wire, ep, nmos3.findPortInst("diff-bottom"), con_bitb.getOnlyPortInst())

    # 3. PMOS Row (Continuous Shared P-Active Diffusion)
    # Pull-up loads: W=3.0, L=2.0
    pmos0 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x_d0, y_pmos), 22.0, 15.0, cell, Orientation.R, "pmos@0")
    pmos0.setPrimitiveNodeSize(3.0, 2.0, ep)
    pmos1 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(x_d1, y_pmos), 22.0, 15.0, cell, Orientation.R, "pmos@1")
    pmos1.setPrimitiveNodeSize(3.0, 2.0, ep)

    con_q_pmos     = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_q, y_pmos), 17.0, 17.0, cell, Orientation.IDENT, "con_q_pmos")
    con_vdd_shared = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_gnd, y_pmos), 17.0, 17.0, cell, Orientation.IDENT, "con_vdd_shared")
    con_qb_pmos    = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(x_qb, y_pmos), 17.0, 17.0, cell, Orientation.IDENT, "con_qb_pmos")

    make_manhattan_arc(p_act_wire, ep, con_q_pmos.getOnlyPortInst(), pmos0.findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, pmos0.findPortInst("diff-bottom"), con_vdd_shared.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, con_vdd_shared.getOnlyPortInst(), pmos1.findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, pmos1.findPortInst("diff-bottom"), con_qb_pmos.getOnlyPortInst())

    # 4. Vertical Gate Columns (Gate 1 & Gate 2) and Inverter Cross-Coupling
    # Gate 1: Vertical poly line connecting pmos0 and nmos0 at x_d0 = -6.5 lambda
    pin_g1_mid = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x_d0, y_cross_qb), 2.0, 2.0, cell, Orientation.IDENT, "pin_g1_mid")
    make_manhattan_arc(poly_wire, ep, pmos0.findPortInst("poly-left"), pin_g1_mid.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, pin_g1_mid.getOnlyPortInst(), nmos0.findPortInst("poly-right"))

    con_gate1 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(0.0, y_cross_qb), 5.0, 5.0, cell, Orientation.IDENT, "con_gate1")
    make_manhattan_arc(poly_wire, ep, pin_g1_mid.getOnlyPortInst(), con_gate1.getOnlyPortInst())

    # Gate 2: Vertical poly line connecting pmos1 and nmos1 at x_d1 = +6.5 lambda
    pin_g2_mid = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(x_d1, y_cross_q), 2.0, 2.0, cell, Orientation.IDENT, "pin_g2_mid")
    make_manhattan_arc(poly_wire, ep, pmos1.findPortInst("poly-left"), pin_g2_mid.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, pin_g2_mid.getOnlyPortInst(), nmos1.findPortInst("poly-right"))

    con_gate2 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(0.0, y_cross_q), 5.0, 5.0, cell, Orientation.IDENT, "con_gate2")
    make_manhattan_arc(poly_wire, ep, con_gate2.getOnlyPortInst(), pin_g2_mid.getOnlyPortInst())

    # 5. Storage Node Q and Node QB Vertical Metal-1 Trunks
    # Trunk Q at X = x_q (-11.0 lambda)
    pin_q_cross = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_q, y_cross_q), 3.0, 3.0, cell, Orientation.IDENT, "pin_q_cross")
    make_manhattan_arc(m1_wire, ep, con_q_pmos.getOnlyPortInst(), pin_q_cross.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_q_cross.getOnlyPortInst(), con_q_nmos.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_q_cross.getOnlyPortInst(), con_gate2.getOnlyPortInst())

    # Trunk QB at X = x_qb (+11.0 lambda)
    pin_qb_cross = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_qb, y_cross_qb), 3.0, 3.0, cell, Orientation.IDENT, "pin_qb_cross")
    make_manhattan_arc(m1_wire, ep, con_qb_pmos.getOnlyPortInst(), pin_qb_cross.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_qb_cross.getOnlyPortInst(), con_qb_nmos.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_gate1.getOnlyPortInst(), pin_qb_cross.getOnlyPortInst())

    # 6. Access gates down to Metal-1-Polysilicon-1-Con contacts on Wordline
    # Poly lines extend down from access NMOS to poly-metal-1 contacts on the WL rail:
    con_wl_a0 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(x_a0, y_wl), 5.0, 5.0, cell, Orientation.IDENT, "con_wl_a0")
    make_manhattan_arc(poly_wire, ep, nmos2.findPortInst("poly-left"), con_wl_a0.getOnlyPortInst())

    con_wl_a1 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(x_a1, y_wl), 5.0, 5.0, cell, Orientation.IDENT, "con_wl_a1")
    make_manhattan_arc(poly_wire, ep, nmos3.findPortInst("poly-left"), con_wl_a1.getOnlyPortInst())

    # Wordline is a low-resistance horizontal METAL-1 Rail extending left and right:
    pin_wl_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-x_edge, y_wl), 3.0, 3.0, cell, Orientation.IDENT, "pin_wl_l")
    pin_wl_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_edge, y_wl), 3.0, 3.0, cell, Orientation.IDENT, "pin_wl_r")
    make_manhattan_arc(m1_wire, ep, pin_wl_l.getOnlyPortInst(), con_wl_a0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_wl_a0.getOnlyPortInst(), con_wl_a1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_wl_a1.getOnlyPortInst(), pin_wl_r.getOnlyPortInst())

    # 7. Horizontal GND Rail at y_gnd = -14.0 lambda with P-well tap
    pin_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-x_edge, y_gnd), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_l")
    tap_gnd   = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(0.0, y_gnd), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd")
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_edge, y_gnd), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")
    make_manhattan_arc(m1_wire, ep, pin_gnd_l.getOnlyPortInst(), tap_gnd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_gnd.getOnlyPortInst(), pin_gnd_r.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_gnd_shared.getOnlyPortInst(), tap_gnd.getOnlyPortInst())

    # 8. Horizontal VDD Rail at y_vdd = +48.0 lambda with N-well tap
    pin_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-x_edge, y_vdd), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_l")
    tap_vdd   = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(0.0, y_vdd), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd")
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x_edge, y_vdd), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")
    make_manhattan_arc(m1_wire, ep, pin_vdd_l.getOnlyPortInst(), tap_vdd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_vdd.getOnlyPortInst(), pin_vdd_r.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_vdd_shared.getOnlyPortInst(), tap_vdd.getOnlyPortInst())

    # 9. Bitlines (Vertical Metal-2 Rails at x_bl and x_blb)
    via_bit = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x_bl, y_via_bl), 5.0, 5.0, cell, Orientation.IDENT, "via_bit")
    make_manhattan_arc(m1_wire, ep, con_bit.getOnlyPortInst(), via_bit.getOnlyPortInst())
    pin_bit_b = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(x_bl, y_wl), 3.0, 3.0, cell, Orientation.IDENT, "pin_bit_b")
    pin_bit_t = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(x_bl, y_vdd), 3.0, 3.0, cell, Orientation.IDENT, "pin_bit_t")
    make_manhattan_arc(m2_wire, ep, pin_bit_b.getOnlyPortInst(), via_bit.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_bit.getOnlyPortInst(), pin_bit_t.getOnlyPortInst())

    via_bitb = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(x_blb, y_via_bl), 5.0, 5.0, cell, Orientation.IDENT, "via_bitb")
    make_manhattan_arc(m1_wire, ep, con_bitb.getOnlyPortInst(), via_bitb.getOnlyPortInst())
    pin_bitb_b = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(x_blb, y_wl), 3.0, 3.0, cell, Orientation.IDENT, "pin_bitb_b")
    pin_bitb_t = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(x_blb, y_vdd), 3.0, 3.0, cell, Orientation.IDENT, "pin_bitb_t")
    make_manhattan_arc(m2_wire, ep, pin_bitb_b.getOnlyPortInst(), via_bitb.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_bitb.getOnlyPortInst(), pin_bitb_t.getOnlyPortInst())

    # 10. Well Enclosures
    w_width = 2.0 * x_edge
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(0.0, (y_vdd + y_pmos) / 2.0), w_width, (y_vdd - y_pmos) + 16.0, cell, Orientation.IDENT, "nwell@0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(0.0, (y_nmos + y_gnd) / 2.0), w_width, (y_nmos - y_gnd) + 16.0, cell, Orientation.IDENT, "pwell@0")

    # 11. Top-Level Exports matching 6T_cell{sch}
    Export.newInst(cell, pin_vdd_l.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, pin_gnd_l.getOnlyPortInst(), "GND", PortCharacteristic.GND)
    Export.newInst(cell, pin_wl_l.getOnlyPortInst(), "WL", PortCharacteristic.IN)
    Export.newInst(cell, pin_bit_t.getOnlyPortInst(), "BIT", PortCharacteristic.OUT)
    Export.newInst(cell, pin_bitb_t.getOnlyPortInst(), "BITB", PortCharacteristic.BIDIR)

    width = 2.0 * x_edge
    height = y_vdd - y_wl
    area = width * height
    print("Constructed Shared-Diffusion 6T Cell: Width=%.1f lambda (%.2f um), Height=%.1f lambda (%.2f um), Area=%.0f lambda^2 (%.2f um^2)" % (
        width, width * 0.09, height, height * 0.09, area, area * 0.09 * 0.09))
    return cell

def verify_cell(lib):
    """Executes full Manhattan perpendicularity, LVS/NCC, and DRC verification."""
    print("\n" + "=" * 60)
    print("Verifying Shared-Diffusion Cell: 6T_cell")
    print("=" * 60)

    sch_cell = lib.findNodeProto("6T_cell{sch}")
    lay_cell = lib.findNodeProto("6T_cell{lay}")

    if sch_cell is None or lay_cell is None:
        raise Exception("Failed to find schematic or layout views!")

    # 1. Manhattan Routing Check
    ait = lay_cell.getArcs()
    non_m = 0
    total_arcs = 0
    while ait.hasNext():
        a = ait.next()
        total_arcs += 1
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        if abs(p1.getX() - p2.getX()) > 0.001 and abs(p1.getY() - p2.getY()) > 0.001:
            print("Non-manhattan arc:", a.getName(), "(%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
            non_m += 1

    if non_m > 0:
        raise Exception("Manhattan Check Failed: %d non-perpendicular arcs found!" % non_m)
    print("1. Manhattan Routing Check: PASS (%d arcs, 100%% perpendicular)" % total_arcs)

    # 2. LVS / NCC Check
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch_cell, None, lay_cell, None, opts)
    if not res.match():
        raise Exception("NCC / LVS Check Failed: match=%s" % res.match())
    print("2. NCC / LVS Check: PASS (match=%s)" % res.match())

    # 3. Quick DRC Check (ALGO_SWEEP)
    m_chk = None
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m_chk = m
            m_chk.setAccessible(True)
            break

    logger = ErrorLogger()
    prefs = DRC.DRCPreferences(False)
    mode = GeometryHandler.GHMode.ALGO_SWEEP
    m_chk.invoke(None, [logger, lay_cell, None, None, None, None, prefs, mode, False])

    n_err = logger.getNumErrors()
    n_warn = logger.getNumWarnings()
    if n_err > 0 or n_warn > 0:
        lit = logger.getLogs()
        while lit.hasNext():
            print("DRC LOG:", lit.next().getMessageString())
        raise Exception("Quick DRC Check Failed: %d errors, %d warnings found!" % (n_err, n_warn))
    print("3. Quick DRC Check: PASS (0 errors, 0 warnings)")

def main():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    print("Opening library: " + jelib_path)

    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    mocmos = Technology.findTechnology("mocmos")
    if mocmos is None:
        raise Exception("Technology 'mocmos' not found!")

    # Enforce MOSIS CMOS scale to lambda = 90 nm (TSMC 0.18 um)
    edb = lib.getDatabase()
    batch = Setting.SettingChangeBatch()
    batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
    edb.implementSettingChanges(batch)
    print("Enforced Technology 'mocmos' scale to: %.1f nm" % mocmos.getScale())

    # Build Layout
    build_shared_diffusion_6t_cell(lib, ep, mocmos)

    # Verify Cell
    verify_cell(lib)

    # Save to disk
    print("\n" + "=" * 60)
    print("Saving updated library to disk: " + jelib_path)
    print("=" * 60)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library saved successfully with Shared-Diffusion 6T_cell{lay}!")

if __name__ == "__main__":
    main()
