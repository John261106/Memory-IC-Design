# scripts/18_layout_8bit_reg.py
# Clean, compact, DRC/LVS-clean layout generator for 8Bit_reg{lay} in Memory-IC-Design.jelib
# Architecture: 8-Bit Parallel-In Parallel-Out (PIPO) Register
# Technology: MOSIS SCMOS_SUBM (mocmos), lambda = 90nm
# Features:
# 1. Standard-cell hierarchical architecture:
#    - 8 D Flip-Flop standard cell instances (D_flipfl@0 to D_flipfl@7) instantiating D_flipflop{lay}
#    - Pitched uniformly along standard-cell rows with pitch DY = 86.0 lambda
# 2. Structured vertical Metal-2 power grid straps and clock distribution:
#    - VDD strap at X = -38.0 lambda
#    - GND strap at X = -46.0 lambda
#    - CLK strap at X = -30.0 lambda
# 3. 100% Manhattan perpendicular routing (0 non-perpendicular arcs).
# 4. Zero DRC errors & warnings (Quick ALGO_SWEEP).
# 5. 100% LVS / NCC match with checkSizes = True against 8Bit_reg{sch} (19 exports, topologies, transistor sizes).

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

def build_8bit_reg_layout(lib, ep, mocmos, jelib_path):
    print("\n" + "=" * 60)
    print("Building Standard-Cell Layout: 8Bit_reg{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("8Bit_reg{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "8Bit_reg{lay}")
    else:
        clear_cell_contents(cell)
    cell.setTechnology(mocmos)

    sch = lib.findNodeProto("8Bit_reg{sch}")
    dff_lay = lib.findNodeProto("D_flipflop{lay}")

    m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
    m1_wire = mocmos.findArcProto("Metal-1")
    m2_wire = mocmos.findArcProto("Metal-2")

    DY = 86.0  # Standard-cell row pitch
    NUM_BITS = 8

    dff_insts = []
    vias_v = []
    vias_g = []
    vias_clk = []

    # 1. Instantiate 8 D Flip-Flops and power/clock grid
    for i in range(NUM_BITS):
        y_row = i * DY
        dff = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, y_row), 287.0, 56.0, cell, Orientation.IDENT, "D_flipfl@%d" % i)
        dff_insts.append(dff)

        # VDD via at X = -38.0, Y = y_row + 28.0
        vv = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, y_row + 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_v%d" % i)
        vias_v.append(vv)
        make_manhattan_arc(m1_wire, ep, vv.getOnlyPortInst(), dff.findPortInst("VDD"))

        # GND via at X = -46.0, Y = y_row - 28.0
        vg = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, y_row - 28.0), 5.0, 5.0, cell, Orientation.IDENT, "via_g%d" % i)
        vias_g.append(vg)
        make_manhattan_arc(m1_wire, ep, vg.getOnlyPortInst(), dff.findPortInst("GND"))

        # CLK via at X = -30.0, Y = y_row
        vclk = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, y_row), 5.0, 5.0, cell, Orientation.IDENT, "via_clk%d" % i)
        vias_clk.append(vclk)
        make_manhattan_arc(m1_wire, ep, vclk.getOnlyPortInst(), dff.findPortInst("CLK"))

        # Export D and Q for this bit
        Export.newInst(cell, dff.findPortInst("D"), "D%d" % i, PortCharacteristic.IN)
        Export.newInst(cell, dff.findPortInst("Q"), "Q%d" % i, PortCharacteristic.OUT)

    # 2. Connect vertical Metal-2 straps
    for i in range(NUM_BITS - 1):
        make_manhattan_arc(m2_wire, ep, vias_v[i].getOnlyPortInst(), vias_v[i+1].getOnlyPortInst())
        make_manhattan_arc(m2_wire, ep, vias_g[i].getOnlyPortInst(), vias_g[i+1].getOnlyPortInst())
        make_manhattan_arc(m2_wire, ep, vias_clk[i].getOnlyPortInst(), vias_clk[i+1].getOnlyPortInst())

    # 3. Export global power and clock pins
    Export.newInst(cell, vias_v[0].getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, vias_g[0].getOnlyPortInst(), "GND", PortCharacteristic.GND)
    Export.newInst(cell, vias_clk[0].getOnlyPortInst(), "CLK", PortCharacteristic.IN)

    # 4. Verification: Manhattan check
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
        raise AssertionError("Non-Manhattan arcs detected in 8Bit_reg{lay}!")

    # 5. Verification: Quick DRC
    print("Running Quick DRC on 8Bit_reg{lay}...")
    n_err, n_warn = run_drc(cell)
    if n_err > 0 or n_warn > 0:
        raise AssertionError("DRC failed with %d errors, %d warnings!" % (n_err, n_warn))

    # 6. Verification: NCC LVS with checkSizes = True
    print("Running NCC against 8Bit_reg{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())
    if not res.match():
        raise AssertionError("NCC LVS comparison failed for 8Bit_reg{lay}!")

    # 7. Save library to disk
    print("Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Successfully saved 8Bit_reg{lay} to %s" % jelib_path)

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

    build_8bit_reg_layout(lib, ep, mocmos, jelib_path)

if __name__ == "__main__":
    main()
