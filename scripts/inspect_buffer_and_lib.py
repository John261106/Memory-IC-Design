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

print("=== Library Cells ===")
cit = lib.getCells()
while cit.hasNext():
    c = cit.next()
    print("Cell: %s view=%s" % (c.getName(), c.getView()))

buf_sch = lib.findNodeProto("buffer{sch}")
print("\n=== buffer{sch} Nodes ===")
nit = buf_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    pname = n.getProto().getName()
    if "Transistor" in pname:
        vars_str = []
        vit = n.getVariables()
        while vit.hasNext():
            v = vit.next()
            vars_str.append("%s=%s" % (v.getKey().getName(), v.getObject()))
        print("Node: %s (%s) [%s]" % (n.getName(), pname, ", ".join(vars_str)))

java.lang.System.exit(0)
