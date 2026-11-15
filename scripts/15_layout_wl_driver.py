# scripts/15_layout_wl_driver.py
# Clean, compact, DRC/LVS-clean layout generator for WL_driver{lay} in Memory-IC-Design.jelib
# Rules: MOSIS SCMOS_SUBM (mocmos), lambda = 90nm
# Features:
# 1. Minimum contact-to-channel distance: dx = 4.5 lambda (0.405 um) across all transistors.
# 2. Continuous shared active diffusion regions:
#    - PMOS NAND pair (pmos@0 & pmos@1) shares continuous P-active with shared drain contact (NAND_OUT).
#    - NMOS NAND pair (nmos@0 & nmos@1) shares continuous N-active with shared series contact (net@9).
# 3. Compact standard cell pitch: height = 56.0 lambda, width = 52.0 lambda.
# 4. Straight, low-resistance vertical Metal-1 lines and horizontal power rails.
# 5. 100% Manhattan perpendicular routing (0 non-perpendicular arcs).
# 6. Zero DRC errors & warnings (Quick ALGO_SWEEP).
# 7. 100% LVS / NCC match with checkSizes = True against WL_driver{sch}.

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
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

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

def build_wl_driver_layout(lib, ep, mocmos, jelib_path):
    sch = lib.findNodeProto("WL_driver{sch}")
    if not sch:
        raise AssertionError("WL_driver{sch} not found in library!")

    cell = lib.findNodeProto("WL_driver{lay}")
    if not cell:
        cell = Cell.makeInstance(lib, "WL_driver{lay}")
    else:
        clear_cell_contents(cell)
    cell.setTechnology(mocmos)

    # Node prototypes
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

    # Geometry parameters
    Y_VDD = 28.0
    Y_GND = -28.0
    Y_P = 14.0
    Y_N = -14.0
    dx = 4.5

    # Coordinates:
    # Col 0: pmos@1 (W=4), nmos@1 (W=4) at X0 = 10.0 (Gate: EN)
    # Col 1: pmos@0 (W=4), nmos@0 (W=4) at X1 = 19.0 (Gate: IN, pitch 9.0)
    # Col 2: Inverter pmos@2 (W=8), nmos@2 (W=4) at X2 = 40.0 (Gate: NAND_OUT, Output: WL)
    X0 = 10.0
    X1 = 19.0
    X2 = 40.0
    X_MAX = 52.0

    # N-well & P-well
    NodeInst.makeInstance(n_well_node, ep, Point2D.Double(X_MAX / 2.0, 19.0), X_MAX + 16.0, 32.0, cell, Orientation.IDENT, "nwell_core")
    NodeInst.makeInstance(p_well_node, ep, Point2D.Double(X_MAX / 2.0, -19.0), X_MAX + 16.0, 32.0, cell, Orientation.IDENT, "pwell_core")

    # Transistors:
    p1 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(X0, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@1")
    p1.setPrimitiveNodeSize(4.0, 2.0, ep)

    n1 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(X0, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@1")
    n1.setPrimitiveNodeSize(4.0, 2.0, ep)

    p0 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(X1, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@0")
    p0.setPrimitiveNodeSize(4.0, 2.0, ep)

    n0 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(X1, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@0")
    n0.setPrimitiveNodeSize(4.0, 2.0, ep)

    p2 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(X2, Y_P), 22.0, 15.0, cell, Orientation.R, "pmos@2")
    p2.setPrimitiveNodeSize(8.0, 2.0, ep)

    n2 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(X2, Y_N), 22.0, 15.0, cell, Orientation.R, "nmos@2")
    n2.setPrimitiveNodeSize(4.0, 2.0, ep)

    # Active Contacts:
    # 1. PMOS NAND pair (X0=10.0, X1=19.0):
    # Left (5.5): VDD
    pc_vdd_0 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X0 - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_vdd_0")
    make_manhattan_arc(p_act_wire, ep, pc_vdd_0.getOnlyPortInst(), p1.findPortInst("diff-top"))

    # Shared middle (14.5): NAND_OUT
    pcm_01 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(14.5, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_mid_01")
    make_manhattan_arc(p_act_wire, ep, p1.findPortInst("diff-bottom"), pcm_01.getOnlyPortInst())
    make_manhattan_arc(p_act_wire, ep, pcm_01.getOnlyPortInst(), p0.findPortInst("diff-top"))

    # Right (23.5): VDD
    pc_vdd_1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X1 + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_vdd_1")
    make_manhattan_arc(p_act_wire, ep, p0.findPortInst("diff-bottom"), pc_vdd_1.getOnlyPortInst())

    # 2. NMOS NAND pair (X0=10.0, X1=19.0):
    # Left (5.5): GND
    nc_gnd_0 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(X0 - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_gnd_0")
    make_manhattan_arc(n_act_wire, ep, nc_gnd_0.getOnlyPortInst(), n1.findPortInst("diff-top"))

    # Shared middle (14.5): net@9 (internal series node)
    ncm_01 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(14.5, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_mid_01")
    make_manhattan_arc(n_act_wire, ep, n1.findPortInst("diff-bottom"), ncm_01.getOnlyPortInst())
    make_manhattan_arc(n_act_wire, ep, ncm_01.getOnlyPortInst(), n0.findPortInst("diff-top"))

    # Right (23.5): NAND_OUT
    nc_out_1 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(X1 + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_out_1")
    make_manhattan_arc(n_act_wire, ep, n0.findPortInst("diff-bottom"), nc_out_1.getOnlyPortInst())

    # 3. Inverter Buffer (X2 = 40.0):
    # PMOS: Left (35.5) = VDD, Right (44.5) = WL
    pc_vdd_2 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X2 - dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_vdd_2")
    make_manhattan_arc(p_act_wire, ep, pc_vdd_2.getOnlyPortInst(), p2.findPortInst("diff-top"))

    pc_wl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X2 + dx, Y_P), 17.0, 17.0, cell, Orientation.IDENT, "p_con_wl")
    make_manhattan_arc(p_act_wire, ep, p2.findPortInst("diff-bottom"), pc_wl.getOnlyPortInst())

    # NMOS: Left (35.5) = GND, Right (44.5) = WL
    nc_gnd_2 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(X2 - dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_gnd_2")
    make_manhattan_arc(n_act_wire, ep, nc_gnd_2.getOnlyPortInst(), n2.findPortInst("diff-top"))

    nc_wl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(X2 + dx, Y_N), 17.0, 17.0, cell, Orientation.IDENT, "n_con_wl")
    make_manhattan_arc(n_act_wire, ep, n2.findPortInst("diff-bottom"), nc_wl.getOnlyPortInst())

    # Power Rails: VDD & GND
    vdd_x_map = {}
    tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(-2.0, Y_VDD), 17.0, 17.0, cell, Orientation.IDENT, "tap_vdd")
    vdd_x_map[-2.0] = tap_vdd
    pin_vdd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_vdd_r")
    vdd_x_map[X_MAX] = pin_vdd_r

    # VDD vertical drops: pc_vdd_0 (5.5), pc_vdd_1 (23.5), pc_vdd_2 (35.5)
    for con, x in [(pc_vdd_0, 5.5), (pc_vdd_1, 23.5), (pc_vdd_2, 35.5)]:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_VDD), 3.0, 3.0, cell, Orientation.IDENT, "pin_v_%.1f" % x)
        vdd_x_map[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_vdd_x = sorted(vdd_x_map.keys())
    for i in range(len(sorted_vdd_x) - 1):
        make_manhattan_arc(m1_wire, ep, vdd_x_map[sorted_vdd_x[i]].getOnlyPortInst(), vdd_x_map[sorted_vdd_x[i+1]].getOnlyPortInst())

    gnd_x_map = {}
    tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(-2.0, Y_GND), 17.0, 17.0, cell, Orientation.IDENT, "tap_gnd")
    gnd_x_map[-2.0] = tap_gnd
    pin_gnd_r = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_gnd_r")
    gnd_x_map[X_MAX] = pin_gnd_r

    # GND vertical drops: nc_gnd_0 (5.5), nc_gnd_2 (35.5)
    for con, x in [(nc_gnd_0, 5.5), (nc_gnd_2, 35.5)]:
        pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_GND), 3.0, 3.0, cell, Orientation.IDENT, "pin_g_%.1f" % x)
        gnd_x_map[x] = pin
        make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

    sorted_gnd_x = sorted(gnd_x_map.keys())
    for i in range(len(sorted_gnd_x) - 1):
        make_manhattan_arc(m1_wire, ep, gnd_x_map[sorted_gnd_x[i]].getOnlyPortInst(), gnd_x_map[sorted_gnd_x[i+1]].getOnlyPortInst())

    Export.newInst(cell, tap_vdd.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, tap_gnd.getOnlyPortInst(), "GND", PortCharacteristic.GND)

    # NAND_OUT connection to Inverter input:
    # NAND_OUT connects pcm_01 (14.5, 14.0), nc_out_1 (23.5, -14.0), and inverter gate contact con_ginv at (33.0, 0.0)
    pin_pm_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(14.5, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_pm_out")
    make_manhattan_arc(m1_wire, ep, pcm_01.getOnlyPortInst(), pin_pm_out.getOnlyPortInst())

    pin_nm_out = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(23.5, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_nm_out")
    make_manhattan_arc(m1_wire, ep, nc_out_1.getOnlyPortInst(), pin_nm_out.getOnlyPortInst())

    con_ginv = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(33.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_ginv")

    # Horizontal M1 wire for NAND_OUT connecting pin_pm_out -> pin_nm_out -> con_ginv
    make_manhattan_arc(m1_wire, ep, pin_pm_out.getOnlyPortInst(), pin_nm_out.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_nm_out.getOnlyPortInst(), con_ginv.getOnlyPortInst())

    # Inverter gate poly: along X2 = 40.0 connecting p2 and n2 gates, with pin at (40.0, 0.0)
    pin_ginv = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(X2, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "pin_ginv")
    make_manhattan_arc(poly_wire, ep, con_ginv.getOnlyPortInst(), pin_ginv.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, p2.findPortInst("poly-left"), pin_ginv.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, pin_ginv.getOnlyPortInst(), n2.findPortInst("poly-right"))

    # WL Output: vertical M1 line at X = 44.5 connecting pc_wl and nc_wl
    pin_wl = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X2 + dx, 0.0), 3.0, 3.0, cell, Orientation.IDENT, "pin_wl")
    make_manhattan_arc(m1_wire, ep, pc_wl.getOnlyPortInst(), pin_wl.getOnlyPortInst())
    make_manhattan_arc(m1_wire, ep, pin_wl.getOnlyPortInst(), nc_wl.getOnlyPortInst())
    Export.newInst(cell, pin_wl.getOnlyPortInst(), "WL", PortCharacteristic.OUT)

    # Inputs IN and EN:
    # EN at Col 0 (X0 = 10.0): poly connects p1 and n1 gates, with poly branching left to con_en at (0.0, 0.0)
    pin_en_mid = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(X0, 0.0), 2.0, 2.0, cell, Orientation.IDENT, "pin_en_mid")
    make_manhattan_arc(poly_wire, ep, p1.findPortInst("poly-left"), pin_en_mid.getOnlyPortInst())
    make_manhattan_arc(poly_wire, ep, pin_en_mid.getOnlyPortInst(), n1.findPortInst("poly-right"))

    con_en = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(0.0, 0.0), 5.0, 5.0, cell, Orientation.IDENT, "con_en")
    make_manhattan_arc(poly_wire, ep, con_en.getOnlyPortInst(), pin_en_mid.getOnlyPortInst())
    Export.newInst(cell, con_en.getOnlyPortInst(), "EN", PortCharacteristic.IN)

    # IN at Col 1 (X1 = 19.0): poly connects p0 and n0 gates, with con_in at (19.0, -21.0)
    con_in = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(X1, -21.0), 5.0, 5.0, cell, Orientation.IDENT, "con_in")
    make_manhattan_arc(poly_wire, ep, p0.findPortInst("poly-left"), n0.findPortInst("poly-right"))
    make_manhattan_arc(poly_wire, ep, n0.findPortInst("poly-left"), con_in.getOnlyPortInst())
    Export.newInst(cell, con_in.getOnlyPortInst(), "IN", PortCharacteristic.IN)

    # Verification: Manhattan Arcs
    ait = cell.getArcs()
    total_arcs = 0
    non_manhattan = 0
    while ait.hasNext():
        a = ait.next()
        total_arcs += 1
        p1_pt = a.getHeadPortInst().getCenter()
        p2_pt = a.getTailPortInst().getCenter()
        dx_val = abs(p1_pt.getX() - p2_pt.getX())
        dy_val = abs(p1_pt.getY() - p2_pt.getY())
        if dx_val > 0.001 and dy_val > 0.001:
            print("  Non-Manhattan arc: %s (%f,%f) -> (%f,%f)" % (a.getName(), p1_pt.getX(), p1_pt.getY(), p2_pt.getX(), p2_pt.getY()))
            non_manhattan += 1
    print("Manhattan Check: %d / %d arcs perpendicular." % (total_arcs - non_manhattan, total_arcs))
    if non_manhattan > 0:
        raise AssertionError("Found non-Manhattan arcs!")

    # Verification: Quick DRC
    print("Running Quick DRC on WL_driver{lay}...")
    n_err, n_warn = run_drc(cell)
    if n_err > 0 or n_warn > 0:
        raise AssertionError("DRC failed with %d errors, %d warnings!" % (n_err, n_warn))

    # Verification: NCC LVS with checkSizes = True
    print("Running NCC against WL_driver{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())
    if not res.match():
        raise AssertionError("NCC comparison failed!")

    print("Saving updated library to disk: " + jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Library written successfully to jelib file: %s" % jelib_path)

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

    build_wl_driver_layout(lib, ep, mocmos, jelib_path)

if __name__ == "__main__":
    main()
