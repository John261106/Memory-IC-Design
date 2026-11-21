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
print("=== buffer{sch} Nodes ===")
nit = buf_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    vars_str = []
    vit = n.getVariables()
    while vit.hasNext():
        v = vit.next()
        vars_str.append("%s=%s" % (v.getKey().getName(), v.getObject()))
    print("Node: %s, proto=%s, vars=[%s]" % (n.getName(), n.getProto().getName(), ", ".join(vars_str)))

print("\n=== buffer{sch} Exports ===")
eit = buf_sch.getExports()
while eit.hasNext():
    e = eit.next()
    print("Export: %s -> port %s of %s" % (e.getName(), e.getPortInst().getName(), e.getPortInst().getNodeInst().getName()))

pkg_sch = lib.findNodeProto("package{sch}")
print("\n=== package{sch} Nodes ===")
nit = pkg_sch.getNodes()
while nit.hasNext():
    n = nit.next()
    print("Node: %s, proto=%s" % (n.getName(), n.getProto().getName()))

print("\n=== package{sch} Exports ===")
eit = pkg_sch.getExports()
while eit.hasNext():
    e = eit.next()
    print("Export: %s -> port %s of %s" % (e.getName(), e.getPortInst().getName(), e.getPortInst().getNodeInst().getName()))

java.lang.System.exit(0)
