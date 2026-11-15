# scripts/test_nand3_m1.py
import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library
from com.sun.electric.database import EditingPreferences
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
    print("Quick DRC: %d errors" % n_err)
    if n_err > 0:
        it = logger.getLogs()
        while it.hasNext():
            print("  DRC:", it.next().getMessageString())
    return n_err

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

test_cell = Cell.newInst(lib, "Test_Nand3_M1{lay}")
test_cell.setTechnology(mocmos)

n_proto = mocmos.findNodeProto("N-Transistor")
m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
n_act_wire = mocmos.findArcProto("N-Active")
m1_wire = mocmos.findArcProto("Metal-1")

dx = 4.5
cols = [20.0, 44.0, 68.0]
t_nodes = []
c_left = []
c_right = []

for i, xc in enumerate(cols):
    n = NodeInst.makeInstance(n_proto, ep, Point2D.Double(xc, -14.0), 22.0, 15.0, test_cell, Orientation.R, "nmos@%d" % (i+6))
    n.setPrimitiveNodeSize(6.0, 2.0, ep)
    t_nodes.append(n)

    cl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, -14.0), 17.0, 17.0, test_cell, Orientation.IDENT, "cl_%d" % i)
    cr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, -14.0), 17.0, 17.0, test_cell, Orientation.IDENT, "cr_%d" % i)
    c_left.append(cl)
    c_right.append(cr)

    ArcInst.makeInstance(n_act_wire, ep, cl.getOnlyPortInst(), n.findPortInst("diff-top"))
    ArcInst.makeInstance(n_act_wire, ep, n.findPortInst("diff-bottom"), cr.getOnlyPortInst())

# Connect series on Metal-1: c_right[0] to c_left[1]; c_right[1] to c_left[2]
ArcInst.makeInstance(m1_wire, ep, c_right[0].getOnlyPortInst(), c_left[1].getOnlyPortInst())
ArcInst.makeInstance(m1_wire, ep, c_right[1].getOnlyPortInst(), c_left[2].getOnlyPortInst())

run_drc(test_cell)

test_cell.kill()
