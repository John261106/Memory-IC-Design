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
#   - Split 8-track vertical Metal-2 address bus:
#       Left of Nand:  A2 (-72), A2_B (-64), A3 (-56), A3_B (-48)
#       Right of Nand: A0 (+46), A0_B (+54), A1 (+62), A1_B (+70)
#   - Pitch-matched compacted standard cell rows stacked at DY = 72.0 lambda
#   - Vertical Metal-2 VDD & GND straps with horizontal Metal-1 row rails
#
# Technology: mocmos (MOSIS CMOS, TSMC 0.18 um, lambda = 90 nm)
#
# Verification:
#   1. Manhattan Routing: 100% perpendicular (horizontal and vertical arcs only)
#   2. LVS / NCC: 100% match with checkSizes=True (topology, exports, sizing)
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

    ait = cell.getArcs()
    arc_kill = []
    while ait.hasNext():
        arc_kill.append(ait.next())
    for a in arc_kill:
        a.kill()

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
    X_NOT  = 100.0  # Compacted Not{lay} spans [-20,+20], so [80, 120]

    # Split 8-track vertical Metal-2 address bus:
    # Left of Nand [-40,+40]:
    #   Bit 2 (B): True @ -72.0, Comp @ -64.0
    #   Bit 3 (A): True @ -56.0, Comp @ -48.0
    # Right of Nand [-40,+40], Left of Not [80,120]:
    #   Bit 0 (D): True @ +46.0, Comp @ +54.0
    #   Bit 1 (C): True @ +62.0, Comp @ +70.0
    tracks_true = [-56.0, -72.0, 62.0, 46.0]  # [Bit3(A), Bit2(B), Bit1(C), Bit0(D)]
    tracks_comp = [-48.0, -64.0, 70.0, 54.0]  # [Bit3(A), Bit2(B), Bit1(C), Bit0(D)]

    # Power strap X coordinates (right of output inverters [80,120])
    X_VDD_STRAP = 126.0
    X_GND_STRAP = 134.0
    X_OUT_PIN   = 140.0

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
        nand_k = NodeInst.makeInstance(nand_lay, ep, Point2D.Double(X_NAND, yk), 80.0, 69.0, cell, Orientation.IDENT, "Nand@%d" % k)
        not_k  = NodeInst.makeInstance(not_lay,  ep, Point2D.Double(X_NOT,  yk), 40.0, 69.0, cell, Orientation.IDENT, "Not@%d" % (k + 4))

        # Horizontal power & ground rail bridge between NAND and NOT (on Metal-1, passing under M2 address tracks)
        make_arc(m1_wire, ep, nand_k.findPortInst("VDD"), not_k.findPortInst("VDD"))
        make_arc(m1_wire, ep, nand_k.findPortInst("GND"), not_k.findPortInst("GND"))

        # Connect Nand.OUT (36.0, yk+7.0) to Not.IN (93.0, yk) on Metal-1 via 2-segment Manhattan dogleg at X=75.0
        p_nand_out = nand_k.findPortInst("OUT")
        p_not_in   = not_k.findPortInst("IN")
        p_mid1 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(75.0, yk + 7.0), 3.0, 3.0, cell, Orientation.IDENT, "p_mid1_%d" % k)
        p_mid2 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(75.0, yk),       3.0, 3.0, cell, Orientation.IDENT, "p_mid2_%d" % k)
        make_arc(m1_wire, ep, p_nand_out, p_mid1.getOnlyPortInst())
        make_arc(m1_wire, ep, p_mid1.getOnlyPortInst(), p_mid2.getOnlyPortInst())
        make_arc(m1_wire, ep, p_mid2.getOnlyPortInst(), p_not_in)

        # Output pin and export OUTk (passes cleanly under VDD/GND M2 straps at Y = yk)
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

        # Input A (Bit 3, port @ -13.5, yk) -> M2 across Nand (-21.0) to -28.0, then M1 to inner tracks (-56 or -48)
        port_A = nand_k.findPortInst("A")
        net_A = "A3" if b3 == 1 else "A3_B"
        tx_A = tracks_true[0] if b3 == 1 else tracks_comp[0]
        va_in = NodeInst.makeInstance(via1, ep, Point2D.Double(-13.5, yk), 5.0, 5.0, cell, Orientation.IDENT, "va_in_%d" % k)
        make_arc(m1_wire, ep, port_A, va_in.getOnlyPortInst())
        va_br = NodeInst.makeInstance(via1, ep, Point2D.Double(-28.0, yk), 5.0, 5.0, cell, Orientation.IDENT, "va_br_%d" % k)
        make_arc(m2_wire, ep, va_in.getOnlyPortInst(), va_br.getOnlyPortInst())
        va_trk = NodeInst.makeInstance(via1, ep, Point2D.Double(tx_A, yk), 5.0, 5.0, cell, Orientation.IDENT, "va_trk_%d" % k)
        make_arc(m1_wire, ep, va_br.getOnlyPortInst(), va_trk.getOnlyPortInst())
        track_nodes[net_A].append(va_trk.getOnlyPortInst())

        # Input B (Bit 2, port @ -4.5, yk) -> M2 up to channel yk+36, then M1 left across A3/A3_B to outer tracks (-72 or -64)
        port_B = nand_k.findPortInst("B")
        net_B = "A2" if b2 == 1 else "A2_B"
        tx_B = tracks_true[1] if b2 == 1 else tracks_comp[1]
        vb_in = NodeInst.makeInstance(via1, ep, Point2D.Double(-4.5, yk), 5.0, 5.0, cell, Orientation.IDENT, "vb_in_%d" % k)
        make_arc(m1_wire, ep, port_B, vb_in.getOnlyPortInst())
        vb_ch = NodeInst.makeInstance(via1, ep, Point2D.Double(-4.5, yk + 36.0), 5.0, 5.0, cell, Orientation.IDENT, "vb_ch_%d" % k)
        make_arc(m2_wire, ep, vb_in.getOnlyPortInst(), vb_ch.getOnlyPortInst())
        vb_trk = NodeInst.makeInstance(via1, ep, Point2D.Double(tx_B, yk + 36.0), 5.0, 5.0, cell, Orientation.IDENT, "vb_trk_%d" % k)
        make_arc(m1_wire, ep, vb_ch.getOnlyPortInst(), vb_trk.getOnlyPortInst())
        track_nodes[net_B].append(vb_trk.getOnlyPortInst())

        # Input C (Bit 1, port @ +4.5, yk) -> M2 up to channel yk+36, then M1 right across A0/A0_B to outer tracks (+62 or +70)
        port_C = nand_k.findPortInst("C")
        net_C = "A1" if b1 == 1 else "A1_B"
        tx_C = tracks_true[2] if b1 == 1 else tracks_comp[2]
        vc_in = NodeInst.makeInstance(via1, ep, Point2D.Double(4.5, yk), 5.0, 5.0, cell, Orientation.IDENT, "vc_in_%d" % k)
        make_arc(m1_wire, ep, port_C, vc_in.getOnlyPortInst())
        vc_ch = NodeInst.makeInstance(via1, ep, Point2D.Double(4.5, yk + 36.0), 5.0, 5.0, cell, Orientation.IDENT, "vc_ch_%d" % k)
        make_arc(m2_wire, ep, vc_in.getOnlyPortInst(), vc_ch.getOnlyPortInst())
        vc_trk = NodeInst.makeInstance(via1, ep, Point2D.Double(tx_C, yk + 36.0), 5.0, 5.0, cell, Orientation.IDENT, "vc_trk_%d" % k)
        make_arc(m1_wire, ep, vc_ch.getOnlyPortInst(), vc_trk.getOnlyPortInst())
        track_nodes[net_C].append(vc_trk.getOnlyPortInst())

        # Input D (Bit 0, port @ +13.5, yk) -> M1 directly right to inner tracks (+46 or +54)
        port_D = nand_k.findPortInst("D")
        net_D = "A0" if b0 == 1 else "A0_B"
        tx_D = tracks_true[3] if b0 == 1 else tracks_comp[3]
        vd_trk = NodeInst.makeInstance(via1, ep, Point2D.Double(tx_D, yk), 5.0, 5.0, cell, Orientation.IDENT, "vd_trk_%d" % k)
        make_arc(m1_wire, ep, port_D, vd_trk.getOnlyPortInst())
        track_nodes[net_D].append(vd_trk.getOnlyPortInst())

    # -------------------------------------------------------------------------
    # 2. Place 4 Input Inverters (Not@3, Not@2, Not@1, Not@0) in Rows 16..19 (+12.0 lambda offset)
    # -------------------------------------------------------------------------
    # Not{lay} IDENT: IN @ -7.0, OUT @ +4.5, VDD/GND @ +16.0
    # Not{lay} X:     IN @ +7.0, OUT @ -4.5, VDD/GND @ -16.0
    input_inv_info = [
        (3, "Not@3", 16, tracks_true[0], tracks_comp[0], "A3", "A3_B", Orientation.IDENT),
        (2, "Not@2", 17, tracks_true[1], tracks_comp[1], "A2", "A2_B", Orientation.IDENT),
        (1, "Not@1", 18, tracks_true[2], tracks_comp[2], "A1", "A1_B", Orientation.X),
        (0, "Not@0", 19, tracks_true[3], tracks_comp[3], "A0", "A0_B", Orientation.X)
    ]

    for bit, name, row_idx, t_track_x, c_track_x, t_name, c_name, orient in input_inv_info:
        y_inv = row_idx * DY + 12.0
        # Place all 4 input inverters centered at X = 0.0
        inv_node = NodeInst.makeInstance(not_lay, ep, Point2D.Double(0.0, y_inv), 40.0, 69.0, cell, orient, name)

        # True track tap on Metal-1 from inv.IN to t_track_x
        v_in = NodeInst.makeInstance(via1, ep, Point2D.Double(t_track_x, y_inv), 5.0, 5.0, cell, Orientation.IDENT, "v_in_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("IN"), v_in.getOnlyPortInst())
        track_nodes[t_name].append(v_in.getOnlyPortInst())
        Export.newInst(cell, v_in.getOnlyPortInst(), "A%d" % bit, PortCharacteristic.IN)

        # Complementary track tap: drop from inv.OUT to channel y_inv - 36.0 on M2, then M1 to c_track_x
        x_out_inv = 4.5 if orient == Orientation.IDENT else -4.5
        v_out = NodeInst.makeInstance(via1, ep, Point2D.Double(x_out_inv, y_inv), 5.0, 5.0, cell, Orientation.IDENT, "v_out_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("OUT"), v_out.getOnlyPortInst())

        y_jog = y_inv - 36.0
        v_jog1 = NodeInst.makeInstance(via1, ep, Point2D.Double(x_out_inv, y_jog), 5.0, 5.0, cell, Orientation.IDENT, "vjog1_%d" % bit)
        v_jog2 = NodeInst.makeInstance(via1, ep, Point2D.Double(c_track_x, y_jog), 5.0, 5.0, cell, Orientation.IDENT, "vjog2_%d" % bit)
        make_arc(m2_wire, ep, v_out.getOnlyPortInst(), v_jog1.getOnlyPortInst())
        make_arc(m1_wire, ep, v_jog1.getOnlyPortInst(), v_jog2.getOnlyPortInst())
        track_nodes[c_name].append(v_jog2.getOnlyPortInst())

        # Power strap connections for input inverters (on Metal-1 to X_VDD_STRAP / X_GND_STRAP)
        v_inv_vdd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_VDD_STRAP, y_inv + 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_inv_vdd_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("VDD"), v_inv_vdd.getOnlyPortInst())
        track_nodes["VDD"].append(v_inv_vdd.getOnlyPortInst())

        v_inv_gnd = NodeInst.makeInstance(via1, ep, Point2D.Double(X_GND_STRAP, y_inv - 26.0), 5.0, 5.0, cell, Orientation.IDENT, "v_inv_gnd_%d" % bit)
        make_arc(m1_wire, ep, inv_node.findPortInst("GND"), v_inv_gnd.getOnlyPortInst())
        track_nodes["GND"].append(v_inv_gnd.getOnlyPortInst())

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
        seen = set()
        while lit.hasNext():
            msg = lit.next().getMessageString()
            if msg not in seen:
                seen.add(msg)
                print("DRC LOG:", msg)
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
