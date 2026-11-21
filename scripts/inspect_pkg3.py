from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

jelib_path = 'D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib'
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, 'Memory-IC-Design', FileType.JELIB, False)

top_pkg = lib.findNodeProto('Top_package{sch}')
pkg3 = top_pkg.findNode('package@3')
pit = pkg3.getPortInsts()
while pit.hasNext():
    pi = pit.next()
    print('Port: %s' % pi.getPortProto().getName())
    ait = pi.getConnectedArcs()
    while ait.hasNext():
        ai = ait.next()
        other = ai.getHeadPortInst() if ai.getTailPortInst() == pi else ai.getTailPortInst()
        print('   arc to: %s [%s], net: %s' % (other.getNodeInst().getName(), other.getPortProto().getName(), ai.getNet().getName() if ai.getNet() else 'none'))
