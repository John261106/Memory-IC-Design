# -*- coding: utf-8 -*-
from com.sun.electric.database.hierarchy import View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

cit = lib.getCells()
usernamed_total = 0
while cit.hasNext():
    c = cit.next()
    if c.getView() == View.LAYOUT:
        nit = c.getNodes()
        c_usernamed = 0
        names = []
        while nit.hasNext():
            n = nit.next()
            if n.isUsernamed():
                c_usernamed += 1
                names.append(n.getName())
        if c_usernamed > 0:
            print("Cell %s has %d usernamed nodes: %s" % (c.getName(), c_usernamed, names[:10]))
            usernamed_total += c_usernamed

print("Total usernamed nodes across all layout cells: %d" % usernamed_total)
java.lang.System.exit(0)
