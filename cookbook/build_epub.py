# -*- coding: utf-8 -*-
"""Build the Vital Theory cookbook as a reflowable ePub (ebooklib)."""
import os
import re
from ebooklib import epub
from recipes_data import BOOK, CATEGORIES, RECIPES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Vital_Theory_Secret_Recipes.epub")
IMGDIR = os.path.join(HERE, "img")


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def img_path(title):
    p = os.path.join(IMGDIR, slug(title) + ".jpg")
    return p if os.path.exists(p) else None

CSS = """
body { font-family: Georgia, 'Times New Roman', serif; color: #0f172a; line-height: 1.6; margin: 0 6%; }
h1, h2, h3, .eyebrow { font-family: 'Helvetica Neue', Arial, sans-serif; }
h1 { color: #2563eb; font-size: 1.9em; margin: .6em 0 .1em; line-height: 1.15; }
h2 { color: #0f172a; font-size: 1.5em; border-bottom: 3px solid #06b6d4; padding-bottom: .2em; }
.eyebrow { color: #06b6d4; text-transform: uppercase; letter-spacing: .12em; font-size: .75em; font-weight: bold; }
.intro { font-style: italic; color: #475569; font-size: 1.05em; }
.chef { color: #06b6d4; font-style: italic; font-family: Georgia, serif; margin: -.2em 0 .4em; font-size: .98em; }
.meta { background: #f0f7ff; border-radius: 10px; padding: .6em .9em; margin: 1em 0; font-family: Arial, sans-serif; font-size: .9em; color: #1e293b; }
.meta b { color: #2563eb; }
h3.sec { color: #2563eb; font-size: 1.15em; margin-bottom: .3em; }
ul.ing { list-style: none; padding-left: 0; }
ul.ing li { padding: .15em 0 .15em 1.1em; position: relative; }
ul.ing li:before { content: '▪'; color: #06b6d4; position: absolute; left: 0; }
ol.steps li { margin-bottom: .55em; padding-left: .2em; }
.tip { background: #f0f7ff; border-left: 4px solid #06b6d4; padding: .8em 1em; border-radius: 8px; margin: 1.2em 0; }
.tip b { color: #2563eb; font-family: Arial, sans-serif; font-size: .8em; letter-spacing: .08em; display: block; margin-bottom: .3em; }
.tip span { font-style: italic; }
.cover-t { text-align: center; margin-top: 22%; }
.cover-t .brand { font-size: 2.6em; font-weight: bold; color: #3a3122; }
.cover-t .script { font-size: 2.2em; font-style: italic; color: #b08442; }
.cover-t .sub { font-family: Arial, sans-serif; letter-spacing: .1em; font-size: .8em; color: #6f6450; margin-top: 1em; }
.cover-t .tag { font-style: italic; color: #6f6450; margin-top: 2em; }
.rimg { width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; margin: .3em 0 1em; display:block; }
.cover-img { width: 62%; border-radius: 50%; display:block; margin: 2em auto 0; border: 6px solid #b08442; }
.chapter-hero { text-align:center; background:#2563eb; color:#fff; padding: 2.4em 1em; border-radius: 14px; margin-bottom: 1.4em; }
.chapter-hero .heroimg { width:100%; max-height:220px; object-fit:cover; border-radius:10px; margin-bottom:1em; }
.chapter-hero .c { color:#a5d8ff; letter-spacing:.15em; font-family:Arial,sans-serif; font-size:.8em; }
.chapter-hero h1 { color:#fff; font-size:2.4em; margin:.2em 0; }
.chapter-hero p { color:#e0edff; font-style:italic; margin:0; }
table.conv { width:100%; border-collapse: collapse; margin: 1em 0; font-family: Arial, sans-serif; font-size:.92em; }
table.conv td { padding: .45em .6em; border-bottom: 1px solid #e2e8f0; }
table.conv td:first-child { font-weight: bold; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 2em 0; }
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build():
    book = epub.EpubBook()
    book.set_identifier("vital-theory-secret-recipes")
    book.set_title(BOOK["title"])
    book.set_language("en")
    book.add_author(BOOK["author"])
    book.add_metadata("DC", "description", BOOK["tagline"])

    style = epub.EpubItem(uid="style", file_name="style/main.css",
                          media_type="text/css", content=CSS)
    book.add_item(style)

    # Register every image used, as embedded EpubImage items
    embedded = {}

    def embed(path):
        if not path:
            return None
        base = os.path.basename(path)
        if base not in embedded:
            with open(path, "rb") as f:
                item = epub.EpubImage(uid="img_" + slug(base), file_name="images/" + base,
                                      media_type="image/jpeg", content=f.read())
            book.add_item(item)
            embedded[base] = "images/" + base
        return embedded[base]

    chapters = []

    # Cover / title page
    cover = epub.EpubHtml(title="Title", file_name="cover.xhtml", lang="en")
    cover.add_item(style)
    hero_src = embed(os.path.join(IMGDIR, "hero.jpg")) if os.path.exists(os.path.join(IMGDIR, "hero.jpg")) else None
    hero_html = f'<img class="cover-img" src="{hero_src}" alt="Fresh healthy bowl"/>' if hero_src else ""
    cover.content = f"""<html><head><link rel="stylesheet" href="style/main.css"/></head><body>
    <div class="cover-t">
      <div class="brand">Vital Theory's</div>
      <div class="script">Secret Recipes</div>
      <div class="sub">{esc(BOOK['subtitle']).upper()}</div>
      {hero_html}
      <div class="tag">{esc(BOOK['tagline'])}</div>
    </div></body></html>"""
    book.add_item(cover)
    chapters.append(cover)

    # Welcome
    welcome = epub.EpubHtml(title="Welcome", file_name="welcome.xhtml", lang="en")
    welcome.add_item(style)
    welcome.content = """<html><head><link rel="stylesheet" href="style/main.css"/></head><body>
    <p class="eyebrow">Welcome</p>
    <h1>A note before you cook</h1>
    <p>Welcome to your kitchen's new best friend. Vital Theory began with a simple belief:
    that delicious, nourishing food shouldn't require rare ingredients, fancy equipment, or
    hours of your evening. It should be real food, made real easy.</p>
    <p>Inside you'll find recipes across ten everyday categories &mdash; from creamy pastas and
    juicy chicken to bright salads, cozy soups, and decadent desserts. Every one is
    kitchen-tested, written in clear numbered steps, and built for real weeknights. Most land
    on the table in about 30 minutes.</p>
    <p>Each recipe lists its prep time, cook time, servings, and difficulty up front, and a
    little chef's tip closes every page to help you nail it the first time.</p>
    <p>So preheat the oven, pour a glass of something you love, and let's make dinner you're
    genuinely proud of. Welcome to the table.</p>
    <p style="color:#2563eb;font-style:italic;">&mdash; The Vital Theory Kitchen</p>
    </body></html>"""
    book.add_item(welcome)
    chapters.append(welcome)

    # Attribution / disclaimer
    about = epub.EpubHtml(title="About These Recipes", file_name="about.xhtml", lang="en")
    about.add_item(style)
    about.content = """<html><head><link rel="stylesheet" href="style/main.css"/></head><body>
    <p class="eyebrow">About these recipes</p>
    <h1>Inspired by the greats</h1>
    <p>This collection celebrates the dishes that made the world's most beloved cooks famous
    &mdash; the roast chickens, ragus, curries, tarts and breads that have earned their place
    at great tables everywhere.</p>
    <p>Every recipe here is an original interpretation, written from scratch in our own words.
    Where a dish is closely associated with a particular chef, we credit them as inspiration
    ("Inspired by &hellip;") out of respect for their influence on how we all cook today.</p>
    <p>These recipes are not copied from, affiliated with, or endorsed by the chefs named. They
    are our own tested, everyday-friendly versions of the classics those chefs are celebrated
    for &mdash; reworked with clear steps and simple ingredients so anyone can make them at home.</p>
    <p>Consider each attribution a tip of the hat, and an invitation to explore the wonderful
    work of the cooks who inspired it.</p>
    </body></html>"""
    book.add_item(about)
    chapters.append(about)

    # One chapter file per category, with a hero + all its recipes
    toc = []
    for idx, (name, blurb) in enumerate(CATEGORIES, 1):
        recs = [r for r in RECIPES if r["category"] == name]
        hero = embed(img_path(recs[0]["title"])) if recs else None
        hero_tag = f'<img class="heroimg" src="{hero}" alt="{esc(name)}"/>' if hero else ""
        parts = [f"""<html><head><link rel="stylesheet" href="style/main.css"/></head><body>
        <div class="chapter-hero">{hero_tag}<div class="c">CHAPTER {idx:02d}</div>
        <h1>{esc(name)}</h1><p>{esc(blurb)}</p></div>"""]
        for r in recs:
            ings = "".join(f"<li>{esc(i)}</li>" for i in r["ingredients"])
            steps = "".join(f"<li>{esc(s)}</li>" for s in r["steps"])
            rimg = embed(img_path(r["title"]))
            rimg_tag = f'<img class="rimg" src="{rimg}" alt="{esc(r["title"])}"/>' if rimg else ""
            parts.append(f"""
            <p class="eyebrow">{esc(r['category'])}</p>
            <h2>{esc(r['title'])}</h2>
            <p class="chef">{esc(r.get('chef',''))}</p>
            {rimg_tag}
            <p class="intro">{esc(r['intro'])}</p>
            <p class="meta"><b>Prep</b> {esc(r['prep'])} &nbsp;·&nbsp; <b>Cook</b> {esc(r['cook'])}
            &nbsp;·&nbsp; <b>Serves</b> {esc(r['serves'])} &nbsp;·&nbsp; <b>Level</b> {esc(r['level'])}</p>
            <h3 class="sec">Ingredients</h3>
            <ul class="ing">{ings}</ul>
            <h3 class="sec">Instructions</h3>
            <ol class="steps">{steps}</ol>
            <div class="tip"><b>CHEF'S TIP</b><span>{esc(r['tip'])}</span></div>
            <hr/>""")
        parts.append("</body></html>")
        ch = epub.EpubHtml(title=name, file_name=f"ch{idx:02d}.xhtml", lang="en")
        ch.add_item(style)
        ch.content = "".join(parts)
        book.add_item(ch)
        chapters.append(ch)
        toc.append(ch)

    # Conversions
    conv = epub.EpubHtml(title="Conversion Chart", file_name="conversions.xhtml", lang="en")
    conv.add_item(style)
    conv.content = """<html><head><link rel="stylesheet" href="style/main.css"/></head><body>
    <p class="eyebrow">Reference</p><h1>Kitchen Conversion Chart</h1>
    <h3 class="sec">Volume</h3>
    <table class="conv">
    <tr><td>1 tablespoon</td><td>3 teaspoons / 15 ml</td></tr>
    <tr><td>1/4 cup</td><td>4 tablespoons / 60 ml</td></tr>
    <tr><td>1/2 cup</td><td>8 tablespoons / 120 ml</td></tr>
    <tr><td>1 cup</td><td>16 tablespoons / 240 ml</td></tr>
    <tr><td>1 pint</td><td>2 cups / 475 ml</td></tr>
    <tr><td>1 quart</td><td>4 cups / 950 ml</td></tr></table>
    <h3 class="sec">Weight</h3>
    <table class="conv">
    <tr><td>1 ounce</td><td>28 grams</td></tr>
    <tr><td>4 ounces</td><td>113 grams</td></tr>
    <tr><td>8 ounces</td><td>227 grams</td></tr>
    <tr><td>1 pound</td><td>454 grams</td></tr></table>
    <h3 class="sec">Oven Temperature</h3>
    <table class="conv">
    <tr><td>325 &deg;F</td><td>160 &deg;C / Gas 3</td></tr>
    <tr><td>350 &deg;F</td><td>175 &deg;C / Gas 4</td></tr>
    <tr><td>400 &deg;F</td><td>200 &deg;C / Gas 6</td></tr>
    <tr><td>425 &deg;F</td><td>220 &deg;C / Gas 7</td></tr></table>
    <hr/><p style="text-align:center;color:#2563eb;"><b>Happy cooking! &nbsp;·&nbsp; vitaltheory.shop</b></p>
    </body></html>"""
    book.add_item(conv)
    chapters.append(conv)

    # Navigation
    book.toc = [cover, welcome, about] + [(epub.Section(name), (ch,))
                                          for (name, _), ch in zip(CATEGORIES, toc)] + [conv]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    epub.write_epub(OUT, book)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Built {path}\nSize: {os.path.getsize(path)/1024:.0f} KB  |  Recipes: {len(RECIPES)}")
