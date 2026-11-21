from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cit = lib.getCells()
cells = []
while cit.hasNext():
    c = cit.next()
    cells.append("%s{%s}" % (c.getName(), c.getView().getAbbreviation()))

for c in sorted(cells):
    print(c)
