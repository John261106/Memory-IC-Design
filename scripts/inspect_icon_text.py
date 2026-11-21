from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

for ni in cell_sch.getNodes():
    proto = ni.getProto()
    pname = proto.getName() if proto else ""
    if pname == "3Bit_counter":
        td = ni.getTextDescriptor(NodeInst.NODE_NAME)
        print("3Bit_counter NodeInst name=%s, td=%s" % (ni.getName(), td))
        # check proto icon exports/artwork
        icon_cell = proto.getCell()
        print("Icon cell:", icon_cell)
        if icon_cell:
            for n in icon_cell.getNodes():
                print("  icon node:", n.getProto().getName() if n.getProto() else None, n.getName())
                vit = n.getVariables()
                while vit.hasNext():
                    v = vit.next()
                    print("    var:", v.getKey().getName(), v.getObject())
        break
