# scripts/test_nand3_drc.py
import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
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

test_cell = Cell.newInst(lib, "Test_Nand3{lay}")
test_cell.setTechnology(mocmos)

n_proto = mocmos.findNodeProto("N-Transistor")
m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
n_act_wire = mocmos.findArcProto("N-Active")

# 3 NMOS in series: X = 20, 29, 38 (pitch 9), W = 6.0
n6 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(20.0, -14.0), 22.0, 15.0, test_cell, Orientation.R, "nmos@6")
n6.setPrimitiveNodeSize(6.0, 2.0, ep)
print("n6 bounds: " + str(n6.getBounds()))
print("n6 size: (%f, %f)" % (n6.getXSize(), n6.getYSize()))
n7 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(29.0, -14.0), 22.0, 15.0, test_cell, Orientation.R, "nmos@7")
n7.setPrimitiveNodeSize(6.0, 2.0, ep)
n8 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(38.0, -14.0), 22.0, 15.0, test_cell, Orientation.R, "nmos@8")
n8.setPrimitiveNodeSize(6.0, 2.0, ep)

# Left contact
ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(20.0 - 4.5, -14.0), 17.0, 17.0, test_cell, Orientation.IDENT, "ncl")
ArcInst.makeInstance(n_act_wire, ep, ncl.getOnlyPortInst(), n6.findPortInst("diff-top"))

# Shared series contacts with contact nodes
ncm1 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(24.5, -14.0), 17.0, 17.0, test_cell, Orientation.R, "ncm1")
ncm1.setPrimitiveNodeSize(6.0, 4.0, ep)
ArcInst.makeInstance(n_act_wire, ep, n6.findPortInst("diff-bottom"), ncm1.getOnlyPortInst())
ArcInst.makeInstance(n_act_wire, ep, ncm1.getOnlyPortInst(), n7.findPortInst("diff-top"))

ncm2 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(33.5, -14.0), 17.0, 17.0, test_cell, Orientation.R, "ncm2")
ncm2.setPrimitiveNodeSize(6.0, 4.0, ep)
ArcInst.makeInstance(n_act_wire, ep, n7.findPortInst("diff-bottom"), ncm2.getOnlyPortInst())
ArcInst.makeInstance(n_act_wire, ep, ncm2.getOnlyPortInst(), n8.findPortInst("diff-top"))

# Right contact
ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(38.0 + 4.5, -14.0), 17.0, 17.0, test_cell, Orientation.IDENT, "ncr")
ArcInst.makeInstance(n_act_wire, ep, n8.findPortInst("diff-bottom"), ncr.getOnlyPortInst())

run_drc(test_cell)

test_cell.kill()
