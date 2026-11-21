"""Reference models of the electronics, built in SolidWorks from manufacturer datasheet dimensions.

Every part is modelled directly in the NODE ASSEMBLY frame (box back = z 0, box centre = x/y 0,
pod hangs below y = -82.5), so each one is inserted at the origin and lands exactly where it mounts.
Simplified envelopes: boards, modules, connectors and sensor heads at their real outline/height,
no pin-level detail. Dimension sources are noted next to each part.
"""
import math, os, re, sys
from swlib import T, say, sketch_on, box_rect, com, typed, hide_planes, OUT
from params import *

DIR = os.path.join(OUT, "cad", "components")

# ------------------------------------------------------------------ colours (r, g, b)
PCB_GREEN, PCB_BLUE, PCB_BLACK, PCB_PURPLE = (0.08, 0.40, 0.18), (0.08, 0.20, 0.62), (0.06, 0.06, 0.07), (0.38, 0.12, 0.55)
SILVER, GOLD, BLACK, WHITE = (0.78, 0.78, 0.80), (0.85, 0.68, 0.25), (0.08, 0.08, 0.09), (0.93, 0.93, 0.91)
CELL_BLUE, GREY, ORANGE, RED = (0.10, 0.35, 0.75), (0.45, 0.46, 0.48), (0.95, 0.45, 0.10), (0.75, 0.12, 0.10)
CABLE = (0.12, 0.12, 0.13)

# ------------------------------------------------------------------ primitive builder
_planes = {}

def _plane(axis, off):
    ref = {"z": "front", "y": "top", "x": "right"}[axis]
    if abs(off) < 1e-9:
        return ref
    key = (axis, round(off, 4))
    if key not in _planes:
        r = T("create_plane", offset_mm=abs(off), reference=ref, flip=off < 0)
        _planes[key] = re.search(r"'([^']+)'", r).group(1)
    return _planes[key]

def _arr(v):
    import pythoncom
    from win32com.client import VARIANT
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x) for x in v])

def _colour(rgb, transp=0.0):
    """Colour every face created by the last feature."""
    v = _arr([rgb[0], rgb[1], rgb[2], 1.0, 1.0, 0.4, 0.3, transp, 0.0])
    def f(doc):
        d = typed(doc, "IModelDoc2")
        for fc in typed(d.FeatureByPositionReverse(0), "IFeature").GetFaces() or []:
            typed(fc, "IFace2").MaterialPropertyValues = v
    try:
        com(f)
    except Exception as e:
        say("   colour:", e)

def box(x0, x1, y0, y1, z0, z1, rgb):
    m = sketch_on(_plane("z", z0))
    box_rect(m, ((x0 + x1) / 2, (y0 + y1) / 2, z0), (x1 - x0, y1 - y0, 0))
    T("extrude", z1 - z0); _colour(rgb)

def cyl(axis, c, d, a0, a1, rgb, sides=0):
    """Cylinder (or n-sided prism if sides) along axis from a0 to a1; c = centre in the other two axes."""
    m = sketch_on(_plane(axis, a0))
    if axis == "z":   p = m(c[0], c[1], a0)
    elif axis == "y": p = m(c[0], a0, c[1])
    else:             p = m(a0, c[0], c[1])
    if sides:
        T("sketch_polygon", sides, d / math.cos(math.pi / sides), p[0], p[1])
    else:
        T("sketch_circle", d, p[0], p[1])
    T("extrude", a1 - a0); _colour(rgb)

def prism_x(pts_zy, x0, x1, rgb):
    """Polygon given in (z, y) extruded along x from x0 to x1."""
    m = sketch_on(_plane("x", x0))
    q = [m(x0, y, z) for z, y in pts_zy]
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        T("sketch_line", a[0], a[1], b[0], b[1])
    T("extrude", x1 - x0); _colour(rgb)

def part(name, build):
    global _planes
    _planes = {}
    for _ in range(4):
        if "ERROR" in T("close_document", discard_changes=True):
            break
    T("new_part")
    build()
    hide_planes(tuple(_planes.values()))
    os.makedirs(DIR, exist_ok=True)
    p = os.path.join(DIR, name + ".SLDPRT")
    T("save_document", p, overwrite=True)
    T("close_document")
    say("  built", name)
    return p

# ------------------------------------------------------------------ layout (box frame)
PB_Z = WALL + PB_H                 # perfboard underside (top of standoffs) = 9
PB_T = 1.6
PB_TOP = PB_Z + PB_T               # 10.6
ESP_X, ESP_Y0 = -17.0, 19.0        # DevKitC centre x, PCB bottom edge y (USB end down)
RA_C = (18.0, 64.0)                # Ra-02 adapter centre
TP_C = (18.0, 36.0)                # TP4056 centre
BOT_L = (-10.0, 3.5)               # JSN-SR04T driver board (flood)
BOT_R = (22.0, 3.0)                # YL-83 comparator (flood) / MPU6050 (landslide)
POD_TOP = -H / 2                   # -82.5
FLOOR = POD_TOP - POD_H + POD_WALL # pod floor top, -134.5

# ------------------------------------------------------------------ COMMON parts
def perfboard():
    # 70 x 90 x 1.6 mm FR-4 prototype board on the 4 standoffs
    box(-35, 35, PB_CY - 45, PB_CY + 45, PB_Z, PB_TOP, PCB_GREEN)

def esp32_devkitc():
    # Espressif ESP32-DevKitC V4, official dimension drawing (esp32_devkitc_v4_dimensions.pdf):
    # PCB 27.94 wide x 50.85 long (48.26 pin span + 1.29 + 1.30), 2x19 pins @2.54 in rows 25.40 apart,
    # ESP32-WROOM-32 module 18.00 wide x 25.5 x 3.1 mm whose RF antenna overhangs the top edge by 6.04,
    # micro-USB + EN/BOOT buttons at the bottom edge.
    # Plugged into 2x19 female headers (8.5 mm) on the perfboard; male header plastic 2.5 mm.
    L, Wd = 50.85, 27.94
    y0p, y1p = ESP_Y0 + 1.29, ESP_Y0 + 1.29 + 48.26                            # first / last pin centres
    for x in (ESP_X - 12.70, ESP_X + 12.70):
        box(x - 1.27, x + 1.27, y0p - 1.27, y1p + 1.27, PB_TOP, PB_TOP + 8.5, BLACK)         # female header
        box(x - 1.27, x + 1.27, y0p - 1.27, y1p + 1.27, PB_TOP + 8.5, PB_TOP + 11.0, BLACK)  # male header body
    zb = PB_TOP + 11.0
    box(ESP_X - Wd / 2, ESP_X + Wd / 2, ESP_Y0, ESP_Y0 + L, zb, zb + 1.6, PCB_BLACK)
    zm = zb + 1.6
    mtop = ESP_Y0 + L + 6.04
    box(ESP_X - 9.0, ESP_X + 9.0, mtop - 25.5, mtop, zm, zm + 0.8, PCB_BLACK)              # WROOM PCB + antenna
    box(ESP_X - 7.9, ESP_X + 7.9, mtop - 25.5 + 0.7, mtop - 25.5 + 0.7 + 17.6, zm + 0.8, zm + 3.1, SILVER)  # shield
    box(ESP_X - 3.9, ESP_X + 3.9, ESP_Y0 - 0.8, ESP_Y0 + 4.6, zm, zm + 2.6, SILVER)        # micro-USB
    for x in (ESP_X - 8.6, ESP_X + 8.6):                                                  # EN / BOOT
        box(x - 1.9, x + 1.9, ESP_Y0 + 0.8, ESP_Y0 + 6.6, zm, zm + 1.8, GREY)
    box(ESP_X - 2.6, ESP_X + 2.6, ESP_Y0 + 9.5, ESP_Y0 + 14.7, zm, zm + 0.9, BLACK)        # CP2102N
    box(ESP_X - 1.0, ESP_X + 5.0, ESP_Y0 + 17.5, ESP_Y0 + 22.5, zm, zm + 1.6, BLACK)       # AMS1117 LDO

def ra02():
    # Ai-Thinker Ra-02 (SX1278 433 MHz): 17 x 16 x 3.2 mm, on a 22 x 22 mm 2.54-pitch adapter
    # raised 2.5 mm on pin headers; IPEX (U.FL) at the top edge.
    cx, cy = RA_C
    z0 = PB_TOP + 2.5
    box(cx - 3, cx + 3, cy - 11, cy + 11, PB_TOP, z0, BLACK)                   # header strip
    box(cx - 11, cx + 11, cy - 11, cy + 11, z0, z0 + 1.6, PCB_BLUE)            # adapter
    zm = z0 + 1.6
    box(cx - 8.5, cx + 8.5, cy - 8.0, cy + 8.0, zm, zm + 0.8, PCB_BLACK)       # module PCB
    box(cx - 7.5, cx + 7.5, cy - 7.0, cy + 6.0, zm + 0.8, zm + 3.2, SILVER)    # shield
    box(cx + 4.5, cx + 7.5, cy + 6.2, cy + 7.8, zm + 0.8, zm + 2.0, GOLD)      # IPEX

def tp4056():
    # TP4056 USB-C charger with DW01A protection: 28 x 17 x 1.6 mm (long axis vertical),
    # USB-C 9.0 x 7.4 x 3.2 mm at the bottom end; 2.5 mm header standoff.
    cx, cy = TP_C
    z0 = PB_TOP + 2.5
    box(cx - 7, cx + 7, cy - 13, cy + 13, PB_TOP, z0, BLACK)
    box(cx - 8.5, cx + 8.5, cy - 14, cy + 14, z0, z0 + 1.6, PCB_BLUE)
    zt = z0 + 1.6
    box(cx - 4.5, cx + 4.5, cy - 14.8, cy - 7.4, zt, zt + 3.2, SILVER)         # USB-C
    box(cx - 2.5, cx + 2.5, cy - 2, cy + 3, zt, zt + 1.5, BLACK)               # TP4056 IC
    box(cx - 1.5, cx + 1.5, cy + 6, cy + 9, zt, zt + 1.2, BLACK)               # DW01A
    box(cx - 2.0, cx + 2.0, cy + 10, cy + 13, zt, zt + 1.2, BLACK)             # FS8205A

def battery_pack():
    # 2 x 18650 parallel holder 78 x 40 x 21 mm (black ABS) with 2 x 18650 cells (18.4 x 65.2 mm)
    y0, y1, z0 = BAT_CY - 20, BAT_CY + 20, WALL
    box(-39, 39, y0, y1, z0, z0 + 2.0, BLACK)                                   # floor
    for sx in (-1, 1):
        box(sx * 39 - (2 if sx > 0 else 0), sx * 39 + (2 if sx < 0 else 0), y0, y1, z0, z0 + 21, BLACK)  # end walls
    box(-37, 37, y0, y0 + 1.2, z0, z0 + 12, BLACK); box(-37, 37, y1 - 1.2, y1, z0, z0 + 12, BLACK)

def cells():
    zc = WALL + 2.0 + 9.2
    for yc in (BAT_CY - 9.45, BAT_CY + 9.45):
        cyl("x", (yc, zc), 18.4, -32.6, 32.6, CELL_BLUE)

def foam():
    box(-38, 38, BAT_CY - 6, BAT_CY + 6, WALL + 21, WALL + 22, (0.20, 0.20, 0.22))

def antenna():
    # 10 mm bulkhead (3/8"-32 TNC-style / SMA with reducer), hex nuts both sides, 433 MHz
    # rubber-duck antenna 110 mm, knuckle 15 mm.
    hy, x, z = H / 2, 0.0, SMA_Z
    cyl("y", (x, z), 9.5, hy - WALL - SMA_BOSS_T - 4.0, hy + 4.0, GOLD)          # threaded body
    cyl("y", (x, z), 14.0, hy - WALL - SMA_BOSS_T - 3.0, hy - WALL - SMA_BOSS_T, GOLD, sides=6)  # inner nut
    cyl("y", (x, z), 14.0, hy, hy + 3.0, GOLD, sides=6)                          # outer nut + O-ring
    cyl("y", (x, z), 10.0, hy + 4.0, hy + 19.0, BLACK)                           # knuckle
    cyl("y", (x, z), 10.0, hy + 19.0, hy + 125.0, BLACK)                         # whip

def pigtail():
    # U.FL -> bulkhead pigtail (1.13 mm coax), drawn as a 2 mm cable
    zc = PB_TOP + 2.5 + 1.6 + 2.0
    cyl("y", (RA_C[0] + 6.0, zc), 2.0, RA_C[1] + 7.8, RA_C[1] + 9.0, CABLE)
    cyl("x", (RA_C[1] + 9.0, zc), 2.0, 4.0, RA_C[0] + 6.0, CABLE)
    cyl("y", (4.0, zc), 2.0, RA_C[1] + 9.0, H / 2 - WALL - SMA_BOSS_T - 3.0, CABLE)

def glands():
    # 3 x PG7 (outside: 19 mm hex body + 15 mm dome; inside: 19 AF lock nut) + M12 breather vent
    yb = -H / 2
    for x in GLANDS_X:
        cyl("y", (x, PORT_Z), 19.0, yb - 4.0, yb, GREY, sides=6)
        cyl("y", (x, PORT_Z), 15.0, yb - 14.0, yb - 4.0, GREY)
        cyl("y", (x, PORT_Z), 19.0, yb + WALL, yb + WALL + 5.0, GREY, sides=6)
    cyl("y", (VENT_X, PORT_Z), 15.0, yb - 7.0, yb, (0.25, 0.25, 0.27))
    cyl("y", (VENT_X, PORT_Z), 17.0, yb + WALL, yb + WALL + 4.0, (0.25, 0.25, 0.27), sides=6)

def solar_cable():
    # 2-core solar lead in through G3, out of the pod's back cable hole
    # outside: gland G3 -> down into the pod -> out of the pod's back cable hole (y = -94.5)
    x, yb = GLANDS_X[2], -H / 2
    yh = yb - 12.0
    cyl("y", (x, PORT_Z), 4.0, yh, yb - 14.0, CABLE)
    cyl("z", (x, yh), 4.0, -25.0, PORT_Z, CABLE)
    # inside: up from the gland nut, over the battery clamp (z = 36), to the TP4056 IN+/IN- pads
    # (4 mm 2-core lead; drops onto the perfboard beside the TP4056's USB-C, clear of every board)
    zc, ye, xe = 36.0, 20.5, 29.0
    cyl("y", (x, PORT_Z), 4.0, yb + WALL + 5.0, yb + WALL + 9.0, CABLE)
    cyl("z", (x, yb + WALL + 9.0), 4.0, PORT_Z, zc, CABLE)
    cyl("y", (x, zc), 4.0, yb + WALL + 9.0, ye, CABLE)
    cyl("x", (ye, zc), 4.0, xe, x, CABLE)
    cyl("z", (xe, ye), 4.0, PB_TOP, zc, CABLE)

# ------------------------------------------------------------------ BOX-SIDE driver boards
def jsn_board():
    # JSN-SR04T v3 driver board 41 x 28.5 x 1.6 mm, transducer connector + crystal + 4-pin header
    cx, cy = BOT_L
    z0 = PB_TOP + 2.5
    box(cx - 20.5, cx + 20.5, cy - 14.25, cy + 14.25, z0, z0 + 1.6, PCB_GREEN)
    box(cx - 3, cx + 3, cy - 14, cy + 14, PB_TOP, z0, BLACK)
    zt = z0 + 1.6
    box(cx + 9, cx + 17, cy - 4, cy + 4, zt, zt + 6.0, WHITE)                   # XH connector
    box(cx - 15, cx - 5, cy - 3, cy + 3, zt, zt + 3.5, SILVER)                  # crystal
    box(cx - 2, cx + 6, cy - 8, cy + 8, zt, zt + 1.5, BLACK)                    # ICs

def yl83_comp():
    # YL-83 / FC-37 LM393 comparator board 30 x 16 x 1.6 mm + blue trim pot
    cx, cy = BOT_R
    z0 = PB_TOP + 2.5
    box(cx - 8, cx + 8, cy - 15, cy + 15, z0, z0 + 1.6, PCB_BLUE)
    box(cx - 3, cx + 3, cy - 14, cy + 14, PB_TOP, z0, BLACK)
    box(cx - 3.5, cx + 3.5, cy + 4, cy + 11, z0 + 1.6, z0 + 1.6 + 6.5, (0.15, 0.35, 0.85))

def mpu6050():
    # GY-521 MPU6050 breakout 21.2 x 16.4 x 1.6 mm, QFN 4 x 4 mm; screwed flat (rigid) on the board
    cx, cy = BOT_R
    z0 = PB_TOP + 2.5
    box(cx - 8.2, cx + 8.2, cy - 10.6, cy + 10.6, z0, z0 + 1.6, PCB_BLUE)
    box(cx - 3, cx + 3, cy - 10, cy + 10, PB_TOP, z0, BLACK)
    box(cx - 2, cx + 2, cy - 2, cy + 2, z0 + 1.6, z0 + 2.5, BLACK)

# ------------------------------------------------------------------ POD sensors (box frame)
def bme280():
    # GY-BME280 breakout 15.4 x 11.6 x 1.6 mm (sellers: 15.3-15.4 x 11.5-11.6), standing in its
    # card slot (x = -44), BME280 LGA 2.5 x 2.5 x 0.93 mm
    x = -44.0
    y0 = FLOOR + 2.0
    box(x - 0.8, x + 0.8, y0, y0 + 11.6, 26 - 7.7, 26 + 7.7, PCB_PURPLE)
    box(x + 0.8, x + 1.73, y0 + 6.5, y0 + 9.0, 24.75, 27.25, SILVER)

def mq_module():
    # MQ-2 / MQ-135 module: PCB 32 x 22 x 1.6 mm in the card slot at x = 30, sensor head
    # 19.8 mm dia x 16 mm (stainless mesh) facing +x towards the louvers
    x, y0, zc = 30.0, FLOOR + 2.0, 25.0
    box(x - 0.8, x + 0.8, y0, y0 + 22.0, zc - 16, zc + 16, PCB_BLUE)
    cyl("x", (y0 + 11.0, zc), 19.8, x + 0.8, x + 0.8 + 6.0, (0.70, 0.55, 0.35))     # bakelite base
    cyl("x", (y0 + 11.0, zc), 18.0, x + 6.8, x + 16.8, SILVER)                         # mesh cap
    box(x - 6.8, x - 0.8, y0 + 13, y0 + 19, zc + 4, zc + 10, (0.15, 0.35, 0.85))       # trim pot (above the slot block)

def ky026():
    # KY-026 flame sensor PCB 36 x 15 x 1.6 mm, 4 mm deep in its card slot (block 10 mm) at x = 15;
    # 5 mm IR photodiode at the board end, on the axis of the 18 mm window (centre y = -119)
    x, y0 = 15.0, FLOOR + 10.0 - 4.0
    box(x - 0.8, x + 0.8, y0, y0 + 15.0, 7.0, 43.0, PCB_BLACK)
    cyl("z", (x, -119.0), 5.0, 43.0, 48.8, (0.12, 0.12, 0.16))
    box(x - 7.8, x - 0.8, y0 + 8, y0 + 14, 18, 25, (0.15, 0.35, 0.85))               # trim pot (-x face)

def gp2y1010():
    # Sharp GP2Y1010AU0F 46 x 30 x 17.6 mm, lying on its 4 posts (top 8 mm above floor)
    # with its 9 mm sensing hole vertical
    y0 = FLOOR + 8.0
    box(-31, 15, y0, y0 + 17.6, 11, 41, (0.10, 0.10, 0.11))
    box(-4, 4, y0 + 17.6, y0 + 19.0, 20, 32, WHITE)                             # connector

def jsn_probe():
    # JSN-SR04T transducer: face lip 22 mm dia x 2 mm under the floor, body 18 mm dia x 23 mm
    # up through the socket, cable up to gland G1
    yb = POD_TOP - POD_H
    cyl("y", (15.0, 26.0), 22.0, yb - 2.0, yb, (0.10, 0.10, 0.11))
    cyl("y", (15.0, 26.0), JSN_D - 0.2, yb, yb + 23.0, (0.10, 0.10, 0.11))
    cyl("y", (15.0, 26.0), 5.0, yb + 23.0, yb + 30.0, CABLE)

def sensor_cables(xs):
    # leads from the glands down into the pod
    yb = -H / 2 - 14.0
    for x, ytop in xs:
        cyl("y", (x, PORT_Z), 4.0, ytop, yb, CABLE)

def rain_plate():
    # YL-83 rain plate 54 x 40 x 1.6 mm on the 20 deg tray of SN_Flood_RainPlateMount
    # (mount placed at (0, RAIN_Y0, -15); tray top from (z=0, y=64) falling at 20 deg)
    t = math.radians(20)
    u, n = (math.cos(t), -math.sin(t)), (math.sin(t), math.cos(t))
    oz, oy = -15.0, RAIN_Y0 + 64.0
    p0 = (oz + 5 * u[0] + 0.1 * n[0], oy + 5 * u[1] + 0.1 * n[1]); p1 = (p0[0] + 40 * u[0], p0[1] + 40 * u[1])
    pts = [p0, p1, (p1[0] + 1.6 * n[0], p1[1] + 1.6 * n[1]), (p0[0] + 1.6 * n[0], p0[1] + 1.6 * n[1])]
    prism_x(pts, -27, 27, PCB_BLUE)

def soil_probe():
    # Capacitive soil moisture sensor v1.2: 98 x 23 x 1.6 mm, electronics end inside the printed cap;
    # shown 40 mm below the pod, buried up to the cap
    x, z, ytop = 20.0, 26.0, POD_TOP - POD_H - 40.0
    box(x - 11.5, x + 11.5, ytop - 98.0, ytop - 4.0, z - 0.8, z + 0.8, PCB_BLACK)
    cyl("y", (x, z), 4.0, ytop, POD_TOP - POD_H + 5.0, CABLE)

# ------------------------------------------------------------------ which parts go in which node
COMMON = [("C_Perfboard_70x90", perfboard), ("C_ESP32_DevKitC_V4", esp32_devkitc), ("C_Ra-02_SX1278", ra02),
          ("C_TP4056_USB-C", tp4056), ("C_18650x2_Holder", battery_pack), ("C_18650_Cells", cells),
          ("C_Battery_Foam", foam), ("C_Antenna_433MHz", antenna), ("C_UFL_Pigtail", pigtail),
          ("C_PG7_Glands_Vent", glands), ("C_Solar_Cable", solar_cable)]
NODE = {
    "FLD1_Flood": [("C_JSN-SR04T_Board", jsn_board), ("C_YL-83_Comparator", yl83_comp), ("C_BME280", bme280),
                   ("C_JSN-SR04T_Probe", jsn_probe), ("C_YL-83_RainPlate", rain_plate),
                   ("C_Cables_FLD1", lambda: sensor_cables([(GLANDS_X[0], FLOOR + 14.0), (GLANDS_X[1], FLOOR + 26.0)]))],
    "SLD2_Landslide": [("C_MPU6050_GY-521", mpu6050), ("C_BME280", bme280), ("C_SoilProbe_v1.2", soil_probe),
                       ("C_Cables_SLD2", lambda: sensor_cables([(GLANDS_X[0], FLOOR + 14.0), (GLANDS_X[1], FLOOR + 3.0)]))],
    "FIR3_Fire": [("C_BME280", bme280), ("C_MQ_Module", mq_module), ("C_KY-026", ky026),
                  ("C_Cables_FIR3", lambda: sensor_cables([(GLANDS_X[0], FLOOR + 14.0), (GLANDS_X[1], FLOOR + 26.0)]))],
    "POL4_Pollution": [("C_MQ_Module", mq_module), ("C_GP2Y1010AU0F", gp2y1010),
                       ("C_Cables_POL4", lambda: sensor_cables([(GLANDS_X[0], FLOOR + 26.5), (GLANDS_X[1], FLOOR + 26.5)]))],
}

if __name__ == "__main__":
    want = set(sys.argv[1:])
    done = set()
    for name, fn in COMMON + [p for v in NODE.values() for p in v]:
        if name in done or (want and name not in want):
            continue
        part(name, fn); done.add(name)
