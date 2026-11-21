"""Reference stills per node: lid + gasket hidden and the sensor pod see-through, so the
electronics and pod sensors are visible in place."""
import os, sys
from swlib import T, say, com, typed, OUT
import pythoncom
from win32com.client import VARIANT

DBL = lambda v: VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x) for x in v])

def still(node):
    for _ in range(6):
        if "ERROR" in T("close_document", discard_changes=True):
            break
    T("open_document", os.path.join(OUT, "cad", f"SN_Node_{node}.SLDASM"))
    out = os.path.join(OUT, "renders", f"SN_Node_{node}_inside.png")

    def f(doc):
        d = typed(doc, "IModelDoc2"); a = typed(doc, "IAssemblyDoc")
        for c in a.GetComponents(True):
            c = typed(c, "IComponent2")
            n = c.Name2
            if n.startswith("SN_Lid") or n.startswith("SN_Gasket"):
                c.Visible = 0                                     # swComponentHidden
            elif n.startswith("SN_Pod_"):
                v = DBL([0.80, 0.82, 0.84, 1, 1, 0.3, 0.3, 0.72, 0])                       # 72 % transparent
                try:
                    ok = c.SetMaterialPropertyValues2(v, 2, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, []))
                except Exception:
                    ok = False
                if not ok:
                    c.Visible = 0                                 # fall back: hide the pod shell
        d.ShowNamedView2("", 1)                                   # front ...
        typed(d.ActiveView, "IModelView").RotateAboutCenter(-0.38, -0.55)   # ... turned to a 3/4 view
        d.GraphicsRedraw2()
        d.ViewZoomtofit2()
        d.SaveAs3(out, 0, 1 | 2)
        return out
    say(com(f))
    T("close_document", discard_changes=True)

for node in (sys.argv[1:] or ["FLD1_Flood", "SLD2_Landslide", "FIR3_Fire", "POL4_Pollution"]):
    still(node)
