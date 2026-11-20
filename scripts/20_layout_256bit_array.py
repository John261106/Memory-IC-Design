# scripts/20_layout_256bit_array.py
# Hierarchical Physical Layout Generator for 256bit_array{lay} (16x16 6T SRAM Bitcell Matrix)
# Technology: MOSIS SCMOS_SUBM (mocmos), lambda = 90 nm
#
# Architecture:
#   - 16 rows x 16 cols = 256 instances of compacted 6T_cell{lay}
#   - Pitch-matched horizontal Metal-1 rails for WL0..WL15, VDD, and GND
#   - Vertical Metal-2 bitlines BL0..BL15 and BLB0..BLB15
#   - Vertical Metal-2 VDD & GND power grid straps on the left edge
#   - 50 exports matching 256bit_array{sch}:
#       BL0..BL15, BLB0..BLB15, WL0..WL15, VDD, GND
#
# Verification:
#   1. 100% Manhattan perpendicular routing (0 non-Manhattan arcs)
#   2. 0 Quick DRC errors & warnings (ALGO_SWEEP)
#   3. 100% NCC / LVS match with checkSizes = True against 256bit_array{sch}

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
                if idx > 20:
                    print("  ... (more DRC messages truncated)")
                    break
    return n_err, n_warn

def build_256bit_array_layout(lib, ep, mocmos, jelib_path):
    print("\n" + "=" * 60)
    print("Building Hierarchical Layout: 256bit_array{lay}...")
    print("=" * 60)

    cell = lib.findNodeProto("256bit_array{lay}")
    if cell is None:
        cell = Cell.newInst(lib, "256bit_array{lay}")
    else:
        clear_cell_contents(cell)
    cell.setTechnology(mocmos)

    sch = lib.findNodeProto("256bit_array{sch}")
    c6t = lib.findNodeProto("6T_cell{lay}")
    if sch is None or c6t is None:
        raise Exception("Missing 256bit_array{sch} or 6T_cell{lay}!")

    m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
    m1_pin    = mocmos.findNodeProto("Metal-1-Pin")
    m1_wire   = mocmos.findArcProto("Metal-1")
    m2_wire   = mocmos.findArcProto("Metal-2")

    ROWS = 16
    COLS = 16
    DX = 51.0   # 6T_cell well width = 45.0 -> 6.0 lambda well spacing (rule 1.3 Mosis)
    DY = 81.0   # 6T_cell bounds height = 80.5 -> 0.5 lambda clearance between N-Well and P-Well (rule 1.4 Mosis)

    X_VDD_STRAP = -32.0
    X_GND_STRAP = -40.0
    X_WL_PORT   = -46.0

    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    vdd_vias = []
    gnd_vias = []

    # 1. Instantiate 16x16 6T_cell matrix and connect horizontal row rails
    for r in range(ROWS):
        yr = r * DY
        for c in range(COLS):
            xc = c * DX
            inst = NodeInst.makeInstance(c6t, ep, Point2D.Double(xc, yr), 57.0, 80.5, cell, Orientation.IDENT, "6T_cell@%d" % (r * COLS + c))
            grid[r][c] = inst

        # Horizontal Metal-1 rails across all 16 columns in row r
        for c in range(COLS - 1):
            make_manhattan_arc(m1_wire, ep, grid[r][c].findPortInst("WL"),  grid[r][c+1].findPortInst("WL"))
            make_manhattan_arc(m1_wire, ep, grid[r][c].findPortInst("VDD"), grid[r][c+1].findPortInst("VDD"))
            make_manhattan_arc(m1_wire, ep, grid[r][c].findPortInst("GND"), grid[r][c+1].findPortInst("GND"))

        # Left power strap taps on Metal-1 -> Metal-2
        vv = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_VDD_STRAP, yr + 44.0), 5.0, 5.0, cell, Orientation.IDENT, "v_vdd_%d" % r)
        make_manhattan_arc(m1_wire, ep, vv.getOnlyPortInst(), grid[r][0].findPortInst("VDD"))
        vdd_vias.append(vv)

        vg = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(X_GND_STRAP, yr - 14.0), 5.0, 5.0, cell, Orientation.IDENT, "v_gnd_%d" % r)
        make_manhattan_arc(m1_wire, ep, vg.getOnlyPortInst(), grid[r][0].findPortInst("GND"))
        gnd_vias.append(vg)

        # Export WLr on Metal-1 at X_WL_PORT (passes cleanly underneath VDD/GND Metal-2 straps)
        pwl = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_WL_PORT, yr - 24.0), 3.0, 3.0, cell, Orientation.IDENT, "p_wl_%d" % r)
        make_manhattan_arc(m1_wire, ep, pwl.getOnlyPortInst(), grid[r][0].findPortInst("WL"))
        Export.newInst(cell, pwl.getOnlyPortInst(), "WL%d" % r, PortCharacteristic.IN)

    # 2. Connect vertical Metal-2 power straps on left edge
    for r in range(ROWS - 1):
        make_manhattan_arc(m2_wire, ep, vdd_vias[r].getOnlyPortInst(), vdd_vias[r+1].getOnlyPortInst())
        make_manhattan_arc(m2_wire, ep, gnd_vias[r].getOnlyPortInst(), gnd_vias[r+1].getOnlyPortInst())

    Export.newInst(cell, vdd_vias[0].getOnlyPortInst(), "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, gnd_vias[0].getOnlyPortInst(), "GND", PortCharacteristic.GND)

    # 3. Connect vertical Metal-2 bitlines (BLc, BLBc) across all 16 rows and export at bottom/top
    for c in range(COLS):
        for r in range(ROWS - 1):
            make_manhattan_arc(m2_wire, ep, grid[r][c].findPortInst("BIT"),  grid[r+1][c].findPortInst("BIT"))
            make_manhattan_arc(m2_wire, ep, grid[r][c].findPortInst("BITB"), grid[r+1][c].findPortInst("BITB"))

        # Export BLc and BLBc at row 0 (bottom) for clean peripheral attachment (Precharge / TG_bitline)
        Export.newInst(cell, grid[0][c].findPortInst("BIT"),  "BL%d" % c,  PortCharacteristic.BIDIR)
        Export.newInst(cell, grid[0][c].findPortInst("BITB"), "BLB%d" % c, PortCharacteristic.BIDIR)

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
        raise AssertionError("Non-Manhattan arcs detected in 256bit_array{lay}!")

    # 5. Verification: Quick DRC
    print("Running Quick DRC on 256bit_array{lay}...")
    n_err, n_warn = run_drc(cell)
    if n_err > 0 or n_warn > 0:
        raise AssertionError("DRC failed with %d errors, %d warnings!" % (n_err, n_warn))

    # 6. Verification: NCC LVS with checkSizes = True
    print("Running NCC against 256bit_array{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())
    if not res.match():
        raise AssertionError("NCC LVS comparison failed for 256bit_array{lay}!")

    # 7. Save library to disk
    print("Saving library to %s..." % jelib_path)
    Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
    print("Successfully saved 256bit_array{lay} to %s" % jelib_path)

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

    build_256bit_array_layout(lib, ep, mocmos, jelib_path)

if __name__ == "__main__":
    main()
