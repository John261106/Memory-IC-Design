# ==============================================================================
# Electric VLSI 9.08 - Standard Cell Layout Generator for Not and Nand
#
# Generates compact physical layout views:
#   1. Not{lay}   - Standard CMOS Inverter (PMOS W=8, NMOS W=4, L=2)
#   2. Nand{lay}  - 4-Input Static CMOS NAND Gate (PMOS 4x W=4, NMOS 4x W=4, L=2)
#
# Technology: mocmos (MOSIS CMOS, TSMC 0.18 um, lambda = 90 nm)
#
# Layout Features:
#   - 100% Perpendicular (Manhattan) routing (strictly horizontal & vertical lines)
#   - Aligned standard cell height with VDD rail at Y = +38 and GND rail at Y = -38
#   - Continuous active diffusion sharing on series NMOS stack and parallel PMOS fingers
#   - Built-in well tap substrate contacts on VDD (N-well) and GND (P-well)
#   - 0 DRC errors and 0 DRC warnings verified by Electric's built-in Quick DRC engine
#   - 100% LVS / NCC clean: verified for exact topology, export names, and transistor sizing
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
from com.sun.electric.tool.drc import DRC, Quick

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
    # Kill exports
    eit = cell.getExports()
    exp_kill = []
    while eit.hasNext():
        exp_kill.append(eit.next())
    for e in exp_kill:
        e.kill()

    # Kill nodes (except Facet-Center if present)
    nit = cell.getNodes()
    to_kill = []
    while nit.hasNext():
        n = nit.next()
        if "Facet-Center" not in n.getProto().getName():
            to_kill.append(n)
    for n in to_kill:
        n.kill()

def build_not_layout(lib, ep, mocmos):
    """Builds the compact CMOS inverter Not{lay}."""
    print("\n" + "=" * 60)
    print("Building Not{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("Not{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "Not{lay}")
    cell.setTechnology(mocmos)
    clear_cell_contents(cell)

    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")

    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
    m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

    m1_pin = mocmos.findNodeProto("Metal-1-Pin")
    n_well_node = mocmos.findNodeProto("N-Well-Node")
    p_well_node = mocmos.findNodeProto("P-Well-Node")

    m1_wire = mocmos.findArcProto("Metal-1")
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    n_act_wire = mocmos.findArcProto("N-Active")
    p_act_wire = mocmos.findArcProto("P-Active")

    Y_P = 22.0
    Y_N = -20.0
    Y_VDD = 38.0
    Y_GND = -38.0
    X_CON = 16.0

    # PMOS W=8, L=2 @ Y=+22; NMOS W=4, L=2 @ Y=-20
    pmos0 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(0.0, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@0")
    pmos0.setPrimitiveNodeSize(8.0, 2.0, ep)

    nmos0 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(0.0, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@0")
    nmos0.setPrimitiveNodeSize(4.0, 2.0, ep)

    # PMOS active diffusion contacts
    con_p_vdd = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(-X_CON, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_vdd")
    con_p_out = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X_CON, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_out")
    make_manhattan_arc(p_act_wire, ep, con_p_vdd.getOnlyPortInst(), pmos0.findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, pmos0.findPortInst("diff-bottom"), con_p_out.getOnlyPortInst())

    # NMOS active diffusion contacts
    con_n_gnd = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-X_CON, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "con_n_gnd")
    con_n_out = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(X_CON, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "con_n_out")
    make_manhattan_arc(n_act_wire, ep, con_n_gnd.getOnlyPortInst(), nmos0.findPortInst("diff-top"))
    make_manhattan_arc(n_act_wire, ep, nmos0.findPortInst("diff-bottom"), con_n_out.getOnlyPortInst())

    # Shared gate column and input contact IN @ (0, 0)
    con_in = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(0.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_in")
    make_manhattan_arc(poly_wire, ep, pmos0.findPortInst("poly-left"), con_in.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, con_in.getOnlyPortInst(), nmos0.findPortInst("poly-right"))

    # Shared drain output M1 trunk
    pin_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_CON, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_out")
    make_manhattan_arc(m1_wire, ep, con_p_out.getOnlyPortInst(), pin_out.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_out.getOnlyPortInst(), con_n_out.getOnlyPortInst())

    # Horizontal VDD Rail at Y = +38
    pin_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-28.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_l")
    pin_vdd_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-X_CON, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_m")
    tap_vdd   = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(0.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd")
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(28.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")

    make_manhattan_arc(m1_wire, ep, pin_vdd_l.getOnlyPortInst(), pin_vdd_m.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_m.getOnlyPortInst(), tap_vdd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_vdd.getOnlyPortInst(), pin_vdd_r.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_p_vdd.getOnlyPortInst(), pin_vdd_m.getOnlyPortInst())

    # Horizontal GND Rail at Y = -38
    pin_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-28.0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_l")
    pin_gnd_m = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-X_CON, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_m")
    tap_gnd   = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(0.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd")
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(28.0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")

    make_manhattan_arc(m1_wire, ep, pin_gnd_l.getOnlyPortInst(), pin_gnd_m.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_gnd_m.getOnlyPortInst(), tap_gnd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_gnd.getOnlyPortInst(), pin_gnd_r.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_n_gnd.getOnlyPortInst(), pin_gnd_m.getOnlyPortInst())

    # Well nodes
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(0.0, 30.0), 56.0, 30.0, cell, Orientation.IDENT, "nwell@0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(0.0, -29.0), 56.0, 30.0, cell, Orientation.IDENT, "pwell@0")

    # Exports
    Export.newInst(cell, con_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)
    Export.newInst(cell, pin_out.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
    Export.newInst(cell, pin_vdd_r.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, pin_gnd_r.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    print("Not{lay} successfully constructed (Width = 56 lambda, Height = 76 lambda).")
    return cell

def build_nand_layout(lib, ep, mocmos):
    """Builds the compact 4-input CMOS NAND gate Nand{lay}."""
    print("\n" + "=" * 60)
    print("Building Nand{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("Nand{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "Nand{lay}")
    cell.setTechnology(mocmos)
    clear_cell_contents(cell)

    n_proto = mocmos.findNodeProto("N-Transistor")
    p_proto = mocmos.findNodeProto("P-Transistor")

    m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
    m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
    m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

    m1_pin = mocmos.findNodeProto("Metal-1-Pin")
    n_well_node = mocmos.findNodeProto("N-Well-Node")
    p_well_node = mocmos.findNodeProto("P-Well-Node")

    m1_wire = mocmos.findArcProto("Metal-1")
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    n_act_wire = mocmos.findArcProto("N-Active")
    p_act_wire = mocmos.findArcProto("P-Active")

    Y_P = 22.0
    Y_N = -20.0
    Y_VDD = 38.0
    Y_GND = -38.0
    Y_OUT = 8.0

    # Pitch = 28 lambda between inputs A, B, C, D
    # gx = [-42.0, -14.0, 14.0, 42.0]
    gx = [-42.0, -14.0, 14.0, 42.0]
    in_names = ["A", "B", "C", "D"]

    p_insts = []
    n_insts = []
    in_cons = []

    for i in range(4):
        p = NodeInst.makeInstance(p_proto, ep, Point2D.Double(gx[i], Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@%d" % i)
        p.setPrimitiveNodeSize(4.0, 2.0, ep)
        p_insts.append(p)

        n = NodeInst.makeInstance(n_proto, ep, Point2D.Double(gx[i], Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@%d" % i)
        n.setPrimitiveNodeSize(4.0, 2.0, ep)
        n_insts.append(n)

        # Gate column with input contact at Y = 0
        con_g = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(gx[i], 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_" + in_names[i])
        make_manhattan_arc(poly_wire, ep, p.findPortInst("poly-left"), con_g.getOnlyPortInst())
        make_manhattan_arc(poly_wire, ep, con_g.getOnlyPortInst(), n.findPortInst("poly-right"))
        in_cons.append(con_g)

    # Parallel PMOS active stack with pairwise shared contacts:
    # VDD contacts @ X = -56, 0, +56
    # OUT contacts @ X = -28, +28
    con_p_vdd0 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(-56.0, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_vdd0")
    con_p_out0 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(-28.0, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_out0")
    con_p_vdd1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(0.0, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_vdd1")
    con_p_out1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(28.0, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_out1")
    con_p_vdd2 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(56.0, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "con_p_vdd2")

    make_manhattan_arc(p_act_wire, ep, con_p_vdd0.getOnlyPortInst(), p_insts[0].findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, p_insts[0].findPortInst("diff-bottom"), con_p_out0.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, con_p_out0.getOnlyPortInst(), p_insts[1].findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, p_insts[1].findPortInst("diff-bottom"), con_p_vdd1.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, con_p_vdd1.getOnlyPortInst(), p_insts[2].findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, p_insts[2].findPortInst("diff-bottom"), con_p_out1.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, con_p_out1.getOnlyPortInst(), p_insts[3].findPortInst("diff-top"))
    make_manhattan_arc(p_act_wire, ep, p_insts[3].findPortInst("diff-bottom"), con_p_vdd2.getOnlyPortInst())

    # Series NMOS active stack (continuous shared diffusion):
    # Left end contact: OUT @ (-56, -20)
    con_n_out = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(-56.0, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "con_n_out")
    make_manhattan_arc(n_act_wire, ep, con_n_out.getOnlyPortInst(), n_insts[0].findPortInst("diff-top"))

    # Series shared diffusion links: nmos0 -> nmos1 -> nmos2 -> nmos3
    for i in range(3):
        make_manhattan_arc(n_act_wire, ep, n_insts[i].findPortInst("diff-bottom"), n_insts[i+1].findPortInst("diff-top"))

    # Right end contact: GND @ (+56, -20)
    con_n_gnd = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(56.0, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "con_n_gnd")
    make_manhattan_arc(n_act_wire, ep, n_insts[3].findPortInst("diff-bottom"), con_n_gnd.getOnlyPortInst())

    # Horizontal VDD Rail at Y = +38
    pin_vdd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-68.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_l")
    pin_vdd_0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-56.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_0")
    pin_vdd_1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(0.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_1")
    pin_vdd_2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(56.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_2")
    tap_vdd   = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(68.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd")
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(80.0, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")

    make_manhattan_arc(m1_wire, ep, pin_vdd_l.getOnlyPortInst(), pin_vdd_0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_0.getOnlyPortInst(), pin_vdd_1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_1.getOnlyPortInst(), pin_vdd_2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_vdd_2.getOnlyPortInst(), tap_vdd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_vdd.getOnlyPortInst(), pin_vdd_r.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, con_p_vdd0.getOnlyPortInst(), pin_vdd_0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_p_vdd1.getOnlyPortInst(), pin_vdd_1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_p_vdd2.getOnlyPortInst(), pin_vdd_2.getOnlyPortInst())

    # Horizontal GND Rail at Y = -38
    pin_gnd_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-68.0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_l")
    pin_gnd_2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(56.0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_2")
    tap_gnd   = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(68.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd")
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(80.0, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")

    make_manhattan_arc(m1_wire, ep, pin_gnd_l.getOnlyPortInst(), pin_gnd_2.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_gnd_2.getOnlyPortInst(), tap_gnd.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, tap_gnd.getOnlyPortInst(), pin_gnd_r.getOnlyPortInst())

    make_manhattan_arc(m1_wire, ep, con_n_gnd.getOnlyPortInst(), pin_gnd_2.getOnlyPortInst())

    # Shared OUT interconnect on Metal-1
    pin_out_0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-28.0, Y_OUT), 3.0, 3.0, cell, Orientation.IDENT, "pin_out_0")
    pin_out_1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(28.0, Y_OUT), 3.0, 3.0, cell, Orientation.IDENT, "pin_out_1")
    pin_out_l = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-56.0, Y_OUT), 3.0, 3.0, cell, Orientation.IDENT, "pin_out_l")
    pin_out_node = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-56.0, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_out")

    make_manhattan_arc(m1_wire, ep, con_p_out0.getOnlyPortInst(), pin_out_0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, con_p_out1.getOnlyPortInst(), pin_out_1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_out_l.getOnlyPortInst(), pin_out_0.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_out_0.getOnlyPortInst(), pin_out_1.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_out_l.getOnlyPortInst(), pin_out_node.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_out_node.getOnlyPortInst(), con_n_out.getOnlyPortInst())

    # Well nodes
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(6.0, 30.0), 150.0, 30.0, cell, Orientation.IDENT, "nwell@0")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(6.0, -29.0), 150.0, 30.0, cell, Orientation.IDENT, "pwell@0")

    # Exports
    for i in range(4):
        Export.newInst(cell, in_cons[i].getOnlyPortInst(), in_names[i], PortCharacteristic.IN)
    Export.newInst(cell, pin_out_node.getOnlyPortInst(), "OUT", PortCharacteristic.OUT)
    Export.newInst(cell, pin_vdd_r.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, pin_gnd_r.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    print("Nand{lay} successfully constructed (Width = 148 lambda, Height = 76 lambda).")
    return cell

def verify_cell(lib, cell_name):
    """Executes full Manhattan, LVS/NCC, and DRC verification for a cell."""
    print("\n" + "=" * 60)
    print("Verifying Cell: %s" % cell_name)
    print("=" * 60)

    sch_cell = lib.findNodeProto(cell_name + "{sch}")
    lay_cell = lib.findNodeProto(cell_name + "{lay}")

    if sch_cell is None or lay_cell is None:
        raise Exception("Cell %s missing schematic or layout view" % cell_name)

    # 1. Check Manhattan Perpendicularity
    ait = lay_cell.getArcs()
    non_manhattan = 0
    total_arcs = 0
    while ait.hasNext():
        a = ait.next()
        total_arcs += 1
        p1 = a.getHeadPortInst().getCenter()
        p2 = a.getTailPortInst().getCenter()
        dx = abs(p1.getX() - p2.getX())
        dy = abs(p1.getY() - p2.getY())
        if dx > 0.001 and dy > 0.001:
            print("ERROR: Non-perpendicular arc %s: (%f,%f) -> (%f,%f)" % (a.getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
            non_manhattan += 1

    if non_manhattan > 0:
        raise Exception("Manhattan Verification Failed: %d non-perpendicular arcs found!" % non_manhattan)
    print("1. Manhattan Routing Check: PASS (%d arcs, 100%% perpendicular)" % total_arcs)

    # 2. Check LVS with NCC
    opts = NccOptions()
    opts.checkSizes = True
    results = Ncc.compare(sch_cell, None, lay_cell, None, opts)
    if not results.match() or not results.exportMatch() or not results.topologyMatch():
        raise Exception("LVS / NCC Verification Failed for %s!" % cell_name)
    print("2. NCC / LVS Verification: PASS (Exports Match, Topologies Match, Transistor Sizes Match)")

    # 3. Check DRC with Quick synchronous engine
    prefs = DRC.DRCPreferences(False)
    logger = Quick.checkDesignRules(prefs, lay_cell, None, None)
    num_errors = logger.getNumErrors()
    num_warnings = logger.getNumWarnings()
    if num_errors > 0 or num_warnings > 0:
        it = logger.getLogs()
        while it.hasNext():
            print("  DRC log: " + it.next().getMessage())
        raise Exception("DRC Verification Failed for %s: %d errors, %d warnings!" % (cell_name, num_errors, num_warnings))
    print("3. Electric DRC Verification: PASS (0 Errors, 0 Warnings)")

def main():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    print("Opening library: " + jelib_path)

    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    mocmos = Technology.findTechnology("mocmos")
    if mocmos is None:
        raise Exception("Technology 'mocmos' not found!")

    # Explicitly enforce MOSIS CMOS scale to lambda = 90 nm (TSMC 0.18 um)
    edb = lib.getDatabase()
    batch = Setting.SettingChangeBatch()
    batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
    edb.implementSettingChanges(batch)
    print("Enforced Technology 'mocmos' scale to: %.1f nm" % mocmos.getScale())

    # Build Layouts
    build_not_layout(lib, ep, mocmos)
    build_nand_layout(lib, ep, mocmos)

    # Verify Both Cells
    verify_cell(lib, "Not")
    verify_cell(lib, "Nand")

    # Save to disk
    print("\n" + "=" * 60)
    print("Saving updated library to disk: " + jelib_path)
    print("=" * 60)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library saved successfully!")

if __name__ == "__main__":
    main()
