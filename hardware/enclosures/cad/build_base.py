from swlib import *
from params import *

hx, hy = W / 2, H / 2
T("close_document", discard_changes=True)
T("new_part")
# body + back edge round, then shell open at the lid side
m = sketch_on("front"); rrect(W, H, R); T("extrude", D)
T("fillet", 3.0, edge_points=[[hx, 0, 0]])
T("shell", WALL, open_face_points=[[0, 0, D]])
zi = WALL  # inner back face
# lid screw pillars (merge into the corner walls), flush with the rim
m = sketch_on(face=[0, 0, zi])
for sx in (-1, 1):
    for sy in (-1, 1):
        circle(m, PILLAR_D, sx * PILLAR_C[0], sy * PILLAR_C[1], zi)
T("extrude", D - zi)
T("hole", [[sx * PILLAR_C[0], sy * PILLAR_C[1], D] for sx in (-1, 1) for sy in (-1, 1)],
  diameter_mm=INSERT_D, depth_mm=INSERT_L)
# perfboard standoffs
m = sketch_on(face=[0, 0, zi])
pts = [(sx * PB_DX / 2, PB_CY + sy * PB_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]
for x, y in pts: circle(m, 7.0, x, y, zi)
T("extrude", PB_H)
T("hole", [[x, y, zi + PB_H] for x, y in pts], diameter_mm=2.5, depth_mm=PB_H)
# battery cradle frame (3 mm lip) + clamp-bar posts
m = sketch_on(face=[0, 10, zi])
s = m(0, BAT_CY, zi)
T("sketch_rectangle", BAT_L + 4, BAT_W + 4, s[0], s[1])
T("sketch_rectangle", BAT_L, BAT_W, s[0], s[1])
T("extrude", 3.0)
m = sketch_on(face=[0, 10, zi])
for sx in (-1, 1): circle(m, 8.0, sx * BAT_POST_X, BAT_CY, zi)
T("extrude", BAT_POST_H)
T("hole", [[sx * BAT_POST_X, BAT_CY, zi + BAT_POST_H] for sx in (-1, 1)], diameter_mm=2.5, depth_mm=10)
# internal bosses on the bottom wall for the sensor-pod screws (blind from outside -> stays sealed)
yb = -hy + WALL
m = sketch_on(face=[0, yb, 20])
for x, z in POD_BOSS: circle(m, 9.0, x, yb, z)
T("extrude", 8.0)
# ports in the bottom wall (outside face)
T("hole", [[x, -hy, PORT_Z] for x in GLANDS_X], diameter_mm=GLAND_D, depth_mm=WALL + 0.5)
T("hole", [[VENT_X, -hy, PORT_Z]], diameter_mm=VENT_D, depth_mm=WALL + 0.5)
T("hole", [[x, -hy, z] for x, z in POD_BOSS], diameter_mm=INSERT_D, depth_mm=WALL + 6.0)
# antenna bulkhead on top wall: inner boss (stiffens the 3 mm wall, flat seat for the nut) + 10 mm hole
yt = hy - WALL
m = sketch_on(face=[30, yt, SMA_Z])
circle(m, SMA_BOSS_D, 0, yt, SMA_Z); T("extrude", SMA_BOSS_T)
T("hole", [[0, hy, SMA_Z]], diameter_mm=SMA_D, depth_mm=WALL + SMA_BOSS_T + 0.5)
# mounting ears flush with the back (4x, M4 / U-bolt rail / wall screws)
m = sketch_on("front")
for sx in (-1, 1):
    for sy in (-1, 1):
        cx = sx * (hx + EAR_L / 2 - 1.0)
        T("sketch_rectangle", EAR_L + 2.0, EAR_W, cx, sy * EAR_Y)
T("extrude", EAR_T)
m = sketch_on("front")
for sx in (-1, 1):
    for sy in (-1, 1):
        T("sketch_circle", EAR_W, sx * (hx + EAR_L), sy * EAR_Y)
T("extrude", EAR_T)
T("hole", [[sx * (hx + EAR_L), sy * EAR_Y, EAR_T] for sx in (-1, 1) for sy in (-1, 1)],
  diameter_mm=EAR_HOLE, through_all=True)
T("set_material", "ABS")
say(T("get_bounding_box"))
say(T("check_model"))
save("SN_Base")
say(shot("SN_Base")); shot("SN_Base", "front")
