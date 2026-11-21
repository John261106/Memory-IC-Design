from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

pkg = lib.findNodeProto("package{sch}")
for ni in pkg.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else "None"
    vars_list = []
    vit = ni.getVariables()
    while vit.hasNext():
        v = vit.next()
        vars_list.append("%s=%s" % (v.getKey().getName(), v.getObject()))
    print("Node: %s (%s) at (%.1f, %.1f), vars=%s" % (ni.getName(), pname, ni.getTrueCenterX(), ni.getTrueCenterY(), vars_list))
