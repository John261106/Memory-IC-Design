from java.awt.geom import Point2D
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_lay = lib.findNodeProto('Top{lay}')
p_in = lib.findNodeProto('input_buffer{lay}')
p_out = lib.findNodeProto('output_buffer{lay}')

inst_in = NodeInst.makeInstance(p_in, ep, Point2D.Double(-600.0, -860.0), 114.0, 73.0, top_lay, Orientation.IDENT, 'test_in')
inst_out = NodeInst.makeInstance(p_out, ep, Point2D.Double(1000.0, -664.0), 191.0, 101.0, top_lay, Orientation.IDENT, 'test_out')

print('inst_in bounds: %s' % inst_in.getBounds())
pit = inst_in.getPortInsts()
while pit.hasNext():
    p = pit.next()
    print('  in_buf port: %s at (%f, %f)' % (p.getPortProto().getName(), p.getCenter().getX(), p.getCenter().getY()))

print('inst_out bounds: %s' % inst_out.getBounds())
pit = inst_out.getPortInsts()
while pit.hasNext():
    p = pit.next()
    print('  out_buf port: %s at (%f, %f)' % (p.getPortProto().getName(), p.getCenter().getX(), p.getCenter().getY()))

inst_in.kill()
inst_out.kill()
