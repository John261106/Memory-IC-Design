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

top_sch = lib.findNodeProto("Top{sch}")
print("=== Top{sch} Exports Nodes ===")
eit = top_sch.getExports()
while eit.hasNext():
    e = eit.next()
    pi = e.getOriginalPort()
    ni = pi.getNodeInst()
    print("Export %s: node %s (proto=%s) at (%.1f, %.1f)" % (
        e.getName(), ni.getName(), ni.getProto().getName(), ni.getAnchorCenterX(), ni.getAnchorCenterY()))

java.lang.System.exit(0)
