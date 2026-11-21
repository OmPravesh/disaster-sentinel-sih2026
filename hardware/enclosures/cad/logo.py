"""TEAM WAYWOT · SIH 2026 front logo, engraved into the lid's outside face (z = LID_T)."""
import math
from swlib import T, sketch_on, sketch_text

DEPTH = 0.8          # 4 layers at 0.2 mm; fill with paint for contrast (see README)
STROKE = 1.6         # line-art stroke width (4 extrusion widths with a 0.4 mm nozzle)

# text: (string, cap height mm, font, bold, char spacing %, baseline y, measured left/right ink at x=0)
# ink extents were measured in SolidWorks at a reference size and scale with height
TEXT = [
    ("TEAM",     6.0, "Century Gothic", False, 200, 20.0, (0.06 / 5, 30.30 / 5)),
    ("WAYWOT",  12.0, "Segoe UI",       True,  100,  3.0, (1.33 / 14, 92.84 / 14)),
    ("SIH 2026", 7.0, "Century Gothic", False, 160, -17.0, (0.32 / 6, 52.54 / 6)),
]

def _cut(z, draw):
    m = sketch_on(face=[0, -40, z])          # lid face, clear of all artwork
    draw(m)
    T("cut_extrude", DEPTH)

def _arc_band(m, z, cx, cy, r1, r2, a0, a1):
    p = lambda r, a: m(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), z)
    c = m(cx, cy, z)
    o0, o1, i0, i1 = p(r2, a0), p(r2, a1), p(r1, a0), p(r1, a1)
    T("sketch_arc", c[0], c[1], o0[0], o0[1], o1[0], o1[1], True)
    T("sketch_line", o1[0], o1[1], i1[0], i1[1])
    T("sketch_arc", c[0], c[1], i1[0], i1[1], i0[0], i0[1], False)
    T("sketch_line", i0[0], i0[1], o0[0], o0[1])

def engrave(z):
    # --- mark: two Himalayan peaks drawn as one rounded ridge line, LoRa arcs from the summit
    ridge = [(-19, 31), (-9, 43), (-4, 37.5), (3, 49), (19, 31)]
    for a, b in zip(ridge, ridge[1:]):
        def d(m, a=a, b=b):
            pa, pb = m(a[0], a[1], z), m(b[0], b[1], z)
            T("sketch_slot", pa[0], pa[1], pb[0], pb[1], STROKE)
        _cut(z, d)
    sx, sy = 3, 49
    for r in (5.0, 9.0):
        _cut(z, lambda m, r=r: _arc_band(m, z, sx, sy, r, r + STROKE, 50, 130))
    # --- words, centred on x = 0 from their measured ink extents
    for s, h, font, bold, sp, y, (l, r) in TEXT:
        x0 = -(l + r) * h / 2
        _cut(z, lambda m, s=s, h=h, font=font, bold=bold, sp=sp, y=y, x0=x0:
             sketch_text(s, *m(x0, y, z), h, font, bold, 100, sp))
    # --- thin rule between WAYWOT and SIH 2026
    _cut(z, lambda m: T("sketch_rectangle", 46, 1.0, *m(0, -5.5, z)))
