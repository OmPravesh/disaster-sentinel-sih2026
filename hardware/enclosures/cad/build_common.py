from swlib import *
from params import *
import sys
ONLY = set(sys.argv[1:])
want = lambda k: not ONLY or k in ONLY
hx, hy = W / 2, H / 2
PC = [(sx * PILLAR_C[0], sy * PILLAR_C[1]) for sx in (-1, 1) for sy in (-1, 1)]

def fresh():
    T("close_document", discard_changes=True); T("new_part")


def build_lid():
    # frame: sealing face z=0 (sits on the gasket), outside face z=LID_T, skirt goes into the box (-z)
    fresh()
    sketch_on("front"); rrect(W, H, R); T("extrude", LID_T)
    T("chamfer", 1.2, edge_points=[[hx, 0, LID_T]])
    # locating skirt (inside the walls, 0.4 mm gap) - also a labyrinth behind the gasket
    iw, ih, ir = W - 2 * WALL - 2 * SKIRT_GAP, H - 2 * WALL - 2 * SKIRT_GAP, R - WALL - SKIRT_GAP
    m = sketch_on(face=[0, 0, 0])
    rrect(iw, ih, ir); rrect(iw - 2 * SKIRT_T, ih - 2 * SKIRT_T, max(ir - SKIRT_T, 1.0))
    T("extrude", SKIRT_H)
    # clearance for the corner pillars
    m = sketch_on(face=[0, ih / 2 - SKIRT_T / 2, -SKIRT_H])
    for x, y in PC: circle(m, PILLAR_D + 1.0, x, y, -SKIRT_H)
    T("cut_extrude", SKIRT_H)
    # gasket compression bead on the rim centre line (0.8 wide, 0.6 high)
    m = sketch_on(face=[0, 0, 0])
    c = WALL / 2
    rrect(W - 2 * c + 0.8, H - 2 * c + 0.8, R - c + 0.4); rrect(W - 2 * c - 0.8, H - 2 * c - 0.8, R - c - 0.4)
    T("extrude", 0.6)
    # screw holes M3 + shallow spot-face for a sealing washer
    T("hole", [[x, y, LID_T] for x, y in PC], diameter_mm=3.4, through_all=True,
      style="counterbore", counterbore_diameter_mm=7.5, counterbore_depth_mm=1.0)
    # front logo: TEAM WAYWOT · SIH 2026 (engraved)
    import logo; logo.engrave(LID_T)
    # small recessed panel for the node-ID sticker (FLD1 / SLD2 / FIR3 / POL4)
    m = sketch_on(face=[0, -40, LID_T])
    rrect(56, 13, 3, *m(0, -58, LID_T)); T("cut_extrude", 0.6)
    T("set_material", "ABS")
    say(T("check_model")); save("SN_Lid"); shot("SN_Lid"); shot("SN_Lid", "front")

def build_gasket():
    fresh()
    sketch_on("front"); rrect(W, H, R); rrect(W - 2 * WALL, H - 2 * WALL, R - WALL)
    T("extrude", GASKET_T)
    m = sketch_on("front")
    for x, y in PC: T("sketch_circle", PILLAR_D, x, y)
    T("extrude", GASKET_T)
    T("hole", [[x, y, GASKET_T] for x, y in PC], diameter_mm=3.4, through_all=True)
    T("set_material", "Rubber")
    say(T("check_model")); save("SN_Gasket_TPU"); shot("SN_Gasket_TPU")

def build_rail():
    # back of rail (pole side) z<0, front pads bolt to the ears and leave a 6 mm gap for the hose clamp
    RL, RW, RT, PAD = 2 * (hx + EAR_L) + 16, 24.0, 5.0, 6.0
    fresh()
    sketch_on("front"); rrect(RL, RW, 4); T("extrude", RT)
    m = sketch_on(face=[0, 0, RT])
    for sx in (-1, 1): T("sketch_rectangle", 18, RW, sx * (hx + EAR_L), 0)
    T("extrude", PAD)
    T("hole", [[sx * (hx + EAR_L), 0, RT + PAD] for sx in (-1, 1)], diameter_mm=4.5, through_all=True)
    # band-clamp slots (for 9-13 mm stainless hose clamps), pole 40-110 mm
    m = sketch_on(face=[0, 0, RT])
    for sx in (-1, 1): T("sketch_rectangle", 3.5, 15, *m(sx * 30, 0, RT))
    T("cut_extrude", through_all=True)
    # V-saddle ribs on the pole side
    m = sketch_on("front")
    for sx in (-1, 1): T("sketch_rectangle", 4, RW, sx * 13, 0)
    T("extrude", 4, reverse=True)
    T("set_material", "ABS")
    say(T("check_model")); save("SN_PoleRail"); shot("SN_PoleRail")

def build_clamp():
    fresh()
    sketch_on("front"); rrect(2 * BAT_POST_X + 10, 12, 4); T("extrude", 3)
    T("hole", [[sx * BAT_POST_X, 0, 3] for sx in (-1, 1)], diameter_mm=3.4, through_all=True)
    T("set_material", "ABS")
    say(T("check_model")); save("SN_BatteryClamp"); shot("SN_BatteryClamp")

for k in ('lid', 'gasket', 'rail', 'clamp'):
    if want(k):
        globals()['build_' + k]()
