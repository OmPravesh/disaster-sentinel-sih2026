"""Assembly animation per node: every part flies in to its mounted position, the lid closes,
then the camera orbits the finished node. Frames are captured from SolidWorks and encoded to MP4."""
import math, os, shutil, sys
from swlib import T, say, com, typed, OUT, S, _loop
import imageio.v2 as imageio
import pythoncom
from win32com.client import VARIANT
DBL = lambda v: VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x) for x in v])

FPS, MOVE, HOLD, ORBIT = 24, 6, 2, 48
VID = os.path.join(OUT, "video")

def plan(name):
    """(group order, explode offset mm) for a component name."""
    n = name.upper()
    table = [
        ("POLERAIL", 0, (0, 0, -90)), ("POD_", 1, (0, -110, 0)), ("PG7", 2, (0, -60, 0)),
        ("SOLAR", 3, (0, -60, -40)), ("18650X2", 4, (0, 0, 120)), ("CELLS", 5, (0, 0, 130)),
        ("FOAM", 6, (0, 0, 130)), ("BATTERYCLAMP", 7, (0, 0, 130)), ("PERFBOARD", 8, (0, 0, 140)),
        ("ESP32", 9, (0, 0, 150)), ("RA-02", 10, (0, 0, 150)), ("TP4056", 11, (0, 0, 150)),
        ("JSN-SR04T_BOARD", 12, (0, 0, 150)), ("YL-83_COMP", 12, (0, 0, 150)), ("MPU6050", 12, (0, 0, 150)),
        ("ANTENNA", 13, (0, 140, 0)), ("PIGTAIL", 14, (0, 0, 150)),
        ("BME280", 15, (0, 0, 150)), ("MQ_", 15, (0, 0, 150)), ("KY-026", 15, (0, 0, 150)),
        ("GP2Y", 15, (0, 0, 150)), ("JSN-SR04T_PROBE", 15, (0, -120, 0)), ("SOILPROBE", 15, (0, -120, 0)),
        ("CABLES", 16, (0, 0, 150)), ("RAINPLATEMOUNT", 17, (0, 120, 0)), ("RAINPLATE", 18, (0, 140, 0)),
        ("GASKET", 19, (0, 0, 120)), ("LID", 20, (0, 0, 160)),
    ]
    for key, g, off in table:
        if key in n:
            return g, off
    return None, None

def run(node):
    asm = os.path.join(OUT, "cad", f"SN_Node_{node}.SLDASM")
    for _ in range(6):
        if "ERROR" in T("close_document", discard_changes=True): break
    say(T("open_document", asm))
    frames_dir = os.path.join(VID, "_frames_" + node)
    shutil.rmtree(frames_dir, ignore_errors=True); os.makedirs(frames_dir)
    state = {}
    base = {}

    def setup(doc):
        d = typed(doc, "IModelDoc2"); a = typed(doc, "IAssemblyDoc")
        mu = typed(typed(S.get_sw(), "ISldWorks").GetMathUtility(), "IMathUtility")
        comps = []
        for c in a.GetComponents(True):
            c = typed(c, "IComponent2")
            g, off = plan(c.Name2)
            if g is None:
                continue
            if c.IsFixed():
                c.Select4(False, None, False); a.UnfixComponent()
            comps.append((g, off, c))
            base[c.Name2] = list(typed(c.Transform2, "IMathTransform").ArrayData)
        state.update(d=d, a=a, mu=mu, comps=comps)
        d.ShowNamedView2("", 7)                      # isometric
        return len(comps)
    say(node, "moving parts:", com(setup))

    def place(c, off, k):
        """k = 1 fully exploded, 0 at home."""
        arr = list(base[c.Name2])
        for i in range(3):
            arr[9 + i] += off[i] * k / 1000.0          # add the fly-in offset to the part's real placement
        c.Transform2 = typed(state["mu"].CreateTransform(DBL(arr)), "IMathTransform")

    n = [0]
    def grab(doc, repeat=1):
        d = state["d"]; d.GraphicsRedraw2()
        p = os.path.join(frames_dir, f"f{n[0]:05d}.png")
        d.SaveAs3(p, 0, 1 | 2)
        for _ in range(repeat - 1):
            n[0] += 1; shutil.copy(p, os.path.join(frames_dir, f"f{n[0]:05d}.png"))
        n[0] += 1

    def explode_all(doc):
        for g, off, c in state["comps"]:
            place(c, off, 1.0)
        state["d"].GraphicsRedraw2()
        state["d"].ViewZoomtofit2()
        v = typed(state["d"].ActiveView, "IModelView")
        v.Scale2 = v.Scale2 * 0.9                       # margin so nothing is clipped
    com(explode_all)
    com(lambda doc: grab(doc, FPS))                  # 1 s on the exploded view

    groups = sorted({g for g, _, _ in state["comps"]})
    for g in groups:
        members = [(off, c) for gg, off, c in state["comps"] if gg == g]
        for i in range(1, MOVE + 1):
            k = 1 - (1 - math.cos(math.pi * i / MOVE)) / 2      # ease in-out
            def step(doc, k=k, members=members):
                for off, c in members:
                    place(c, off, k)
                grab(doc)
            com(step)
        com(lambda doc: grab(doc, HOLD))
    com(lambda doc: (state["d"].GraphicsRedraw2(), state["d"].ViewZoomtofit2(), grab(doc, FPS)))
    def orbit(doc):
        v = typed(state["d"].ActiveView, "IModelView")
        for i in range(ORBIT):
            v.RotateAboutCenter(0.0, 2 * math.pi / ORBIT)
            grab(doc)
    com(orbit)
    com(lambda doc: grab(doc, FPS))

    os.makedirs(VID, exist_ok=True)
    out = os.path.join(VID, f"SN_Node_{node}_assembly.mp4")
    files = sorted(os.listdir(frames_dir))
    first = imageio.imread(os.path.join(frames_dir, files[0]))
    h, w = (first.shape[0] // 2) * 2, (first.shape[1] // 2) * 2
    with imageio.get_writer(out, fps=FPS, codec="libx264", quality=8, macro_block_size=2) as wr:
        for f in files:
            wr.append_data(imageio.imread(os.path.join(frames_dir, f))[:h, :w, :3])
    shutil.copy(os.path.join(frames_dir, files[-1]), os.path.join(OUT, "renders", f"SN_Node_{node}_complete.png"))
    shutil.rmtree(frames_dir, ignore_errors=True)
    T("close_document", discard_changes=True)
    say("video:", out, len(files), "frames")

for node in (sys.argv[1:] or ["FLD1_Flood", "SLD2_Landslide", "FIR3_Fire", "POL4_Pollution"]):
    run(node)
