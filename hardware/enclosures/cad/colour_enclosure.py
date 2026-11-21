"""Give the printed enclosure parts display colours (ASA light grey, TPU black, ...)."""
import os
from swlib import T, say, com, typed, OUT
import pythoncom
from win32com.client import VARIANT
COL = {"SN_Base": (0.86, 0.87, 0.88), "SN_Lid": (0.93, 0.93, 0.91), "SN_Gasket_TPU": (0.05, 0.05, 0.05),
       "SN_PoleRail": (0.30, 0.31, 0.33), "SN_BatteryClamp": (0.30, 0.31, 0.33),
       "SN_Flood_RainPlateMount": (0.80, 0.81, 0.82), "SN_Landslide_SoilProbeCap": (0.80, 0.81, 0.82),
       "SN_Pod_Flood_FLD1": (0.80, 0.82, 0.84), "SN_Pod_Landslide_SLD2": (0.80, 0.82, 0.84),
       "SN_Pod_Fire_FIR3": (0.80, 0.82, 0.84), "SN_Pod_Pollution_POL4": (0.80, 0.82, 0.84)}
for n, c in COL.items():
    T("open_document", os.path.join(OUT, "cad", n + ".SLDPRT"))
    v = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [c[0], c[1], c[2], 1.0, 1.0, 0.3, 0.3, 0.0, 0.0])
    def f(doc):
        typed(doc, "IModelDoc2").MaterialPropertyValues = v
    com(f)
    T("save_document"); T("close_document")
    say("coloured", n)
