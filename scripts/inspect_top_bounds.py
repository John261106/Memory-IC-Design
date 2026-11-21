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
for name in ['8Bit_shi@0', '3Bit_cou@0', 'Control_@0', 'Decoder@0', 'Decoder@1', 'Sense_am@0', 'Write_dr@0', 'Not@0', 'D_flipfl@0']:
    node = top_lay.findNode(name)
    if node:
        print('%-15s bounds: %s' % (name, node.getBounds()))
