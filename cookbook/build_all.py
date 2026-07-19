# -*- coding: utf-8 -*-
"""Build both the PDF and ePub cookbook in one step.

Usage:  python build_all.py
Requires:  pip install fpdf2 ebooklib pillow
"""
import build_pdf
import build_epub

if __name__ == "__main__":
    from recipes_data import CATEGORIES
    pdf_path, count = build_pdf.build()
    epub_path = build_epub.build()
    print("=" * 50)
    print(f"  {count} recipes across {len(CATEGORIES)} categories")
    print(f"  PDF :  {pdf_path}")
    print(f"  ePub:  {epub_path}")
    print("  (Kindle: send the .epub via Amazon 'Send to Kindle')")
    print("=" * 50)
