#!/usr/bin/env python3
"""Читает PDF методички: печатает текст каждой страницы и сохраняет PNG страниц (для картинок с командами/YAML).

    ~/.cache/practice-report-venv/bin/python -I pdf_to_text.py методичка.pdf [каталог_для_png] [dpi]

Почему PNG: в методичках команды, манифесты и код часто вставлены КАРТИНКАМИ, в текстовом слое их нет. Страницы, где
после «выглядит следующим образом:» пусто, нужно открыть как изображение (Read). dpi 80 – команды, 105+ – YAML.
Без pdftoppm/pdftotext: используется только pymupdf.
"""
import os, sys

import pymupdf

pdf = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/practice-report-pages"
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 105
os.makedirs(out, exist_ok=True)
doc = pymupdf.open(pdf)
print(f"страниц: {len(doc)}")
for i, page in enumerate(doc, 1):
    png = os.path.join(out, f"p{i}.png")
    page.get_pixmap(dpi=dpi).save(png)
    print(f"\n--- страница {i} (картинок на странице: {len(page.get_images())}) -> {png}")
    print(page.get_text())
