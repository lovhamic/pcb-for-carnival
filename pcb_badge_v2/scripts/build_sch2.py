import uuid
U = lambda: str(uuid.uuid4())
ROOT = U()
def sym_R():
    return '''(symbol "Badge:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
  (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
  (property "Value" "R" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "R_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none))))
  (symbol "R_1_1"
    (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
    (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))'''
def sym_LED():
    # vertical LED: anode (pin 2) on top, cathode (pin 1) at the bottom
    return '''(symbol "Badge:LED" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
  (property "Reference" "D" (at 2.54 0 90) (effects (font (size 1.27 1.27))))
  (property "Value" "LED" (at -2.54 0 90) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "LED_0_1"
    (polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    (polyline (pts (xy 1.524 0.508) (xy 2.794 1.778) (xy 2.286 1.778) (xy 2.794 1.778) (xy 2.794 1.27)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 1.524 -0.508) (xy 2.794 0.762) (xy 2.286 0.762) (xy 2.794 0.762) (xy 2.794 0.254)) (stroke (width 0) (type default)) (fill (type none))))
  (symbol "LED_1_1"
    (pin passive line (at 0 -3.81 90) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
    (pin passive line (at 0 3.81 270) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))'''
def sym_BT():
    return '''(symbol "Badge:Battery_Cell" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
  (property "Reference" "BT" (at 2.54 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
  (property "Value" "Battery_Cell" (at 2.54 0 0) (effects (font (size 1.27 1.27)) (justify left)))
  (property "Footprint" "" (at 0 1.524 90) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "~" (at 0 1.524 90) (effects (font (size 1.27 1.27)) hide))
  (symbol "Battery_Cell_0_1"
    (polyline (pts (xy -1.778 0.762) (xy 1.778 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))
    (polyline (pts (xy -0.889 -0.254) (xy 0.889 -0.254)) (stroke (width 0.508) (type default)) (fill (type none)))
    (polyline (pts (xy 0 0.762) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 0 -0.254) (xy 0 -2.54)) (stroke (width 0) (type default)) (fill (type none))))
  (symbol "Battery_Cell_1_1"
    (pin passive line (at 0 3.81 270) (length 1.27) (name "+" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
    (pin passive line (at 0 -3.81 90) (length 1.27) (name "-" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))'''

out = []
out.append(f'(kicad_sch (version 20230121) (generator eeschema) (uuid {ROOT}) (paper "A4")')
out.append('(title_block (title "Space Carnival PCB Badge - Echoes of Years") (date "2026-11-11") (rev "1.0") (company "Tinkerspace Kochi - PCB Badge Design Competition"))')
out.append('(lib_symbols ' + sym_R() + sym_LED() + sym_BT() + ')')

def inst(lib, ref, val, fp, x, y):
    parts = [f'(symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})',
      f'(property "Reference" "{ref}" (at {x+3} {y-1.5} 0) (effects (font (size 1.27 1.27)) (justify left)))',
      f'(property "Value" "{val}" (at {x+3} {y+1.5} 0) (effects (font (size 1.27 1.27)) (justify left)))',
      f'(property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))',
      '(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))']
    for pn in ('1', '2'): parts.append(f'(pin "{pn}" (uuid {U()}))')
    parts.append(f'(instances (project "pcb_badge" (path "/{ROOT}" (reference "{ref}") (unit 1))))')
    parts.append(')')
    return ' '.join(parts)
def wire(x1, y1, x2, y2): return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid {U()}))'
def junc(x, y): return f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {U()}))'
def label(t, x, y, a=0): return f'(label "{t}" (at {x} {y} {a}) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {U()}))'
def text(t, x, y, s=2.0): return f'(text "{t}" (at {x} {y} 0) (effects (font (size {s} {s})) (justify left)) (uuid {U()}))'

X0, DX = 110.0, 18.0
TOP = 58.0          # VBAT rail
RAIL = 84.0         # VLED rail
DY = 96.0           # LED centre
BOT = 114.0         # GND rail
BTX, BTY = 40.0, 86.0
RX, RYc = 80.0, 70.0
out.append(inst('Badge:Battery_Cell', 'BT1', 'CR2032 3V', 'PCBBadge:CR2032_Holder_THT_20mm', BTX, BTY))
out.append(inst('Badge:R', 'R1', '68R', 'PCBBadge:R_Axial_P10.16mm', RX, RYc))
tags = ['T (top)', 'UL', 'UR', 'L', 'R', 'Hub', 'LL', 'LR']
xs = [X0 + i*DX for i in range(8)]
for i, x in enumerate(xs):
    out.append(inst('Badge:LED', f'D{i+1}', 'LED 3mm', 'PCBBadge:LED_D3.0mm_Pitch2.54mm', x, DY))
    out.append(wire(x, RAIL, x, DY-3.81)); out.append(wire(x, DY+3.81, x, BOT))
    out.append(text(tags[i], x-3, DY+10, 1.0))
    out.append(junc(x, RAIL)) if 0 < i < 7 else None
    out.append(junc(x, BOT)) if 0 < i < 7 else None
out.append(junc(xs[0], RAIL)); out.append(junc(xs[0], BOT))
# VBAT: battery + -> R1 top
out.append(wire(BTX, BTY-3.81, BTX, TOP)); out.append(wire(BTX, TOP, RX, TOP)); out.append(wire(RX, TOP, RX, RYc-3.81))
# VLED: R1 bottom -> rail -> every LED anode
out.append(wire(RX, RYc+3.81, RX, RAIL)); out.append(wire(RX, RAIL, xs[0], RAIL))
for i in range(7): out.append(wire(xs[i], RAIL, xs[i+1], RAIL)); out.append(wire(xs[i], BOT, xs[i+1], BOT))
# GND: battery - -> rail
out.append(wire(BTX, BTY+3.81, BTX, BOT)); out.append(wire(BTX, BOT, xs[0], BOT))
out.append(label('VBAT', BTX+4, TOP)); out.append(label('VLED', RX+4, RAIL)); out.append(label('GND', BTX+4, BOT))
out.append(text('Space Carnival PCB Badge - 8 x 3 mm LEDs on one CR2032 (3 V)', 40, 30, 2.5))
out.append(text('One shared 68R limits the total current (~12-16 mA, ~1.5-2 mA per LED). LEDs sit on the Ferris-wheel joints.', 40, 38, 1.5))
out.append('(sheet_instances (path "/" (page "1")))')
out.append(')')
open('/home/claude/badge/out2/sch/pcb_badge.kicad_sch', 'w').write('\n'.join(o for o in out if o))
