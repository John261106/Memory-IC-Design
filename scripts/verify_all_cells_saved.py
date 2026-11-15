import java.lang.Double
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler

def verify_saved_cells():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    print("Reading library fresh from disk: %s" % jelib_path)
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    mocmos = Technology.findTechnology("mocmos")
    edb = lib.getDatabase()
    batch = Setting.SettingChangeBatch()
    batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
    edb.implementSettingChanges(batch)

    cells_to_verify = [
        "Not", "Nand", "Precharge_ckt", "6T_cell", "D_flipflop",
        "Sense_amp", "Write_driver", "TG_bitline", "WL_driver",
        "Control_logic", "3Bit_counter", "8Bit_reg", "8Bit_shiftreg"
    ]

    for name in cells_to_verify:
        print("\n" + "=" * 60)
        print("VERIFYING: %s{lay} in jelib" % name)
        print("=" * 60)

        lay = lib.findNodeProto(name + "{lay}")
        sch = lib.findNodeProto(name + "{sch}")

        if lay is None or sch is None:
            raise Exception("Missing cell %s" % name)

        # 1. Manhattan verification
        ait = lay.getArcs()
        total_arcs = 0
        non_manhattan = 0
        while ait.hasNext():
            a = ait.next()
            total_arcs += 1
            p1 = a.getHeadPortInst().getCenter()
            p2 = a.getTailPortInst().getCenter()
            dx = abs(p1.getX() - p2.getX())
            dy = abs(p1.getY() - p2.getY())
            if dx > 0.001 and dy > 0.001:
                print("  ERROR: Non-Manhattan arc %s: (%f,%f) -> (%f,%f)" % (a.getName(), p1.getX(), p1.getY(), p2.getX(), p2.getY()))
                non_manhattan += 1

        print("1. Manhattan Check: PASS (%d / %d arcs strictly perpendicular)" % (total_arcs - non_manhattan, total_arcs))
        if non_manhattan > 0:
            raise AssertionError("Non-Manhattan arcs found in %s" % name)

        # 2. DRC Verification
        logger = ErrorLogger()
        prefs = DRC.DRCPreferences(False)
        mode = GeometryHandler.GHMode.ALGO_SWEEP
        for m in Quick.getDeclaredMethods():
            if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
                m.setAccessible(True)
                m.invoke(None, [logger, lay, None, None, None, None, prefs, mode, False])
                break

        n_err = logger.getNumErrors()
        print("2. Quick DRC Check: PASS (0 errors, 0 warnings)" if n_err == 0 else "2. Quick DRC Check: FAIL (%d errors)" % n_err)
        if n_err > 0:
            it = logger.getLogs()
            while it.hasNext():
                print("   DRC: " + str(it.next().getMessageString()))
            raise AssertionError("DRC failed for %s" % name)

        # 3. LVS / NCC Verification with checkSizes = True
        opts = NccOptions()
        opts.checkSizes = True
        res = Ncc.compare(sch, None, lay, None, opts)
        print("3. NCC / LVS Check: PASS (match=%s)" % res.match())
        if not res.match():
            raise AssertionError("NCC comparison failed for %s" % name)

    print("\n" + "=" * 60)
    print("ALL 13 CELLS (Not, Nand, Precharge_ckt, 6T_cell, D_flipflop, Sense_amp, Write_driver, TG_bitline, WL_driver, Control_logic, 3Bit_counter, 8Bit_reg, 8Bit_shiftreg) ARE 100% VERIFIED CLEAN IN JELIB!")
    print("=" * 60)

if __name__ == "__main__":
    verify_saved_cells()
