# -*- coding: utf-8 -*-
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

buf_ic = lib.findNodeProto("buffer{ic}")
print("buffer{ic}:", buf_ic)
if buf_ic:
    eit = buf_ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("  Export in buffer{ic}:", e.getName())

pkg_ic = lib.findNodeProto("package{ic}")
print("package{ic}:", pkg_ic)
if pkg_ic:
    eit = pkg_ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("  Export in package{ic}:", e.getName())

top_ic = lib.findNodeProto("Top{ic}")
print("Top{ic}:", top_ic)
if top_ic:
    eit = top_ic.getExports()
    while eit.hasNext():
        e = eit.next()
        print("  Export in Top{ic}:", e.getName())

java.lang.System.exit(0)
