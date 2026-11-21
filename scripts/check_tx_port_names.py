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
nit = buf_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    if n.getName() == "pmos@5":
        pit = n.getPortInsts()
        while pit.hasNext():
            p = pit.next()
            print("Port: %s" % p.getPortProto().getName())
        break

java.lang.System.exit(0)
