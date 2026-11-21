# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from java.awt.geom import Point2D
import java.lang.Double
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

buf_sch = lib.findNodeProto("buffer{sch}")
sch_tech = Technology.findTechnology("schematic")
wire_sch = sch_tech.findArcProto("wire")
tx_proto = sch_tech.findNodeProto("Transistor")

pmos5 = buf_sch.findNode("pmos@5")
nmos6 = buf_sch.findNode("nmos@6")
pin_g_p = buf_sch.findNode("pin@28")
pin_g_n = buf_sch.findNode("pin@29")
pin_vdd = buf_sch.findNode("pin@38")
pin_gnd = buf_sch.findNode("pin@39")
pin_out = buf_sch.findNode("pin@46")

print("Found existing nodes:", pmos5, nmos6, pin_g_p, pin_g_n, pin_vdd, pin_gnd, pin_out)

# 1. Update pmos@5 to W=16.0
vit = pmos5.getVariables()
while vit.hasNext():
    v = vit.next()
    if "width" in v.getKey().getName().lower():
        pmos5.addVar(v.withObject(java.lang.Double(16.0)))
        print("Updated pmos@5 to W=16.0")

# 2. Update nmos@6 to W=8.0
vit = nmos6.getVariables()
while vit.hasNext():
    v = vit.next()
    if "width" in v.getKey().getName().lower():
        nmos6.addVar(v.withObject(java.lang.Double(8.0)))
        print("Updated nmos@6 to W=8.0")

# 3. Create pmos@6 (W=16.0) and nmos@7 (W=8.0)
pmos6 = NodeInst.makeInstance(tx_proto, ep, Point2D.Double(pmos5.getAnchorCenterX() + 15.0, pmos5.getAnchorCenterY()),
                              pmos5.getXSize(), pmos5.getYSize(), buf_sch, Orientation.IDENT, "pmos@6")
pmos6.copyVarsFrom(pmos5)

nmos7 = NodeInst.makeInstance(tx_proto, ep, Point2D.Double(nmos6.getAnchorCenterX() + 15.0, nmos6.getAnchorCenterY()),
                              nmos6.getXSize(), nmos6.getYSize(), buf_sch, Orientation.IDENT, "nmos@7")
nmos7.copyVarsFrom(nmos6)

# 4. Wire pmos@6
ArcInst.makeInstance(wire_sch, ep, pin_g_p.getOnlyPortInst(), pmos6.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, pmos6.findPortInst("d"), pin_vdd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, pmos6.findPortInst("s"), pin_out.getOnlyPortInst())

# 5. Wire nmos@7
ArcInst.makeInstance(wire_sch, ep, pin_g_n.getOnlyPortInst(), nmos7.findPortInst("g"))
ArcInst.makeInstance(wire_sch, ep, nmos7.findPortInst("s"), pin_gnd.getOnlyPortInst())
ArcInst.makeInstance(wire_sch, ep, nmos7.findPortInst("d"), pin_out.getOnlyPortInst())

print("pmos@6 and nmos@7 successfully wired in parallel!")

java.lang.System.exit(0)
