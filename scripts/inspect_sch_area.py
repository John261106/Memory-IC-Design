from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_sch = lib.findNodeProto('Top{sch}')
targets = ['3Bit_cou@0', 'Control_@0', 'in_buf_clk', 'in_buf_ctrl', 'in_buf_addr', 'in_buf_din', 'out_buf_dout', '8Bit_shi@0']
for t in targets:
    n = top_sch.findNode(t)
    if n:
        print('%-15s proto: %-15s bounds: %s' % (t, n.getProto().getName(), n.getBounds()))
        pit = n.getPortInsts()
        while pit.hasNext():
            pi = pit.next()
            print('   port: %-10s at (%f, %f)' % (pi.getPortProto().getName(), pi.getCenter().getX(), pi.getCenter().getY()))
