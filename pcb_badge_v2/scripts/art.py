import cv2, numpy as np
from shapely.geometry import Polygon, MultiPolygon, box, Point
from shapely.ops import unary_union
from shapely import affinity

W = 40.0

def load_mask(path, up=4):
    im = cv2.imread(path)
    h, w = im.shape[:2]
    im = cv2.resize(im, (w*up, h*up), interpolation=cv2.INTER_CUBIC)
    b, g, r = cv2.split(im.astype(int))
    gray = (b+g+r)//3
    # dark pixels only; green corners (g high, r low) are excluded by requiring low green too
    mask = ((gray < 110) & (g < 110)).astype(np.uint8)*255
    return mask, w, h

def mask_to_geom(mask, w, h, up=4, mirror=False, tol=0.02, min_area=0.03):
    s = W/(w*up)  # mm per px
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]
    polys = []
    for i, c in enumerate(cnts):
        if hier[i][3] != -1:  # hole, handled by parent
            continue
        if len(c) < 4: continue
        outer = [(p[0][0]*s, p[0][1]*s) for p in c]
        holes = []
        j = hier[i][2]
        while j != -1:
            if len(cnts[j]) >= 4:
                holes.append([(p[0][0]*s, p[0][1]*s) for p in cnts[j]])
            j = hier[j][0]
        try:
            pg = Polygon(outer, holes)
            if not pg.is_valid: pg = pg.buffer(0)
            polys.append(pg)
        except Exception:
            pass
    g = unary_union(polys)
    # thicken hair-lines to fab-safe width, then smooth
    g = g.buffer(0.045, join_style=1).buffer(-0.015, join_style=1)
    g = g.simplify(tol)
    if mirror:
        g = affinity.scale(g, xfact=-1, yfact=1, origin=(W/2, 0))
    return g

def polys(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    return [p for p in getattr(g, 'geoms', []) if isinstance(p, Polygon) and not p.is_empty]
