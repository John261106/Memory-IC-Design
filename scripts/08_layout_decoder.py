# ==============================================================================
# Electric VLSI 9.08 - 4-to-16 Address Decoder Physical Layout Generator
#
# Generates hierarchical physical layout view:
#   Decoder{lay} - 4-to-16 Address Decoder matching Decoder{sch}
#
# Circuit Architecture:
#   - 4 Input Inverters (Not@0..3) producing inverted address lines A0_B..A3_B
#   - 16 4-Input NAND Gates (Nand@0..15) generating 16 active-low minterms
#   - 16 Output Inverters (Not@4..19) generating active-high word selects OUT0..OUT15
#   - 8-track vertical Metal-2 address bus (A0..A3 true and complementary lines)
#   - Pitch-matched standard cell rows stacked at DY = 76.0 lambda
#   - Vertical Metal-2 VDD & GND straps with horizontal Metal-1 row rails
#
# Technology: mocmos (MOSIS CMOS, TSMC 0.18 um, lambda = 90 nm)
#
# Verification:
#   1. Manhattan Routing: 100% perpendicular (horizontal and vertical arcs only)
#   2. LVS / NCC: 100% match (topology, exports, transistor sizing)
#   3. DRC: 0 errors, 0 warnings (native Electric VLSI ALGO_SWEEP)
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

def make_arc(arc_proto, ep, port1, port2):
    """Creates an arc between two ports and strictly verifies it is Manhattan perpendicular."""
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

def build_decoder_layout(lib, ep, mocmos):
    """Builds the complete hierarchical physical layout Decoder{lay}."""
    print("\n" + "=" * 60)
    print("Building Hierarchical Decoder{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("Decoder{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "Decoder{lay}")
    cell.setTechnology(mocmos)
    clear_cell_contents(cell)

    not_lay = lib.findNodeProto("Not{lay}")
    nand_lay = lib.findNodeProto("Nand{lay}")
    if not_lay is None or nand_lay is None:
        raise Exception("Subcells Not{lay} or Nand{lay} not found in library!")

    m1_wire = mocmos.findArcProto("Metal-1")
    m2_wire = mocmos.findArcProto("Metal-2")
    via1    = mocmos.findNodeProto("Metal-1-Metal-2-Con")
    m1_pin  = mocmos.findNodeProto("Metal-1-Pin")
    m2_pin  = mocmos.findNodeProto("Metal-2-Pin")

    DY = 72.0
    X_NAND = 0.0
    X_NOT  = 88.0

    # Address bus track X coordinates
    # Group 3 (Bit 3, Input A @ -39.0): True @ -43.0, Comp @ -35.0
    # Group 2 (Bit 2, Input B @ -13.0): True @ -17.0, Comp @  -9.0
    # Group 1 (Bit 1, Input C @ +13.0): True @  +9.0, Comp @ +17.0
    # Group 0 (Bit 0, Input D @ +39.0): True @ +39.0, Comp @ +31.0
    tracks_true = [-43.0, -17.0,  9.0, 39.0]
    tracks_comp = [-35.0,  -9.0, 17.0, 31.0]

    # Power strap X coordinates (right of output inverters)
    X_VDD_STRAP = 116.0
    X_GND_STRAP = 124.0
    X_OUT_PIN   = 130.0

    track_nodes = {
        "A3": [], "A3_B": [],
        "A2": [], "A2_B": [],
        "A1": [], "A1_B": [],
        "A0": [], "A0_B": [],
        "VDD": [], "GND": []
    }

    # -------------------------------------------------------------------------
    # 1. Place 16 Decode Rows (Nand@k and Not@(k+4)) for k = 0 .. 15
    # -------------------------------------------------------------------------
    for k in range(16):
        yk = k * DY
        nand_k = NodeInst.makeInstance(nand_lay, ep, Point2D.Double(X_NAND, yk), 116.0, 52.0, cell, Orientation.IDENT, "Nand@%d" % k)
        not_k  = NodeInst.makeInstance(not_lay,  ep, Point2D.Double(X_NOT,  yk),  42.0, 52.0, cell, Orientation.IDENT, "Not@%d" % (k + 4))

        # Horizontal power & ground rail bridge between NAND and NOT
        make_arc(m1_wire, ep, nand_k.findPortInst("VDD"), not_k.findPortInst("VDD"))
        make_arc(m1_wire, ep, nand_k.findPortInst("GND"), not_k.findPortInst("GND"))

        # Connect Nand.OUT (at 58.0, yk + 7.0) to Not.IN (at 88.0, yk) via 2-segment Manhattan dogleg
        p_nand_out = nand_k.findPortInst("OUT")
        p_not_in   = not_k.findPortInst("IN")
        p_mid1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(63.0, yk + 7.0), 3.0, 3.0, cell, Orientation.IDENT, "p_mid1_%d" % k)
        p_mid2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(63.0, yk),       3.0, 3.0, cell, Orientation.IDENT, "p_mid2_%d" % k)
        make_arc(m1_wire, ep, p_nand_out, p_mid1.getOnlyPortInst())
        make_arc(m1_wire, ep, p_mid1.getOnlyPortInst(), p_mid2.getOnlyPortInst())
        make_arc(m1_wire, ep, p_mid2.getOnlyPortInst(), p_not_in)

        # Output pin and export OUTk
        p_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_OUT_PIN, yk), 3.0, 3.0, cell, Orientation.IDENT, "p_out_%d" % k)
        make_arc(m1_wire, ep, not_k.findPortInst("OUT"), p_out.getOnlyPortInst())
        Export.newInst(cell, p_out.getOnlyPortInst(), "OUT%d" % k, PortCharacteristic.OUT)

        # Vertical power strap tap vias
        v_vdd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_VDD_STRAP, yk + 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_vdd_%d" % k)
        make_arc(m1_wire, ep, not_k.findPortInst("VDD"), v_vdd.findPortInst("metal-1-metal-2"))
        track_nodes["VDD"].append(v_vdd.findPortInst("metal-1-metal-2"))

        v_gnd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_GND_STRAP, yk - 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_gnd_%d" % k)
        make_arc(m1_wire, ep, not_k.findPortInst("GND"), v_gnd.findPortInst("metal-1-metal-2"))
        track_nodes["GND"].append(v_gnd.findPortInst("metal-1-metal-2"))

        # Address tap connections to NAND inputs A, B, C, D
        b3 = (k >> 3) & 1
        b2 = (k >> 2) & 1
        b1 = (k >> 1) & 1
        b0 = k & 1

        # Input A (Bit 3, index 0)
        port_A = nand_k.findPortInst("A")
        if b3 == 1:
            v_a = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_true[0], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_a_%d" % k)
            make_arc(m1_wire, ep, v_a.findPortInst("metal-1-metal-2"), port_A)
            track_nodes["A3"].append(v_a.findPortInst("metal-1-metal-2"))
        else:
            v_a = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_comp[0], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_a_%d" % k)
            make_arc(m1_wire, ep, v_a.findPortInst("metal-1-metal-2"), port_A)
            track_nodes["A3_B"].append(v_a.findPortInst("metal-1-metal-2"))

        # Input B (Bit 2, index 1)
        port_B = nand_k.findPortInst("B")
        if b2 == 1:
            v_b = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_true[1], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_b_%d" % k)
            make_arc(m1_wire, ep, v_b.findPortInst("metal-1-metal-2"), port_B)
            track_nodes["A2"].append(v_b.findPortInst("metal-1-metal-2"))
        else:
            v_b = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_comp[1], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_b_%d" % k)
            make_arc(m1_wire, ep, v_b.findPortInst("metal-1-metal-2"), port_B)
            track_nodes["A2_B"].append(v_b.findPortInst("metal-1-metal-2"))

        # Input C (Bit 1, index 2)
        port_C = nand_k.findPortInst("C")
        if b1 == 1:
            v_c = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_true[2], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_c_%d" % k)
            make_arc(m1_wire, ep, v_c.findPortInst("metal-1-metal-2"), port_C)
            track_nodes["A1"].append(v_c.findPortInst("metal-1-metal-2"))
        else:
            v_c = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_comp[2], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_c_%d" % k)
            make_arc(m1_wire, ep, v_c.findPortInst("metal-1-metal-2"), port_C)
            track_nodes["A1_B"].append(v_c.findPortInst("metal-1-metal-2"))

        # Input D (Bit 0, index 3)
        port_D = nand_k.findPortInst("D")
        if b0 == 1:
            v_d = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_true[3], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_d_%d" % k)
            make_arc(m1_wire, ep, v_d.findPortInst("metal-1-metal-2"), port_D)
            track_nodes["A0"].append(v_d.findPortInst("metal-1-metal-2"))
        else:
            v_d = NodeInst.makeInstance(via1, ep, Point2D.Double(tracks_comp[3], yk), 5.0, 5.0, cell, Orientation.IDENT, "v_d_%d" % k)
            make_arc(m1_wire, ep, v_d.findPortInst("metal-1-metal-2"), port_D)
            track_nodes["A0_B"].append(v_d.findPortInst("metal-1-metal-2"))

    # -------------------------------------------------------------------------
    # 2. Place 4 Input Inverters (Not@3, Not@2, Not@1, Not@0) in Rows 16..19
    # -------------------------------------------------------------------------
    # Bit 3: Not@3 in Row 16, Orient IDENT: IN @ -43.0, OUT @ -30.0, Comp track @ -35.0
    # Bit 2: Not@2 in Row 17, Orient IDENT: IN @ -17.0, OUT @  -4.0, Comp track @  -9.0
    # Bit 1: Not@1 in Row 18, Orient IDENT: IN @   9.0, OUT @  22.0, Comp track @  17.0
    # Bit 0: Not@0 in Row 19, Orient X:     IN @  39.0, OUT @  26.0, Comp track @  31.0
    input_inv_info = [
        (3, "Not@3", 16, tracks_true[0], tracks_comp[0], "A3", "A3_B", Orientation.IDENT, tracks_true[0] + 13.0),
        (2, "Not@2", 17, tracks_true[1], tracks_comp[1], "A2", "A2_B", Orientation.IDENT, tracks_true[1] + 13.0),
        (1, "Not@1", 18, tracks_true[2], tracks_comp[2], "A1", "A1_B", Orientation.IDENT, tracks_true[2] + 13.0),
        (0, "Not@0", 19, tracks_true[3], tracks_comp[3], "A0", "A0_B", Orientation.X,     tracks_true[3] - 13.0)
    ]

    for bit, name, row_idx, x_pos, c_track_x, t_name, c_name, orient, x_out_pin in input_inv_info:
        y_inv = row_idx * DY
        inv_node = NodeInst.makeInstance(not_lay, ep, Point2D.Double(x_pos, y_inv), 42.0, 52.0, cell, orient, name)

        # Via directly on inv.IN (at x_pos, y_inv)
        v_in = NodeInst.makeInstance(via1, ep, Point2D.Double(x_pos, y_inv), 5.0, 5.0, cell, Orientation.IDENT, "v_in_%d" % bit)
        make_arc(m1_wire, ep, v_in.findPortInst("metal-1-metal-2"), inv_node.findPortInst("IN"))
        track_nodes[t_name].append(v_in.findPortInst("metal-1-metal-2"))

        # Export Input A_bit on Metal-1
        pin_in_x = (x_pos + 10.0) if orient == Orientation.X else (x_pos - 10.0)
        pin_in = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(pin_in_x, y_inv), 3.0, 3.0, cell, Orientation.IDENT, "pin_in_%d" % bit)
        make_arc(m1_wire, ep, pin_in.getOnlyPortInst(), inv_node.findPortInst("IN"))
        Export.newInst(cell, pin_in.getOnlyPortInst(), "A%d" % bit, PortCharacteristic.IN)

        # Via directly on inv.OUT (at x_out_pin, y_inv)
        v_out = NodeInst.makeInstance(via1, ep, Point2D.Double(x_out_pin, y_inv), 5.0, 5.0, cell, Orientation.IDENT, "v_out_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("OUT"), v_out.findPortInst("metal-1-metal-2"))

        # Drop down on Metal-2 into the channel at y_jog = y_inv - 36.0
        y_jog = y_inv - 36.0
        p_jog1 = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(x_out_pin, y_jog), 3.0, 3.0, cell, Orientation.IDENT, "pj1_%d" % bit)
        p_jog2 = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(c_track_x,  y_jog), 3.0, 3.0, cell, Orientation.IDENT, "pj2_%d" % bit)

        make_arc(m2_wire, ep, v_out.findPortInst("metal-1-metal-2"), p_jog1.getOnlyPortInst())
        make_arc(m2_wire, ep, p_jog1.getOnlyPortInst(), p_jog2.getOnlyPortInst())
        track_nodes[c_name].append(p_jog2.getOnlyPortInst())

        # Power strap connections for input inverters
        v_inv_vdd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_VDD_STRAP, y_inv + 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_inv_vdd_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("VDD"), v_inv_vdd.findPortInst("metal-1-metal-2"))
        track_nodes["VDD"].append(v_inv_vdd.findPortInst("metal-1-metal-2"))

        v_inv_gnd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_GND_STRAP, y_inv - 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_inv_gnd_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("GND"), v_inv_gnd.findPortInst("metal-1-metal-2"))
        track_nodes["GND"].append(v_inv_gnd.findPortInst("metal-1-metal-2"))

    # -------------------------------------------------------------------------
    # 3. Chain All 8 Vertical Address Lines and 2 Power Straps on Metal-2
    # -------------------------------------------------------------------------
    for net_name, p_list in track_nodes.items():
        sorted_p = sorted(p_list, key=lambda p: p.getCenter().getY())
        for i in range(len(sorted_p) - 1):
            make_arc(m2_wire, ep, sorted_p[i], sorted_p[i + 1])

    # Export VDD and GND power ports
    top_vdd = track_nodes["VDD"][-1]
    top_gnd = track_nodes["GND"][-1]
    Export.newInst(cell, top_vdd, "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, top_gnd, "GND", PortCharacteristic.GND)

    print("Decoder{lay} construction completed successfully!")
    return cell

def verify_decoder(lib):
    """Runs Manhattan routing check, LVS / NCC, and DRC on Decoder{lay}."""
    print("\n" + "=" * 60)
    print("Verifying Decoder{lay}...")
    print("=" * 60)

    sch_cell = lib.findNodeProto("Decoder{sch}")
    lay_cell = lib.findNodeProto("Decoder{lay}")

    if sch_cell is None or lay_cell is None:
        raise Exception("Decoder{sch} or Decoder{lay} not found!")

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
        raise Exception("Manhattan Routing Check Failed: %d non-perpendicular arcs found!" % non_m)
    print("1. Manhattan Routing Check: PASS (%d arcs, 100%% perpendicular)" % total_arcs)

    # 2. NCC / LVS Check
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch_cell, None, lay_cell, None, opts)
    if not res.match():
        raise Exception("NCC / LVS Check Failed: match=%s, exportMatch=%s, topologyMatch=%s" % (res.match(), res.exportMatch(), res.topologyMatch()))
    print("2. NCC / LVS Check: PASS (match=%s, exportMatch=%s, topologyMatch=%s)" % (res.match(), res.exportMatch(), res.topologyMatch()))

    # 3. Quick DRC Check
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
            print("DRC LOG:", lit.next().getMessage())
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
    build_decoder_layout(lib, ep, mocmos)

    # Verify Decoder{lay}
    verify_decoder(lib)

    # Save to disk
    print("\n" + "=" * 60)
    print("Saving updated library to disk: " + jelib_path)
    print("=" * 60)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library saved successfully with Decoder{lay}!")

if __name__ == "__main__":
    main()
