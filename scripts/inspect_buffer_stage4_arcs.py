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
ait = buf_sch.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst().getNodeInst()
    t = a.getTailPortInst().getNodeInst()
    hp = a.getHeadPortInst().getPortProto().getName()
    tp = a.getTailPortInst().getPortProto().getName()
    if h.getName() in ["pmos@5", "nmos@6"] or t.getName() in ["pmos@5", "nmos@6"]:
        print("Arc: %s (%s) from %s.%s to %s.%s" % (a.getName(), a.getProto().getName(), h.getName(), hp, t.getName(), tp))

java.lang.System.exit(0)
