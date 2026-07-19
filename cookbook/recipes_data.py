# -*- coding: utf-8 -*-
"""Vital Theory's Secret Recipes — book metadata + recipe loader.

The 200 recipes live in recipes.json (assembled from parts/). Each recipe:
category, title, chef, prep, cook, serves, level, intro, ingredients[],
steps[], tip, image_query.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BOOK = {
    "title": "Vital Theory's Secret Recipes",
    "subtitle": "Nourishing Ingredients. Timeless Wisdom. Extraordinary Results.",
    "tagline": "200 Chef-Inspired Recipes for Everyday Life",
    "author": "Vital Theory",
    "year": "2026",
    "emoji": "🥗",
}

# 16 chapters, in book order, with the exact category names used in recipes.json
CATEGORIES = [
    ("Pasta",                "World-famous pasta, from silky carbonara to rich, slow-cooked ragu."),
    ("Chicken",              "Roasts, curries and skillet classics the great chefs built their names on."),
    ("Beef",                 "Steaks, braises and showstoppers worth the occasion."),
    ("Pork",                 "Slow-roasts, chops and ribs — comfort from the world's best kitchens."),
    ("Seafood",              "Bright, flaky and fast — the chef's way with fish and shellfish."),
    ("Soups",                "Restaurant-worthy bowls of comfort for every season."),
    ("Salads",              "Crisp, vibrant plates from the world's most celebrated tables."),
    ("Sauces & Dressings",   "The mother sauces and modern classics that lift everything they touch."),
    ("Vegetarian",           "Vegetable-forward cooking that quietly steals the show."),
    ("Sides",                "The supporting dishes chefs are secretly famous for."),
    ("Breakfast",            "Bright, satisfying starts worth waking up early for."),
    ("Desserts",             "Iconic sweets from the world's pastry legends."),
    ("Baking & Bread",       "Breads, bakes and pastry from the master bakers."),
    ("Drinks & Smoothies",   "Refreshers, smoothies and cafe-style favorites."),
    ("Appetizers & Snacks",  "Small plates and starters to open any meal in style."),
    ("Grains & Rice",        "Risottos, paellas, pilafs and grain bowls done right."),
]

with open(os.path.join(HERE, "recipes.json"), encoding="utf-8") as _f:
    RECIPES = json.load(_f)

# keep recipes grouped in chapter order
_order = {name: i for i, (name, _) in enumerate(CATEGORIES)}
RECIPES.sort(key=lambda r: (_order.get(r["category"], 999)))
