"""Gera a coleção de caras de papelão que vem com o mod.

Cada cara é desenhada a canetão sobre papelão, com borda rasgada e fita adesiva, na
proporção da placa (22 x 28). As caras são montadas a partir de peças (rosto, olhos,
sobrancelhas, nariz, boca e extras) listadas em RECEITAS; a semente fixa deixa o
resultado reproduzível.

Uso: python3 gerar.py <pasta-de-saida>
Requer Pillow.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 880, 1120
INK = (25, 22, 20, 255)
RED = (200, 55, 45, 255)
BLUE = (40, 90, 200, 255)
GREEN = (30, 140, 70, 255)
YELLOW = (240, 190, 40, 255)
PINK = (230, 120, 150, 255)
WHITE = (245, 242, 232, 255)
BLUSH = (220, 90, 80, 130)

TONES = [(196, 154, 108), (188, 146, 100), (204, 162, 112), (184, 142, 98), (200, 158, 110), (176, 136, 92)]


# ---------- papelão ----------

def cardboard(rnd, tone):
    img = Image.new("RGBA", (W, H), tone + (255,))
    px = img.load()
    phase = rnd.uniform(0, 6)
    for x in range(W):
        band = 10 * math.sin(x / 7.5 + phase)
        for y in range(H):
            d = band + rnd.randint(-12, 12)
            r, g, b = tone
            px[x, y] = (int(r + d), int(g + d * 0.85), int(b + d * 0.7), 255)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    stains = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(stains)
    for _ in range(4):
        cx, cy, rr = rnd.randint(0, W), rnd.randint(0, H), rnd.randint(50, 130)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(120, 80, 40, 22))
    vy = rnd.randint(H // 6, H // 3)
    d.line([(0, vy), (W, vy + rnd.randint(-30, 30))], fill=(120, 85, 50, 70), width=5)
    img.alpha_composite(stains.filter(ImageFilter.GaussianBlur(18)))
    return img.filter(ImageFilter.GaussianBlur(1.0))


def torn_mask(rnd, margin=26):
    pts = []
    for x in range(0, W + 1, 18):
        pts.append((x, margin + rnd.randint(-14, 14)))
    for y in range(0, H + 1, 18):
        pts.append((W - margin + rnd.randint(-14, 14), y))
    for x in range(W, -1, -18):
        pts.append((x, H - margin + rnd.randint(-14, 14)))
    for y in range(H, -1, -18):
        pts.append((margin + rnd.randint(-14, 14), y))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def tape(img, rnd, x, y, ang):
    t = Image.new("RGBA", (190, 60), (235, 230, 200, 170))
    td = ImageDraw.Draw(t)
    for i in range(0, 190, 9):
        td.line([(i, 0), (i + rnd.randint(-3, 3), 60)], fill=(255, 255, 240, 40), width=2)
    t = t.rotate(ang, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))


TAPE_SPOTS = [
    [(150, 120, -35), (730, 120, 35)],
    [(440, 70, 3)],
    [(130, 960, 40), (750, 970, -40)],
    [(150, 110, -30), (730, 1010, -30)],
    [(440, 1060, -2)],
    [(150, 1000, 30), (730, 120, 30)],
]


# ---------- traço ----------

def wobble(points, rnd, amp=4):
    return [(x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)) for x, y in points]


def stroke(d, rnd, points, width=14, color=INK, passes=2):
    for _ in range(passes):
        p = wobble(points, rnd)
        d.line(p, fill=color, width=width, joint="curve")
        for x, y in (p[0], p[-1]):
            d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=color)


def arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def blob(img, rnd, cx, cy, r, color, soft=False):
    p = wobble(arc(cx, cy, r, r, 0, 360, 30), rnd, amp=r * 0.08)
    if color[3] == 255 and not soft:
        ImageDraw.Draw(img).polygon(p, fill=color)
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(p, fill=color)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6)))


def fill(d, rnd, points, color, amp=4):
    d.polygon(wobble(points, rnd, amp), fill=color)


# ---------- peças ----------
# Geometria comum: rosto centrado em (440, 590); olhos em y=480, x=330 e 550; boca em y~710.
EL, ER, EY = 330, 550, 480


def face_oval(img, d, rnd, c):
    stroke(d, rnd, wobble(arc(440, 590, 320, 400, 0, 360, 40), rnd, 6), 16, c)


def face_round(img, d, rnd, c):
    stroke(d, rnd, wobble(arc(440, 600, 340, 340, 0, 360, 40), rnd, 6), 16, c)


def face_square(img, d, rnd, c):
    stroke(d, rnd, wobble([(150, 230), (730, 220), (740, 940), (140, 950), (150, 230)], rnd, 6), 18, c)


def face_egg(img, d, rnd, c):
    pts = arc(440, 560, 280, 360, 180, 360, 20) + arc(440, 560, 330, 420, 0, 180, 20)
    stroke(d, rnd, wobble(pts + [pts[0]], rnd, 6), 16, c)


def face_none(img, d, rnd, c):
    pass


def eyes_dots(img, d, rnd, c):
    for x in (EL, ER):
        blob(img, rnd, x, EY, 34, c)


def eyes_pupils(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, arc(x, EY, 48, 42, 0, 360), 10, c)
        blob(img, rnd, x + 8, EY + 8, 16, c)


def eyes_wide(img, d, rnd, c):
    for x in (EL, ER):
        d.ellipse([x - 70, EY - 60, x + 70, EY + 60], fill=WHITE)
        stroke(d, rnd, arc(x, EY, 70, 60, 0, 360), 10, c)
        blob(img, rnd, x, EY + 5, 18, c)


def eyes_happy(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, arc(x, EY + 20, 50, 40, 200, 340), 14, c)


def eyes_sleepy(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, arc(x, EY - 10, 50, 30, 20, 160), 14, c)


def eyes_x(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, [(x - 40, EY - 40), (x + 40, EY + 40)], 14, c)
        stroke(d, rnd, [(x + 40, EY - 40), (x - 40, EY + 40)], 14, c)


def eyes_wink(img, d, rnd, c):
    blob(img, rnd, EL, EY, 34, c)
    stroke(d, rnd, arc(ER, EY + 20, 50, 40, 200, 340), 14, c)


def eyes_spiral(img, d, rnd, c):
    for x in (EL, ER):
        pts = [(x + (3 + 1.5 * a) * math.cos(math.radians(a * 15)), EY + (3 + 1.5 * a) * math.sin(math.radians(a * 15)))
               for a in range(0, 50)]
        stroke(d, rnd, pts, 8, c, passes=1)


def eyes_hearts(img, d, rnd, c):
    for x in (EL, ER):
        pts = [(x + 16 * 3.2 * math.sin(t) ** 3, EY - 3.2 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
               for t in [i * 2 * math.pi / 40 for i in range(41)]]
        fill(d, rnd, pts, RED, 2)


def eyes_stars(img, d, rnd, c):
    for x in (EL, ER):
        pts = []
        for i in range(11):
            r = 55 if i % 2 == 0 else 22
            a = math.radians(-90 + i * 36)
            pts.append((x + r * math.cos(a), EY + r * math.sin(a)))
        fill(d, rnd, pts, YELLOW, 2)
        stroke(d, rnd, pts, 7, c, passes=1)


def eyes_cyclops(img, d, rnd, c):
    d.ellipse([440 - 95, EY - 75, 440 + 95, EY + 75], fill=WHITE)
    stroke(d, rnd, arc(440, EY, 95, 75, 0, 360), 12, c)
    blob(img, rnd, 440, EY + 5, 30, c)


def eyes_sunglasses(img, d, rnd, c):
    for x0 in (220, 470):
        fill(d, rnd, [(x0, EY - 60), (x0 + 190, EY - 60), (x0 + 175, EY + 50), (x0 + 15, EY + 40)], c)
        stroke(d, rnd, [(x0 + 30, EY - 40), (x0 + 70, EY - 40)], 8, (240, 240, 240, 220), passes=1)
    stroke(d, rnd, [(410, EY - 40), (470, EY - 40)], 14, c)


def eyes_round_glasses(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, arc(x, EY, 75, 75, 0, 360), 10, c)
        blob(img, rnd, x, EY, 16, c)
    stroke(d, rnd, [(EL + 75, EY - 10), (ER - 75, EY - 10)], 10, c)


def eyes_patch(img, d, rnd, c):
    blob(img, rnd, EL, EY, 34, c)
    fill(d, rnd, arc(ER, EY, 75, 60, 0, 360), c)
    stroke(d, rnd, [(150, 330), (ER, EY), (735, 600)], 10, c, passes=1)


def eyes_angry(img, d, rnd, c):
    # meia-lua com o topo inclinado para o centro
    for x, s in ((EL, 1), (ER, -1)):
        top = [(x - 55, EY - 30 - 18 * s), (x + 55, EY - 30 + 18 * s)]
        bottom = arc(x, EY - 22, 55, 60, 0, 180, 16)
        fill(d, rnd, top + bottom[::-1] if s == 1 else top + bottom[::-1], c, 2)


def eyes_tired(img, d, rnd, c):
    for x in (EL, ER):
        blob(img, rnd, x, EY, 26, c)
        stroke(d, rnd, arc(x, EY + 40, 50, 25, 20, 160), 7, c, passes=1)
        stroke(d, rnd, arc(x, EY + 58, 45, 22, 30, 150), 6, c, passes=1)


def brows_none(img, d, rnd, c):
    pass


def brows_flat(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, [(x - 60, EY - 95), (x + 60, EY - 95)], 18, c)


def brows_angry(img, d, rnd, c):
    stroke(d, rnd, [(EL - 60, EY - 115), (EL + 60, EY - 80)], 20, c)
    stroke(d, rnd, [(ER - 60, EY - 80), (ER + 60, EY - 115)], 20, c)


def brows_sad(img, d, rnd, c):
    stroke(d, rnd, [(EL - 60, EY - 80), (EL + 60, EY - 115)], 16, c)
    stroke(d, rnd, [(ER - 60, EY - 115), (ER + 60, EY - 80)], 16, c)


def brows_raised(img, d, rnd, c):
    for x in (EL, ER):
        stroke(d, rnd, arc(x, EY - 80, 60, 40, 200, 340), 14, c)


def brows_uni(img, d, rnd, c):
    stroke(d, rnd, [(EL - 70, EY - 95), (440, EY - 110), (ER + 70, EY - 95)], 26, c)


def brows_thick(img, d, rnd, c):
    stroke(d, rnd, [(270, EY - 80), (340, EY - 100), (400, EY - 75)], 24, c)
    stroke(d, rnd, [(480, EY - 75), (540, EY - 102), (610, EY - 82)], 24, c)


def nose_none(img, d, rnd, c):
    pass


def nose_l(img, d, rnd, c):
    stroke(d, rnd, [(440, 520), (415, 610), (460, 615)], 12, c)


def nose_dot(img, d, rnd, c):
    blob(img, rnd, 440, 600, 14, c)


def nose_triangle(img, d, rnd, c):
    stroke(d, rnd, [(440, 530), (400, 620), (480, 620), (440, 530)], 10, c)


def nose_clown(img, d, rnd, c):
    blob(img, rnd, 440, 590, 48, RED)
    blob(img, rnd, 425, 575, 10, (255, 255, 255, 200), soft=True)


def nose_pig(img, d, rnd, c):
    d.ellipse([385, 555, 495, 635], fill=PINK)
    stroke(d, rnd, arc(440, 595, 55, 40, 0, 360), 9, c)
    blob(img, rnd, 420, 595, 9, c)
    blob(img, rnd, 460, 595, 9, c)


def nose_cat(img, d, rnd, c):
    fill(d, rnd, [(410, 585), (470, 585), (440, 620)], PINK, 2)
    for s in (-1, 1):
        for dy in (-15, 15):
            stroke(d, rnd, [(440 + s * 70, 615), (440 + s * 260, 600 + dy * 2)], 6, c, passes=1)


def mouth_smile(img, d, rnd, c):
    stroke(d, rnd, arc(440, 650, 190, 130, 15, 165), 18, c)


def mouth_grin(img, d, rnd, c):
    pts = arc(440, 680, 190, 120, 0, 180, 20)
    fill(d, rnd, [(250, 680)] + pts[::-1][1:] + [(630, 680)], WHITE, 2)
    stroke(d, rnd, [(250, 680), (630, 680)] , 12, c)
    stroke(d, rnd, pts, 12, c)
    for x in range(300, 600, 55):
        stroke(d, rnd, [(x, 680), (x, 680 + 100 * math.sin(math.acos(max(-1, min(1, (x - 440) / 190)))))], 6, c, passes=1)


def mouth_o(img, d, rnd, c):
    stroke(d, rnd, arc(440, 740, 60, 75, 0, 360), 16, c)


def mouth_flat(img, d, rnd, c):
    stroke(d, rnd, [(350, 740), (530, 740)], 16, c)


def mouth_smirk(img, d, rnd, c):
    stroke(d, rnd, [(330, 720), (450, 735), (560, 690)], 16, c)


def mouth_frown(img, d, rnd, c):
    stroke(d, rnd, arc(440, 820, 150, 90, 200, 340), 18, c)


def mouth_tongue(img, d, rnd, c):
    stroke(d, rnd, [(330, 720), (550, 720)], 16, c)
    fill(d, rnd, arc(480, 750, 45, 55, 0, 180) + [(435, 720), (525, 720)], RED, 2)
    stroke(d, rnd, [(480, 735), (480, 790)], 6, c, passes=1)


def mouth_zigzag(img, d, rnd, c):
    stroke(d, rnd, [(320, 740), (360, 710), (400, 750), (440, 710), (480, 750), (520, 710), (560, 740)], 12, c)


def mouth_fangs(img, d, rnd, c):
    stroke(d, rnd, arc(440, 680, 160, 70, 15, 165), 16, c)
    for x in (380, 500):
        fill(d, rnd, [(x - 18, 742), (x + 18, 742), (x, 800)], WHITE, 1)
        stroke(d, rnd, [(x - 18, 742), (x, 800), (x + 18, 742)], 6, c, passes=1)


def mouth_laugh(img, d, rnd, c):
    pts = arc(440, 690, 170, 150, 0, 180, 20)
    fill(d, rnd, [(270, 690)] + pts[::-1][1:] + [(610, 690)], (90, 25, 25, 255), 2)
    fill(d, rnd, arc(440, 800, 70, 30, 180, 360, 12), RED, 2)
    stroke(d, rnd, [(270, 690), (610, 690)] + pts[::-1], 14, c)


def mouth_mustache(img, d, rnd, c):
    p = arc(375, 690, 85, 45, 200, 340) + arc(505, 690, 85, 45, 200, 340)
    fill(d, rnd, p + [(590, 700), (440, 720), (290, 700)], c, 5)
    stroke(d, rnd, [(380, 800), (500, 795)], 12, c)


def mouth_wavy(img, d, rnd, c):
    stroke(d, rnd, [(330 + i * 10, 740 + 18 * math.sin(i / 2.2)) for i in range(23)], 14, c)


def mouth_robot(img, d, rnd, c):
    stroke(d, rnd, wobble([(270, 690), (610, 690), (610, 780), (270, 780), (270, 690)], rnd, 4), 12, c)
    for x in range(330, 600, 60):
        stroke(d, rnd, [(x, 690), (x, 780)], 8, c, passes=1)


def extra_blush(img, d, rnd, c):
    for x in (250, 630):
        blob(img, rnd, x, 650, 45, BLUSH, soft=True)


def extra_freckles(img, d, rnd, c):
    for cx in (270, 610):
        for _ in range(9):
            blob(img, rnd, cx + rnd.randint(-55, 55), 610 + rnd.randint(-30, 30), 6, (110, 60, 30, 255))


def extra_hair_scribble(img, d, rnd, c):
    for i in range(14):
        x = 200 + i * 37
        stroke(d, rnd, [(x, 250), (x + rnd.randint(-40, 40), 140 + rnd.randint(-30, 30))], 10, c, passes=1)


def extra_crayon_hair(img, d, rnd, c):
    for i in range(9):
        a = 200 + i * 17
        x, y = 440 + 300 * math.cos(math.radians(a)), 600 + 380 * math.sin(math.radians(a))
        stroke(d, rnd, [(x, y), (x + rnd.randint(-30, 30), y - 110)], 12, YELLOW, passes=1)


def extra_antenna(img, d, rnd, c):
    stroke(d, rnd, [(440, 230), (440, 140)], 12, c)
    blob(img, rnd, 440, 130, 30, RED)


def extra_scar(img, d, rnd, c):
    stroke(d, rnd, [(560, 360), (610, 600)], 10, c, passes=1)
    for t in (0.25, 0.5, 0.75):
        x, y = 560 + 50 * t, 360 + 240 * t
        stroke(d, rnd, [(x - 25, y), (x + 25, y - 6)], 7, c, passes=1)


def extra_tear(img, d, rnd, c):
    fill(d, rnd, [(EL + 10, EY + 40), (EL - 12, EY + 95), (EL + 10, EY + 115), (EL + 32, EY + 95)], (110, 170, 230, 255), 2)


def extra_sweat(img, d, rnd, c):
    fill(d, rnd, [(690, 300), (665, 360), (690, 380), (715, 360)], (110, 170, 230, 255), 2)


def extra_beard(img, d, rnd, c):
    pts = arc(440, 690, 300, 330, 10, 170, 24)
    for x, y in pts[2:-2]:
        for _ in range(3):
            blob(img, rnd, x + rnd.randint(-30, 30), y - rnd.randint(0, 120), 5, c)


def extra_bow(img, d, rnd, c):
    fill(d, rnd, [(560, 210), (660, 160), (660, 270)], PINK, 3)
    fill(d, rnd, [(760, 210), (660, 160), (660, 270)], PINK, 3)
    stroke(d, rnd, [(560, 210), (660, 160), (660, 270), (560, 210)], 8, c, passes=1)
    stroke(d, rnd, [(760, 210), (660, 160), (660, 270), (760, 210)], 8, c, passes=1)
    blob(img, rnd, 660, 215, 22, RED)


def extra_cat_ears(img, d, rnd, c):
    for s in (-1, 1):
        stroke(d, rnd, [(440 + s * 150, 260), (440 + s * 230, 110), (440 + s * 280, 300)], 16, c)


def extra_monocle(img, d, rnd, c):
    stroke(d, rnd, arc(ER, EY, 80, 80, 0, 360), 10, YELLOW)
    stroke(d, rnd, [(ER + 50, EY + 62), (ER + 90, EY + 260)], 5, YELLOW, passes=1)


def extra_bandage(img, d, rnd, c):
    t = Image.new("RGBA", (230, 70), (240, 210, 170, 255))
    td = ImageDraw.Draw(t)
    for x in range(85, 150, 18):
        for y in range(15, 60, 18):
            td.ellipse([x, y, x + 6, y + 6], fill=(170, 130, 90, 255))
    t = t.rotate(25, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(t, (470, 560))


def extra_stitches(img, d, rnd, c):
    stroke(d, rnd, [(160, 560), (720, 540)], 7, c, passes=1)
    for x in range(190, 720, 45):
        stroke(d, rnd, [(x, 530), (x + 8, 575)], 7, c, passes=1)


# ---------- receitas ----------
# (nome, rosto, olhos, sobrancelhas, nariz, boca, extras, cor do traço)
RECEITAS = [
    ("sorriso", face_oval, eyes_dots, brows_none, nose_none, mouth_smile, [extra_blush], INK),
    ("bigodudo", face_oval, eyes_pupils, brows_thick, nose_l, mouth_mustache, [], INK),
    ("assustado", face_oval, eyes_wide, brows_raised, nose_none, mouth_o, [extra_hair_scribble], INK),
    ("oculos-escuros", face_oval, eyes_sunglasses, brows_none, nose_none, mouth_smirk, [], INK),
    ("giz-de-cera", face_oval, eyes_dots, brows_none, nose_l, mouth_wavy, [extra_crayon_hair], RED),
    ("robo", face_square, eyes_pupils, brows_none, nose_none, mouth_robot, [extra_antenna], INK),
    ("feliz", face_round, eyes_happy, brows_none, nose_dot, mouth_grin, [extra_blush], INK),
    ("sonolento", face_egg, eyes_sleepy, brows_flat, nose_none, mouth_flat, [], INK),
    ("nocaute", face_round, eyes_x, brows_none, nose_none, mouth_tongue, [], INK),
    ("piscadinha", face_oval, eyes_wink, brows_raised, nose_none, mouth_smirk, [extra_freckles], INK),
    ("hipnotizado", face_round, eyes_spiral, brows_none, nose_none, mouth_zigzag, [], INK),
    ("apaixonado", face_oval, eyes_hearts, brows_none, nose_dot, mouth_smile, [extra_blush], INK),
    ("estrela", face_round, eyes_stars, brows_none, nose_none, mouth_laugh, [], INK),
    ("ciclope", face_egg, eyes_cyclops, brows_uni, nose_none, mouth_grin, [], GREEN),
    ("nerd", face_oval, eyes_round_glasses, brows_flat, nose_triangle, mouth_smile, [extra_freckles], INK),
    ("pirata", face_oval, eyes_patch, brows_angry, nose_l, mouth_smirk, [extra_scar, extra_beard], INK),
    ("bravo", face_square, eyes_angry, brows_angry, nose_none, mouth_frown, [], RED),
    ("cansado", face_egg, eyes_tired, brows_sad, nose_l, mouth_flat, [], INK),
    ("palhaco", face_round, eyes_wide, brows_raised, nose_clown, mouth_laugh, [extra_hair_scribble], INK),
    ("porquinho", face_round, eyes_dots, brows_none, nose_pig, mouth_smile, [extra_blush], INK),
    ("gato", face_oval, eyes_happy, brows_none, nose_cat, mouth_wavy, [extra_cat_ears], INK),
    ("vampiro", face_egg, eyes_angry, brows_angry, nose_none, mouth_fangs, [], INK),
    ("chorao", face_oval, eyes_pupils, brows_sad, nose_none, mouth_frown, [extra_tear], BLUE),
    ("nervoso", face_round, eyes_wide, brows_sad, nose_none, mouth_zigzag, [extra_sweat], INK),
    ("barbudo", face_oval, eyes_dots, brows_thick, nose_l, mouth_flat, [extra_beard], INK),
    ("lacinho", face_oval, eyes_happy, brows_none, nose_dot, mouth_smile, [extra_bow, extra_blush], INK),
    ("monoculo", face_egg, eyes_dots, brows_raised, nose_l, mouth_mustache, [extra_monocle], INK),
    ("machucado", face_round, eyes_x, brows_sad, nose_none, mouth_wavy, [extra_bandage], INK),
    ("costurado", face_square, eyes_x, brows_none, nose_none, mouth_zigzag, [extra_stitches], INK),
    ("minimalista", face_none, eyes_dots, brows_none, nose_none, mouth_flat, [], INK),
]


def gerar(i, receita, out):
    nome, rosto, olhos, sobr, nariz, boca, extras, cor = receita
    rnd = random.Random(1000 + i)
    img = cardboard(rnd, TONES[i % len(TONES)])
    d = ImageDraw.Draw(img)
    for parte in [rosto, *extras, sobr, olhos, nariz, boca]:
        parte(img, d, rnd, cor if parte in (rosto, boca) or cor == INK else INK)
        d = ImageDraw.Draw(img)
    m = torn_mask(rnd)
    final = Image.new("RGBA", (W, H), (120, 88, 55, 255))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((60, 40, 20, 255), mask=m)
    final.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(3)))
    final.paste(img, mask=m)
    for x, y, a in TAPE_SPOTS[i % len(TAPE_SPOTS)]:
        tape(final, rnd, x, y, a)
    final.convert("RGB").save(out / f"{nome}.png")


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(RECEITAS):
        gerar(i, r, out)
    print(f"{len(RECEITAS)} caras em {out}")
