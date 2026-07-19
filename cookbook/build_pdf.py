# -*- coding: utf-8 -*-
"""Build the Vital Theory cookbook PDF in the warm editorial 'template' style:
cream background, terracotta accents, dark serif headings, a full-page cover,
a two-column table of contents, and flowing two-up recipe cards."""
import os
import re
from fpdf import FPDF
from PIL import Image
from recipes_data import BOOK, CATEGORIES, RECIPES

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = r"C:\Windows\Fonts"
OUT = os.path.join(HERE, "Vital_Theory_Secret_Recipes.pdf")
IMGDIR = os.path.join(HERE, "img")
PDFIMG = os.path.join(IMGDIR, "_pdf")
COVER = os.path.join(IMGDIR, "_cover", "cover.jpg")
os.makedirs(PDFIMG, exist_ok=True)

# ---- palette (sampled from the template) ----
CREAM = (250, 246, 241)
WHITE = (255, 255, 255)
TERRA = (191, 73, 42)          # headings / accents
BADGE = (203, 90, 50)          # number badges
DARK = (43, 41, 35)            # titles
BODY = (66, 60, 54)            # body text
MUTED = (150, 140, 130)        # labels / leaders
TAGBG = (245, 229, 220)        # category pill
TIPBG = (245, 239, 227)        # chef-tip banner
BORDER = (228, 219, 208)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def img_for(title):
    p = os.path.join(IMGDIR, slug(title) + ".jpg")
    return p if os.path.exists(p) else None


def crop_cover(src, ratio, tag):
    out = os.path.join(PDFIMG, f"{os.path.splitext(os.path.basename(src))[0]}_{tag}.jpg")
    if os.path.exists(out):
        return out
    im = Image.open(src).convert("RGB")
    w, h = im.size
    cur = w / h
    if cur > ratio:
        nw = int(h * ratio); x = (w - nw) // 2; im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / ratio); y = (h - nh) // 2; im = im.crop((0, y, w, y + nh))
    im.save(out, "JPEG", quality=88, optimize=True)
    return out


class Book(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(False)
        self.set_margins(20, 20, 20)
        self.add_font("Serif", "", os.path.join(FONTS, "georgia.ttf"))
        self.add_font("Serif", "B", os.path.join(FONTS, "georgiab.ttf"))
        self.add_font("Serif", "I", os.path.join(FONTS, "georgiai.ttf"))
        self.add_font("Sans", "", os.path.join(FONTS, "arial.ttf"))
        self.add_font("Sans", "B", os.path.join(FONTS, "arialbd.ttf"))
        self.add_font("Sans", "I", os.path.join(FONTS, "ariali.ttf"))
        self.cursor = 0

    def header(self):
        # cream background on every page
        self.set_fill_color(*CREAM)
        self.rect(0, 0, 210, 297, "F")

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-13)
        self.set_font("Serif", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, str(self.page_no()), align="C")


def rrect(pdf, x, y, w, h, color, r=3.2, style="F"):
    pdf.set_fill_color(*color)
    try:
        pdf.rect(x, y, w, h, style=style, round_corners=True, corner_radius=r)
    except TypeError:
        pdf.rect(x, y, w, h, style=style)


def count_lines(pdf, w, text, fam, st, sz):
    pdf.set_font(fam, st, sz)
    return max(1, len(pdf.multi_cell(w, 5, text, dry_run=True, output="LINES")))


# ---------------- cover ----------------
def cover(pdf):
    pdf.add_page()
    if os.path.exists(COVER):
        pdf.image(COVER, x=0, y=0, w=210, h=297)
    else:
        pdf.set_font("Serif", "B", 40)
        pdf.set_xy(0, 120)
        pdf.set_text_color(*DARK)
        pdf.cell(210, 20, "Vital Theory's Secret Recipes", align="C")


# ---------------- about / credits ----------------
def about(pdf):
    pdf.add_page()
    pdf.set_xy(0, 40)
    pdf.set_font("Sans", "B", 10)
    pdf.set_text_color(*TERRA)
    pdf.cell(210, 6, "T H E   C O L L E C T I O N", align="C")
    pdf.set_xy(0, 50)
    pdf.set_font("Serif", "B", 30)
    pdf.set_text_color(*DARK)
    pdf.cell(210, 14, "About These Recipes", align="C")
    # rule
    pdf.set_draw_color(*TERRA); pdf.set_line_width(0.6)
    pdf.line(85, 70, 125, 70)

    pdf.set_xy(30, 84)
    pdf.set_font("Serif", "", 12)
    pdf.set_text_color(*BODY)
    paras = [
        "Two hundred recipes, inspired by the cooks who made them famous. From roast chickens "
        "and slow ragus to golden tarts and crusty breads, this collection reimagines the "
        "world's best-loved dishes as easy, everyday meals you can actually make at home.",
        "Every recipe is written from scratch in our own words, with clear steps, honest prep "
        "and cook times, a full-color photo, and a chef's tip. Where a dish is closely tied to "
        "a particular chef, we credit them as inspiration out of respect for their influence.",
        "These recipes are original interpretations. They are not copied from, affiliated with, "
        "or endorsed by the chefs named - each credit is simply a tip of the hat to the cooking "
        "that inspired it. Now tie on an apron, and let's get cooking.",
    ]
    for p in paras:
        pdf.set_x(30)
        pdf.multi_cell(150, 7.4, p)
        pdf.ln(4)
    pdf.ln(2)
    pdf.set_x(30)
    pdf.set_font("Serif", "I", 13)
    pdf.set_text_color(*TERRA)
    pdf.cell(150, 8, "- The Vital Theory Kitchen", align="C")


# ---------------- table of contents ----------------
def render_toc(pdf, outline):
    cols_x = [20, 110]
    col_w = 80
    TOP_FIRST, TOP_REST, BOTTOM = 64, 24, 274
    st = {"col": 0, "y": TOP_FIRST, "top": TOP_FIRST}

    pdf.set_xy(0, 24)
    pdf.set_font("Sans", "B", 10); pdf.set_text_color(*TERRA)
    pdf.cell(210, 6, "T H E   C O L L E C T I O N", align="C")
    pdf.set_xy(0, 33); pdf.set_font("Serif", "B", 27); pdf.set_text_color(*DARK)
    pdf.cell(210, 13, "Table of Contents", align="C")
    pdf.set_draw_color(*TERRA); pdf.set_line_width(0.6); pdf.line(90, 52, 120, 52)

    def flow(need):
        if st["y"] + need <= BOTTOM:
            return
        if st["col"] == 0:
            st["col"] = 1; st["y"] = st["top"]
        else:
            pdf.add_page()
            st["col"] = 0; st["top"] = TOP_REST; st["y"] = TOP_REST

    idx = 0
    for s in outline:
        if s.level == 0:                       # category header
            flow(18)
            x = cols_x[st["col"]]
            pdf.set_xy(x, st["y"])
            pdf.set_font("Serif", "B", 13); pdf.set_text_color(*TERRA)
            pdf.cell(col_w, 8, s.name)
            pdf.set_draw_color(*BORDER); pdf.set_line_width(0.4)
            pdf.line(x, st["y"] + 8.5, x + col_w, st["y"] + 8.5)
            st["y"] += 12.5
        else:                                  # recipe entry
            idx += 1
            flow(5.6)
            x = cols_x[st["col"]]; y = st["y"]
            num = str(idx); page = str(s.page_number)
            pdf.set_xy(x, y)
            pdf.set_font("Sans", "B", 8.5); pdf.set_text_color(*TERRA)
            pdf.cell(8, 5, num)
            name_x = x + 8
            pdf.set_font("Sans", "", 9.3); pdf.set_text_color(*BODY)
            name = s.name
            pw = pdf.get_string_width(page)
            while pdf.get_string_width(name) > col_w - 8 - pw - 5 and len(name) > 6:
                name = name[:-2]
            if name != s.name:
                name = name.rstrip() + "..."
            name_w = pdf.get_string_width(name)
            pdf.set_xy(name_x, y); pdf.cell(name_w + 2, 5, name)
            avail = col_w - 8 - name_w - pw - 4
            dotw = pdf.get_string_width(".") or 1
            pdf.set_text_color(*MUTED)
            pdf.cell(avail, 5, "." * max(0, int(avail / dotw)))
            pdf.set_text_color(*BODY)
            pdf.cell(pw + 2, 5, page, align="R")
            st["y"] += 5.6


# ---------------- recipe card ----------------
# card geometry (compact, two-up)
PAD = 7
PHOTO_W = 38
ING_X = 20 + PAD + PHOTO_W + 5      # 70
ING_W = 36
STEP_X = ING_X + ING_W + 4          # 110
STEP_W = 190 - PAD - STEP_X         # 73
FS, LH = 7.9, 4.05
CR = 2.3                            # step number radius
ING_TW = ING_W - 3.5
STEP_TW = STEP_W - 2 * CR - 3
LEFT_H = PHOTO_W + 3 + 12           # photo + gap + meta boxes
HEAD_H = 21
TIPLH = 4.05


def measure(pdf, r):
    ing_h = sum(count_lines(pdf, ING_TW, i, "Sans", "", FS) for i in r["ingredients"]) * LH + 8
    step_h = sum(count_lines(pdf, STEP_TW, s, "Sans", "", FS) * LH + 1.2 for s in r["steps"]) + 8
    body_h = max(LEFT_H, ing_h, step_h)
    tip_h = count_lines(pdf, 150, r["tip"], "Serif", "I", 8.0) * TIPLH + 6.5
    return PAD + HEAD_H + body_h + 4 + tip_h + PAD


def new_content_page(pdf):
    pdf.add_page()
    pdf.cursor = 22


def place_recipe(pdf, r, num, is_first_in_cat):
    ch = measure(pdf, r)
    if pdf.cursor + ch > 278:
        new_content_page(pdf)
    top = pdf.cursor
    x, pad = 20, PAD

    if is_first_in_cat:
        pdf.start_section(r["category"], level=0)
    pdf.start_section(r["title"], level=1)

    rrect(pdf, x, top, 170, ch, WHITE, r=4)

    # number badge
    br = 6.5
    bx, by = x + pad + br, top + pad + br
    pdf.set_fill_color(*BADGE)
    pdf.ellipse(bx - br, by - br, 2 * br, 2 * br, style="F")
    pdf.set_text_color(*WHITE)
    ns = 12 if num < 100 else 10
    pdf.set_font("Serif", "B", ns)
    pdf.set_xy(bx - br, by - ns / 5.4)
    pdf.cell(2 * br, ns / 2.2, str(num), align="C")

    # title
    tx = x + pad + 2 * br + 5
    pdf.set_xy(tx, top + pad + 0.5)
    pdf.set_font("Serif", "B", 14)
    pdf.set_text_color(*DARK)
    size = 14
    maxw = 190 - tx - pad
    while pdf.get_string_width(r["title"]) > maxw and size > 9.5:
        size -= 0.5
        pdf.set_font("Serif", "B", size)
    pdf.cell(0, 8, r["title"])

    # category tag pill + chef line
    ty = top + pad + 10
    pdf.set_font("Sans", "B", 6.6)
    tag = r["category"].upper()
    tw = pdf.get_string_width(tag) + 9
    rrect(pdf, tx, ty, tw, 6, TAGBG, r=3)
    pdf.set_xy(tx, ty + 0.5)
    pdf.set_text_color(*TERRA)
    pdf.cell(tw, 5, tag, align="C")
    if r.get("chef"):
        pdf.set_xy(tx + tw + 4, ty + 0.5)
        pdf.set_font("Serif", "I", 8.2)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, r["chef"])

    body_top = top + pad + HEAD_H

    # photo
    photo = img_for(r["title"])
    px = x + pad
    if photo:
        pdf.image(crop_cover(photo, 1.0, "sq"), x=px, y=body_top, w=PHOTO_W, h=PHOTO_W)
        pdf.set_draw_color(*BORDER); pdf.set_line_width(0.3)
        try:
            pdf.rect(px, body_top, PHOTO_W, PHOTO_W, round_corners=True, corner_radius=3)
        except TypeError:
            pdf.rect(px, body_top, PHOTO_W, PHOTO_W)
    # meta boxes
    meta = [("PREP", r["prep"]), ("COOK", r["cook"]), ("SERVES", r["serves"])]
    mbw = (PHOTO_W - 3) / 3
    for i, (lab, val) in enumerate(meta):
        mx = px + i * (mbw + 1.5)
        my = body_top + PHOTO_W + 3
        pdf.set_draw_color(*BORDER); pdf.set_line_width(0.3)
        try:
            pdf.rect(mx, my, mbw, 12, style="D", round_corners=True, corner_radius=2)
        except TypeError:
            pdf.rect(mx, my, mbw, 12)
        pdf.set_xy(mx, my + 1.6)
        pdf.set_font("Sans", "", 5.2); pdf.set_text_color(*MUTED)
        pdf.cell(mbw, 3, lab, align="C")
        pdf.set_xy(mx, my + 5.2)
        pdf.set_font("Sans", "B", 7.4); pdf.set_text_color(*DARK)
        pdf.cell(mbw, 4, val, align="C")

    # ingredients column
    pdf.set_xy(ING_X, body_top)
    pdf.set_font("Serif", "B", 10.5); pdf.set_text_color(*TERRA)
    pdf.cell(ING_W, 6, "Ingredients")
    pdf.set_draw_color(*TERRA); pdf.set_line_width(0.4)
    pdf.line(ING_X, body_top + 6, ING_X + ING_W, body_top + 6)
    yy = body_top + 9
    for ing in r["ingredients"]:
        pdf.set_xy(ING_X, yy)
        pdf.set_text_color(*TERRA); pdf.set_font("Sans", "", FS); pdf.cell(3, LH, "•")
        pdf.set_text_color(*BODY)
        pdf.set_xy(ING_X + 3.5, yy)
        pdf.multi_cell(ING_TW, LH, ing)
        yy = pdf.get_y()

    # instructions column
    pdf.set_xy(STEP_X, body_top)
    pdf.set_font("Serif", "B", 10.5); pdf.set_text_color(*TERRA)
    pdf.cell(STEP_W, 6, "Instructions")
    pdf.set_draw_color(*TERRA); pdf.set_line_width(0.4)
    pdf.line(STEP_X, body_top + 6, STEP_X + STEP_W, body_top + 6)
    yy = body_top + 9
    for i, step in enumerate(r["steps"], 1):
        pdf.set_fill_color(*TERRA)
        pdf.ellipse(STEP_X, yy + 0.3, 2 * CR, 2 * CR, style="F")
        pdf.set_text_color(*WHITE); pdf.set_font("Sans", "B", 6.2)
        pdf.set_xy(STEP_X, yy + 0.6)
        pdf.cell(2 * CR, 3.8, str(i), align="C")
        pdf.set_text_color(*BODY); pdf.set_font("Sans", "", FS)
        pdf.set_xy(STEP_X + 2 * CR + 3, yy)
        pdf.multi_cell(STEP_TW, LH, step)
        yy = pdf.get_y() + 1.3

    # chef's tip banner (positioned from the measured card height)
    tip_h = count_lines(pdf, 150, r["tip"], "Serif", "I", 8.0) * TIPLH + 6.5
    tipy = top + ch - PAD - tip_h
    rrect(pdf, x + pad, tipy, 170 - 2 * pad, tip_h, TIPBG, r=3)
    pdf.set_fill_color(*TERRA)
    pdf.rect(x + pad, tipy, 1.6, tip_h, "F")
    pdf.set_xy(x + pad + 5, tipy + 2.0)
    pdf.set_font("Serif", "B", 8.4)
    pdf.set_text_color(*TERRA)
    pdf.cell(15, 4.4, "Chef's Tip")
    pdf.set_xy(x + pad + 21, tipy + 2.0)
    pdf.set_font("Serif", "I", 8.0); pdf.set_text_color(*BODY)
    pdf.multi_cell(170 - 2 * pad - 25, TIPLH, r["tip"])

    pdf.cursor = top + ch + 6   # card bottom + gap


def toc_page_count():
    """Simulate render_toc's two-column flow to get the exact page count."""
    TOP_FIRST, TOP_REST, BOTTOM = 64, 24, 274
    col, y, top, pages = 0, TOP_FIRST, TOP_FIRST, 1
    entries = []
    for name, _ in CATEGORIES:
        entries.append("h")
        entries += ["e"] * len([x for x in RECIPES if x["category"] == name])
    for e in entries:
        need = 18 if e == "h" else 5.6
        adv = 12.5 if e == "h" else 5.6
        if y + need > BOTTOM:
            if col == 0:
                col = 1; y = top
            else:
                pages += 1; col = 0; top = TOP_REST; y = TOP_REST
        y += adv
    return pages


def build():
    pdf = Book()
    cover(pdf)
    about(pdf)

    toc_pages = toc_page_count()
    pdf.add_page()
    pdf.insert_toc_placeholder(render_toc, pages=toc_pages)

    # insert_toc_placeholder leaves us on a fresh content page — use it directly
    pdf.set_fill_color(*CREAM); pdf.rect(0, 0, 210, 297, "F")
    pdf.cursor = 22
    num = 0
    for name, _ in CATEGORIES:
        items = [x for x in RECIPES if x["category"] == name]
        for j, r in enumerate(items):
            num += 1
            place_recipe(pdf, r, num, is_first_in_cat=(j == 0))

    pdf.output(OUT)
    return OUT, len(RECIPES)


if __name__ == "__main__":
    path, count = build()
    print(f"Built {path}\nRecipes: {count}  |  Size: {os.path.getsize(path)/1024:.0f} KB")
