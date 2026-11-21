"""Synchronous helpers over the solidworks-mcp tool functions (github.com/MatteoBaisini/solidworks-mcp).
Each call runs the MCP server's own tool implementation, so the build is identical to driving the
server from an MCP client, but it is a re-runnable, parametric script."""
import asyncio, os, re
from solidworks_mcp import server as S
import logging
logging.getLogger("SW-MCP").setLevel(logging.CRITICAL)
S.CONFIG.command_timeout_s = 900.0   # large assemblies / frame capture take longer than the 90 s default

_loop = asyncio.new_event_loop()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.abspath(OUT)
LOG = []

def T(name, *a, **k):
    try:
        r = _loop.run_until_complete(getattr(S, name)(*a, **k))
    except Exception as e:
        r = f"ERROR {type(e).__name__}: {e}"
    s = r if isinstance(r, str) else str(r)
    LOG.append(f"{name}: {s[:160]}")
    low = s.lower()
    if any(w in low for w in ("error", "failed", "could not", "not found", "no face", "nothing")):
        print(f"  !! {name}{a}{k}: {s}", flush=True)
    return r

def say(*a):
    print(*a, flush=True)

# ---------- sketch helpers -------------------------------------------------
_MAP = {}
_vec = r"\(([-\d.e]+), ([-\d.e]+), ([-\d.e]+)\)"

def _parse(msg):
    m = re.search(r"origin at model " + _vec + r".*?sketch X runs along model " + _vec +
                  r", sketch Y along model " + _vec, msg)
    if not m:
        raise RuntimeError("cannot parse sketch axes: " + msg)
    v = [float(x) for x in m.groups()]
    return v[0:3], v[3:6], v[6:9]

def sketch_on(plane=None, face=None):
    """Open a sketch on a named/base plane or on the face through model point `face`.
    Returns a function m(x,y,z)->(sx,sy) converting model mm to sketch mm."""
    if plane:
        T("select_plane", plane)
    else:
        T("select_face_at_point", *face)
    msg = T("start_sketch")
    o, X, Y = _parse(msg)
    def m(x, y, z):
        d = (x - o[0], y - o[1], z - o[2])
        return (round(sum(a * b for a, b in zip(d, X)), 4), round(sum(a * b for a, b in zip(d, Y)), 4))
    return m

def rrect(w, h, r, cx=0.0, cy=0.0):
    """Rounded rectangle centred at (cx,cy) in sketch coords, drawn as 4 lines + 4 arcs."""
    if r <= 0:
        T("sketch_rectangle", w, h, cx, cy); return
    a, b = w / 2 - r, h / 2 - r
    T("sketch_line", cx - a, cy - h / 2, cx + a, cy - h / 2)
    T("sketch_line", cx + w / 2, cy - b, cx + w / 2, cy + b)
    T("sketch_line", cx + a, cy + h / 2, cx - a, cy + h / 2)
    T("sketch_line", cx - w / 2, cy + b, cx - w / 2, cy - b)
    T("sketch_arc", cx + a, cy - b, cx + a, cy - h / 2, cx + w / 2, cy - b, True)
    T("sketch_arc", cx + a, cy + b, cx + w / 2, cy + b, cx + a, cy + h / 2, True)
    T("sketch_arc", cx - a, cy + b, cx - a, cy + h / 2, cx - w / 2, cy + b, True)
    T("sketch_arc", cx - a, cy - b, cx - w / 2, cy - b, cx - a, cy - h / 2, True)

def circle(m, d, x, y, z):
    sx, sy = m(x, y, z)
    T("sketch_circle", d, sx, sy)

def rect(m, w_model_axis, h_model_axis, x, y, z, w, h):
    """Rectangle centred at model point; w,h are sizes along sketch X/Y."""
    sx, sy = m(x, y, z)
    T("sketch_rectangle", w, h, sx, sy)

def poly(pts):
    """Closed polyline from sketch points."""
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        T("sketch_line", a[0], a[1], b[0], b[1])

def last_feature():
    tree = T("get_feature_tree")
    return tree

def save(name, stl=True):
    path = os.path.join(OUT, "cad", name + ".SLDPRT")
    T("save_document", path, overwrite=True)
    fm = ["step", "stl"] if stl else ["step"]
    T("export_document", fm, os.path.join(OUT, "{format}"))
    say("saved", path)

def shot(name, view="isometric"):
    r = _loop.run_until_complete(S.get_screenshot(view))
    # get_screenshot returns an MCP Image; write its bytes
    data = getattr(r, "data", None)
    if data is None and isinstance(r, (list, tuple)):
        for it in r:
            data = getattr(it, "data", None) or data
    if data:
        import base64
        p = os.path.join(OUT, "renders", f"{name}_{view}.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        raw = data if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
        open(p, "wb").write(raw)
        return p
    say("  (no screenshot data)", type(r))

def box_rect(m, c, d):
    """Rectangle for a model-space box centred at c with sizes d (one of them ~0 along the normal)."""
    p1 = m(c[0] - d[0] / 2, c[1] - d[1] / 2, c[2] - d[2] / 2)
    p2 = m(c[0] + d[0] / 2, c[1] + d[1] / 2, c[2] + d[2] / 2)
    w, h = abs(p2[0] - p1[0]), abs(p2[1] - p1[1])
    T("sketch_rectangle", w, h, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def com(fn):
    """Run a raw COM callable fn(doc) on the MCP server's COM thread."""
    def work():
        return fn(S.active_doc())
    return _loop.run_until_complete(S.com_tool(work))

def hide_planes(names=("Plane1", "Plane2")):
    for n in names:
        if "ERROR" in T("select_plane", n): continue
        try:
            com(lambda doc: doc.BlankRefGeom())
        except Exception:
            pass
    try:
        com(lambda doc: doc.ClearSelection2(True))
    except Exception:
        pass

# ---------- early-bound access (needed for sketch text) ----------
_TLB = r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldworks.tlb"
_mod = None

def typed(obj, iface):
    global _mod
    import pythoncom, win32com.client
    from win32com.client import gencache
    if _mod is None:
        tl = pythoncom.LoadTypeLib(_TLB)
        a = tl.GetLibAttr()
        _mod = gencache.EnsureModule(str(a[0]), a[1], a[3], a[4])
    return getattr(_mod, iface)(getattr(obj, '_oleobj_', obj))

def sketch_text(text, x, y, height_mm, font="Bahnschrift", bold=True, width_pct=100, spacing_pct=100):
    """Insert centred text into the OPEN sketch at sketch (x, y) mm. Returns its sketch bounding size."""
    def f(doc):
        d = typed(doc, "IModelDoc2")
        st = d.InsertSketchText(x / 1000, y / 1000, 0.0, text, 2, 0, 0, width_pct, spacing_pct)
        if st is None:
            raise RuntimeError("InsertSketchText returned nothing")
        st = typed(st, "ISketchText")
        tf = typed(st.GetTextFormat(), "ITextFormat")
        tf.TypeFaceName = font; tf.CharHeight = height_mm / 1000; tf.Bold = bold
        st.SetTextFormat(False, tf)
        d.GraphicsRedraw2()
        return True
    return com(f)
