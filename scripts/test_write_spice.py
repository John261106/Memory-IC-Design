from com.sun.electric.tool.io.output import Spice
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
out_path = 'D:/Projects/Memory-IC-Design/spice/Top_layout_extracted.spi'
Spice.writeDeck(top_lay, out_path, None)
print('Successfully exported SPICE deck to %s' % out_path)
