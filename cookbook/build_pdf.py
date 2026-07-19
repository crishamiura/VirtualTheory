# -*- coding: utf-8 -*-
"""Build the Vital Theory cookbook as a designed PDF (fpdf2)."""
import os
import re
from fpdf import FPDF
from PIL import Image
from recipes_data import BOOK, CATEGORIES, RECIPES

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = r"C:\Windows\Fonts"
OUT = os.path.join(HERE, "Vital_Theory_Secret_Recipes.pdf")
IMGDIR = os.path.join(HERE, "img")
PDFIMG = os.path.join(IMGDIR, "_pdf")          # cropped versions for print
os.makedirs(PDFIMG, exist_ok=True)


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def img_for(title):
    p = os.path.join(IMGDIR, slug(title) + ".jpg")
    return p if os.path.exists(p) else None


def crop_cover(src, ratio, tag):
    """Center-crop an image to `ratio` (w/h) and cache it; return the path."""
    out = os.path.join(PDFIMG, f"{os.path.splitext(os.path.basename(src))[0]}_{tag}.jpg")
    if os.path.exists(out):
        return out
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target = ratio
    cur = w / h
    if cur > target:                 # too wide -> crop sides
        nw = int(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:                            # too tall -> crop top/bottom
        nh = int(w / target)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    im.save(out, "JPEG", quality=88, optimize=True)
    return out


def count_lines(pdf, w, text, family, style, size):
    """How many wrapped lines `text` needs at the given font/width (no drawing)."""
    pdf.set_font(family, style, size)
    lines = pdf.multi_cell(w, 5, text, dry_run=True, output="LINES")
    return max(1, len(lines))


def circle_img(src, size=600):
    """Return a circular (transparent-corner) PNG of the image."""
    from PIL import ImageDraw
    out = os.path.join(PDFIMG, f"{os.path.splitext(os.path.basename(src))[0]}_circle.png")
    if os.path.exists(out):
        return out
    im = Image.open(crop_cover(src, 1.0, "sq")).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    im.putalpha(mask)
    im.save(out, "PNG")
    return out

# palette
BLUE = (37, 99, 235)
CYAN = (6, 182, 212)
INK = (15, 23, 42)
SLATE = (71, 85, 105)
LIGHT = (240, 247, 255)
TAN = (236, 227, 212)
TAN_DK = (58, 49, 34)
GOLD = (176, 132, 66)
WHITE = (255, 255, 255)


class Cookbook(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(True, margin=20)
        self.set_margins(20, 20, 20)
        # Unicode fonts
        self.add_font("Sans", "", os.path.join(FONTS, "arial.ttf"))
        self.add_font("Sans", "B", os.path.join(FONTS, "arialbd.ttf"))
        self.add_font("Sans", "I", os.path.join(FONTS, "ariali.ttf"))
        self.add_font("Serif", "", os.path.join(FONTS, "georgia.ttf"))
        self.add_font("Serif", "B", os.path.join(FONTS, "georgiab.ttf"))
        self.add_font("Serif", "I", os.path.join(FONTS, "georgiai.ttf"))
        self.toc = []  # (title, category, page)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-15)
        self.set_font("Sans", "", 8)
        self.set_text_color(*SLATE)
        self.cell(0, 8, "Vital Theory's Secret Recipes", align="L")
        self.cell(0, 8, str(self.page_no()), align="R")


def rect(pdf, x, y, w, h, color):
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, style="F")


# ---------------- Cover ----------------
def cover(pdf):
    pdf.add_page()
    rect(pdf, 0, 0, 210, 297, TAN)
    # decorative border
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.8)
    pdf.rect(14, 14, 182, 269)
    pdf.set_line_width(0.3)
    pdf.rect(17, 17, 176, 263)

    pdf.set_text_color(*TAN_DK)
    pdf.set_xy(0, 46)
    pdf.set_font("Serif", "B", 52)
    pdf.cell(210, 20, "Vital Theory's", align="C")
    pdf.set_xy(0, 70)
    pdf.set_font("Serif", "I", 46)
    pdf.set_text_color(*GOLD)
    pdf.cell(210, 20, "Secret Recipes", align="C")

    pdf.set_text_color(90, 78, 58)
    pdf.set_xy(30, 100)
    pdf.set_font("Sans", "", 10)
    pdf.multi_cell(150, 6, BOOK["subtitle"].upper(), align="C")

    # medallion — real food photo in a gold ring (matches the site's book)
    cx, cy, r = 105, 168, 38
    hero = os.path.join(IMGDIR, "hero.jpg")
    pdf.set_fill_color(*GOLD)
    pdf.ellipse(cx - r - 2, cy - r - 2, 2 * (r + 2), 2 * (r + 2), style="F")
    if os.path.exists(hero):
        pdf.image(circle_img(hero), x=cx - r, y=cy - r, w=2 * r, h=2 * r)
    else:
        pdf.set_fill_color(*TAN)
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="F")
    # small seal badge overlapping the lower-right
    sx, sy, sr = 138, 198, 15
    pdf.set_fill_color(*TAN_DK)
    pdf.ellipse(sx - sr, sy - sr, 2 * sr, 2 * sr, style="F")
    pdf.set_text_color(*TAN)
    pdf.set_font("Sans", "B", 6)
    pdf.set_xy(sx - sr, sy - 7)
    pdf.multi_cell(2 * sr, 3.4, "DELICIOUS\nHEALTHY\nRECIPES", align="C")

    pdf.set_xy(20, 232)
    pdf.set_font("Serif", "I", 14)
    pdf.set_text_color(90, 78, 58)
    pdf.multi_cell(170, 8, BOOK["tagline"], align="C")

    pdf.set_xy(0, 262)
    pdf.set_font("Sans", "B", 11)
    pdf.set_text_color(*TAN_DK)
    pdf.cell(210, 6, "VITAL  THEORY", align="C")


# ---------------- Simple text page ----------------
def title_band(pdf, eyebrow, title):
    rect(pdf, 0, 0, 210, 62, BLUE)
    rect(pdf, 0, 58, 210, 4, CYAN)
    pdf.set_xy(20, 20)
    pdf.set_font("Sans", "B", 10)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 6, eyebrow.upper())
    pdf.set_xy(20, 30)
    pdf.set_font("Serif", "B", 30)
    pdf.cell(0, 14, title)
    pdf.set_xy(20, 74)
    pdf.set_text_color(*INK)


def welcome(pdf):
    pdf.add_page()
    title_band(pdf, "Welcome", "A note before you cook")
    pdf.set_font("Sans", "", 12)
    pdf.set_text_color(*SLATE)
    paras = [
        "Welcome to your kitchen's new best friend. Vital Theory began with a simple belief: that "
        "delicious, nourishing food shouldn't require rare ingredients, fancy equipment, or hours of "
        "your evening. It should be real food, made real easy.",
        "Inside you'll find recipes across ten everyday categories — from creamy pastas and juicy "
        "chicken to bright salads, cozy soups, and decadent desserts. Every one is kitchen-tested, "
        "written in clear numbered steps, and built for real weeknights. Most land on the table in "
        "about 30 minutes.",
        "Each recipe lists its prep time, cook time, servings, and difficulty up front, so you always "
        "know what you're getting into. And a little chef's tip closes every page to help you nail it "
        "the first time.",
        "So preheat the oven, pour a glass of something you love, and let's make dinner you're genuinely "
        "proud of. Welcome to the table.",
    ]
    for p in paras:
        pdf.multi_cell(0, 7, p)
        pdf.ln(3)
    pdf.ln(4)
    pdf.set_font("Serif", "I", 14)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 8, "— The Vital Theory Kitchen")


def how_to(pdf):
    pdf.add_page()
    title_band(pdf, "How to use this book", "Getting the most from every recipe")
    items = [
        ("Read it through first", "Give each recipe a quick read before you start so there are no surprises mid-cook."),
        ("Prep before you heat", "Chop, measure, and line up your ingredients. Calm cooking is good cooking."),
        ("Trust the times", "Prep and cook times are real-world tested — use them to plan your evening."),
        ("Season as you go", "Taste and adjust salt, acid, and heat. Recipes are a map, your palate is the compass."),
        ("Don't skip the tip", "The chef's tip at the bottom of each recipe is where the magic usually hides."),
    ]
    for head, body in items:
        pdf.set_font("Sans", "B", 13)
        pdf.set_text_color(*BLUE)
        pdf.cell(6, 8, "•")
        pdf.cell(0, 8, head, ln=1)
        pdf.set_x(26)
        pdf.set_font("Sans", "", 11)
        pdf.set_text_color(*SLATE)
        pdf.multi_cell(0, 6, body)
        pdf.ln(3)


# ---------------- Attribution / disclaimer ----------------
def about_recipes(pdf):
    pdf.add_page()
    title_band(pdf, "About these recipes", "Inspired by the greats")
    pdf.set_font("Sans", "", 12)
    pdf.set_text_color(*SLATE)
    paras = [
        "This collection celebrates the dishes that made the world's most beloved cooks "
        "famous — the roast chickens, ragus, curries, tarts and breads that have earned their "
        "place at great tables everywhere.",
        "Every recipe here is an original interpretation, written from scratch in our own words. "
        "Where a dish is closely associated with a particular chef, we credit them as inspiration "
        '("Inspired by ...") out of respect for their influence on how we all cook today.',
        "These recipes are not copied from, affiliated with, or endorsed by the chefs named. They "
        "are our own tested, everyday-friendly versions of the classics those chefs are celebrated "
        "for — reworked with clear steps and simple ingredients so anyone can make them at home.",
        "Consider each attribution a tip of the hat, and an invitation to explore the wonderful "
        "work of the cooks who inspired it.",
    ]
    for p in paras:
        pdf.multi_cell(0, 7, p)
        pdf.ln(3)


# ---------------- Table of contents ----------------
def render_toc(pdf, outline):
    """Called by fpdf2 to fill reserved TOC pages with correct page numbers."""
    title_band(pdf, "Contents", "What's inside")
    pdf.set_y(74)
    for section in outline:
        if pdf.get_y() > 262:
            pdf.add_page()
            pdf.set_y(24)
        page = section.page_number
        if section.level == 0:  # category
            pdf.ln(2)
            pdf.set_font("Sans", "B", 12)
            pdf.set_text_color(*CYAN)
            pdf.set_x(20)
            pdf.cell(0, 9, section.name.upper(), ln=1)
            continue
        name = section.name
        pdf.set_font("Sans", "", 11)
        pdf.set_text_color(*INK)
        title_w = pdf.get_string_width(name)
        page_str = str(page)
        page_w = pdf.get_string_width(page_str)
        avail = 170 - title_w - page_w - 6
        dot_w = pdf.get_string_width(".")
        dots = "." * max(0, int(avail / dot_w))
        pdf.set_x(24)
        pdf.cell(title_w + 2, 7, name)
        pdf.set_text_color(200, 210, 224)
        pdf.cell(avail, 7, dots)
        pdf.set_text_color(*INK)
        pdf.cell(page_w + 2, 7, page_str, ln=1, align="R")


# ---------------- Category divider ----------------
def divider(pdf, index, name, blurb):
    pdf.add_page()
    pdf.start_section(name, level=0)
    rect(pdf, 0, 0, 210, 297, LIGHT)

    # headliner photo (first recipe in this category)
    headliner = next((x["title"] for x in RECIPES if x["category"] == name), None)
    photo = img_for(headliner) if headliner else None
    if photo:
        pdf.image(crop_cover(photo, 210 / 150, "divider"), x=0, y=0, w=210, h=150)
    else:
        rect(pdf, 0, 0, 210, 150, INK)
    rect(pdf, 0, 150, 210, 4, CYAN)

    # chapter title block
    rect(pdf, 0, 154, 210, 90, BLUE)
    rect(pdf, 0, 244, 210, 4, CYAN)
    pdf.set_xy(0, 172)
    pdf.set_font("Serif", "B", 18)
    pdf.set_text_color(*CYAN)
    pdf.cell(210, 10, "CHAPTER %02d" % index, align="C")
    pdf.set_xy(0, 186)
    pdf.set_font("Serif", "B", 44)
    pdf.set_text_color(*WHITE)
    pdf.cell(210, 20, name, align="C")
    pdf.set_xy(30, 216)
    pdf.set_font("Serif", "I", 15)
    pdf.set_text_color(230, 240, 255)
    pdf.multi_cell(150, 8, blurb, align="C")


# ---------------- Recipe page ----------------
def recipe_page(pdf, r):
    pdf.add_page()
    pdf.start_section(r["title"], level=1)

    # full-bleed food photo banner
    photo = img_for(r["title"])
    if photo:
        pdf.image(crop_cover(photo, 210 / 58, "rbanner"), x=0, y=0, w=210, h=58)
    else:
        rect(pdf, 0, 0, 210, 58, INK)

    # title band below the photo (solid, keeps text legible)
    band_top = 58
    band_h = 34
    rect(pdf, 0, band_top, 210, band_h, INK)
    rect(pdf, 0, band_top - 4, 210, 4, CYAN)
    pdf.set_xy(20, band_top + 6)
    pdf.set_font("Sans", "B", 9)
    pdf.set_text_color(*CYAN)
    pdf.cell(0, 5, r["category"].upper())
    pdf.set_xy(20, band_top + 12)
    pdf.set_font("Serif", "B", 23)
    pdf.set_text_color(*WHITE)
    size = 23
    while pdf.get_string_width(r["title"]) > 170 and size > 13:
        size -= 1
        pdf.set_font("Serif", "B", size)
    pdf.cell(0, 11, r["title"])
    if r.get("chef"):
        pdf.set_xy(20, band_top + 24)
        pdf.set_font("Serif", "I", 10.5)
        pdf.set_text_color(*CYAN)
        pdf.cell(0, 6, r["chef"])

    # meta chips
    chip_y = 98
    chips = [("PREP", r["prep"]), ("COOK", r["cook"]),
             ("SERVES", r["serves"]), ("LEVEL", r["level"])]
    x = 20
    for label, val in chips:
        w = 42
        rect(pdf, x, chip_y, w, 15, LIGHT)
        pdf.set_xy(x, chip_y + 2)
        pdf.set_font("Sans", "B", 8)
        pdf.set_text_color(*BLUE)
        pdf.cell(w, 5, label, align="C")
        pdf.set_xy(x, chip_y + 6.5)
        pdf.set_font("Sans", "B", 11)
        pdf.set_text_color(*INK)
        pdf.cell(w, 6, val, align="C")
        x += w + 4

    # intro
    pdf.set_xy(20, chip_y + 20)
    pdf.set_font("Serif", "I", 11.5)
    pdf.set_text_color(*SLATE)
    pdf.multi_cell(170, 6, r["intro"])
    pdf.ln(2.5)

    top = pdf.get_y()
    box_w = 74           # ingredients column
    ix = 102             # instructions column x
    step_w = 190 - (ix + 9)   # instruction text width

    # --- pick a font/line-height that fits both columns on one page ---
    COL_MAX = 248        # columns must end above this (leaves room for the tip)
    avail = COL_MAX - (top + 8)
    chosen = None
    for fs, lh in [(10.5, 5.8), (10, 5.4), (9.5, 5.1), (9, 4.8), (8.5, 4.5)]:
        ing_h = sum(count_lines(pdf, box_w - 4, ing, "Sans", "", fs) * lh
                    for ing in r["ingredients"])
        steps_h = sum(count_lines(pdf, step_w, s, "Sans", "", fs) * lh + 1.5
                      for s in r["steps"])
        if max(ing_h, steps_h) <= avail:
            chosen = (fs, lh)
            break
    fs, lh = chosen or (8.5, 4.5)

    # ingredients
    pdf.set_font("Sans", "B", 13)
    pdf.set_text_color(*BLUE)
    pdf.set_xy(20, top)
    pdf.cell(box_w, 8, "Ingredients", ln=1)
    pdf.set_text_color(*INK)
    for ing in r["ingredients"]:
        pdf.set_x(20)
        pdf.set_font("Sans", "", fs)
        pdf.set_text_color(*CYAN)
        pdf.cell(4, lh, "▪")
        pdf.set_text_color(*INK)
        pdf.multi_cell(box_w - 4, lh, ing)
    ing_bottom = pdf.get_y()

    # instructions
    pdf.set_xy(ix, top)
    pdf.set_font("Sans", "B", 13)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 8, "Instructions", ln=1)
    for i, step in enumerate(r["steps"], 1):
        y = pdf.get_y()
        pdf.set_fill_color(*BLUE)
        pdf.ellipse(ix, y + 0.4, 5.6, 5.6, style="F")
        pdf.set_text_color(*WHITE)
        pdf.set_font("Sans", "B", 8.5)
        pdf.set_xy(ix, y + 1)
        pdf.cell(5.6, 4.5, str(i), align="C")
        pdf.set_font("Sans", "", fs)
        pdf.set_text_color(*INK)
        pdf.set_xy(ix + 9, y)
        pdf.multi_cell(step_w, lh, step)
        pdf.ln(1.5)
    steps_bottom = pdf.get_y()

    # chef's tip (measured height, never overlaps)
    tip_lines = count_lines(pdf, 155, r["tip"], "Serif", "I", 11)
    tip_h = 12 + tip_lines * 6
    y = max(ing_bottom, steps_bottom) + 5
    if y + tip_h > 276:
        y = 276 - tip_h
    rect(pdf, 20, y, 170, tip_h, LIGHT)
    rect(pdf, 20, y, 3, tip_h, CYAN)
    pdf.set_xy(28, y + 4)
    pdf.set_font("Sans", "B", 10)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 5, "CHEF'S TIP", ln=1)
    pdf.set_xy(28, y + 10)
    pdf.set_font("Serif", "I", 11)
    pdf.set_text_color(*INK)
    pdf.multi_cell(155, 6, r["tip"])


# ---------------- Conversion chart ----------------
def conversions(pdf):
    pdf.add_page()
    title_band(pdf, "Reference", "Kitchen conversion chart")
    pdf.set_y(76)

    def table(heading, rows):
        pdf.set_font("Sans", "B", 13)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 9, heading, ln=1)
        pdf.set_font("Sans", "", 11)
        for a, b in rows:
            y = pdf.get_y()
            pdf.set_fill_color(*LIGHT)
            if (pdf.get_y() // 8) % 2 == 0:
                rect(pdf, 20, y, 170, 8, (247, 250, 255))
            pdf.set_text_color(*INK)
            pdf.set_x(24)
            pdf.cell(85, 8, a)
            pdf.set_text_color(*SLATE)
            pdf.cell(80, 8, b, ln=1)
        pdf.ln(4)

    table("Volume", [
        ("1 tablespoon", "3 teaspoons  /  15 ml"),
        ("1/4 cup", "4 tablespoons  /  60 ml"),
        ("1/2 cup", "8 tablespoons  /  120 ml"),
        ("1 cup", "16 tablespoons  /  240 ml"),
        ("1 pint", "2 cups  /  475 ml"),
        ("1 quart", "4 cups  /  950 ml"),
    ])
    table("Weight", [
        ("1 ounce", "28 grams"),
        ("4 ounces", "113 grams"),
        ("8 ounces", "227 grams"),
        ("1 pound", "454 grams"),
    ])
    table("Oven temperature", [
        ("325 °F", "160 °C  /  Gas 3"),
        ("350 °F", "175 °C  /  Gas 4"),
        ("400 °F", "200 °C  /  Gas 6"),
        ("425 °F", "220 °C  /  Gas 7"),
    ])


def closing(pdf):
    pdf.add_page()
    rect(pdf, 0, 0, 210, 297, BLUE)
    pdf.set_xy(0, 110)
    pdf.set_font("Serif", "B", 34)
    pdf.set_text_color(*WHITE)
    pdf.cell(210, 16, "Happy cooking!", align="C")
    pdf.set_xy(30, 140)
    pdf.set_font("Sans", "", 13)
    pdf.set_text_color(225, 238, 255)
    pdf.multi_cell(150, 8,
        "Thank you for cooking with Vital Theory. We hope these recipes bring "
        "warmth, flavor, and a little less stress to your kitchen for years to come.",
        align="C")
    pdf.set_xy(0, 200)
    pdf.set_font("Sans", "B", 12)
    pdf.set_text_color(*WHITE)
    pdf.cell(210, 8, "vitaltheory.shop", align="C")


def build():
    pdf = Cookbook()
    cover(pdf)
    welcome(pdf)
    how_to(pdf)
    about_recipes(pdf)

    # Reserve TOC pages; fpdf2 fills them with correct page numbers at the end.
    n = len(RECIPES) + len(CATEGORIES)
    toc_pages = max(2, (n + 6 + 33) // 34)
    pdf.add_page()
    pdf.insert_toc_placeholder(render_toc, pages=toc_pages)

    for idx, (name, blurb) in enumerate(CATEGORIES, 1):
        divider(pdf, idx, name, blurb)
        for r in [x for x in RECIPES if x["category"] == name]:
            recipe_page(pdf, r)
    conversions(pdf)
    closing(pdf)
    pdf.output(OUT)
    return OUT, len(RECIPES)


if __name__ == "__main__":
    path, count = build()
    size = os.path.getsize(path)
    print(f"Built {path}\nRecipes: {count}  |  Size: {size/1024:.0f} KB")
