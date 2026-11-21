# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Export
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io.output import Output
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
import java.lang.System

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

# Let's import build_buffer from build_buffer_layout
import sys
sys.path.append("scripts")
import build_buffer_layout

mocmos = Technology.findTechnology("mocmos")
cell = build_buffer_layout.build_buffer(lib, ep, mocmos)

logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP
for m in Quick.getDeclaredMethods():
    if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
        m.setAccessible(True)
        m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
        break

print("\n=== Detailed DRC Errors (%d) ===" % logger.getNumErrors())
it = logger.getLogs()
while it.hasNext():
    log = it.next()
    print("Error: %s" % log.getMessageString())
    for obj in log.getObjectList():
        if isinstance(obj, NodeInst):
            print("   Node: %s (%s) at (%.1f, %.1f) size (%.1f, %.1f)" % (
                obj.getName(), obj.getProto().getName(),
                obj.getAnchorCenterX(), obj.getAnchorCenterY(),
                obj.getXSize(), obj.getYSize()))
        elif isinstance(obj, ArcInst):
            print("   Arc: %s (%s) from (%.1f, %.1f) to (%.1f, %.1f)" % (
                obj.getName(), obj.getProto().getName(),
                obj.getHeadPortInst().getCenter().getX(), obj.getHeadPortInst().getCenter().getY(),
                obj.getTailPortInst().getCenter().getX(), obj.getTailPortInst().getCenter().getY()))

cell.kill()
java.lang.System.exit(0)
