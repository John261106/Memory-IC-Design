from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

top_lay = lib.findNodeProto("Top{lay}")
for ni in top_lay.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else "Primitive"
    if "buffer" in pname:
        print("Buffer in Top{lay}:", ni.getName(), pname, ni.getTrueCenterX(), ni.getTrueCenterY())
