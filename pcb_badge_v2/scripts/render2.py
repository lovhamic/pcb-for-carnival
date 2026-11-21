import json, math
from PIL import Image, ImageDraw, ImageFilter
from shapely import wkt
from shapely.geometry import Polygon
import pcbnew
OUT='/home/claude/badge/out2'
OX=OY=100.0; W=40.0; S=30   # px per mm
M=40                          # margin px
lay=json.load(open(OUT+'/layout.json'))
board=pcbnew.LoadBoard(OUT+'/pcb_badge.kicad_pcb')
front=wkt.loads(open(OUT+'/silk_front.wkt').read()); back=wkt.loads(open(OUT+'/silk_back.wkt').read())

R_TL,R_TR,R_BR,R_BL=0.8,7.0,0.8,7.0
def arcpts(cx,cy,r,a0,a1,n=40): return [(cx+r*math.cos(math.radians(a0+(a1-a0)*k/n)),cy+r*math.sin(math.radians(a0+(a1-a0)*k/n))) for k in range(n+1)]
pts=[(R_TL,0)]+arcpts(W-R_TR,R_TR,R_TR,-90,0)+arcpts(W-R_BR,W-R_BR,R_BR,0,90)+arcpts(R_BL,W-R_BL,R_BL,90,180)+arcpts(R_TL,R_TL,R_TL,180,270)
OUTL=Polygon(pts)

def tp(x,y,mirror): return ((W-x if mirror else x)*S+M, y*S+M)
def poly_px(g,mirror): return [tp(x,y,mirror) for x,y in g.exterior.coords]

def draw_geom(d,g,fill,mirror,holes_fill):
    geoms=[g] if g.geom_type=='Polygon' else list(g.geoms)
    for p in geoms:
        d.polygon(poly_px(p,mirror),fill=fill)
        for h in p.interiors: d.polygon([tp(x,y,mirror) for x,y in h.coords],fill=holes_fill)

def render(side, lit):
    mirror=(side=='back'); SZ=int(W*S+2*M)
    bg=(36,38,44) if lit else (226,228,232)
    im=Image.new('RGB',(SZ,SZ),bg)
    # shadow
    sh=Image.new('L',(SZ,SZ),0); ImageDraw.Draw(sh).polygon([(x+6,y+8) for x,y in poly_px(OUTL,mirror)],fill=150)
    sh=sh.filter(ImageFilter.GaussianBlur(7)); im.paste((0,0,0),mask=sh)
    d=ImageDraw.Draw(im)
    mask_col=(244,244,238)
    d.polygon(poly_px(OUTL,mirror),fill=mask_col)
    d.line(poly_px(OUTL,mirror),fill=(200,200,194),width=2)
    # silk
    draw_geom(d,back if mirror else front,(18,18,20),mirror,mask_col)
    # pads and bodies
    glow=Image.new('RGBA',(SZ,SZ),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    for fp in board.GetFootprints():
        ref=fp.GetReference(); fx=fp.GetPosition().x/1e6-OX; fy=fp.GetPosition().y/1e6-OY
        for pad in fp.Pads():
            px=pad.GetPosition().x/1e6-OX; py=pad.GetPosition().y/1e6-OY
            sx=pad.GetSize().x/1e6; sy=pad.GetSize().y/1e6
            if pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                cx,cy=tp(px,py,mirror); r=sx/2*S; d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=bg); continue
            if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:
                cx,cy=tp(px,py,mirror); r=sx/2*S; d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(214,178,92))
                r2=pad.GetDrillSize().x/2e6*S; d.ellipse([cx-r2,cy-r2,cx+r2,cy+r2],fill=bg if lit else (60,60,60)); continue
        if mirror or ref.startswith('H'): continue
        cx,cy=tp(fx,fy,False)
        if ref.startswith('D'):
            glow_c=(255,170,40,60)
            r_f=1.9*S; r_d=1.5*S
            d.ellipse([cx-r_f,cy-r_f,cx+r_f,cy+r_f],fill=(232,150,40) if not lit else (255,200,90))
            d.ellipse([cx-r_d,cy-r_d,cx+r_d,cy+r_d],fill=(255,181,70) if not lit else (255,236,170),outline=(180,110,30))
            d.ellipse([cx-r_d*0.5,cy-r_d*0.7,cx-r_d*0.1,cy-r_d*0.3],fill=(255,245,220))   # highlight
            d.rectangle([cx-r_f,cy-r_f*0.55,cx-r_f+5,cy+r_f*0.55],fill=(200,120,30))        # flat = cathode (left)
            if lit:
                for rr,al in ((95,35),(62,60),(40,100)): gd.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],fill=(255,170,40,al))
        elif ref=='R1':
            x0,y0=tp(fx-3.15,fy-1.15,False); x1,y1=tp(fx+3.15,fy+1.15,False)
            lx0,_=tp(fx-5.08,fy,False); lx1,_=tp(fx+5.08,fy,False)
            d.line([(lx0,cy),(lx1,cy)],fill=(190,190,196),width=5)
            d.rounded_rectangle([x0,y0,x1,y1],radius=14,fill=(214,184,140),outline=(150,120,80))
            for off,col in ((-1.7,(50,90,200)),(-0.8,(130,60,170)),(0.1,(0,0,0)),(1.9,(200,170,60))):
                bx,_=tp(fx+off,fy,False); d.rectangle([bx-4,y0+2,bx+4,y1-2],fill=col)   # 68R bands: blue-grey-black-gold
    if lit and not mirror:
        glow=glow.filter(ImageFilter.GaussianBlur(10)); im.paste(glow,mask=glow.split()[3])
        d=ImageDraw.Draw(im)
    if mirror:
        # CR2032 holder + cell on the back
        hx,hy=tp(28.0,29.0,True); 
        for r,col in ((10.6*S,(70,72,78)),(10.0*S,(168,170,176)),(9.2*S,(198,200,206))):
            d.ellipse([hx-r,hy-r,hx+r,hy+r],fill=col)
        d.text((hx-30,hy-8),'CR2032  3V',fill=(60,60,64))
        d.text((hx-4,hy+14),'+',fill=(60,60,64))
    return im
for side in ('front','back'):
    render(side,False).save(f'{OUT}/render_{side}.png')
render('front',True).save(f'{OUT}/render_front_lit.png')
# overview sheet
a,b,c=[Image.open(f'{OUT}/render_{n}.png') for n in ('front','back','front_lit')]
sheet=Image.new('RGB',(a.width*3,a.height),(226,228,232)); 
for i,im in enumerate((a,b,c)): sheet.paste(im,(i*a.width,0))
sheet.save(f'{OUT}/render_overview.png')
print('ok')
