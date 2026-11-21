from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database.topology import NodeInst, ArcInst

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# Let's inspect nodes in Top{sch} around the Sense_amp, Not, D_flipflop region (X ~ 290 to 350)
print("--- Nodes in region X in [280, 360], Y in [40, 70] ---")
for ni in cell_sch.getNodes():
    cx = ni.getTrueCenterX()
    cy = ni.getTrueCenterY()
    if 280 <= cx <= 360 and 40 <= cy <= 70:
        print("Node: proto=%s, name=%s, pos=(%s, %s)" % (ni.getProto().getName() if ni.getProto() else None, ni.getName(), cx, cy))
        vit = ni.getVariables()
        while vit.hasNext():
            v = vit.next()
            print("   var: %s = %s (display=%s)" % (v.getKey().getName(), v.getObject(), v.isDisplayed()))

print("--- Arcs in region X in [280, 360], Y in [40, 70] ---")
for ai in cell_sch.getArcs():
    hl = ai.getHeadLocation()
    tl = ai.getTailLocation()
    if (280 <= hl.getX() <= 360 and 40 <= hl.getY() <= 70) or (280 <= tl.getX() <= 360 and 40 <= tl.getY() <= 70):
        print("Arc: name=%s, head=%s, tail=%s" % (ai.getName(), hl, tl))
        vit = ai.getVariables()
        while vit.hasNext():
            v = vit.next()
            print("   var: %s = %s (display=%s)" % (v.getKey().getName(), v.getObject(), v.isDisplayed()))
