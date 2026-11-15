from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
import java.awt.geom.Point2D as Point2D

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

cell = Cell.makeInstance(lib, "debug_nand{lay}")
cell.setTechnology(mocmos)

p_proto = mocmos.findNodeProto("P-Transistor")
m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
p_act_wire = mocmos.findArcProto("P-Active")

# Test 2 PMOS with pitch 9.0
p0 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(10.0, 14.0), 22.0, 15.0, cell, Orientation.R, "pmos@0")
p0.setPrimitiveNodeSize(4.0, 2.0, ep)

p1 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(19.0, 14.0), 22.0, 15.0, cell, Orientation.R, "pmos@1")
p1.setPrimitiveNodeSize(4.0, 2.0, ep)

c0 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(5.5, 14.0), 17.0, 17.0, cell, Orientation.IDENT, "con_0")
c1 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(14.5, 14.0), 17.0, 17.0, cell, Orientation.IDENT, "con_1")
c2 = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(23.5, 14.0), 17.0, 17.0, cell, Orientation.IDENT, "con_2")

ArcInst.makeInstance(p_act_wire, ep, c0.getOnlyPortInst(), p0.findPortInst("diff-top"))
ArcInst.makeInstance(p_act_wire, ep, p0.findPortInst("diff-bottom"), c1.getOnlyPortInst())
ArcInst.makeInstance(p_act_wire, ep, c1.getOnlyPortInst(), p1.findPortInst("diff-top"))
ArcInst.makeInstance(p_act_wire, ep, p1.findPortInst("diff-bottom"), c2.getOnlyPortInst())

# Test adding Inverter PMOS W=8 at X2
X2 = 40.0
p2 = NodeInst.makeInstance(p_proto, ep, Point2D.Double(X2, 14.0), 22.0, 15.0, cell, Orientation.R, "pmos@2")
p2.setPrimitiveNodeSize(8.0, 2.0, ep)

c_inv_l = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X2 - 4.5, 14.0), 17.0, 17.0, cell, Orientation.IDENT, "con_inv_l")
c_inv_r = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(X2 + 4.5, 14.0), 17.0, 17.0, cell, Orientation.IDENT, "con_inv_r")

ArcInst.makeInstance(p_act_wire, ep, c_inv_l.getOnlyPortInst(), p2.findPortInst("diff-top"))
ArcInst.makeInstance(p_act_wire, ep, p2.findPortInst("diff-bottom"), c_inv_r.getOnlyPortInst())

# Test NMOS row with pitch 9.0 and X2 = 40.0
n_proto = mocmos.findNodeProto("N-Transistor")
m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
n_act_wire = mocmos.findArcProto("N-Active")

n0 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(10.0, -14.0), 22.0, 15.0, cell, Orientation.R, "nmos@0")
n0.setPrimitiveNodeSize(4.0, 2.0, ep)

n1 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(19.0, -14.0), 22.0, 15.0, cell, Orientation.R, "nmos@1")
n1.setPrimitiveNodeSize(4.0, 2.0, ep)

n2 = NodeInst.makeInstance(n_proto, ep, Point2D.Double(40.0, -14.0), 22.0, 15.0, cell, Orientation.R, "nmos@2")
n2.setPrimitiveNodeSize(4.0, 2.0, ep)

nc0 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(5.5, -14.0), 17.0, 17.0, cell, Orientation.IDENT, "ncon_0")
nc1 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(14.5, -14.0), 17.0, 17.0, cell, Orientation.IDENT, "ncon_1")
nc2 = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(23.5, -14.0), 17.0, 17.0, cell, Orientation.IDENT, "ncon_2")

nc_inv_l = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(35.5, -14.0), 17.0, 17.0, cell, Orientation.IDENT, "ncon_inv_l")
nc_inv_r = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(44.5, -14.0), 17.0, 17.0, cell, Orientation.IDENT, "ncon_inv_r")

ArcInst.makeInstance(n_act_wire, ep, nc0.getOnlyPortInst(), n0.findPortInst("diff-top"))
ArcInst.makeInstance(n_act_wire, ep, n0.findPortInst("diff-bottom"), nc1.getOnlyPortInst())
ArcInst.makeInstance(n_act_wire, ep, nc1.getOnlyPortInst(), n1.findPortInst("diff-top"))
ArcInst.makeInstance(n_act_wire, ep, n1.findPortInst("diff-bottom"), nc2.getOnlyPortInst())

ArcInst.makeInstance(n_act_wire, ep, nc_inv_l.getOnlyPortInst(), n2.findPortInst("diff-top"))
ArcInst.makeInstance(n_act_wire, ep, n2.findPortInst("diff-bottom"), nc_inv_r.getOnlyPortInst())



logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break

print("DRC errors: %d, warnings: %d" % (logger.getNumErrors(), logger.getNumWarnings()))
it = logger.getLogs()
while it.hasNext():
    print("  DRC log:", it.next().getMessageString())
