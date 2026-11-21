import os, sys
from swlib import *
from params import *
C = lambda n: os.path.join(OUT, "cad", n + ".SLDPRT")
NODES = {
    "FLD1_Flood": ("SN_Pod_Flood_FLD1", [("SN_Flood_RainPlateMount", 0, H / 2 + 25, -15)]),
    "SLD2_Landslide": ("SN_Pod_Landslide_SLD2", []),
    "FIR3_Fire": ("SN_Pod_Fire_FIR3", []),
    "POL4_Pollution": ("SN_Pod_Pollution_POL4", []),
}
for node, (pod, extra) in NODES.items():
    if sys.argv[1:] and node not in sys.argv[1:]:
        continue
    for _ in range(6):
        if "ERROR" in T("close_document", discard_changes=True): break
    T("new_assembly")
    T("insert_component", C("SN_Base"), 0, 0, 0)
    T("insert_component", C("SN_Gasket_TPU"), 0, 0, D)
    T("insert_component", C("SN_Lid"), 0, 0, D + GASKET_T)
    T("insert_component", C("SN_BatteryClamp"), 0, BAT_CY, WALL + BAT_POST_H)
    T("insert_component", C(pod), 0, -H / 2, 0)
    for y in (EAR_Y, -EAR_Y):
        T("insert_component", C("SN_PoleRail"), 0, y, -11)
    for n, x, y, z in extra:
        T("insert_component", C(n), x, y, z)
    say(node, T("check_interference"))
    p = os.path.join(OUT, "cad", f"SN_Node_{node}.SLDASM")
    T("save_document", p, overwrite=True)
    T("export_document", ["step"], os.path.join(OUT, "step"))
    shot(f"SN_Node_{node}"); shot(f"SN_Node_{node}", "front")
