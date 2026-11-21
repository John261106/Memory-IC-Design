# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

c = lib.findNodeProto("Not{lay}")
nit = c.getNodes()
while nit.hasNext():
    n = nit.next()
    if "pin@6" in n.getName() or "pin@7" in n.getName() or "well@0" in n.getName() or "pin@2" in n.getName() or "substr@0" in n.getName():
        print("Node: %s (%s) at (%.1f, %.1f) size (%.1f, %.1f)" % (
            n.getName(), n.getProto().getName(), n.getAnchorCenterX(), n.getAnchorCenterY(), n.getXSize(), n.getYSize()))

java.lang.System.exit(0)
