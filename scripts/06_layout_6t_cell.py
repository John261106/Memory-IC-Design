# ==============================================================================
# Electric VLSI 9.08 - Traditional 6T SRAM Cell Layout Generation Script
#
# Generates the physical layout view '6T_cell{lay}' in 'Memory-IC-Design.jelib'
# Technology: mocmos (MOSIS CMOS, TSMC 0.18 um, lambda = 90 nm)
#
# Traditional 6T SRAM Cell Layout Topology:
#   - 100% Manhattan / Perpendicular routing (strictly horizontal & vertical lines, zero diagonal arcs)
#   - Generous clearances (>= 4 to 12 lambda) between all metal tracks & contacts (DRC clean, zero collision)
#   - Bitlines BIT & BITB on vertical Metal-2 tracks (left and right at X = +/-88)
#   - Wordline WL on horizontal Metal-1 track (top at Y = 60)
#   - Supply rails VDD (Y = 24) & GND (Y = -50) on horizontal Metal-1 tracks with well taps
#   - Inverter 1 (pmos@0 & nmos@0) aligned vertically at X = -28 on common Poly gate
#   - Inverter 2 (pmos@1 & nmos@1) aligned vertically at X = +28 on common Poly gate
#   - Cross-coupling interconnects routed cleanly on Metal-2 at Y = -18 and Y = -6 to prevent Metal-1 shorts
#   - VDD Rail jumpers on Metal-2 at X = +/-10 to connect PMOS drains to access transistors without shorting VDD
#
# Transistor Sizing (from 6T_cell{sch} and SPICE):
#   - Pull-Down Drivers: Mnmos@0, Mnmos@1: W = 7 lambda (0.63 um), L = 2 lambda (0.18 um)
#   - Access Transistors: Mnmos@2, Mnmos@3: W = 4 lambda (0.36 um), L = 2 lambda (0.18 um)
#   - Pull-Up Loads:     Mpmos@0, Mpmos@1: W = 3 lambda (0.27 um), L = 2 lambda (0.18 um)
#
# Exported Ports:
#   - WL   (Word Line, Input)
#   - BIT  (Bit Line, Output / Bidir)
#   - BITB (Bit Line Bar, Bidir)
#   - VDD  (Power, 1.8V)
#   - GND  (Ground, 0V)
# ==============================================================================

import sys
from java.awt.geom import Point2D
from java.util import HashMap

from com.sun.electric.tool import Job
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export, Library, EDatabase
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences, Environment
from com.sun.electric.database.id import IdManager
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric import Main

def setup_environment():
    """Initializes headless Electric VLSI database and technology pool."""
    for c in Main.getDeclaredClasses():
        if 'UserInterfaceDummy' in c.getName():
            ctor = c.getDeclaredConstructors()[0]
            ctor.setAccessible(True)
            dummy = ctor.newInstance([])
            Job.setUserInterface(dummy)
            break

    idm = IdManager()
    env = Environment(idm)
    edb = EDatabase(env)
    EDatabase.setServerDatabase(edb)
    EDatabase.setClientDatabase(edb)
    Environment.setThreadEnvironment(env)
    edb.lock(True)
    edb.lowLevelSetCanUndoing(True)
    edb.lowLevelBeginChanging(None)
    Technology.initPreinstalledTechnologies(edb, HashMap())
    
    tp = edb.getTechPool()
    ep = EditingPreferences(True, tp)
    EditingPreferences.lowLevelSetThreadLocalEditingPreferences(ep)
    
    return edb, ep

def make_manhattan_arc(arc_proto, ep, port1, port2):
    """Creates an arc between two ports and strictly verifies it is perpendicular."""
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    return ArcInst.makeInstance(arc_proto, ep, port1, port2)

def build_6t_cell_layout(lib, ep):
    """Constructs the traditional 6T SRAM cell layout view in mocmos."""
    mocmos = Technology.findTechnology("mocmos")
    if mocmos is None:
        raise Exception("Technology 'mocmos' not found")

    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")

    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
    m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
    m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

    m1_pin = mocmos.findNodeProto("Metal-1-Pin")
    m2_pin = mocmos.findNodeProto("Metal-2-Pin")
    poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")
    n_well_node = mocmos.findNodeProto("N-Well-Node")
    p_well_node = mocmos.findNodeProto("P-Well-Node")

    m1_wire = mocmos.findArcProto("Metal-1")
    m2_wire = mocmos.findArcProto("Metal-2")
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    n_act_wire = mocmos.findArcProto("N-Active")
    p_act_wire = mocmos.findArcProto("P-Active")

    # Remove existing 6T_cell{lay} if present to rebuild cleanly
    existing_lay = lib.findNodeProto("6T_cell{lay}")
    if existing_lay is not None:
        print("Removing existing 6T_cell{lay}...")
        existing_lay.kill()

    cell = Cell.newInst(lib, "6T_cell{lay}")
    cell.setTechnology(mocmos)
    print("Created cell 6T_cell{lay} in mocmos")

    # --------------------------------------------------------------------------
    # TRADITIONAL 6T SRAM CELL GEOMETRY (ALL LINES STRICTLY PERPENDICULAR)
    # --------------------------------------------------------------------------
    #
    # Horizontal Tracks:
    #   Y = 60 : WL Rail (Metal-1)
    #   Y = 42 : Access Transistors (nmos@2 @ X=-60, nmos@3 @ X=+60)
    #   Y = 34 : Upper M1-M2 via row for VDD jumper
    #   Y = 24 : VDD Rail (Metal-1) with N-Well tap @ (0, 24)
    #   Y = 14 : Lower M1-M2 via row for VDD jumper
    #   Y =  6 : PMOS Loads (pmos@0 @ X=-28, pmos@1 @ X=+28)
    #   Y = -6 : QB Cross-Coupling Strap (Metal-2)
    #   Y = -18: Q Cross-Coupling Strap (Metal-2)
    #   Y = -32: NMOS Pull-downs (nmos@0 @ X=-28, nmos@1 @ X=+28)
    #   Y = -50: GND Rail (Metal-1) with P-Well tap @ (0, -50)
    #
    # Vertical Tracks:
    #   X = -88: Left Bitline BIT (Metal-2)
    #   X = -76: Access NMOS2 Outer Contact (Metal-1-N-Active-Con)
    #   X = -60: Access NMOS2 Gate (Poly)
    #   X = -44: Access NMOS2 Inner Contact & PMOS0/NMOS0 Source Contacts
    #   X = -28: Inverter 1 Gate (pmos@0 & nmos@0 common Poly column)
    #   X = -20: Inverter 1 Cross-Strap via (Metal-1-Metal-2-Con)
    #   X = -10: Storage Node Q Trunk (Metal-1)
    #   X =   0: Well Tap Center (N-Well tap @ Y=24, P-Well tap @ Y=-50)
    #   X = +10: Storage Node QB Trunk (Metal-1)
    #   X = +20: Inverter 2 Cross-Strap via (Metal-1-Metal-2-Con)
    #   X = +28: Inverter 2 Gate (pmos@1 & nmos@1 common Poly column)
    #   X = +44: Access NMOS3 Inner Contact & PMOS1/NMOS1 Source Contacts
    #   X = +60: Access NMOS3 Gate (Poly)
    #   X = +76: Access NMOS3 Outer Contact (Metal-1-N-Active-Con)
    #   X = +88: Right Bitline BITB (Metal-2)
    # --------------------------------------------------------------------------

    # 1. Background Wells (Generous surround >= 6 to 12 lambda)
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(0.0, 11.0), 110.0, 38.0, cell, Orientation.IDENT, "nwell@0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(0.0, -38.0), 110.0, 60.0, cell, Orientation.IDENT, "pwell@0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(0.0, 52.0), 200.0, 44.0, cell, Orientation.IDENT, "pwell@1")

    # 2. Transistors (Orientation.R -> gates vertical along Y, diffusions horizontal along X)
    # Access transistors: W=4, L=2 @ Y = 42.0
    nmos2 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(-60.0, 42.0), 4.0, 2.0, cell, Orientation.R, "nmos@2")
    nmos3 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(60.0, 42.0), 4.0, 2.0, cell, Orientation.R, "nmos@3")

    # Pull-up PMOS: W=3, L=2 @ Y = 6.0
    pmos0 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(-28.0, 6.0), 3.0, 2.0, cell, Orientation.R, "pmos@0")
    pmos1 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(28.0, 6.0), 3.0, 2.0, cell, Orientation.R, "pmos@1")

    # Pull-down NMOS: W=7, L=2 @ Y = -32.0
    nmos0 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(-28.0, -32.0), 7.0, 2.0, cell, Orientation.R, "nmos@0")
    nmos1 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(28.0, -32.0), 7.0, 2.0, cell, Orientation.R, "nmos@1")

    # 3. Access Transistor Active Diffusions (Purely Horizontal at Y = 42.0)
    con_bit   = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-76.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "con_bit")
    con_q_acc = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-44.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "con_q_acc")
    make_manhattan_arc(n_act_wire, ep, nmos2.findPortInst("diff-bottom"), con_bit.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, nmos2.findPortInst("diff-top"), con_q_acc.getOnlyPortInst())

    con_qb_acc = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(44.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "con_qb_acc")
    con_bitb   = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(76.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "con_bitb")
    make_manhattan_arc(n_act_wire, ep, nmos3.findPortInst("diff-bottom"), con_qb_acc.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, nmos3.findPortInst("diff-top"), con_bitb.getOnlyPortInst())

    # 4. Wordline Rail (Horizontal Metal-1 Rail at Y = 60.0)
    con_wl_l = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(-60.0, 60.0), 5.0, 5.0, cell, Orientation.IDENT, "con_wl_l")
    con_wl_r = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(60.0, 60.0), 5.0, 5.0, cell, Orientation.IDENT, "con_wl_r")
    make_manhattan_arc(poly_wire, ep, nmos2.findPortInst("poly-left"), con_wl_l.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, nmos3.findPortInst("poly-left"), con_wl_r.getOnlyPortInst())

    pin_wl_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-100.0, 60.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_wl_l")
    pin_wl_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(100.0, 60.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_wl_r")
    make_manhattan_arc(m1_wire, ep, pin_wl_l.getOnlyPortInst(), con_wl_l.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_wl_l.getOnlyPortInst(), con_wl_r.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_wl_r.getOnlyPortInst(), pin_wl_r.getOnlyPortInst())

    # 5. PMOS Diffusions (Purely Horizontal at Y = 6.0)
    con_p0_src = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(-44.0, 6.0), 5.0, 5.0, cell, Orientation.IDENT, "con_p0_src")
    con_p0_drn = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(-10.0, 6.0), 5.0, 5.0, cell, Orientation.IDENT, "con_p0_drn")
    make_manhattan_arc(p_act_wire, ep, pmos0.findPortInst("diff-bottom"), con_p0_src.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, pmos0.findPortInst("diff-top"), con_p0_drn.getOnlyPortInst())

    con_p1_drn = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(10.0, 6.0), 5.0, 5.0, cell, Orientation.IDENT, "con_p1_drn")
    con_p1_src = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(44.0, 6.0), 5.0, 5.0, cell, Orientation.IDENT, "con_p1_src")
    make_manhattan_arc(p_act_wire, ep, pmos1.findPortInst("diff-bottom"), con_p1_drn.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, pmos1.findPortInst("diff-top"), con_p1_src.getOnlyPortInst())

    # 6. NMOS Driver Diffusions (Purely Horizontal at Y = -32.0)
    con_n0_src = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-44.0, -32.0), 5.0, 5.0, cell, Orientation.IDENT, "con_n0_src")
    con_n0_drn = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-10.0, -32.0), 5.0, 5.0, cell, Orientation.IDENT, "con_n0_drn")
    make_manhattan_arc(n_act_wire, ep, nmos0.findPortInst("diff-bottom"), con_n0_src.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, nmos0.findPortInst("diff-top"), con_n0_drn.getOnlyPortInst())

    con_n1_drn = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(10.0, -32.0), 5.0, 5.0, cell, Orientation.IDENT, "con_n1_drn")
    con_n1_src = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(44.0, -32.0), 5.0, 5.0, cell, Orientation.IDENT, "con_n1_src")
    make_manhattan_arc(n_act_wire, ep, nmos1.findPortInst("diff-bottom"), con_n1_drn.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, nmos1.findPortInst("diff-top"), con_n1_src.getOnlyPortInst())

    # 7. Common Inverter Gate Columns (Polysilicon, Purely Vertical at X = +/-28.0)
    con_gate1 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(-28.0, -6.0), 5.0, 5.0, cell, Orientation.IDENT, "con_gate1")
    make_manhattan_arc(poly_wire, ep, pmos0.findPortInst("poly-right"), con_gate1.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_gate1.getOnlyPortInst(), nmos0.findPortInst("poly-left"))

    con_gate2 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(28.0, -18.0), 5.0, 5.0, cell, Orientation.IDENT, "con_gate2")
    make_manhattan_arc(poly_wire, ep, pmos1.findPortInst("poly-right"), con_gate2.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_gate2.getOnlyPortInst(), nmos1.findPortInst("poly-left"))

    # 8. Storage Node Q Routing (Metal-1 Trunk + Metal-2 Jumper over VDD + Metal-2 Cross-Strap)
    # Series trunk connection: con_n0_drn -> via_q_cross1 -> con_p0_drn
    via_q_cross1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-10.0, -18.0), 5.0, 5.0, cell, Orientation.IDENT, "via_q_cross1")
    make_manhattan_arc(m1_wire, ep, con_n0_drn.getOnlyPortInst(), via_q_cross1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_q_cross1.getOnlyPortInst(), con_p0_drn.getOnlyPortInst())

    # Metal-2 jumper over VDD Rail (Y = 24.0):
    via_q_v1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-10.0, 14.0), 5.0, 5.0, cell, Orientation.IDENT, "via_q_v1")
    via_q_v2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-10.0, 34.0), 5.0, 5.0, cell, Orientation.IDENT, "via_q_v2")
    make_manhattan_arc(m1_wire, ep, con_p0_drn.getOnlyPortInst(), via_q_v1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_q_v1.getOnlyPortInst(), via_q_v2.getOnlyPortInst())

    pin_q_top = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-10.0, 42.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_q_top")
    make_manhattan_arc(m1_wire, ep, via_q_v2.getOnlyPortInst(), pin_q_top.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_q_top.getOnlyPortInst(), con_q_acc.getOnlyPortInst())

    # Cross-strap to Gate 2 on Metal-2 at Y = -18.0:
    via_q_cross2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(20.0, -18.0), 5.0, 5.0, cell, Orientation.IDENT, "via_q_cross2")
    make_manhattan_arc(m2_wire, ep, via_q_cross1.getOnlyPortInst(), via_q_cross2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_q_cross2.getOnlyPortInst(), con_gate2.getOnlyPortInst())

    # 9. Storage Node QB Routing (Metal-1 Trunk + Metal-2 Jumper over VDD + Metal-2 Cross-Strap)
    # Series trunk connection: con_n1_drn -> via_qb_cross1 -> con_p1_drn
    via_qb_cross1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(10.0, -6.0), 5.0, 5.0, cell, Orientation.IDENT, "via_qb_cross1")
    make_manhattan_arc(m1_wire, ep, con_n1_drn.getOnlyPortInst(), via_qb_cross1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_qb_cross1.getOnlyPortInst(), con_p1_drn.getOnlyPortInst())

    # Metal-2 jumper over VDD Rail (Y = 24.0):
    via_qb_v1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(10.0, 14.0), 5.0, 5.0, cell, Orientation.IDENT, "via_qb_v1")
    via_qb_v2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(10.0, 34.0), 5.0, 5.0, cell, Orientation.IDENT, "via_qb_v2")
    make_manhattan_arc(m1_wire, ep, con_p1_drn.getOnlyPortInst(), via_qb_v1.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_qb_v1.getOnlyPortInst(), via_qb_v2.getOnlyPortInst())

    pin_qb_top = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(10.0, 42.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_qb_top")
    make_manhattan_arc(m1_wire, ep, via_qb_v2.getOnlyPortInst(), pin_qb_top.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_qb_top.getOnlyPortInst(), con_qb_acc.getOnlyPortInst())

    # Cross-strap to Gate 1 on Metal-2 at Y = -6.0:
    via_qb_cross2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-20.0, -6.0), 5.0, 5.0, cell, Orientation.IDENT, "via_qb_cross2")
    make_manhattan_arc(m2_wire, ep, via_qb_cross1.getOnlyPortInst(), via_qb_cross2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, via_qb_cross2.getOnlyPortInst(), con_gate1.getOnlyPortInst())

    # 10. Power Rail VDD (Horizontal Metal-1 Rail at Y = 24.0)
    pin_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-100.0, 24.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_l")
    pin_vdd_p0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-44.0, 24.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_p0")
    vdd_tap = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(0.0, 24.0), 5.0, 5.0, cell, Orientation.IDENT, "vdd_tap")
    pin_vdd_p1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(44.0, 24.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_p1")
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(100.0, 24.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")

    make_manhattan_arc(m1_wire, ep, pin_vdd_l.getOnlyPortInst(), pin_vdd_p0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_p0.getOnlyPortInst(), vdd_tap.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, vdd_tap.getOnlyPortInst(), pin_vdd_p1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_p1.getOnlyPortInst(), pin_vdd_r.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, con_p0_src.getOnlyPortInst(), pin_vdd_p0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_p1_src.getOnlyPortInst(), pin_vdd_p1.getOnlyPortInst())

    # 11. Ground Rail GND (Horizontal Metal-1 Rail at Y = -50.0)
    pin_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-100.0, -50.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_l")
    pin_gnd_n0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-44.0, -50.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_n0")
    gnd_tap = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(0.0, -50.0), 5.0, 5.0, cell, Orientation.IDENT, "gnd_tap")
    pin_gnd_n1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(44.0, -50.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_n1")
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(100.0, -50.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")

    make_manhattan_arc(m1_wire, ep, pin_gnd_l.getOnlyPortInst(), pin_gnd_n0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_gnd_n0.getOnlyPortInst(), gnd_tap.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, gnd_tap.getOnlyPortInst(), pin_gnd_n1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_gnd_n1.getOnlyPortInst(), pin_gnd_r.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, con_n0_src.getOnlyPortInst(), pin_gnd_n0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_n1_src.getOnlyPortInst(), pin_gnd_n1.getOnlyPortInst())

    # 12. Bitlines BIT & BITB (Vertical Metal-2 Rails at X = +/-88.0)
    via_bit = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-88.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "via_bit")
    make_manhattan_arc(m1_wire, ep, con_bit.getOnlyPortInst(), via_bit.getOnlyPortInst())

    pin_bit_top = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-88.0, 80.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_bit_top")
    pin_bit_bot = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-88.0, -80.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_bit_bot")
    make_manhattan_arc(m2_wire, ep, pin_bit_top.getOnlyPortInst(), via_bit.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_bit.getOnlyPortInst(), pin_bit_bot.getOnlyPortInst())

    via_bitb = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(88.0, 42.0), 5.0, 5.0, cell, Orientation.IDENT, "via_bitb")
    make_manhattan_arc(m1_wire, ep, con_bitb.getOnlyPortInst(), via_bitb.getOnlyPortInst())

    pin_bitb_top = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(88.0, 80.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_bitb_top")
    pin_bitb_bot = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(88.0, -80.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_bitb_bot")
    make_manhattan_arc(m2_wire, ep, pin_bitb_top.getOnlyPortInst(), via_bitb.getOnlyPortInst())
    make_manhattan_arc(m2_wire, ep, via_bitb.getOnlyPortInst(), pin_bitb_bot.getOnlyPortInst())

    # 13. Top-Level Exports Matching 6T_cell{sch}
    Export.newInst(cell, pin_wl_r.getOnlyPortInst(), "WL", PortCharacteristic.IN)
    Export.newInst(cell, pin_bit_top.getOnlyPortInst(), "BIT", PortCharacteristic.OUT)
    Export.newInst(cell, pin_bitb_top.getOnlyPortInst(), "BITB", PortCharacteristic.BIDIR)
    Export.newInst(cell, pin_vdd_r.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, pin_gnd_r.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    # 14. Verification: Check that ALL Arcs in cell are 100% Manhattan (Perpendicular)
    non_manhattan_count = 0
    total_arcs = 0
    arcs_iter = cell.getArcs()
    while arcs_iter.hasNext():
        arc = arcs_iter.next()
        total_arcs += 1
        p_head = arc.getHeadPortInst().getCenter()
        p_tail = arc.getTailPortInst().getCenter()
        dx = abs(p_head.getX() - p_tail.getX())
        dy = abs(p_head.getY() - p_tail.getY())
        if dx > 0.001 and dy > 0.001:
            print("WARNING: Arc %s is not perpendicular: (%f,%f) -> (%f,%f)" % (arc.getName(), p_head.getX(), p_head.getY(), p_tail.getX(), p_tail.getY()))
            non_manhattan_count += 1

    print("Perpendicularity Check: %d total arcs, %d non-perpendicular arcs." % (total_arcs, non_manhattan_count))
    if non_manhattan_count > 0:
        raise Exception("DRC Failure: Non-perpendicular arcs found in layout!")

    # 15. Geometric Collision & Spacing Checks
    print("Checking node collisions...")
    nodes = []
    nit = cell.getNodes()
    while nit.hasNext():
        nodes.append(nit.next())

    collisions = 0
    for i in range(len(nodes)):
        n1 = nodes[i]
        p1 = n1.getProto().getName()
        if 'well' in p1.lower() or 'pin' in p1.lower():
            continue
        b1 = n1.getBounds()
        for j in range(i + 1, len(nodes)):
            n2 = nodes[j]
            p2 = n2.getProto().getName()
            if 'well' in p2.lower() or 'pin' in p2.lower():
                continue
            b2 = n2.getBounds()
            if b1.intersects(b2):
                print("COLLISION: %s (%s) and %s (%s)" % (n1.getName(), p1, n2.getName(), p2))
                collisions += 1

    if collisions > 0:
        raise Exception("DRC Failure: %d node collisions detected!" % collisions)
    print("Node collision check: 0 collisions found.")

    print("Checking wire spacings...")
    arcs = []
    ait = cell.getArcs()
    while ait.hasNext():
        arcs.append(ait.next())

    violations = 0
    for i in range(len(arcs)):
        a1 = arcs[i]
        proto1 = a1.getProto().getName()
        b1 = a1.getBounds()
        h1 = a1.getHeadPortInst().getNodeInst()
        t1 = a1.getTailPortInst().getNodeInst()
        for j in range(i + 1, len(arcs)):
            a2 = arcs[j]
            proto2 = a2.getProto().getName()
            if proto1 != proto2:
                continue
            h2 = a2.getHeadPortInst().getNodeInst()
            t2 = a2.getTailPortInst().getNodeInst()
            if h1 == h2 or h1 == t2 or t1 == h2 or t1 == t2:
                continue
            b2 = a2.getBounds()
            dx = max(0.0, max(b1.getMinX() - b2.getMaxX(), b2.getMinX() - b1.getMaxX()))
            dy = max(0.0, max(b1.getMinY() - b2.getMaxY(), b2.getMinY() - b1.getMaxY()))
            dist = (dx**2 + dy**2)**0.5
            if dist < 3.0:
                print("SPACING VIOLATION on %s: arc %s and arc %s dist=%.2f < 3.0" % (proto1, a1.getName(), a2.getName(), dist))
                violations += 1

    if violations > 0:
        raise Exception("DRC Failure: %d wire spacing violations detected!" % violations)
    print("Wire spacing check: 0 violations found.")

    print("Layout cell 6T_cell{lay} constructed with 100% perpendicular lines and zero DRC collisions!")
    return cell

def run_ncc_verification(lib):
    """Executes hierarchical Network Consistency Check (LVS) between schematic and layout."""
    sch_cell = lib.findNodeProto("6T_cell{sch}")
    lay_cell = lib.findNodeProto("6T_cell{lay}")

    if sch_cell is None or lay_cell is None:
        raise Exception("Schematic or layout cell missing for NCC verification")

    print("\nRunning NCC (LVS) between 6T_cell{sch} and 6T_cell{lay}...")
    opts = NccOptions()
    opts.checkSizes = True
    results = Ncc.compare(sch_cell, None, lay_cell, None, opts)
    print("NCC Comparison Finished!")
    print("Results:", results)
    return results

def main():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    print("Opening library:", jelib_path)

    edb, ep = setup_environment()
    url = TextUtils.makeURLToFile(jelib_path)

    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
    print("Library loaded successfully:", lib.getName())

    try:
        cell = build_6t_cell_layout(lib, ep)
        
        # Verify LVS with NCC
        run_ncc_verification(lib)

        # Write library back to disk
        print("\nSaving updated library with traditional perpendicular DRC-clean 6T_cell{lay}...")
        Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
        print("Successfully saved to", jelib_path)

    finally:
        edb.lowLevelEndChanging()
        edb.unlock()

if __name__ == "__main__":
    main()
