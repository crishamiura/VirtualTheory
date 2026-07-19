# -*- coding: utf-8 -*-
"""Download a real food photo for every one of the 200 recipes.

Sources (both free):
  - TheMealDB   — curated food photography (tried first for matches)
  - Openverse   — Creative-Commons image search (covers everything else)

Saves master JPEGs into img/ and writes images.json (title -> filename).
Runs multi-threaded so 200 downloads finish in a couple of minutes.
"""
import io
import json
import os
import re
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from recipes_data import RECIPES

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
MAP_PATH = os.path.join(HERE, "images.json")
UA = {"User-Agent": "Mozilla/5.0 (VitalTheory cookbook builder)"}

_lock = threading.Lock()
_used = set()
_mealdb_cache = {}


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def http_get(url, tries=3):
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            continue
    return None


def save_image(raw, name):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if min(im.size) < 300:
        return False
    im.thumbnail((1100, 1100), Image.LANCZOS)
    im.save(os.path.join(IMG, name), "JPEG", quality=86, optimize=True)
    return True


def mealdb(term):
    key = term.lower()
    with _lock:
        if key in _mealdb_cache:
            return _mealdb_cache[key]
    url = "https://www.themealdb.com/api/json/v1/1/search.php?s=" + urllib.parse.quote(term)
    data = http_get(url)
    meals = []
    if data:
        try:
            meals = json.loads(data).get("meals") or []
        except Exception:
            meals = []
    with _lock:
        _mealdb_cache[key] = meals
    return meals


def openverse(query):
    url = ("https://api.openverse.org/v1/images/?q=" + urllib.parse.quote(query)
           + "&page_size=8&mature=false")
    data = http_get(url)
    if not data:
        return []
    try:
        return json.loads(data).get("results", [])
    except Exception:
        return []


def claim(url):
    """Reserve a source URL so two recipes don't grab the same photo."""
    with _lock:
        if url in _used:
            return False
        _used.add(url)
        return True


def fetch_one(r):
    title = r["title"]
    q = r.get("image_query") or title
    fname = slug(title) + ".jpg"

    # 1) TheMealDB (best quality) — by image_query, then by title keywords
    for term in [q, title, q.split()[0]]:
        for m in mealdb(term):
            thumb = m.get("strMealThumb")
            if thumb and claim(thumb):
                raw = http_get(thumb)
                if raw and save_image(raw, fname):
                    return title, fname, "mealdb"
                else:
                    with _lock:
                        _used.discard(thumb)

    # 2) Openverse — by image_query variants
    for term in [q + " dish", q + " food", q, title + " food"]:
        for res in openverse(term):
            u = res.get("url")
            if u and claim(u):
                raw = http_get(u)
                if raw and save_image(raw, fname):
                    return title, fname, "openverse"
                else:
                    with _lock:
                        _used.discard(u)
    return title, None, "none"


def main():
    mapping = {}
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for title, fname, src in ex.map(fetch_one, RECIPES):
            mapping[title] = fname
            done += 1
            status = fname if fname else "!! MISSING"
            print(f"[{done:3}/{len(RECIPES)}] {src:9} {title[:42]:42} -> {status}")

    json.dump(mapping, open(MAP_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for v in mapping.values() if v)
    print(f"\nDownloaded {ok}/{len(RECIPES)} images -> {IMG}")
    miss = [t for t, v in mapping.items() if not v]
    if miss:
        print("MISSING:", miss)


if __name__ == "__main__":
    main()
