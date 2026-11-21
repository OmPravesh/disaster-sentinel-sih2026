import sys
from swlib import *
from params import *
hx = W / 2
PH, PW = POD_H, POD_WALL
FT = -PH + PW               # floor top y
ZC = D / 2

def card_slot(xc, zc, pcb_w, h, pcb_t=1.9, depth=None, low_px=False):
    """Block on the floor with a slot that holds a sensor PCB upright (edge in slot + drop of glue).
    PCB plane is YZ (board faces +-x)."""
    m = sketch_on(face=[xc, FT, 47.5])
    box_rect(m, (xc, FT, zc), (6.0, 0, pcb_w + 4.0)); T("extrude", h)
    m = sketch_on(face=[xc + 2.2, FT + h, zc])
    box_rect(m, (xc, FT + h, zc), (pcb_t, 0, pcb_w + 0.6)); T("cut_extrude", depth or (h - 2.0))
    if low_px:
        # cut the +x wall down to a 1 mm lip so a sensor head on the PCB's +x face clears the block
        lip = FT + h - (depth or (h - 2.0)) + 1.0
        m = sketch_on(face=[xc - 2.2, FT + h, zc])
        box_rect(m, (xc + 2.0, FT + h, zc), (2.2, 0, pcb_w + 6.0)); T("cut_extrude", FT + h - lip)

def shell_pod(skip_slots=()):
    T("close_document", discard_changes=True); T("new_part")
    sketch_on("front"); rrect(W, PH, R, 0, -PH / 2); T("extrude", D)
    T("shell", PW, open_face_points=[[0, 0, ZC]])
    # screw pillars (counterbored from below, M3x12 into the box's heat-set inserts)
    m = sketch_on("top")
    for x, z in POD_BOSS: circle(m, 9.0, x, 0, z)
    T("extrude", PH - PW, reverse=True)
    T("hole", [[x, -PH, z] for x, z in POD_BOSS], diameter_mm=3.4, through_all=True,
      style="counterbore", counterbore_diameter_mm=6.5, counterbore_depth_mm=PH - 6.0)
    # angled side louvers: 2.5 mm slots falling 45 deg outward -> no straight path for rain
    pl = T("create_plane", offset_mm=ZC, reference="front")
    import re
    name = re.search(r"'([^']+)'", pl).group(1) if "'" in pl else "Plane1"
    m = sketch_on(name)
    for y0 in (-14, -20, -26, -32, -38):
        for s in (-1, 1):
            pts = [(s * 51.0, y0), (s * 51.0, y0 + 2.5), (s * 55.5, y0 - 2.0), (s * 55.5, y0 - 4.5)]
            poly([m(px, py, ZC) for px, py in pts])
    T("cut_extrude", 20.0, depth2_mm=20.0)
    # floor slots: drainage + air intake + zip-tie anchors
    m = sketch_on(face=[0, -PH, 47.5])
    for i in range(12):
        x = -33 + 6 * i
        if any(a <= x <= b for a, b in skip_slots):
            continue
        a, b = m(x, -PH, 12), m(x, -PH, 40)
        T("sketch_slot", a[0], a[1], b[0], b[1], 3.0)
    T("cut_extrude", PW + 0.5)
    # cable exits in the back wall (soil probe / rain plate / solar)
    T("hole", [[sx * GLANDS_X[2], -12, 0] for sx in (-1, 1)], diameter_mm=8.0, depth_mm=PW + 0.5)

def finish(name):
    T("set_material", "ABS")
    say(name, T("check_model"), T("get_bounding_box"))
    hide_planes(); save(name); shot(name); shot(name, "top")

def flood():
    shell_pod(skip_slots=[(-2, 32)])
    card_slot(-44, 26, 16, 8)                         # BME280 (GY-BME280, 13-15 mm wide)
    # JSN-SR04T probe socket, looking straight down at the water
    m = sketch_on(face=[0, FT, 47.5])
    circle(m, 30, 15, FT, 26); circle(m, JSN_D, 15, FT, 26); T("extrude", 8)
    T("hole", [[15, -PH, 26]], diameter_mm=JSN_D, depth_mm=PW + 0.5)
    finish("SN_Pod_Flood_FLD1")

def landslide():
    shell_pod(skip_slots=[(12, 28)])
    card_slot(-44, 26, 16, 8)                         # BME280
    T("hole", [[20, -PH, 26]], diameter_mm=10.0, depth_mm=PW + 0.5)   # soil-probe cable, drips down
    finish("SN_Pod_Landslide_SLD2")

def fire():
    shell_pod(skip_slots=[(-1.5, 1.5), (12, 18), (27, 33)])
    # divider: keeps the MQ-2 heater (~0.8 W) away from the BME280
    m = sketch_on("top"); box_rect(m, (0, 0, ZC), (2.0, 0, D - 2 * PW)); T("extrude", PH - PW, reverse=True)
    m = sketch_on("top"); box_rect(m, (0, 0, 24), (4.0, 0, 10.0)); T("cut_extrude", 6.0)
    card_slot(-44, 26, 16, 8)                         # BME280 (left, cool chamber)
    card_slot(30, 25, 33, 8, low_px=True)             # MQ-2 module 32 x 22, dome facing +x louvers
    card_slot(15, 25, 36, 10, depth=4)                 # KY-026 flame: shallow slot, IR LED at the board end in line with the window
    # IR window: 18 mm aperture, 25 x 2 mm acrylic/glass disc glued in from inside, rain visor above
    T("hole", [[15, -36.5, D]], diameter_mm=18.0, depth_mm=PW + 0.5)
    m = sketch_on(face=[15, -24.0, D - PW]); circle(m, 25.4, 15, -36.5, D - PW); T("cut_extrude", 1.6)
    # 45 deg wedge visor (prints upright without support)
    pl = T("create_plane", offset_mm=15.0, reference="right")
    m = sketch_on("Plane2")
    poly([m(15, y, z) for z, y in ((D - 1, -21.0), (D + 9, -21.0), (D - 1, -31.0))])
    T("extrude", 32.0, end_condition="midplane")
    finish("SN_Pod_Fire_FIR3")

def pollution():
    shell_pod(skip_slots=[(27, 33)])
    card_slot(30, 25, 33, 8, low_px=True)             # MQ-135 module, dome facing +x louvers
    # GP2Y1010AU0F (46 x 30 x 17.6) lies flat on 4 posts so air convects up through its hole;
    # zip-tie it through the floor slots
    m = sketch_on(face=[0, FT, 47.5])
    for x in (-29, 13):
        for z in (13, 39): circle(m, 6, x, FT, z)
    T("extrude", 8)
    finish("SN_Pod_Pollution_POL4")

for n in (sys.argv[1:] or ["flood", "landslide", "fire", "pollution"]):
    globals()[n]()
