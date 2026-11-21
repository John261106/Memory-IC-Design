from com.sun.electric.tool.io.output import Spice
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, EDatabase
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
import java.lang.Double

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

EDatabase.setClientDatabase(lib.getDatabase())
EDatabase.setServerDatabase(lib.getDatabase())

top_lay = lib.findNodeProto('Top{lay}')

PrefClass = None
for c in Spice.getDeclaredClasses():
    if 'SpicePreferences' in c.getSimpleName():
        PrefClass = c

prefs = PrefClass(False, True)
spi_path = 'D:/Projects/Memory-IC-Design/spice/test_scale90.spi'
prefs.doOutput(top_lay, None, spi_path)

f = open(spi_path, 'r')
for line in f:
    if line.startswith('Mnmos@5'):
        print("Found line:", line.strip())
        break
f.close()
