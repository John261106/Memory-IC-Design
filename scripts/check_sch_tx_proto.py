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

buf_sch = lib.findNodeProto("buffer{sch}")
for name in ["pmos@5", "nmos@6"]:
    n = buf_sch.findNode(name)
    if n:
        print("Node: %s proto=%s (tech=%s)" % (n.getName(), n.getProto().getName(), n.getProto().getTechnology().getName()))
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            print("  Var: %s = %s" % (v.getKey().getName(), v.getObject()))

java.lang.System.exit(0)
