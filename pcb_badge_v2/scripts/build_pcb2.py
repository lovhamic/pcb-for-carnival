import math, os, json
import pcbnew
from pcbnew import FromMM, VECTOR2I
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
import art

OX, OY = 100.0, 100.0          # board origin on the KiCad sheet
W = 40.0
OUT = '/home/claude/badge/out2'
os.makedirs(OUT, exist_ok=True)

def P(x, y): return VECTOR2I(FromMM(OX + x), FromMM(OY + y))

board = pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.m_CopperEdgeClearance = FromMM(0.3)
ds.m_TrackMinWidth = FromMM(0.2)
ds.m_ViasMinSize = FromMM(0.6)
ds.m_MinThroughDrill = FromMM(0.3)
ds.SetAuxOrigin(P(0, 0))

# ---------------- nets
def mknet(name):
    n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); return n
N_GND = mknet('GND'); N_VBAT = mknet('VBAT'); N_VLED = mknet('VLED')

# ---------------- outline
R_TL, R_TR, R_BR, R_BL = 0.8, 7.0, 0.8, 7.0
def seg(a, b):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1)); board.Add(s)
def arc(start, mid, end):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(P(*start), P(*mid), P(*end)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1)); board.Add(s)
c45 = math.sqrt(0.5)
seg((R_TL, 0), (W - R_TR, 0))
arc((W - R_TR, 0), (W - R_TR + R_TR*c45, R_TR - R_TR*c45), (W, R_TR))
seg((W, R_TR), (W, W - R_BR))
arc((W, W - R_BR), (W - R_BR + R_BR*c45, W - R_BR + R_BR*c45), (W - R_BR, W))
seg((W - R_BR, W), (R_BL, W))
arc((R_BL, W), (R_BL - R_BL*c45, W - R_BL + R_BL*c45), (0, W - R_BL))
seg((0, W - R_BL), (0, R_TL))
arc((0, R_TL), (R_TL - R_TL*c45, R_TL - R_TL*c45), (R_TL, 0))

def arcpts(cx, cy, r, a0, a1, n=24):
    return [(cx + r*math.cos(math.radians(a0 + (a1-a0)*k/n)), cy + r*math.sin(math.radians(a0 + (a1-a0)*k/n))) for k in range(n+1)]
pts = [(R_TL, 0)]
pts += arcpts(W - R_TR, R_TR, R_TR, -90, 0)
pts += arcpts(W - R_BR, W - R_BR, R_BR, 0, 90)
pts += arcpts(R_BL, W - R_BL, R_BL, 90, 180)
pts += arcpts(R_TL, R_TL, R_TL, 180, 270)
OUTLINE = Polygon(pts)

# lanyard hole (NPTH)
HOLE = (3.6, 3.6); HOLE_D = 2.4
def add_npth(x, y, d):
    fp = pcbnew.FOOTPRINT(board); fp.SetReference('H1'); fp.SetValue('Lanyard')
    fp.SetFPID(pcbnew.LIB_ID('PCBBadge', 'LanyardHole_2.4mm'))
    pad = pcbnew.PAD(fp); pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(VECTOR2I(FromMM(d), FromMM(d))); pad.SetDrillSize(VECTOR2I(FromMM(d), FromMM(d)))
    ls=pcbnew.LSET(); ls.AddLayer(pcbnew.F_Mask); ls.AddLayer(pcbnew.B_Mask); pad.SetLayerSet(ls); pad.SetPos0(VECTOR2I(0, 0)); fp.Add(pad)
    fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    board.Add(fp); fp.SetPosition(P(x, y))
add_npth(*HOLE, HOLE_D)

# ---------------- footprints
def tpad(fp, num, x, y, net, d=1.8, drill=0.9, rect=False):
    p = pcbnew.PAD(fp); p.SetNumber(str(num)); p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(pcbnew.PAD_SHAPE_RECT if rect else pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(VECTOR2I(FromMM(d), FromMM(d))); p.SetDrillSize(VECTOR2I(FromMM(drill), FromMM(drill)))
    p.SetLayerSet(p.PTHMask()); p.SetPos0(VECTOR2I(FromMM(x), FromMM(y))); p.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    p.SetNet(net); fp.Add(p); return p

# 3 mm LED centres = joints of the Ferris wheel (mm, front view). The bottom joint is hidden by the tent.
LEDS = {
 'T':  (12.3,  8.6),   # top
 'UL': ( 6.0, 10.75),  # upper-left
 'UR': (18.6, 10.75),  # upper-right
 'L':  ( 3.7, 16.0),   # left
 'R':  (20.9, 16.0),   # right
 'H':  (12.3, 16.0),   # centre hub
 'LL': ( 5.6, 21.7),   # lower-left
 'LR': (19.0, 21.7),   # lower-right
}
KEYS = list(LEDS.keys())
LP = 1.27   # half of 2.54 mm lead pitch
for i, k in enumerate(KEYS):
    qx, qy = LEDS[k]
    led = pcbnew.FOOTPRINT(board); led.SetReference(f'D{i+1}'); led.SetValue('LED_D3.0mm')
    led.SetFPID(pcbnew.LIB_ID('PCBBadge', 'LED_D3.0mm_Pitch2.54mm'))
    tpad(led, 1, -LP, 0, N_GND, rect=True)      # cathode (flat side) on the LEFT
    tpad(led, 2, +LP, 0, N_VLED)                # anode on the RIGHT
    led.Reference().SetVisible(False); led.Value().SetVisible(False)
    board.Add(led); led.SetPosition(P(qx, qy))
    if k == 'LR': led.SetOrientationDegrees(231)
# one shared current-limiting resistor (axial, 10.16 mm pitch)
RC = (10.58, 31.0)
rr = pcbnew.FOOTPRINT(board); rr.SetReference('R1'); rr.SetValue('68R')
rr.SetFPID(pcbnew.LIB_ID('PCBBadge', 'R_Axial_P10.16mm'))
tpad(rr, 1, -5.08, 0, N_VLED); tpad(rr, 2, +5.08, 0, N_VBAT)
rr.Reference().SetVisible(False); rr.Value().SetVisible(False)
board.Add(rr); rr.SetPosition(P(*RC))
R_P1 = (RC[0]-5.08, RC[1]); R_P2 = (RC[0]+5.08, RC[1])

# battery holder (generic 2-pin THT CR2032 holder, 20 mm pin pitch), mounted on the BACK
HC = (28.0, 29.0); PITCH = 20.0
bt = pcbnew.FOOTPRINT(board); bt.SetReference('BT1'); bt.SetValue('CR2032 holder')
bt.SetFPID(pcbnew.LIB_ID('PCBBadge', 'CR2032_Holder_THT_20mm'))
def tht_pad(fp, num, x, net, d=2.4, drill=1.3):
    p = pcbnew.PAD(fp); p.SetNumber(str(num)); p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(VECTOR2I(FromMM(d), FromMM(d))); p.SetDrillSize(VECTOR2I(FromMM(drill), FromMM(drill)))
    p.SetLayerSet(p.PTHMask()); p.SetPos0(VECTOR2I(FromMM(x), 0)); p.SetPosition(VECTOR2I(FromMM(x), 0)); p.SetNet(net); fp.Add(p); return p
tht_pad(bt, 1, +PITCH/2, N_VBAT)    # after the flip to the back this lands on the LEFT of the board (+)
tht_pad(bt, 2, -PITCH/2, N_GND)

pass
bt.Reference().SetVisible(False); bt.Value().SetVisible(False)
board.Add(bt); bt.SetPosition(P(*HC)); bt.Flip(P(*HC), True)
pp = {pad.GetNumber(): pad for pad in bt.Pads()}
PPLUS = ((pp['1'].GetPosition().x/1e6 - OX), (pp['1'].GetPosition().y/1e6 - OY))
PMINUS = ((pp['2'].GetPosition().x/1e6 - OX), (pp['2'].GetPosition().y/1e6 - OY))
print('holder + at', PPLUS, ' - at', PMINUS)

# ---------------- tracks / vias
def track(a, b, layer, net, w=0.4):
    t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(w))
    t.SetLayer(layer); t.SetNet(net); board.Add(t)
def via(x, y, net, d=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetWidth(FromMM(d)); v.SetDrill(FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(net); board.Add(v)
B = pcbnew.B_Cu
anode = {}
for fp in board.GetFootprints():
    if fp.GetReference().startswith('D'):
        k = KEYS[int(fp.GetReference()[1:]) - 1]
        for pad in fp.Pads():
            if pad.GetNumber() == '2': anode[k] = (pad.GetPosition().x/1e6 - OX, pad.GetPosition().y/1e6 - OY)
BUS = {'T': 13.0, 'UL': 13.0, 'UR': 13.0, 'L': 18.2, 'H': 18.2, 'R': 18.2, 'LL': 24.0, 'LR': 24.0}
for k in KEYS:                                   # each anode drops to its bus row
    track(anode[k], (anode[k][0], BUS[k]), B, N_VLED)
for yb, ks in ((13.0, ['UL', 'UR']), (18.2, ['L', 'R']), (24.0, ['LL', 'LR'])):
    track((anode[ks[0]][0], yb), (anode[ks[1]][0], yb), B, N_VLED)
TX = 9.5                                        # VLED trunk
track(R_P1, (TX, R_P1[1]), B, N_VLED)
track((TX, R_P1[1]), (TX, 13.0), B, N_VLED)
track(PPLUS, R_P2, B, N_VBAT)                    # battery + -> resistor

# ---------------- build copper geometry for checks / stitching
def pad_geom(pad):
    pos = pad.GetPosition(); x = pos.x/1e6 - OX; y = pos.y/1e6 - OY
    sx = pad.GetSize().x/1e6; sy = pad.GetSize().y/1e6
    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE: return Point(x, y).buffer(sx/2, 32)
    return box(x - sx/2, y - sy/2, x + sx/2, y + sy/2)

def copper_objects():
    objs = []  # (layer 'F'/'B', netname, geom, tag)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
            g = pad_geom(pad); n = pad.GetNetname()
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                objs.append(('F', n, g, fp.GetReference())); objs.append(('B', n, g, fp.GetReference()))
            else:
                objs.append(('F' if fp.GetLayer() == pcbnew.F_Cu else 'B', n, g, fp.GetReference()))
    for t in board.GetTracks():
        n = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            g = Point(t.GetPosition().x/1e6 - OX, t.GetPosition().y/1e6 - OY).buffer(t.GetWidth()/2e6, 24)
            objs.append(('F', n, g, 'via')); objs.append(('B', n, g, 'via'))
        else:
            g = LineString([(t.GetStart().x/1e6 - OX, t.GetStart().y/1e6 - OY), (t.GetEnd().x/1e6 - OX, t.GetEnd().y/1e6 - OY)]).buffer(t.GetWidth()/2e6, 8)
            objs.append(('F' if t.GetLayer() == pcbnew.F_Cu else 'B', n, g, 'trk'))
    return objs

def check(min_clear=0.2):
    objs = copper_objects(); bad = []
    for i in range(len(objs)):
        for j in range(i+1, len(objs)):
            a, b = objs[i], objs[j]
            if a[0] != b[0] or a[1] == b[1]: continue
            d = a[2].distance(b[2])
            if d < min_clear: bad.append((a[3], a[1], b[3], b[1], round(d, 3), a[0]))
    edge = OUTLINE.exterior
    for o in objs:
        d = o[2].distance(edge)
        if d < 0.3 or not OUTLINE.contains(o[2]): bad.append((o[3], o[1], 'EDGE', '', round(d, 3), o[0]))
    return bad

print('clearance problems before stitching:', check())

# ---------------- GND stitching vias (auto, only in free space)
objs = copper_objects()
non_gnd = unary_union([o[2] for o in objs if o[1] != 'GND'])
hole = Point(*HOLE).buffer(HOLE_D/2 + 0.6)
cand = []
y = 2.0
while y < W - 1.5:
    x = 2.0
    while x < W - 1.5:
        g = Point(x, y).buffer(0.4)
        if OUTLINE.buffer(-1.0).contains(g) and g.distance(non_gnd) > 0.7 and g.distance(hole) > 0.5:
            cand.append((x, y))
        x += 5.0
    y += 5.0
for (x, y) in cand: via(x, y, N_GND)
print('stitching vias:', len(cand))
print('clearance problems after stitching:', check())

# ---------------- GND zones both sides
inner = OUTLINE.buffer(-0.35)
def add_zone(layer):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(N_GND)
    z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FromMM(0.25)); z.SetThermalReliefSpokeWidth(FromMM(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in list(inner.exterior.coords)[:-1]:
        ol.Append(FromMM(OX + x), FromMM(OY + y))
    board.Add(z)
add_zone(pcbnew.F_Cu); add_zone(pcbnew.B_Cu)

# ---------------- silkscreen art
KEEP_TEXT = [box(PPLUS[0]-0.9, PPLUS[1]-3.6, PPLUS[0]+0.9, PPLUS[1]-2.0), box(PMINUS[0]-0.9, PMINUS[1]-3.6, PMINUS[0]+0.9, PMINUS[1]-2.0)]
def keepouts(side):
    ks = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                pos = pad.GetPosition(); ks.append(Point(pos.x/1e6 - OX, pos.y/1e6 - OY).buffer(HOLE_D/2 + 0.5)); continue
            if side == 'F' and (fp.GetLayer() == pcbnew.F_Cu or pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH):
                ks.append(pad_geom(pad).buffer(0.25))
            if side == 'B' and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                ks.append(pad_geom(pad).buffer(0.25))
    if side == 'F': ks += [k.buffer(0.1) for k in KEEP_TEXT]
    return unary_union(ks)

def add_poly(geom, layer):
    n = 0
    for pg in art.polys(geom):
        if pg.area < 0.02: continue
        ps = pcbnew.SHAPE_POLY_SET()
        ext = pcbnew.SHAPE_LINE_CHAIN()
        for (x, y) in list(pg.exterior.coords)[:-1]: ext.Append(FromMM(OX + x), FromMM(OY + y))
        ext.SetClosed(True); ps.AddOutline(ext)
        for h in pg.interiors:
            hc = pcbnew.SHAPE_LINE_CHAIN()
            for (x, y) in list(h.coords)[:-1]: hc.Append(FromMM(OX + x), FromMM(OY + y))
            hc.SetClosed(True); ps.AddHole(hc)
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_POLY); s.SetPolyShape(ps)
        s.SetFilled(True); s.SetWidth(0); s.SetLayer(layer); board.Add(s); n += 1
    return n

m, w, h = art.load_mask('/home/claude/in2/1.png'); front = art.mask_to_geom(m, w, h)
m, w, h = art.load_mask('/home/claude/in2/2.png')
import numpy as np, cv2
up = 4; x0, x1, y0, y1 = 40*up, 326*up, 84*up, 142*up
crop = m[y0:y1, x0:x1].copy(); m[y0:y1, x0:x1] = 0
ys, xs = np.nonzero(crop); crop = crop[ys.min():ys.max()+1, xs.min():xs.max()+1]
sc = 0.62; crop = cv2.resize(crop, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); crop = ((crop > 110)*255).astype(np.uint8)
mmpx = 40.0/(w*up); tx = int(4.5/mmpx); ty = int(12.1/mmpx)
m[ty:ty+crop.shape[0], tx:tx+crop.shape[1]] |= crop
back = art.mask_to_geom(m, w, h, mirror=True)
safe = OUTLINE.buffer(-0.5)
front = front.intersection(safe).difference(keepouts('F'))
back = back.intersection(safe).difference(keepouts('B'))
open(OUT+'/silk_front.wkt','w').write(front.wkt); open(OUT+'/silk_back.wkt','w').write(back.wkt)
print('silk polys front/back:', add_poly(front, pcbnew.F_SilkS), add_poly(back, pcbnew.B_SilkS))

# polarity text on the front next to the holder pads
def text(s, x, y, layer, size=1.2):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(0.18)); board.Add(t)
text('+', PPLUS[0], PPLUS[1] - 2.8, pcbnew.F_SilkS)
text('-', PMINUS[0], PMINUS[1] - 2.8, pcbnew.F_SilkS)

# ---------------- fill + save
pcbnew.SaveBoard(f'{OUT}/pcb_badge.kicad_pcb', board)
board = pcbnew.LoadBoard(f'{OUT}/pcb_badge.kicad_pcb')
board.BuildConnectivity()
filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
board.BuildConnectivity()
print('unconnected items:', board.GetConnectivity().GetUnconnectedCount(False))
pcbnew.SaveBoard(f'{OUT}/pcb_badge.kicad_pcb', board)

json.dump({'leds': LEDS, 'pplus': PPLUS, 'pminus': PMINUS}, open(f'{OUT}/layout.json', 'w'))

# ---------------- gerbers + drill
gdir = f'{OUT}/gerbers'; os.makedirs(gdir, exist_ok=True)
pc = pcbnew.PLOT_CONTROLLER(board); po = pc.GetPlotOptions()
po.SetOutputDirectory(gdir); po.SetPlotFrameRef(False); po.SetUseGerberAttributes(True)
po.SetUseGerberX2format(True); po.SetCreateGerberJobFile(False); po.SetSubtractMaskFromSilk(True)
po.SetUseAuxOrigin(True); po.SetDrillMarksType(pcbnew.DRILL_MARKS_NO_DRILL_SHAPE); po.SetSkipPlotNPTH_Pads(False)
po.SetGerberPrecision(6)
layers = [('F_Cu', pcbnew.F_Cu), ('B_Cu', pcbnew.B_Cu), ('F_Mask', pcbnew.F_Mask), ('B_Mask', pcbnew.B_Mask),
          ('F_Silkscreen', pcbnew.F_SilkS), ('B_Silkscreen', pcbnew.B_SilkS), ('F_Paste', pcbnew.F_Paste),
          ('B_Paste', pcbnew.B_Paste), ('Edge_Cuts', pcbnew.Edge_Cuts)]
for name, lid in layers:
    pc.SetLayer(lid); pc.OpenPlotfile(name, pcbnew.PLOT_FORMAT_GERBER, name); pc.PlotLayer()
pc.ClosePlot()
ew = pcbnew.EXCELLON_WRITER(board); ew.SetOptions(False, False, P(0, 0), False)
ew.SetFormat(True, pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT, 3, 3)
ew.CreateDrillandMapFilesSet(gdir, True, False)
print(sorted(os.listdir(gdir)))
