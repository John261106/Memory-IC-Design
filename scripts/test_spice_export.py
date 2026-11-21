from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_lay = lib.findNodeProto('Top{lay}')
spi_path = 'sim/Top_layout_test.spi'
Output.writeCell(top_lay, TextUtils.makeURLToFile(spi_path), FileType.SPICE)
print('Exported Top{lay} to %s' % spi_path)

f = open(spi_path, 'r')
lines = [f.readline() for _ in range(40)]
f.close()
for l in lines:
    if 'subckt' in l.lower() or 'top' in l.lower():
        print(l.strip())
