from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.drc import Schematic, DRC
from com.sun.electric.tool.user import ErrorLogger

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
lib = LibraryFiles.readLibrary(None, url, "Memory-IC-Design", FileType.JELIB, False)

cell_sch = lib.findNodeProto("Top{sch}")

# 1. Move CLK branch pins
s1 = cell_sch.findNode("pin_clk_s1")
s2 = cell_sch.findNode("pin_clk_s2")
if s1 and s2:
    s1.move(0.0, -6.0)
    s2.move(0.0, -6.0)
    print("Moved pin_clk_s1 and pin_clk_s2 by dy=-6.0 to Y=56.0")

cnt1 = cell_sch.findNode("pin_clk_cnt1")
cnt2 = cell_sch.findNode("pin_clk_cnt2")
if cnt1 and cnt2:
    cnt1.move(0.0, -4.0)
    cnt2.move(0.0, -4.0)
    print("Moved pin_clk_cnt1 and pin_clk_cnt2 by dy=-4.0 to Y=3.0")

# 2. Adjust WL_driver GND and VDD pins
for col_base in [0, 8]:
    for i in range(7):
        inst_idx = col_base + i
        next_idx = inst_idx + 1
        
        wl_curr = cell_sch.findNode("WL_drive@%d" % inst_idx)
        wl_next = cell_sch.findNode("WL_drive@%d" % next_idx)
        
        cy_curr = wl_curr.getTrueCenterY() # e.g. 85.0
        cy_next = wl_next.getTrueCenterY() # e.g. 65.0
        
        cx = wl_curr.getTrueCenterX()
        
        gnd_y_old = cy_curr - 11.0
        vdd_y_old = cy_next + 11.0
        
        for ni in cell_sch.getNodes():
            if abs(ni.getTrueCenterX() - cx) < 0.1:
                if abs(ni.getTrueCenterY() - gnd_y_old) < 0.1:
                    ni.move(0.0, 2.0)
                    print("Moved WL %d GND pin %s to Y=%.1f" % (inst_idx, ni.getName(), ni.getTrueCenterY()))
                elif abs(ni.getTrueCenterY() - vdd_y_old) < 0.1:
                    ni.move(0.0, -2.0)
                    print("Moved WL %d VDD pin %s to Y=%.1f" % (next_idx, ni.getName(), ni.getTrueCenterY()))

print("\n--- Running Schematic DRC Check on Top{sch} ---")
logger = ErrorLogger()
prefs = DRC.DRCPreferences(False)
sch_drc = Schematic()
sch_drc.doCheck(logger, cell_sch, None, prefs)

print("Schematic DRC Errors:", logger.getNumErrors())
print("Schematic DRC Warnings:", logger.getNumWarnings())
if logger.getNumErrors() > 0:
    for i in range(logger.getNumLogs()):
        print("[%02d] %s" % (i, logger.getLog(i).getMessage()))
else:
    print("TOP{SCH} HAS ZERO DRC ERRORS!")
