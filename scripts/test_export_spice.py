from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.database.hierarchy import Cell, EDatabase
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)
EDatabase.setCurrent(lib.getDatabase())

top_lay = lib.findNodeProto('Top{lay}')
spi_path = 'D:/Projects/Memory-IC-Design/spice/Top_layout_extracted.spi'
Output.exportCellCommand(top_lay, None, spi_path, FileType.SPICE, None)
print('Successfully exported SPICE deck to %s' % spi_path)
