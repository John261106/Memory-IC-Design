# scripts/test_ncc_hier.py
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

# Let's create a temporary layout cell in memory
lay = Cell.makeInstance(lib, "3Bit_counter{lay}")
sch = lib.findNodeProto("3Bit_counter{sch}")

# Run NCC comparison (should fail right now because lay is empty)
opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(sch, None, lay, None, opts)
print("NCC with empty lay: match = %s" % res.match())
# Delete the temporary lay cell so we don't pollute the library
lay.kill()
