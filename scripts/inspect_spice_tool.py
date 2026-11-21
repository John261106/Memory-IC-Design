from com.sun.electric.tool.simulation import Spice
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

for m in Spice.getDeclaredMethods():
    print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
