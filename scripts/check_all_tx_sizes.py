# -*- coding: utf-8 -*-
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.hierarchy import View
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

cit = lib.getCells()
while cit.hasNext():
    c = cit.next()
    if c.getView() == View.SCHEMATIC:
        nit = c.getNodes()
        txs = []
        while nit.hasNext():
            n = nit.next()
            if "Transistor" in n.getProto().getName():
                w = None
                vit = n.getVariables()
                while vit.hasNext():
                    v = vit.next()
                    if "width" in v.getKey().getName().lower():
                        w = v.getObject()
                txs.append("%s(W=%s)" % (n.getName(), w))
        if txs:
            print("Cell %s: %s" % (c.getName(), ", ".join(txs[:6])))

java.lang.System.exit(0)
