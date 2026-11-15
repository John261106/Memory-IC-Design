# scripts/test_strap_placement.py
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
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger

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
                print("  DRC:", msg)
    return n_err, n_warn

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

test_cell = Cell.newInst(lib, "Test_Straps{lay}")
test_cell.setTechnology(mocmos)

dff_lay = lib.findNodeProto("D_flipflop{lay}")
m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
m1_pin = mocmos.findNodeProto("Metal-1-Pin")
m1_wire = mocmos.findArcProto("Metal-1")
m2_wire = mocmos.findArcProto("Metal-2")

# Place dff0 at (0, 86)
dff0 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, 86.0), 287.0, 56.0, test_cell, Orientation.IDENT, "dff0")

# Straps at X = -30.0 (CLK), X = -38.0 (VDD), X = -46.0 (GND)
via_clk = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, 86.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_clk")
pin_clk = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(-14.0, 86.0), 3.0, 3.0, test_cell, Orientation.IDENT, "pin_clk")
ArcInst.makeInstance(m1_wire, ep, dff0.findPortInst("CLK"), via_clk.getOnlyPortInst())

via_vdd = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, 114.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_vdd")
ArcInst.makeInstance(m1_wire, ep, dff0.findPortInst("VDD"), via_vdd.getOnlyPortInst())

via_gnd = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, 58.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_gnd")
ArcInst.makeInstance(m1_wire, ep, dff0.findPortInst("GND"), via_gnd.getOnlyPortInst())

run_drc(test_cell)

test_cell.kill()
