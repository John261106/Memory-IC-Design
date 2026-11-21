# -*- coding: utf-8 -*-
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

pkg_ic = lib.findNodeProto("package{ic}")
print("=== package{ic} ===")
nit = pkg_ic.getNodes()
while nit.hasNext():
    n = nit.next()
    print("Node: %s (%s) at (%.1f, %.1f) size (%.1f, %.1f)" % (
        n.getName(), n.getProto().getName(), n.getAnchorCenterX(), n.getAnchorCenterY(), n.getXSize(), n.getYSize()))

ait = pkg_ic.getArcs()
while ait.hasNext():
    a = ait.next()
    print("Arc: %s (%s) from %s to %s" % (
        a.getName(), a.getProto().getName(),
        a.getHeadPortInst().getNodeInst().getName(),
        a.getTailPortInst().getNodeInst().getName()))

eit = pkg_ic.getExports()
while eit.hasNext():
    e = eit.next()
    print("Export: %s on node %s" % (
        e.getName(), e.getOriginalPort().getNodeInst().getName()))

java.lang.System.exit(0)
