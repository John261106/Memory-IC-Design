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

top_lay = lib.findNodeProto('Top{lay}')
sreg = top_lay.findNode('8Bit_shi@0')
ctrl = top_lay.findNode('Control_@0')
wd = top_lay.findNode('Write_dr@0')

print('sreg.D: (%f, %f), proto: %s' % (sreg.findPortInst('D').getCenter().getX(), sreg.findPortInst('D').getCenter().getY(), sreg.findPortInst('D').getPortProto().getName()))
print('ctrl.CTRL: (%f, %f), proto: %s' % (ctrl.findPortInst('CTRL').getCenter().getX(), ctrl.findPortInst('CTRL').getCenter().getY(), ctrl.findPortInst('CTRL').getPortProto().getName()))
print('wd.DATA: (%f, %f), proto: %s' % (wd.findPortInst('DATA').getCenter().getX(), wd.findPortInst('DATA').getCenter().getY(), wd.findPortInst('DATA').getPortProto().getName()))
