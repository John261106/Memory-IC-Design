# -*- coding: utf-8 -*-
# scripts/21_layout_top.py
# Clean Top layout with input buffers and output buffer, 0 DRC errors, 100% NCC with size check

import java.lang.Double
from java.awt.geom import Point2D
from java.util import ArrayList

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
from com.sun.electric.tool.ncc import Ncc, NccOptions
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger

def make_manhattan_arc(arc_proto, ep, port1, port2, width=None):
    p1 = port1.getCenter()
    p2 = port2.getCenter()
    dx = abs(p1.getX() - p2.getX())
    dy = abs(p1.getY() - p2.getY())
    if dx > 0.001 and dy > 0.001:
        raise AssertionError("Non-perpendicular arc attempted: (%f,%f) to (%f,%f)" % (p1.getX(), p1.getY(), p2.getX(), p2.getY()))
    arc = ArcInst.makeInstance(arc_proto, ep, port1, port2)
    if width is not None:
        arc.setLambdaBaseWidth(width)
    return arc

def clear_cell_contents(cell):
    eit = cell.getExports()
    exp_kill = [eit.next() for _ in range(cell.getNumExports())] if hasattr(cell, "getNumExports") else []
    if not exp_kill:
        while eit.hasNext(): exp_kill.append(eit.next())
    for e in exp_kill: e.kill()

    ait = cell.getArcs()
    arc_kill = []
    while ait.hasNext(): arc_kill.append(ait.next())
    for a in arc_kill: a.kill()

    nit = cell.getNodes()
    node_kill = []
    while nit.hasNext(): node_kill.append(nit.next())
    for n in node_kill: n.kill()

class Router:
    def __init__(self, cell, ep, mocmos):
        self.cell = cell
        self.ep = ep
        self.mocmos = mocmos
        self.uid = 0
        self.wires = {
            1: mocmos.findArcProto("Metal-1"),
            2: mocmos.findArcProto("Metal-2"),
            3: mocmos.findArcProto("Metal-3"),
            4: mocmos.findArcProto("Metal-4"),
            5: mocmos.findArcProto("Metal-5"),
            6: mocmos.findArcProto("Metal-6"),
        }
        self.pins = {
            1: mocmos.findNodeProto("Metal-1-Pin"),
            2: mocmos.findNodeProto("Metal-2-Pin"),
            3: mocmos.findNodeProto("Metal-3-Pin"),
            4: mocmos.findNodeProto("Metal-4-Pin"),
            5: mocmos.findNodeProto("Metal-5-Pin"),
            6: mocmos.findNodeProto("Metal-6-Pin"),
        }
        self.vias = {
            1: mocmos.findNodeProto("Metal-1-Metal-2-Con"),
            2: mocmos.findNodeProto("Metal-2-Metal-3-Con"),
            3: mocmos.findNodeProto("Metal-3-Metal-4-Con"),
            4: mocmos.findNodeProto("Metal-4-Metal-5-Con"),
            5: mocmos.findNodeProto("Metal-5-Metal-6-Con"),
        }

    def pin(self, layer, x, y, name=None):
        proto = self.pins[layer]
        dw = proto.getDefWidth()
        dh = proto.getDefHeight()
        n = NodeInst.makeInstance(proto, self.ep, Point2D.Double(x, y), dw, dh, self.cell, Orientation.IDENT, None)
        return n.getOnlyPortInst()

    def via(self, low_layer, x, y, name=None):
        proto = self.vias[low_layer]
        dw = proto.getDefWidth()
        dh = proto.getDefHeight()
        n = NodeInst.makeInstance(proto, self.ep, Point2D.Double(x, y), dw, dh, self.cell, Orientation.IDENT, None)
        return n.getOnlyPortInst()

    def via_stack(self, x, y, from_layer, to_layer, base_port=None):
        if from_layer == to_layer:
            if base_port is not None:
                bx = base_port.getCenter().getX()
                by = base_port.getCenter().getY()
                if abs(bx - x) > 0.001 or abs(by - y) > 0.001:
                    p = self.pin(from_layer, x, y)
                    make_manhattan_arc(self.wires[from_layer], self.ep, base_port, p)
                    return p
            return base_port

        step = 1 if to_layer > from_layer else -1
        cur_l = from_layer
        cur_p = base_port

        while cur_l != to_layer:
            nxt_l = cur_l + step
            low_l = min(cur_l, nxt_l)
            v = self.via(low_l, x, y)
            if cur_p is not None:
                make_manhattan_arc(self.wires[cur_l], self.ep, cur_p, v)
            cur_p = v
            cur_l = nxt_l

        return cur_p

    def route_pts(self, layer, start_port, points, end_port=None):
        wire = self.wires[layer]
        cur = start_port
        for pt in points:
            x, y = pt
            nxt = self.pin(layer, x, y)
            make_manhattan_arc(wire, self.ep, cur, nxt)
            cur = nxt
        if end_port is not None:
            make_manhattan_arc(wire, self.ep, cur, end_port)
            return end_port
        return cur

def test_build(lib, ep, mocmos):
    sch = lib.findNodeProto("Top{sch}")
    cell = lib.findNodeProto("Top{lay}")
    if cell is None:
        cell = Cell.makeInstance(lib, "Top{lay}")
    clear_cell_contents(cell)

    rt = Router(cell, ep, mocmos)

    p_arr   = lib.findNodeProto("256bit_array{lay}")
    p_dec   = lib.findNodeProto("Decoder{lay}")
    p_wld   = lib.findNodeProto("WL_driver{lay}")
    p_pre   = lib.findNodeProto("Precharge_ckt{lay}")
    p_tg    = lib.findNodeProto("TG_bitline{lay}")
    p_sa    = lib.findNodeProto("Sense_amp{lay}")
    p_wd    = lib.findNodeProto("Write_driver{lay}")
    p_not   = lib.findNodeProto("Not{lay}")
    p_dff   = lib.findNodeProto("D_flipflop{lay}")
    p_sreg  = lib.findNodeProto("8Bit_shiftreg{lay}")
    p_cnt   = lib.findNodeProto("3Bit_counter{lay}")
    p_ctrl  = lib.findNodeProto("Control_logic{lay}")
    p_inbuf = lib.findNodeProto("input_buffer{lay}")
    p_outbuf= lib.findNodeProto("output_buffer{lay}")

    # 1. Macro Placements
    arr = NodeInst.makeInstance(p_arr, ep, Point2D.Double(0.0, 0.0), 800.0, 1280.0, cell, Orientation.IDENT, "256bit_a@0")

    wlds = []
    for r in range(16):
        yr = r * 81.0 - 24.0
        wld = NodeInst.makeInstance(p_wld, ep, Point2D.Double(-115.0, yr), 70.5, 73.0, cell, Orientation.IDENT, "WL_drive@%d" % r)
        wlds.append(wld)

    dec_row = NodeInst.makeInstance(p_dec, ep, Point2D.Double(-445.0, 0.0), 216.0, 1449.0, cell, Orientation.IDENT, "Decoder@0")
    dec_col = NodeInst.makeInstance(p_dec, ep, Point2D.Double(-835.0, 0.0), 216.0, 1449.0, cell, Orientation.IDENT, "Decoder@1")

    pres = []
    for c in range(16):
        xc = c * 51.0
        yc = -65.0 if (c % 2 == 0) else -120.0
        pre = NodeInst.makeInstance(p_pre, ep, Point2D.Double(xc, yc), 53.0, 46.0, cell, Orientation.IDENT, "Precharg@%d" % c)
        pres.append(pre)

    tgs = []
    for c in range(16):
        xc = c * 51.0 - 28.0
        yc = -190.0 if (c % 2 == 0) else -275.0
        tg = NodeInst.makeInstance(p_tg, ep, Point2D.Double(xc, yc), 72.0, 73.0, cell, Orientation.IDENT, "TG_bitli@%d" % c)
        tgs.append(tg)

    sa       = NodeInst.makeInstance(p_sa, ep, Point2D.Double(435.0, -520.0), 78.0, 73.0, cell, Orientation.IDENT, "Sense_am@0")
    wd       = NodeInst.makeInstance(p_wd, ep, Point2D.Double(535.0, -520.0), 94.0, 73.0, cell, Orientation.IDENT, "Write_dr@0")

    not_gate = NodeInst.makeInstance(p_not, ep, Point2D.Double(445.0, -660.0), 40.0, 69.0, cell, Orientation.IDENT, "Not@0")
    dff      = NodeInst.makeInstance(p_dff, ep, Point2D.Double(620.0, -660.0), 308.5, 73.0, cell, Orientation.IDENT, "D_flipfl@0")

    sreg = NodeInst.makeInstance(p_sreg, ep, Point2D.Double(-400.0, -860.0), 366.0, 675.0, cell, Orientation.IDENT, "8Bit_shi@0")
    cnt  = NodeInst.makeInstance(p_cnt,  ep, Point2D.Double(-20.0,  -770.0), 500.0, 429.0, cell, Orientation.IDENT, "3Bit_cou@0")
    ctrl = NodeInst.makeInstance(p_ctrl, ep, Point2D.Double(0.0,    -960.0), 487.5, 73.0,  cell, Orientation.IDENT, "Control_@0")

    # 5 Buffers
    ib_addr = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-550.0, -1240.0), 114.0, 73.0, cell, Orientation.IDENT, "in_buf_addr")
    ib_clk  = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-352.5, -1240.0), 114.0, 73.0, cell, Orientation.IDENT, "in_buf_clk")
    ib_ctrl = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(-100.0, -1240.0), 114.0, 73.0, cell, Orientation.IDENT, "in_buf_ctrl")
    ib_din  = NodeInst.makeInstance(p_inbuf, ep, Point2D.Double(150.0, -1240.0), 114.0, 73.0, cell, Orientation.IDENT, "in_buf_din")
    ob_dout = NodeInst.makeInstance(p_outbuf, ep, Point2D.Double(1000.0, -664.0), 191.0, 101.0, cell, Orientation.IDENT, "out_buf_dout")

    # 2. Wordlines & Row Decoder
    wl_en_vias = []
    for r in range(16):
        make_manhattan_arc(rt.wires[1], ep, wlds[r].findPortInst("WL"), arr.findPortInst("WL%d" % r))
        v_en = rt.via_stack(-115.0, r * 81.0 - 24.0, 1, 4, wlds[r].findPortInst("EN"))
        wl_en_vias.append(v_en)

        y_src = r * 72.0
        y_dst = r * 81.0 - 24.0
        y_wld_in = y_dst - 21.0
        x_trk = -275.0 + r * 7.0

        p_dec_out = dec_row.findPortInst("OUT%d" % r)
        p_in_wld = rt.via_stack(-96.0, y_wld_in, 1, 2, wlds[r].findPortInst("IN"))

        if abs(y_src - y_wld_in) < 0.001:
            p_dec_m1 = rt.route_pts(1, p_dec_out, [(-290.0, y_src)])
            v_dec_m2 = rt.via_stack(-290.0, y_src, 1, 2, p_dec_m1)
            make_manhattan_arc(rt.wires[2], ep, v_dec_m2, p_in_wld)
        elif r == 14:
            y_jog = y_src + 10.0
            p_dec_m1 = rt.route_pts(1, p_dec_out, [(-290.0, y_src), (-290.0, y_jog)])
            v_dec_m2 = rt.via_stack(-290.0, y_jog, 1, 2, p_dec_m1)
            p_jog_m2 = rt.route_pts(2, v_dec_m2, [(x_trk, y_jog)])
            p_trk_m3_top = rt.via_stack(x_trk, y_jog, 2, 3, p_jog_m2)
            p_trk_m3_bot = rt.route_pts(3, p_trk_m3_top, [(x_trk, y_wld_in)])
            p_trk_m2_bot = rt.via_stack(x_trk, y_wld_in, 3, 2, p_trk_m3_bot)
            make_manhattan_arc(rt.wires[2], ep, p_trk_m2_bot, p_in_wld)
        else:
            p_dec_m1 = rt.route_pts(1, p_dec_out, [(-290.0, y_src)])
            v_dec_m2 = rt.via_stack(-290.0, y_src, 1, 2, p_dec_m1)
            p_trk_m2 = rt.route_pts(2, v_dec_m2, [(x_trk, y_src)])
            p_trk_m3_top = rt.via_stack(x_trk, y_src, 2, 3, p_trk_m2)
            p_trk_m3_bot = rt.route_pts(3, p_trk_m3_top, [(x_trk, y_wld_in)])
            p_trk_m2_bot = rt.via_stack(x_trk, y_wld_in, 3, 2, p_trk_m3_bot)
            make_manhattan_arc(rt.wires[2], ep, p_trk_m2_bot, p_in_wld)

    for r in range(15):
        make_manhattan_arc(rt.wires[4], ep, wl_en_vias[r], wl_en_vias[r+1])

    # 3. Bitlines (Precharge & TG)
    for c in range(16):
        x_bl  = c * 51.0 - 20.0
        x_blb = c * 51.0 + 20.0
        xc_pre = c * 51.0
        xc_tg  = c * 51.0 - 28.0
        y_pre  = -65.0 if (c % 2 == 0) else -120.0
        y_tg   = -190.0 if (c % 2 == 0) else -275.0

        p_bl_arr = rt.via(2, x_bl, 48.0)
        make_manhattan_arc(rt.wires[2], ep, arr.findPortInst("BL%d" % c), p_bl_arr)
        p_pre_bit = rt.via_stack(xc_pre - 4.5, y_pre, 1, 3, pres[c].findPortInst("BIT"))
        p_tg_bitu = rt.via_stack(xc_tg + 5.5, y_tg, 1, 3, tgs[c].findPortInst("BIT_U"))

        y_j1 = -32.0 if (c % 2 == 0) else -88.0
        cur = rt.route_pts(3, p_bl_arr, [(x_bl, y_j1), (xc_pre - 4.5, y_j1)], p_pre_bit)
        y_j_tg = -148.0 if (c % 2 == 0) else -232.0
        rt.route_pts(3, cur, [(xc_pre - 4.5, y_j_tg), (xc_tg + 5.5, y_j_tg)], p_tg_bitu)

        p_blb_arr = rt.via(2, x_blb, 48.0)
        make_manhattan_arc(rt.wires[2], ep, arr.findPortInst("BLB%d" % c), p_blb_arr)
        p_pre_bitb = rt.via_stack(xc_pre + 4.5, y_pre, 1, 3, pres[c].findPortInst("BITB"))
        p_tg_bitbu = rt.via_stack(xc_tg + 41.5, y_tg, 1, 3, tgs[c].findPortInst("BITB_U"))

        y_j2 = -38.0 if (c % 2 == 0) else -94.0
        cur_b = rt.route_pts(3, p_blb_arr, [(x_blb, y_j2), (xc_pre + 4.5, y_j2)], p_pre_bitb)
        y_j3 = -154.0 if (c % 2 == 0) else -238.0
        rt.route_pts(3, cur_b, [(xc_pre + 4.5, y_j3), (xc_tg + 41.5, y_j3)], p_tg_bitbu)

    # 4. Data Line Busses (DL and DLB on Metal-4)
    Y_DL  = -330.0
    Y_DLB = -342.0
    dl_nodes = []
    dlb_nodes = []
    for c in range(16):
        xc_tg = c * 51.0 - 28.0
        y_tg  = -190.0 if (c % 2 == 0) else -275.0
        p_tg_d  = rt.via_stack(xc_tg + 15.5, y_tg, 1, 4, tgs[c].findPortInst("BIT_D"))
        p_tg_db = rt.via_stack(xc_tg + 51.5, y_tg, 1, 4, tgs[c].findPortInst("BITB_D"))

        pd_bus  = rt.pin(4, xc_tg + 15.5, Y_DL)
        make_manhattan_arc(rt.wires[4], ep, p_tg_d, pd_bus)
        pdb_j   = rt.pin(4, xc_tg + 51.5, -315.0)
        make_manhattan_arc(rt.wires[4], ep, p_tg_db, pdb_j)
        p_db_m3 = rt.via_stack(xc_tg + 51.5, -315.0, 4, 3, pdb_j)
        p_db_m3t = rt.pin(3, xc_tg + 51.5, Y_DLB)
        make_manhattan_arc(rt.wires[3], ep, p_db_m3, p_db_m3t)
        pdb_bus = rt.via_stack(xc_tg + 51.5, Y_DLB, 3, 4, p_db_m3t)

        dl_nodes.append(pd_bus)
        dlb_nodes.append(pdb_bus)

    # Sense_amp@0 BIT & BITB
    p_sa_bit   = rt.via_stack(447.0, -541.0, 1, 4, sa.findPortInst("BIT"))
    p_sa_b_j1  = rt.pin(4, 447.0, -480.0)
    make_manhattan_arc(rt.wires[4], ep, p_sa_bit, p_sa_b_j1)
    p_sa_m2_1  = rt.via_stack(447.0, -480.0, 4, 2, p_sa_b_j1)
    p_sa_m2_2  = rt.pin(2, 447.0, Y_DL)
    make_manhattan_arc(rt.wires[2], ep, p_sa_m2_1, p_sa_m2_2)
    p_sa_dl    = rt.via_stack(447.0, Y_DL, 2, 4, p_sa_m2_2)

    p_sa_bitb = rt.via_stack(456.0, -541.0, 1, 4, sa.findPortInst("BITB"))
    p_sa_dlb  = rt.pin(4, 456.0, Y_DLB)
    make_manhattan_arc(rt.wires[4], ep, p_sa_bitb, p_sa_dlb)

    dl_nodes.append(p_sa_dl)
    dlb_nodes.append(p_sa_dlb)

    # Write_dr@0 BIT & BITB
    p_wd_bit   = rt.via_stack(540.5, -520.0, 1, 4, wd.findPortInst("BIT"))
    p_wd_b_j1  = rt.pin(4, 540.5, -480.0)
    make_manhattan_arc(rt.wires[4], ep, p_wd_bit, p_wd_b_j1)
    p_wd_m2_1  = rt.via_stack(540.5, -480.0, 4, 2, p_wd_b_j1)
    p_wd_m2_2  = rt.pin(2, 540.5, Y_DL)
    make_manhattan_arc(rt.wires[2], ep, p_wd_m2_1, p_wd_m2_2)
    p_wd_dl    = rt.via_stack(540.5, Y_DL, 2, 4, p_wd_m2_2)

    p_wd_bitb = rt.via_stack(605.5, -520.0, 1, 4, wd.findPortInst("BITB"))
    p_wd_dlb  = rt.pin(4, 605.5, Y_DLB)
    make_manhattan_arc(rt.wires[4], ep, p_wd_bitb, p_wd_dlb)

    dl_nodes.append(p_wd_dl)
    dlb_nodes.append(p_wd_dlb)

    dl_sorted  = sorted(dl_nodes,  key=lambda p: p.getCenter().getX())
    dlb_sorted = sorted(dlb_nodes, key=lambda p: p.getCenter().getX())
    for i in range(len(dl_sorted) - 1):
        make_manhattan_arc(rt.wires[4], ep, dl_sorted[i], dl_sorted[i+1])
    for i in range(len(dlb_sorted) - 1):
        make_manhattan_arc(rt.wires[4], ep, dlb_sorted[i], dlb_sorted[i+1])

    # 5. Column Decoder Outputs (COL0..15)
    for c in range(16):
        x_trk = -685.0 + c * 10.0
        y_src = c * 72.0
        xc_tg = c * 51.0 - 28.0
        y_tg  = -190.0 if (c % 2 == 0) else -275.0
        x_en  = xc_tg + 35.0
        y_en  = y_tg - 21.0
        y_bus = -471.0 + c * 8.0
        p_dec_out = dec_col.findPortInst("OUT%d" % c)
        p_out_v1 = rt.via_stack(x_trk, y_src, 1, 3, p_dec_out)
        p_en_m3 = rt.route_pts(3, p_out_v1, [(x_trk, y_bus)])
        p_en_m2 = rt.via_stack(x_en, y_bus, 3, 2, p_en_m3)
        make_manhattan_arc(rt.wires[2], ep, p_en_m2, tgs[c].findPortInst("EN"))

    # 6. Address Buses
    for idx, q_idx in enumerate([4, 5, 6, 7]):
        a_name = "A%d" % idx
        yq_orig = -860.0 + q_idx * 86.0
        yq_via  = -484.0 if q_idx == 5 else (-340.0 if q_idx == 6 else yq_orig)
        if abs(yq_via - yq_orig) > 0.001:
            p_q_m2 = rt.route_pts(2, sreg.findPortInst("Q%d" % q_idx), [(-128.5, yq_via)])
            p_q = rt.via_stack(-128.5, yq_via, 2, 4, p_q_m2)
        else:
            p_q = rt.via_stack(-128.5, yq_via, 2, 4, sreg.findPortInst("Q%d" % q_idx))
        a_port = dec_row.findPortInst(a_name)
        ax = a_port.getCenter().getX()
        ay = a_port.getCenter().getY()
        p_a = rt.via_stack(ax, ay, 2, 4, a_port)
        x_bus = -555.0 + idx * 10.0
        rt.route_pts(4, p_q, [(x_bus, yq_via), (x_bus, ay)], p_a)

    for idx, q_idx in enumerate([0, 1, 2, 3]):
        a_name = "A%d" % idx
        p_q = rt.via_stack(-128.5, -860.0 + q_idx * 86.0, 2, 3, sreg.findPortInst("Q%d" % q_idx))
        a_port = dec_col.findPortInst(a_name)
        ax = a_port.getCenter().getX()
        ay = a_port.getCenter().getY()
        p_a = rt.via_stack(ax, ay, 2, 4, a_port)
        x_bus = -955.0 + idx * 10.0
        y_q   = -860.0 + q_idx * 86.0
        p_ca_m3 = rt.route_pts(3, p_q, [(x_bus, y_q)])
        p_ca_m4 = rt.via_stack(x_bus, y_q, 3, 4, p_ca_m3)
        rt.route_pts(4, p_ca_m4, [(x_bus, ay)], p_a)

    # 7. Control Signals
    poly_wire = mocmos.findArcProto("Polysilicon-1")
    m1_poly_con = mocmos.findNodeProto("Metal-1-Polysilicon-1-Con")
    p_c7_poly = NodeInst.makeInstance(m1_poly_con, ep, Point2D.Double(115.0, -996.0), 5.0, 5.0, cell, Orientation.IDENT, None)
    make_manhattan_arc(poly_wire, ep, ctrl.findPortInst("COUNT_7"), p_c7_poly.getOnlyPortInst())
    p_c7_src = rt.via_stack(203.5, -770.0, 1, 3, cnt.findPortInst("COUNT_7"))
    p_c7_dst = rt.via_stack(115.0, -996.0, 1, 3, p_c7_poly.getOnlyPortInst())
    rt.route_pts(3, p_c7_src, [(203.5, -880.0), (115.0, -880.0)], p_c7_dst)

    p_wlen_src = rt.via_stack(143.5, -960.0, 1, 3, ctrl.findPortInst("WL_EN"))
    p_wlen_j   = rt.route_pts(3, p_wlen_src, [(143.5, -1092.0), (-108.0, -1092.0), (-108.0, -485.0)])
    p_wlen_m4  = rt.via_stack(-108.0, -485.0, 3, 4, p_wlen_j)
    rt.route_pts(4, p_wlen_m4, [(-108.0, -24.0)], wl_en_vias[0])

    p_wen_src = rt.via_stack(200.5, -960.0, 1, 3, ctrl.findPortInst("WRITE_EN"))
    p_wen_dst = rt.via_stack(545.0, -541.0, 2, 3, wd.findPortInst("WRITE_EN"))
    rt.route_pts(3, p_wen_src, [(200.5, -895.0), (545.0, -895.0)], p_wen_dst)

    # READ_EN
    p_ren_src = rt.via_stack(449.5, -960.0, 1, 4, ctrl.findPortInst("READ_EN"))
    p_ren_dst = rt.via_stack(470.0, -541.0, 1, 4, sa.findPortInst("READ_EN"))
    p_ren_mid = rt.route_pts(4, p_ren_src, [(449.5, -880.0), (470.0, -880.0)])
    p_ren_tap = rt.pin(4, 470.0, -660.0)
    make_manhattan_arc(rt.wires[4], ep, p_ren_mid, p_ren_tap)
    make_manhattan_arc(rt.wires[4], ep, p_ren_tap, p_ren_dst)
    p_not_in  = rt.via_stack(438.0, -660.0, 1, 4, not_gate.findPortInst("IN"))
    make_manhattan_arc(rt.wires[4], ep, p_not_in, p_ren_tap)

    # READ_CLK
    p_not_out = rt.via_stack(449.5, -660.0, 1, 2, not_gate.findPortInst("OUT"))
    p_dff_clk = rt.via_stack(606.0, -660.0, 1, 2, dff.findPortInst("CLK"))
    make_manhattan_arc(rt.wires[2], ep, p_not_out, p_dff_clk)

    # SENSE_OUT
    p_sa_sense = rt.via_stack(490.5, -520.0, 1, 3, sa.findPortInst("SENSE"))
    p_dff_d    = rt.via_stack(675.5, -660.0, 1, 3, dff.findPortInst("D"))
    rt.route_pts(3, p_sa_sense, [(490.5, -460.0), (675.5, -460.0)], p_dff_d)

    # PCB
    p_pcb_src = rt.via_stack(62.5, -960.0, 1, 3, ctrl.findPortInst("PCB"))
    pcb_even = []
    pcb_odd  = []
    for c in range(16):
        xc = c * 51.0
        yc = -65.0 if (c % 2 == 0) else -120.0
        y_bus = yc - 18.0
        p_pcb_m1 = rt.route_pts(1, pres[c].findPortInst("PCB"), [(xc, y_bus)])
        pb = rt.via_stack(xc - 20.0, y_bus, 1, 4, p_pcb_m1)
        if c % 2 == 0:
            pcb_even.append(pb)
        else:
            pcb_odd.append(pb)
    for i in range(7):
        make_manhattan_arc(rt.wires[4], ep, pcb_even[i], pcb_even[i+1])
        make_manhattan_arc(rt.wires[4], ep, pcb_odd[i],  pcb_odd[i+1])
    p_pcb_e_tap = rt.pin(4, -48.0, -83.0)
    p_pcb_o_tap = rt.pin(4, -48.0, -138.0)
    make_manhattan_arc(rt.wires[4], ep, p_pcb_e_tap, pcb_even[0])
    make_manhattan_arc(rt.wires[4], ep, p_pcb_o_tap, pcb_odd[0])
    make_manhattan_arc(rt.wires[4], ep, p_pcb_e_tap, p_pcb_o_tap)
    p_pcb_m3 = rt.route_pts(3, p_pcb_src, [(62.5, -1080.0), (-98.0, -1080.0), (-98.0, -485.0)])
    p_pcb_m4 = rt.via_stack(-98.0, -485.0, 3, 4, p_pcb_m3)
    rt.route_pts(4, p_pcb_m4, [(-98.0, -160.0), (-48.0, -160.0)], p_pcb_o_tap)

    # 8. Clock Tree
    clk_root = rt.pin(4, -250.0, -1020.0, "clk_root")
    p_clk_sreg = rt.via_stack(-476.0, -559.0, 2, 4, sreg.findPortInst("CLK"))
    rt.route_pts(4, clk_root, [(-476.0, -1020.0)], p_clk_sreg)

    p_clk_cnt = rt.via_stack(-50.0, -684.0, 2, 4, cnt.findPortInst("CLK"))
    rt.route_pts(4, clk_root, [(-250.0, -920.0), (-50.0, -920.0), (-50.0, -844.5), (-125.5, -844.5), (-125.5, -684.0)], p_clk_cnt)

    p_clk_ctrl = rt.via_stack(0.0, -960.0, 1, 4, ctrl.findPortInst("CLK"))
    rt.route_pts(4, clk_root, [(-250.0, -1100.0), (108.5, -1100.0), (108.5, -1040.0), (0.0, -1040.0)], p_clk_ctrl)

    # Connect in_buf_clk OUT to clk_root on Metal-4
    p_ib_clk_out_m1 = ib_clk.findPortInst("OUT") # at (-250.0, -1243.5)
    p_ib_clk_out_m4 = rt.via_stack(-250.0, -1243.5, 1, 4, p_ib_clk_out_m1)
    make_manhattan_arc(rt.wires[4], ep, p_ib_clk_out_m4, clk_root)

    # 9. Buffer Signal Routings:
    # in_buf_addr.OUT (-447.5, -1243.5) -> sreg.D (-344.5, -860.0) on Metal-2
    p_ib_addr_out = rt.via_stack(-447.5, -1243.5, 1, 2, ib_addr.findPortInst("OUT"))
    p_sreg_d_m2 = rt.via_stack(-344.5, -860.0, 1, 2, sreg.findPortInst("D"))
    rt.route_pts(2, p_ib_addr_out, [(-344.5, -1243.5)], p_sreg_d_m2)

    # in_buf_ctrl.OUT (2.5, -1243.5) -> ctrl.CTRL (75.0, -960.0) on Metal-2
    p_ib_ctrl_out = rt.via_stack(2.5, -1243.5, 1, 2, ib_ctrl.findPortInst("OUT"))
    p_ctrl_ctrl_m2 = rt.via_stack(75.0, -960.0, 1, 2, ctrl.findPortInst("CTRL"))
    rt.route_pts(2, p_ib_ctrl_out, [(75.0, -1243.5)], p_ctrl_ctrl_m2)

    # in_buf_din.OUT (252.5, -1243.5) -> wd.DATA (556.0, -520.0) on Metal-2
    p_ib_din_out = rt.via_stack(252.5, -1243.5, 1, 2, ib_din.findPortInst("OUT"))
    p_wd_data_m2 = rt.via_stack(556.0, -520.0, 1, 2, wd.findPortInst("DATA"))
    rt.route_pts(2, p_ib_din_out, [(930.0, -1243.5), (930.0, -480.0), (556.0, -480.0)], p_wd_data_m2)

    # out_buf_dout.IN (991.5, -660.0) -> dff.Q (891.5, -660.0) straight on Metal-1
    make_manhattan_arc(rt.wires[1], ep, dff.findPortInst("Q"), ob_dout.findPortInst("IN"))

    # 10. Top-Metal Power Grid
    def strap_pwr(port, cur_layer, target_layer, trunk_x, trunk_y=None):
        px = port.getCenter().getX()
        py = port.getCenter().getY()
        p_top = rt.via_stack(px, py, cur_layer, target_layer, port)
        w_pwr = 8.0
        if trunk_y is None:
            pt = rt.pin(target_layer, trunk_x, py)
            make_manhattan_arc(rt.wires[target_layer], ep, p_top, pt, width=w_pwr)
            return pt
        else:
            pt = rt.pin(target_layer, px, trunk_y)
            make_manhattan_arc(rt.wires[target_layer], ep, p_top, pt, width=w_pwr)
            return pt

    X_VDD_L = -975.0
    X_GND_L = -989.0
    Y_VDD_B = -1120.0
    Y_GND_B = -1134.0
    X_VDD_R = 815.0
    X_GND_R = 829.0

    vdd_left = []
    vdd_left.append(strap_pwr(arr.findPortInst("VDD"), 2, 6, X_VDD_L))
    vdd_left.append(strap_pwr(dec_row.findPortInst("VDD"), 2, 6, X_VDD_L))
    vdd_left.append(strap_pwr(dec_col.findPortInst("VDD"), 2, 6, X_VDD_L))
    vdd_left.append(strap_pwr(sreg.findPortInst("VDD"), 2, 6, X_VDD_L))
    for r in range(16):
        p_wld_v = rt.route_pts(1, wlds[r].findPortInst("VDD"), [(-128.0, r * 81.0 + 4.0)])
        vdd_left.append(strap_pwr(p_wld_v, 1, 6, X_VDD_L))

    vdd_bot = []
    vdd_bot.append(strap_pwr(cnt.findPortInst("VDD"), 2, 6, None, Y_VDD_B))
    p_ctrl_v = rt.route_pts(1, ctrl.findPortInst("VDD"), [(-28.0, -932.0)])
    vdd_bot.append(strap_pwr(p_ctrl_v, 1, 6, None, Y_VDD_B))
    vdd_bot.append(strap_pwr(sa.findPortInst("VDD"), 1, 6, None, Y_VDD_B))
    vdd_bot.append(strap_pwr(wd.findPortInst("VDD"), 1, 6, None, Y_VDD_B))

    for i in range(7):
        c_cur = i * 2
        c_nxt = (i + 1) * 2
        make_manhattan_arc(rt.wires[1], ep, pres[c_cur].findPortInst("VDD"), pres[c_nxt].findPortInst("VDD"))
        c_cur_o = i * 2 + 1
        c_nxt_o = (i + 1) * 2 + 1
        make_manhattan_arc(rt.wires[1], ep, pres[c_cur_o].findPortInst("VDD"), pres[c_nxt_o].findPortInst("VDD"))

    p_pre_e_end = rt.route_pts(1, pres[14].findPortInst("VDD"), [(X_VDD_R, -51.0)])
    p_pre_e_v6  = rt.via_stack(X_VDD_R, -51.0, 1, 6, p_pre_e_end)
    p_pre_o_end = rt.route_pts(1, pres[15].findPortInst("VDD"), [(X_VDD_R, -106.0)])
    p_pre_o_v6  = rt.via_stack(X_VDD_R, -106.0, 1, 6, p_pre_o_end)

    for c in range(16):
        yc_tg = -190.0 if (c % 2 == 0) else -275.0
        p_tg_v = rt.route_pts(1, tgs[c].findPortInst("VDD"), [(c * 51.0 - 5.0, yc_tg + 28.0)])
        vdd_bot.append(strap_pwr(p_tg_v, 1, 6, None, Y_VDD_B))

    # Not & DFF VDD
    p_not_v1 = rt.route_pts(1, not_gate.findPortInst("VDD"), [(476.5, -634.0), (476.5, -632.0)])
    p_dff_v1 = dff.findPortInst("VDD")
    make_manhattan_arc(rt.wires[1], ep, p_not_v1, p_dff_v1)
    p_out_v6 = rt.via_stack(580.0, -632.0, 1, 6, p_dff_v1)
    p_out_v6_b = rt.pin(6, 580.0, Y_VDD_B)
    make_manhattan_arc(rt.wires[6], ep, p_out_v6, p_out_v6_b, width=8.0)
    vdd_bot.append(p_out_v6_b)

    # Input Buffers VDD (M3 straight up to Y_VDD_B, via stack M3 to M6)
    for ib in [ib_addr, ib_clk, ib_ctrl, ib_din]:
        pv = ib.findPortInst("VDD")
        px = pv.getCenter().getX()
        py = pv.getCenter().getY()
        pv_top = rt.route_pts(3, pv, [(px, Y_VDD_B)])
        pv_m6 = rt.via_stack(px, Y_VDD_B, 3, 6, pv_top)
        vdd_bot.append(pv_m6)

    # Output Buffer VDD (M1 at (1179.5, -614.0), drop M6 down to Y_VDD_B)
    p_ob_vdd = ob_dout.findPortInst("VDD")
    p_ob_v6 = rt.via_stack(1179.5, -614.0, 1, 6, p_ob_vdd)
    p_ob_v6_b = rt.pin(6, 1179.5, Y_VDD_B)
    make_manhattan_arc(rt.wires[6], ep, p_ob_v6, p_ob_v6_b, width=8.0)
    vdd_bot.append(p_ob_v6_b)

    vdd_bl = rt.pin(6, X_VDD_L, Y_VDD_B)
    vdd_br = rt.pin(6, 1179.5, Y_VDD_B)
    vdd_left.append(vdd_bl)
    vdd_bot.append(vdd_bl)

    p_sw_r = strap_pwr(arr.findPortInst("VDD"), 2, 6, X_VDD_R)
    vdd_r_nodes = [rt.pin(6, X_VDD_R, Y_VDD_B), p_pre_o_v6, p_pre_e_v6, p_sw_r]
    vdd_bot.append(vdd_r_nodes[0])
    vdd_r_s = sorted(vdd_r_nodes, key=lambda p: p.getCenter().getY())
    for i in range(len(vdd_r_s) - 1):
        make_manhattan_arc(rt.wires[6], ep, vdd_r_s[i], vdd_r_s[i+1], width=8.0)

    vdd_left_s = sorted(vdd_left, key=lambda p: p.getCenter().getY())
    for i in range(len(vdd_left_s) - 1):
        make_manhattan_arc(rt.wires[6], ep, vdd_left_s[i], vdd_left_s[i+1], width=8.0)
    vdd_bot_s = sorted(vdd_bot, key=lambda p: p.getCenter().getX())
    for i in range(len(vdd_bot_s) - 1):
        make_manhattan_arc(rt.wires[6], ep, vdd_bot_s[i], vdd_bot_s[i+1], width=8.0)

    # GND Grid
    gnd_left = []
    gnd_left.append(strap_pwr(arr.findPortInst("GND"), 2, 5, X_GND_L))
    gnd_left.append(strap_pwr(dec_row.findPortInst("GND"), 2, 5, X_GND_L))
    gnd_left.append(strap_pwr(dec_col.findPortInst("GND"), 2, 5, X_GND_L))
    gnd_left.append(strap_pwr(sreg.findPortInst("GND"), 2, 5, X_GND_L))
    for r in range(16):
        p_wld_g = rt.route_pts(1, wlds[r].findPortInst("GND"), [(-132.0, r * 81.0 - 52.0)])
        gnd_left.append(strap_pwr(p_wld_g, 1, 5, X_GND_L))

    gnd_bot = []
    gnd_bot.append(strap_pwr(cnt.findPortInst("GND"), 2, 5, None, Y_GND_B))
    p_ctrl_g = rt.route_pts(1, ctrl.findPortInst("GND"), [(-22.0, -988.0)])
    gnd_bot.append(strap_pwr(p_ctrl_g, 1, 5, None, Y_GND_B))
    gnd_bot.append(strap_pwr(sa.findPortInst("GND"), 1, 5, None, Y_GND_B))
    gnd_bot.append(strap_pwr(wd.findPortInst("GND"), 1, 5, None, Y_GND_B))
    for c in range(16):
        yc_tg = -190.0 if (c % 2 == 0) else -275.0
        p_tg_g = rt.route_pts(1, tgs[c].findPortInst("GND"), [(c * 51.0 - 3.0, yc_tg - 28.0)])
        gnd_bot.append(strap_pwr(p_tg_g, 1, 5, None, Y_GND_B))

    # Not & DFF GND
    p_not_g1 = rt.route_pts(1, not_gate.findPortInst("GND"), [(476.5, -686.0), (476.5, -688.0)])
    p_dff_g1 = dff.findPortInst("GND")
    make_manhattan_arc(rt.wires[1], ep, p_not_g1, p_dff_g1)
    p_out_g5 = rt.via_stack(590.0, -688.0, 1, 5, p_dff_g1)
    p_out_g5_b = rt.pin(5, 590.0, Y_GND_B)
    make_manhattan_arc(rt.wires[5], ep, p_out_g5, p_out_g5_b, width=8.0)
    gnd_bot.append(p_out_g5_b)

    # Input Buffers GND (M3 jog right to +11.0, straight up to Y_GND_B, via stack M3 to M5)
    for ib in [ib_addr, ib_clk, ib_ctrl, ib_din]:
        pg = ib.findPortInst("GND")
        px = pg.getCenter().getX()
        py = pg.getCenter().getY()
        px_jog = px + 11.0
        pg_j = rt.route_pts(3, pg, [(px_jog, py), (px_jog, Y_GND_B)])
        pg_m5 = rt.via_stack(px_jog, Y_GND_B, 3, 5, pg_j)
        gnd_bot.append(pg_m5)

    # Output Buffer GND (M1 at (1179.5, -698.0), jog right to 1191.0, drop M5 down to Y_GND_B)
    p_ob_gnd = ob_dout.findPortInst("GND")
    p_ob_g1 = rt.route_pts(1, p_ob_gnd, [(1191.0, -698.0)])
    p_ob_g5 = rt.via_stack(1191.0, -698.0, 1, 5, p_ob_g1)
    p_ob_g5_b = rt.pin(5, 1191.0, Y_GND_B)
    make_manhattan_arc(rt.wires[5], ep, p_ob_g5, p_ob_g5_b, width=8.0)
    gnd_bot.append(p_ob_g5_b)

    gnd_bl = rt.pin(5, X_GND_L, Y_GND_B)
    gnd_left.append(gnd_bl)
    gnd_bot.append(gnd_bl)
    gnd_left_s = sorted(gnd_left, key=lambda p: p.getCenter().getY())
    for i in range(len(gnd_left_s) - 1):
        make_manhattan_arc(rt.wires[5], ep, gnd_left_s[i], gnd_left_s[i+1], width=8.0)
    gnd_bot_s = sorted(gnd_bot, key=lambda p: p.getCenter().getX())
    for i in range(len(gnd_bot_s) - 1):
        make_manhattan_arc(rt.wires[5], ep, gnd_bot_s[i], gnd_bot_s[i+1], width=8.0)

    # 11. Exports
    Export.newInst(cell, ib_clk.findPortInst("IN"), "CLK", PortCharacteristic.IN)
    Export.newInst(cell, ib_addr.findPortInst("IN"), "ADDR_IN", PortCharacteristic.IN)
    Export.newInst(cell, ib_ctrl.findPortInst("IN"), "CTRL", PortCharacteristic.IN)
    Export.newInst(cell, ib_din.findPortInst("IN"), "DIN", PortCharacteristic.IN)
    Export.newInst(cell, ob_dout.findPortInst("OUT"), "DOUT", PortCharacteristic.OUT)
    Export.newInst(cell, vdd_bl, "VDD", PortCharacteristic.PWR)
    Export.newInst(cell, gnd_bl, "GND", PortCharacteristic.GND)
    Export.newInst(cell, p_sa_dl, "GBL", PortCharacteristic.BIDIR)
    Export.newInst(cell, p_sa_dlb, "GBLB", PortCharacteristic.BIDIR)

    # Ensure all nodes in Top{lay} have isUsernamed = False (no node name text!)
    nit = cell.getNodes()
    while nit.hasNext():
        n = nit.next()
        if n.isUsernamed():
            n.setName("")

    # 12. Verification
    total_arcs = 0
    non_m = 0
    ait = cell.getArcs()
    while ait.hasNext():
        a = ait.next()
        total_arcs += 1
        p1_pt = a.getHeadPortInst().getCenter()
        p2_pt = a.getTailPortInst().getCenter()
        dx_val = abs(p1_pt.getX() - p2_pt.getX())
        dy_val = abs(p1_pt.getY() - p2_pt.getY())
        if dx_val > 0.001 and dy_val > 0.001:
            non_m += 1
    print("Manhattan Check: %d / %d perpendicular (non-Manhattan: %d)" % (total_arcs - non_m, total_arcs, non_m))

    print("Running Quick DRC on Top{lay}...")
    logger = ErrorLogger()
    prefs = DRC.DRCPreferences(False)
    mode = GeometryHandler.GHMode.ALGO_SWEEP
    for m in Quick.getDeclaredMethods():
        if m.getName() == "checkDesignRules" and len(m.getParameterTypes()) == 9:
            m.setAccessible(True)
            m.invoke(None, [logger, cell, None, None, None, None, prefs, mode, False])
            break

    print("Quick DRC summary: total errors=%d, warnings=%d" % (logger.getNumErrors(), logger.getNumWarnings()))
    lit = logger.getLogs()
    while lit.hasNext():
        print("  DRC Log: %s" % lit.next().getMessageString())

    errs = ArrayList()
    DRC.checkDRCHierarchically(prefs, cell, errs, None, mode, False)
    print("Hierarchical DRC errors=%d" % len(errs))

    print("Running Hierarchical NCC against Top{sch} with checkSizes = True...")
    opts = NccOptions()
    opts.checkSizes = True
    res = Ncc.compare(sch, None, cell, None, opts)
    print("NCC result: match = %s" % res.match())

    if logger.getNumErrors() == 0 and len(errs) == 0 and res.match():
        print("PERFECT! Saving library to %s..." % jelib_path)
        Output.writeLibrary(lib, FileType.JELIB, False, False, False, 0)
        print("Successfully saved Top{lay} to %s" % jelib_path)
    else:
        print("Checks not all passing yet; not saving.")

jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
url = TextUtils.makeURLToFile(jelib_path)
ep = EditingPreferences(True, None)
lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)
mocmos = Technology.findTechnology("mocmos")
edb = lib.getDatabase()
batch = Setting.SettingChangeBatch()
batch.add(mocmos.getScaleSetting(), java.lang.Double(90.0))
edb.implementSettingChanges(batch)

test_build(lib, ep, mocmos)
