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

not_ic = lib.findNodeProto("Not{ic}")
if not_ic:
    print("=== Not{ic} ===")
    nit = not_ic.getNodes()
    while nit.hasNext():
        n = nit.next()
        print("Node: %s (%s) at (%.1f, %.1f) size (%.1f, %.1f)" % (
            n.getName(), n.getProto().getName(), n.getAnchorCenterX(), n.getAnchorCenterY(), n.getXSize(), n.getYSize()))
    ait = not_ic.getArcs()
    while ait.hasNext():
        a = ait.next()
        print("Arc: %s (%s)" % (a.getName(), a.getProto().getName()))
    eit = not_ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("Export: %s on port %s" % (e.getName(), e.getOriginalPort().getName()))

java.lang.System.exit(0)
