# scripts/inspect_top_exact_ports.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

top_lay = lib.findNodeProto("Top{lay}")

sreg = top_lay.findNode("8Bit_shi@0")
ctrl = top_lay.findNode("Control_@0")
wd   = top_lay.findNode("Write_dr@0")
dff  = top_lay.findNode("D_flipfl@0")

print("sreg.D center:", sreg.findPortInst("D").getCenter())
print("ctrl.CTRL center:", ctrl.findPortInst("CTRL").getCenter())
print("wd.DATA center:", wd.findPortInst("DATA").getCenter())
print("dff.Q center:", dff.findPortInst("Q").getCenter())

# Also check input_buffer layout ports
ib = lib.findNodeProto("input_buffer{lay}")
print("\n--- input_buffer{lay} ports ---")
eit = ib.getExports()
while eit.hasNext():
    e = eit.next()
    p = e.getOriginalPort()
    print("  %s (%s): at (%f, %f), proto: %s" % (
        e.getName(), e.getCharacteristic(), p.getCenter().getX(), p.getCenter().getY(), p.getNodeInst().getProto().getName()))

ob = lib.findNodeProto("output_buffer{lay}")
print("\n--- output_buffer{lay} ports ---")
eit = ob.getExports()
while eit.hasNext():
    e = eit.next()
    p = e.getOriginalPort()
    print("  %s (%s): at (%f, %f), proto: %s" % (
        e.getName(), e.getCharacteristic(), p.getCenter().getX(), p.getCenter().getY(), p.getNodeInst().getProto().getName()))
