# Vital Theory — Recipe Ebook Landing Page + Cookbook

A complete recreation of the **Vital Theory** recipe-ebook website, plus the actual
downloadable cookbook (PDF + ePub) that the site sells — **200 chef-inspired recipes**
with a real photo for every dish.

## 📁 Project structure

```
Ebook-Recipe-Website/
├── index.html            # The landing page (single page, all sections)
├── styles.css            # All styling (blue→cyan brand, responsive)
├── script.js             # FAQ accordion, mobile nav, book rotate/open
├── assets/img/           # Photos used by the website (category + sample cards)
├── README.md             # This file
├── store/                # Flask store backend (checkout, receipts, admin)
│   ├── app.py            #   routes, orders DB, receipt PDF, admin dashboard
│   ├── templates/        #   checkout / success / receipt / admin pages
│   ├── static/store.css  #   store styling (brand-matched)
│   ├── .env.example      #   config template (price, admin password, Stripe)
│   ├── requirements.txt
│   └── run.bat           #   one-click start (Windows)
└── cookbook/
    ├── recipes.json                       # The 200 recipes (source of truth)
    ├── recipes_data.py                    # Book metadata + loads recipes.json
    ├── parts/                             # Per-chapter JSON the recipes were assembled from
    ├── fetch_images.py                    # Downloads a photo for every recipe -> img/
    ├── images.json                        # recipe title -> image filename
    ├── img/                               # 200 recipe photos + hero
    ├── build_pdf.py                       # Designed, fixed-layout PDF (with photos)
    ├── build_epub.py                      # Reflowable ePub (e-readers / Kindle)
    ├── build_all.py                       # Build both at once
    ├── Vital_Theory_Secret_Recipes.pdf    # ← the cookbook (PDF, ~240 pages)
    └── Vital_Theory_Secret_Recipes.epub   # ← the cookbook (ePub)
```

## 🌐 The website

The landing page (`index.html` + `styles.css` + `script.js` + `assets/`) faithfully
recreates every section of the original:

Navbar · Hero (with rotatable 3-D book) · About / "Real food, real easy" ·
What's Inside (16 chapter cards, each a real dish + chef credit) · Benefits ·
Sample Recipes · Testimonials · Pricing · FAQ (accordion) · Final CTA · Footer.

Every purchase button ("Get the Cookbook", "Unlock All 200 Recipes", etc.) opens your
**Gumroad** product in an on-page cart/checkout overlay:

`https://ivysia8.gumroad.com/l/VitalTheorySecretRecipes`

This is wired with Gumroad's overlay script (`gumroad.com/js/gumroad.js`) + the
`gumroad-button` class, so clicking any buy button pops the Gumroad cart without leaving
the page. Real payments, fulfilment, and buyer receipts are all handled by Gumroad.

### 💰 Where your revenue, buyers & receipts live

Because checkout runs on **Gumroad**, your live numbers are in your **Gumroad dashboard**
(gumroad.com → *Sales*, *Customers*, *Analytics*):

- **Revenue & analytics** — totals, per-day sales, refunds
- **Who bought** — the Customers tab lists every buyer (name, email, country, amount)
- **Receipts** — Gumroad automatically emails each buyer a receipt/invoice
- **Delivery** — Gumroad hosts and delivers the ebook files to buyers

> To sell, upload the two files from `cookbook/` (the PDF and ePub) to your Gumroad
> product as its content, set the price to $9.99, and publish. That's it.

### 🔁 Optional: mirror real Gumroad sales into your own dashboard

If you also want the **custom admin dashboard** (below) to show live revenue and buyers
from real Gumroad sales, point a Gumroad **Ping/webhook** at the store backend:

1. Deploy `store/` somewhere public (Render, Railway, a VPS…), or expose it with a tunnel
   like ngrok for testing.
2. In Gumroad → *Settings ▸ Advanced ▸ Ping* (or the product's Webhook), set the URL to
   `https://YOUR-DOMAIN/webhook/gumroad`.
3. Each sale/refund is then recorded in `store/store.db` and appears in `/admin` with
   revenue, buyer name/email, and status. (Deduplicated by Gumroad `sale_id`.)

## 🛒 The store backend (optional self-hosted checkout + dashboard)

`store/` is a small Flask app. Its **admin dashboard** is the piece most useful alongside
Gumroad (revenue + who-bought, fed by the webhook above). It also includes a full
**self-hosted checkout** (`/checkout`) with its own receipts — handy for testing or if you
ever want to sell without Gumroad. The site's buy buttons use Gumroad, not `/checkout`.

`store/` is a small Flask app that turns the static page into a real storefront. Run it
and everything on the site becomes live.

```bash
cd store
copy .env.example .env      # then edit .env (set ADMIN_PASSWORD!)
pip install -r requirements.txt
python app.py               # or double-click run.bat on Windows
```

Then open **http://127.0.0.1:5000/** — it serves the full landing page *plus*:

| Page | URL | What it does |
|------|-----|--------------|
| Checkout | `/checkout` | Collects name + email, takes payment, creates the order |
| Success  | `/success?token=…` | Confirmation + **instant ebook download** (PDF/ePub) + receipt links |
| Receipt / invoice | `/receipt/<order_no>` and `…​.pdf` | Branded, printable invoice with order no., buyer, total, PAID status |
| Secure download | `/download/<token>/pdf` · `/epub` | Serves the ebook only for a valid paid order |
| **Admin dashboard** | `/admin` | Revenue, paid-order count, customers, AOV, and a **who-bought** table |
| CSV export | `/admin/orders.csv` | Download all orders |

**Admin:** sign in at `/admin` with the `ADMIN_PASSWORD` from your `.env`. The dashboard
shows total revenue and every order (name, email, country, amount, date, method, status),
with a one-click **Refund** action and CSV export. Orders are stored in `store/store.db`
(SQLite).

### Payments in the *self-hosted* checkout (not the Gumroad path)

*Your live site sells via Gumroad — this only applies to the optional `/checkout` page.*

- **Demo mode (default):** with `STRIPE_SECRET_KEY` empty, checkout *simulates* a
  successful payment so you can test the whole flow (orders, receipts, revenue) without
  real money. No card details are ever collected.
- **Real payments:** set `STRIPE_SECRET_KEY` in `.env` and `pip install stripe`. Checkout
  then redirects to **Stripe's own hosted payment page** — customers enter their card on
  Stripe, never on this site, so you never handle card data. Orders/receipts/revenue all
  work the same.

> Receipts are shown and downloadable on-screen; automatic **emailing** of receipts is not
> enabled (it needs your SMTP provider). The success page and admin both link to each
> receipt, and buyers keep their download link.

**Deploying:** the store is a standard Flask app — deploy to Render, Railway, Fly.io, a VPS,
etc. (add a production WSGI server like gunicorn/waitress and set the env vars). To publish
just the static marketing page without the backend, host the root files + `assets/` and point
the buttons at your payment provider instead of `/checkout`.

## 📖 The cookbook

*Vital Theory's Secret Recipes* — **200 recipes across 16 chapters**:
Pasta · Chicken · Beef · Pork · Seafood · Soups · Salads · Sauces & Dressings ·
Vegetarian · Sides · Breakfast · Desserts · Baking & Bread · Drinks & Smoothies ·
Appetizers & Snacks · Grains & Rice.

Every recipe has a **full-page food photo**, prep/cook times, servings, difficulty,
an ingredients list, clear numbered instructions, a chef's tip, and a **"Inspired by
[Chef]"** credit. Front matter includes a photo cover, welcome note, how-to page, an
attribution/disclaimer page, an auto-numbered table of contents, chapter dividers, and
a kitchen conversion chart.

- **PDF** — fixed, fully designed layout with photo banners (best for print / desktop).
- **ePub** — reflowable, photo per recipe (best for phones, tablets, e-readers).
- **Kindle** — send the `.epub` via Amazon's *Send to Kindle* (modern Kindles read ePub).

### ⚖️ A note on chef attribution (important)

These recipes are **original interpretations** of the classic dishes each chef is famous
for, written from scratch in our own words. They are **not** copied from, affiliated with,
or endorsed by the chefs named — each "Inspired by …" credit is a tip of the hat to their
influence. This is stated on the book's *About These Recipes* page. If you sell the book,
keep that page and consider reviewing image licenses (below).

### Rebuild / edit the cookbook

```bash
pip install fpdf2 ebooklib pillow pymupdf
cd cookbook
python fetch_images.py     # downloads a photo for all 200 recipes -> img/  (run once)
python build_all.py        # builds the PDF + ePub using those images
```

To change recipes, edit `cookbook/recipes.json` (each recipe is one JSON object with
`title`, `chef`, `prep`, `cook`, `serves`, `level`, `intro`, `ingredients[]`, `steps[]`,
`tip`, `image_query`), then re-run `fetch_images.py` (for new dishes) and `build_all.py`.
The table of contents, page numbers, and chapter groupings update automatically.

The 200 recipes were assembled from the per-chapter files in `parts/`; you can regenerate
`recipes.json` from those with a simple concat if you prefer to edit chapter-by-chapter.

### Where the images come from

`fetch_images.py` pulls photos from two free sources, matched to each recipe's
`image_query`:

- **[TheMealDB](https://www.themealdb.com)** — public food-recipe API with real dish
  photography (tried first).
- **[Openverse](https://openverse.org)** — Creative-Commons image search (covers the rest).

Images are de-duplicated, center-cropped, and cached under `cookbook/img/`; the site uses
copies in `assets/img/`.

> **Licensing note:** these sources are free to use, but Openverse results carry individual
> Creative-Commons licenses (some require attribution). Before selling the cookbook
> commercially, review the licenses or swap in your own photography — replace the files in
> `cookbook/img/` (keep the same filenames) and re-run `build_all.py`.
