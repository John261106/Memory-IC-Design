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
ait = c.getArcs()
while ait.hasNext():
    a = ait.next()
    h = a.getHeadPortInst().getNodeInst()
    t = a.getTailPortInst().getNodeInst()
    if "Con" in h.getProto().getName() or "Con" in t.getProto().getName():
        print("Arc %s (%s, width=%.1f) connects %s (%s) to %s (%s)" % (
            a.getName(), a.getProto().getName(), a.getLambdaBaseWidth(),
            h.getName(), h.getProto().getName(), t.getName(), t.getProto().getName()))

java.lang.System.exit(0)
