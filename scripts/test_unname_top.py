from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, 'Memory-IC-Design', FileType.JELIB, False)

top_lay = lib.findNodeProto('Top{lay}')
top_sch = lib.findNodeProto('Top{sch}')

nit = top_lay.getNodes()
unnamed_count = 0
while nit.hasNext():
    n = nit.next()
    if n.isUsernamed():
        n.setName('')
        unnamed_count += 1
print('Unnamed %d nodes in Top{lay}' % unnamed_count)

opts = NccOptions()
opts.checkSizes = True
res = Ncc.compare(top_sch, None, top_lay, None, opts)
print('NCC after unnaming: match = %s' % res.match())
