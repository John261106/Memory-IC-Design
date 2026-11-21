from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, 'Memory-IC-Design', FileType.JELIB, False)

top_pkg = lib.findNodeProto('Top_package{sch}')
for ai in top_pkg.getArcs():
    h = ai.getHeadPortInst().getNodeInst().getName()
    t = ai.getTailPortInst().getNodeInst().getName()
    if 'pin@22' in [h, t] or 'package@3' in [h, t] or 'pin@17' in [h, t] or 'pin@18' in [h, t]:
        print('Arc:', h, '->', t, 'arc name:', ai.getName())
