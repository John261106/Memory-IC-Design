# scripts/test_counter_builder.py
import java.lang.Double
from java.awt.geom import Point2D

from com.sun.electric.technology import Technology
from com.sun.electric.database.topology import NodeInst, ArcInst
from com.sun.electric.database.hierarchy import Cell, Library, Export, View
from com.sun.electric.database.prototype import PortCharacteristic
from com.sun.electric.database import EditingPreferences
from com.sun.electric.database.text import Setting
from com.sun.electric.util.math import Orientation
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger

def make_manhattan_arc(arc_proto, ep, port1, port2):
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    return ArcInst.makeInstance(arc_proto, ep, port1, port2)

def run_drc(cell):
    logger = ErrorLogger()
    prefs = DRC.DRCPreferences(False)
    mode = GeometryHandler.GHMode.ALGO_SWEEP
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
            break
    n_err = logger.getNumErrors()
    n_warn = logger.getNumWarnings()
    print("Quick DRC: %d errors, %d warnings" % (n_err, n_warn))
    if n_err > 0 or n_warn > 0:
        it = logger.getLogs()
        seen = set()
        while it.hasNext():
            msg = it.next().getMessageString()
            if msg not in seen:
                seen.add(msg)
                print("  DRC:", msg)
    return n_err, n_warn

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")

edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

test_cell = Cell.newInst(lib, "Test_Counter_Full{lay}")
test_cell.setTechnology(mocmos)

sch = lib.findNodeProto("3Bit_counter{sch}")
dff_lay = lib.findNodeProto("D_flipflop{lay}")

# Prototypes
n_proto = mocmos.findNodeProto("N-Transistor")
p_proto = mocmos.findNodeProto("P-Transistor")
m1_n_con = mocmos.findNodeProto("Metal-1-N-Active-Con")
m1_p_con = mocmos.findNodeProto("Metal-1-P-Active-Con")
m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
m1_m2_con = mocmos.findNodeProto("Metal-1-Metal-2-Con")
m1_n_well_con = mocmos.findNodeProto("Metal-1-N-Well-Con")
m1_p_well_con = mocmos.findNodeProto("Metal-1-P-Well-Con")

n_well_node = mocmos.findNodeProto("N-Well-Node")
p_well_node = mocmos.findNodeProto("P-Well-Node")

m1_pin = mocmos.findNodeProto("Metal-1-Pin")
m2_pin = mocmos.findNodeProto("Metal-2-Pin")
poly_pin = mocmos.findNodeProto("Polysilicon-1-Pin")

m1_wire = mocmos.findArcProto("Metal-1")
m2_wire = mocmos.findArcProto("Metal-2")
poly_wire = mocmos.findArcProto("Polysilicon-1")
n_act_wire = mocmos.findArcProto("N-Active")
p_act_wire = mocmos.findArcProto("P-Active")

# Geometry parameters
DY = 86.0  # Row pitch
Y_ROW0 = 0.0
Y_ROW1 = DY        # 86.0
Y_ROW2 = 2.0 * DY  # 172.0
Y_ROW3 = 3.0 * DY  # 258.0

Y_VDD = 28.0
Y_GND = -28.0
Y_P = 14.0
Y_N = -14.0
dx = 4.5

# 1. Instantiate the 3 D Flip-Flops (Rows 1, 2, 3)
dff0 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW1), 287.0, 56.0, test_cell, Orientation.IDENT, "D_flipfl@3")
dff1 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW2), 287.0, 56.0, test_cell, Orientation.IDENT, "D_flipfl@4")
dff2 = NodeInst.makeInstance(dff_lay, ep, Point2D.Double(0.0, Y_ROW3), 287.0, 56.0, test_cell, Orientation.IDENT, "D_flipfl@5")

# Power grid straps at X = -38.0 (VDD), X = -46.0 (GND), CLK at X = -30.0
via_v0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_VDD), 5.0, 5.0, test_cell, Orientation.IDENT, "via_v0")
via_v1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW1 + 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_v1")
via_v2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW2 + 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_v2")
via_v3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-38.0, Y_ROW3 + 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_v3")

make_manhattan_arc(m2_wire, ep, via_v0.getOnlyPortInst(), via_v1.getOnlyPortInst())
make_manhattan_arc(m2_wire, ep, via_v1.getOnlyPortInst(), via_v2.getOnlyPortInst())
make_manhattan_arc(m2_wire, ep, via_v2.getOnlyPortInst(), via_v3.getOnlyPortInst())

make_manhattan_arc(m1_wire, ep, dff0.findPortInst("VDD"), via_v1.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff1.findPortInst("VDD"), via_v2.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff2.findPortInst("VDD"), via_v3.getOnlyPortInst())
Export.newInst(test_cell, via_v0.getOnlyPortInst(), "VDD", PortCharacteristic.PWR)

via_g0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_GND), 5.0, 5.0, test_cell, Orientation.IDENT, "via_g0")
via_g1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW1 - 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_g1")
via_g2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW2 - 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_g2")
via_g3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-46.0, Y_ROW3 - 28.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_g3")

make_manhattan_arc(m2_wire, ep, via_g0.getOnlyPortInst(), via_g1.getOnlyPortInst())
make_manhattan_arc(m2_wire, ep, via_g1.getOnlyPortInst(), via_g2.getOnlyPortInst())
make_manhattan_arc(m2_wire, ep, via_g2.getOnlyPortInst(), via_g3.getOnlyPortInst())

make_manhattan_arc(m1_wire, ep, dff0.findPortInst("GND"), via_g1.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff1.findPortInst("GND"), via_g2.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff2.findPortInst("GND"), via_g3.getOnlyPortInst())
Export.newInst(test_cell, via_g0.getOnlyPortInst(), "GND", PortCharacteristic.GND)

# Clock network at X = -30.0
via_clk1 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW1), 5.0, 5.0, test_cell, Orientation.IDENT, "via_clk1")
via_clk2 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW2), 5.0, 5.0, test_cell, Orientation.IDENT, "via_clk2")
via_clk3 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-30.0, Y_ROW3), 5.0, 5.0, test_cell, Orientation.IDENT, "via_clk3")

make_manhattan_arc(m1_wire, ep, dff0.findPortInst("CLK"), via_clk1.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff1.findPortInst("CLK"), via_clk2.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, dff2.findPortInst("CLK"), via_clk3.getOnlyPortInst())

make_manhattan_arc(m2_wire, ep, via_clk1.getOnlyPortInst(), via_clk2.getOnlyPortInst())
make_manhattan_arc(m2_wire, ep, via_clk2.getOnlyPortInst(), via_clk3.getOnlyPortInst())
Export.newInst(test_cell, via_clk1.getOnlyPortInst(), "CLK", PortCharacteristic.IN)

# 2. Row 0 Well Coverage
X_MAX_R0 = 330.0
NodeInst.makeInstance(n_well_node, ep, Point2D.Double(X_MAX_R0 / 2.0, 19.0), X_MAX_R0 + 20.0, 32.0, test_cell, Orientation.IDENT, "nwell_r0")
NodeInst.makeInstance(p_well_node, ep, Point2D.Double(X_MAX_R0 / 2.0, -19.0), X_MAX_R0 + 20.0, 32.0, test_cell, Orientation.IDENT, "pwell_r0")

# 3. Transistor Columns in Row 0
col_defs = [
    (0,  0,  8.0, 4.0,  10.0, 'inv'),
    (1,  1,  8.0, 4.0,  34.0, 'inv'),
    (2,  2,  8.0, 4.0,  58.0, 'inv'),
    (3,  3,  4.0, 4.0,  82.0, 'nand2_b'),
    (4,  4,  4.0, 4.0,  91.0, 'nand2_a'),
    (5,  5,  8.0, 4.0, 115.0, 'inv'),
    (6,  6,  4.0, 6.0, 139.0, 'inv_like'),
    (7,  7,  4.0, 6.0, 163.0, 'inv_like'),
    (8,  8,  4.0, 6.0, 187.0, 'inv_like'),
    (9,  9, 12.0, 6.0, 211.0, 'inv'),
    (10, 10, 8.0, 4.0, 235.0, 'inv_like'),
    (11, 11, 8.0, 4.0, 259.0, 'inv_like'),
    (12, 12, 8.0, 4.0, 283.0, 'inv_like'),
    (13, 13, 8.0, 4.0, 307.0, 'inv_like'),
]

p_nodes = {}
n_nodes = {}
p_con_l = {}
p_con_r = {}
n_con_l = {}
n_con_r = {}

vdd_drops_r0 = []
gnd_drops_r0 = []

for cidx, tnum, wp, wn, xc, ctype in col_defs:
    p = NodeInst.makeInstance(p_proto, ep, Point2D.Double(xc, Y_P), 22.0, 15.0, test_cell, Orientation.R, "pmos@%d" % tnum)
    p.setPrimitiveNodeSize(wp, 2.0, ep)
    n = NodeInst.makeInstance(n_proto, ep, Point2D.Double(xc, Y_N), 22.0, 15.0, test_cell, Orientation.R, "nmos@%d" % tnum)
    n.setPrimitiveNodeSize(wn, 2.0, ep)
    p_nodes[tnum] = p
    n_nodes[tnum] = n

    if ctype == 'inv':
        pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcl_%d" % tnum)
        pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcr_%d" % tnum)
        ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncl_%d" % tnum)
        ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncr_%d" % tnum)
        p_con_l[tnum] = pcl
        p_con_r[tnum] = pcr
        n_con_l[tnum] = ncl
        n_con_r[tnum] = ncr
        make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
        make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
        make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
        make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())
        vdd_drops_r0.append((pcl, xc - dx))
        gnd_drops_r0.append((ncl, xc - dx))

    elif ctype == 'nand2_b':
        pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcl_%d" % tnum)
        ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncl_%d" % tnum)
        p_con_l[tnum] = pcl
        n_con_l[tnum] = ncl
        make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
        make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
        vdd_drops_r0.append((pcl, xc - dx))

        pcm = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcm_34")
        ncm = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncm_34")
        p_con_r[tnum] = pcm
        n_con_r[tnum] = ncm
        make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcm.getOnlyPortInst())
        make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncm.getOnlyPortInst())

    elif ctype == 'nand2_a':
        pcm = p_con_r[3]
        ncm = n_con_r[3]
        p_con_l[tnum] = pcm
        n_con_l[tnum] = ncm
        make_manhattan_arc(p_act_wire, ep, pcm.getOnlyPortInst(), p.findPortInst("diff-top"))
        make_manhattan_arc(n_act_wire, ep, ncm.getOnlyPortInst(), n.findPortInst("diff-top"))

        pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcr_%d" % tnum)
        ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncr_%d" % tnum)
        p_con_r[tnum] = pcr
        n_con_r[tnum] = ncr
        make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
        make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())
        vdd_drops_r0.append((pcr, xc + dx))
        gnd_drops_r0.append((ncr, xc + dx))

    elif ctype == 'inv_like':
        pcl = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc - dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcl_%d" % tnum)
        pcr = NodeInst.makeInstance(m1_p_con, ep, Point2D.Double(xc + dx, Y_P), 17.0, 17.0, test_cell, Orientation.IDENT, "pcr_%d" % tnum)
        ncl = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc - dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncl_%d" % tnum)
        ncr = NodeInst.makeInstance(m1_n_con, ep, Point2D.Double(xc + dx, Y_N), 17.0, 17.0, test_cell, Orientation.IDENT, "ncr_%d" % tnum)
        p_con_l[tnum] = pcl
        p_con_r[tnum] = pcr
        n_con_l[tnum] = ncl
        n_con_r[tnum] = ncr
        make_manhattan_arc(p_act_wire, ep, pcl.getOnlyPortInst(), p.findPortInst("diff-top"))
        make_manhattan_arc(p_act_wire, ep, p.findPortInst("diff-bottom"), pcr.getOnlyPortInst())
        make_manhattan_arc(n_act_wire, ep, ncl.getOnlyPortInst(), n.findPortInst("diff-top"))
        make_manhattan_arc(n_act_wire, ep, n.findPortInst("diff-bottom"), ncr.getOnlyPortInst())

        if tnum in [6, 7, 8]:
            vdd_drops_r0.append((pcl, xc - dx))
        if tnum == 8:
            gnd_drops_r0.append((ncr, xc + dx))

# 4. Connect Row 0 Power Rails
vdd_map_r0 = {}
vdd_map_r0[-38.0] = via_v0
pin_vdd_r0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX_R0, Y_VDD), 3.0, 3.0, test_cell, Orientation.IDENT, "pin_vdd_r0")
vdd_map_r0[X_MAX_R0] = pin_vdd_r0
tap_vdd = NodeInst.makeInstance(m1_n_well_con, ep, Point2D.Double(-2.0, Y_VDD), 17.0, 17.0, test_cell, Orientation.IDENT, "tap_vdd_r0")
vdd_map_r0[-2.0] = tap_vdd

for con, x in vdd_drops_r0:
    pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_VDD), 3.0, 3.0, test_cell, Orientation.IDENT, "pin_v_%.1f" % x)
    vdd_map_r0[x] = pin
    make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

sorted_vx = sorted(vdd_map_r0.keys())
for i in range(len(sorted_vx) - 1):
    make_manhattan_arc(m1_wire, ep, vdd_map_r0[sorted_vx[i]].getOnlyPortInst(), vdd_map_r0[sorted_vx[i+1]].getOnlyPortInst())

gnd_map_r0 = {}
gnd_map_r0[-46.0] = via_g0
pin_gnd_r0 = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(X_MAX_R0, Y_GND), 3.0, 3.0, test_cell, Orientation.IDENT, "pin_gnd_r0")
gnd_map_r0[X_MAX_R0] = pin_gnd_r0
tap_gnd = NodeInst.makeInstance(m1_p_well_con, ep, Point2D.Double(-2.0, Y_GND), 17.0, 17.0, test_cell, Orientation.IDENT, "tap_gnd_r0")
gnd_map_r0[-2.0] = tap_gnd

for con, x in gnd_drops_r0:
    pin = NodeInst.makeInstance(m1_pin, ep, Point2D.Double(x, Y_GND), 3.0, 3.0, test_cell, Orientation.IDENT, "pin_g_%.1f" % x)
    gnd_map_r0[x] = pin
    make_manhattan_arc(m1_wire, ep, con.getOnlyPortInst(), pin.getOnlyPortInst())

sorted_gx = sorted(gnd_map_r0.keys())
for i in range(len(sorted_gx) - 1):
    make_manhattan_arc(m1_wire, ep, gnd_map_r0[sorted_gx[i]].getOnlyPortInst(), gnd_map_r0[sorted_gx[i+1]].getOnlyPortInst())

# Gate connections for inverters and NAND gates
con_gates = {}
for cidx, tnum, wp, wn, xc, ctype in col_defs:
    if ctype in ['inv', 'nand2_b', 'nand2_a', 'inv_like']:
        if tnum not in [10, 11, 12, 13]:
            # Connect PMOS poly-left to NMOS poly-right via center poly-pin at (xc, 0.0)
            p0 = NodeInst.makeInstance(poly_pin, ep, Point2D.Double(xc, 0.0), 2.0, 2.0, test_cell, Orientation.IDENT, "p0_%d" % tnum)
            make_manhattan_arc(poly_wire, ep, p_nodes[tnum].findPortInst("poly-left"), p0.getOnlyPortInst())
            make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), n_nodes[tnum].findPortInst("poly-right"))

            # Local gate contact at (xc - 7.0, 0.0)
            if tnum != 4:
                cg = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(xc - 7.0, 0.0), 5.0, 5.0, test_cell, Orientation.IDENT, "cg_%d" % tnum)
                make_manhattan_arc(poly_wire, ep, cg.getOnlyPortInst(), p0.getOnlyPortInst())
                con_gates[tnum] = cg
            else:
                cg4 = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(xc + 7.0, 0.0), 5.0, 5.0, test_cell, Orientation.IDENT, "cg_4")
                make_manhattan_arc(poly_wire, ep, p0.getOnlyPortInst(), cg4.getOnlyPortInst())
                con_gates[4] = cg4

# Connect C0B to dff0[D] via X = -11.0:
pout_0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(14.5, 0.0), 5.0, 5.0, test_cell, Orientation.IDENT, "pout_0")
make_manhattan_arc(m1_wire, ep, p_con_r[0].getOnlyPortInst(), pout_0.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, pout_0.getOnlyPortInst(), n_con_r[0].getOnlyPortInst())

via_c0b_ch0 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(14.5, 44.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_c0b_ch0")
make_manhattan_arc(m2_wire, ep, pout_0.getOnlyPortInst(), via_c0b_ch0.getOnlyPortInst())

via_c0b_x11 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-11.0, 44.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_c0b_x11")
make_manhattan_arc(m1_wire, ep, via_c0b_ch0.getOnlyPortInst(), via_c0b_x11.getOnlyPortInst())

via_d0_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-11.0, Y_ROW1), 3.0, 3.0, test_cell, Orientation.IDENT, "via_d0_turn")
make_manhattan_arc(m2_wire, ep, via_c0b_x11.getOnlyPortInst(), via_d0_turn.getOnlyPortInst())

via_dff0_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW1), 5.0, 5.0, test_cell, Orientation.IDENT, "via_dff0_d")
make_manhattan_arc(m2_wire, ep, via_d0_turn.getOnlyPortInst(), via_dff0_d.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, via_dff0_d.getOnlyPortInst(), dff0.findPortInst("D"))

# Connect D1 to dff1[D] via X = -17.0:
via_d1_x17 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-17.0, 48.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_d1_x17")
via_d1_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-17.0, Y_ROW2), 3.0, 3.0, test_cell, Orientation.IDENT, "via_d1_turn")
make_manhattan_arc(m2_wire, ep, via_d1_x17.getOnlyPortInst(), via_d1_turn.getOnlyPortInst())

via_dff1_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW2), 5.0, 5.0, test_cell, Orientation.IDENT, "via_dff1_d")
make_manhattan_arc(m2_wire, ep, via_d1_turn.getOnlyPortInst(), via_dff1_d.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, via_dff1_d.getOnlyPortInst(), dff1.findPortInst("D"))

# Connect D2 to dff2[D] via X = -23.0:
via_d2_x23 = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(-23.0, 52.0), 5.0, 5.0, test_cell, Orientation.IDENT, "via_d2_x23")
via_d2_turn = NodeInst.makeInstance(m2_pin, ep, Point2D.Double(-23.0, Y_ROW3), 3.0, 3.0, test_cell, Orientation.IDENT, "via_d2_turn")
make_manhattan_arc(m2_wire, ep, via_d2_x23.getOnlyPortInst(), via_d2_turn.getOnlyPortInst())

via_dff2_d = NodeInst.makeInstance(m1_m2_con, ep, Point2D.Double(55.5, Y_ROW3), 5.0, 5.0, test_cell, Orientation.IDENT, "via_dff2_d")
make_manhattan_arc(m2_wire, ep, via_d2_turn.getOnlyPortInst(), via_dff2_d.getOnlyPortInst())
make_manhattan_arc(m1_wire, ep, via_dff2_d.getOnlyPortInst(), dff2.findPortInst("D"))

run_drc(test_cell)

test_cell.kill()
