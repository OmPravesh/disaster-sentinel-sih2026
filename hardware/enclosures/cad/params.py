"""All enclosure dimensions (mm). Change here and re-run the build scripts."""
# ---- main box (common to all 4 nodes). Model frame: back face on z=0 (print bed), lid at z=D.
W, H, D = 110.0, 165.0, 52.0      # outer width (x), height (y), depth (z)
R = 10.0                          # vertical corner radius
WALL = 3.0
PILLAR_D, PILLAR_C = 10.0, (48.0, 75.5)   # lid screw pillars at (+-x, +-y)
INSERT_D, INSERT_L = 4.0, 10.0    # M3 x 5.7 heat-set insert pilot (or self-tap M3 directly)
# perfboard 70x90 on 4 standoffs at a 2.54-grid pattern (25 x 33 pitches) -> drill the board 2.5 mm
PB_DX, PB_DY, PB_CY, PB_H = 63.5, 83.82, 32.5, 6.0
# 2x18650 parallel holder (77-78 x 40-41 x 21 mm) cradle + clamp posts
BAT_L, BAT_W, BAT_CY = 79.4, 41.6, -40.0   # cradle: fits 77.5-78 mm holders with clearance
BAT_POST_X, BAT_POST_H = 46.0, 22.0
# bottom wall: PG7 glands (hole 12.5) + M12 breather vent (hole 12.3); z of their centres
GLAND_D, VENT_D, PORT_Z = 12.5, 12.3, 26.0
GLANDS_X = (-10.5, 10.5, 32.0)    # G1 sensor A, G2 sensor B, G3 solar (21.5 mm apart: PG7 nuts are 19 AF)
VENT_X = -32.0                    # M12 vent; clears the corner lid pillar and the pod bosses
POD_BOSS = [(-40.0, 8.0), (40.0, 8.0), (-40.0, 40.0), (40.0, 40.0)]  # (x,z) pod screw bosses
SMA_D, SMA_Z = 10.0, 26.0         # antenna bulkhead hole on top wall (10 mm)
SMA_BOSS_D, SMA_BOSS_T = 20.0, 3.0  # inner reinforcing boss -> 6 mm total wall at the antenna
EAR_Y, EAR_L, EAR_W, EAR_T, EAR_HOLE = 60.0, 13.0, 16.0, 5.0, 4.5
# ---- lid
LID_T, SKIRT_T, SKIRT_H, SKIRT_GAP = 4.0, 2.0, 5.0, 0.4
GASKET_T = 1.5
# ---- sensor pod (node specific). Pod frame: top (mates box bottom) at y=0, floor at y=-POD_H.
POD_H, POD_WALL = 55.0, 3.0
JSN_D = 18.2                      # JSN-SR04T probe body hole (sellers quote 18 mm; MEASURE yours)

RAIN_Y0 = H / 2 + 88.0           # flood rain-plate mount height on the pole: tray clears the 125 mm antenna
