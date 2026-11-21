# scripts/inspect_user_buffers.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.tool.user import ErrorLogger
from com.sun.electric.database.geometry import GeometryHandler
from java.util import ArrayList
import java.lang.Double

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

prefs = DRC.DRCPreferences(False)
mode = GeometryHandler.GHMode.ALGO_SWEEP

for cell_name in ["input_buffer", "output_buffer"]:
    print("\n==========================================")
    print("Checking %s" % cell_name)
    print("==========================================")
    sch = lib.findNodeProto(cell_name + "{sch}")
    lay = lib.findNodeProto(cell_name + "{lay}")
    ic  = lib.findNodeProto(cell_name + "{ic}")
    
    print("--- Icon Exports ---")
    eit = ic.getExports()
    while eit.hasNext():
        e = eit.next()
        op = e.getOriginalPort()
        print("  Export: %s (%s) at (%.1f, %.1f)" % (
            e.getName(), e.getCharacteristic(), op.getCenter().getX(), op.getCenter().getY()))
        
    print("--- Layout Exports & Bounds ---")
    # compute actual bounding box of nodes
    min_x, max_x = 1e9, -1e9
    min_y, max_y = 1e9, -1e9
    nit = lay.getNodes()
    while nit.hasNext():
        n = nit.next()
        b = n.getBounds()
        if b:
            min_x = min(min_x, b.getX())
            max_x = max(max_x, b.getX() + b.getWidth())
            min_y = min(min_y, b.getY())
            max_y = max(max_y, b.getY() + b.getHeight())
    print("  Actual Node bounds: X in [%.1f, %.1f] (w=%.1f), Y in [%.1f, %.1f] (h=%.1f)" % (
        min_x, max_x, max_x - min_x, min_y, max_y, max_y - min_y))
    
    eit = lay.getExports()
    while eit.hasNext():
        e = eit.next()
        op = e.getOriginalPort()
        print("  Export: %s (%s) at (%.1f, %.1f)" % (
            e.getName(), e.getCharacteristic(), op.getCenter().getX(), op.getCenter().getY()))
        
    # DRC
    logger = ErrorLogger()
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, lay, None, None, None, None, prefs, mode, False])
            break
    print("  Quick DRC: %d errors, %d warnings" % (logger.getNumErrors(), logger.getNumWarnings()))
    
    errs = ArrayList()
    DRC.checkDRCHierarchically(prefs, lay, errs, None, mode, False)
    print("  Hierarchical DRC: %d errors" % len(errs))
    
    # NCC
    opts = NccOptions()
    opts.checkSizes = True
    ncc_res = Ncc.compare(sch, None, lay, None, opts)
    print("  NCC (checkSizes=True): match = %s" % ncc_res.match())
