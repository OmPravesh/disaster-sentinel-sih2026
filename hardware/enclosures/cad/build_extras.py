from swlib import *
from params import *

def fresh():
    T("close_document", discard_changes=True); T("new_part")

# ---------------- FLOOD: YL-83 rain plate mount (clamps to the pole above the box, 20 deg tilt)
fresh()
m = sketch_on("right")
pts_zy = [(0, 0), (4, 0), (4, 30), (30, 49.1), (47, 42.9), (47, 46.9), (0, 64)]
poly([m(0, y, z) for z, y in pts_zy])
T("extrude", 64, end_condition="midplane")
m = sketch_on(face=[0, 8, 0])
for sx in (-1, 1): box_rect(m, (sx * 20, 15, 0), (3.5, 15, 0))
T("cut_extrude", through_all=True)
# drip / cable notch at the low edge so the YL-83 lead runs down behind the tray
T("set_material", "ABS")
say(T("check_model")); save("SN_Flood_RainPlateMount"); shot("SN_Flood_RainPlateMount")

# ---------------- LANDSLIDE: cap for the capacitive soil sensor v1.2 electronics (fill with silicone)
fresh()
sketch_on("front"); rrect(30, 14, 3); T("extrude", 40)
m = sketch_on(face=[0, 0, 0]); box_rect(m, (0, 0, 0), (24.6, 9.0, 0)); T("cut_extrude", 36)
T("hole", [[0, 0, 40]], diameter_mm=6.0, depth_mm=4.5)
T("set_material", "ABS")
say(T("check_model")); save("SN_Landslide_SoilProbeCap"); shot("SN_Landslide_SoilProbeCap")
