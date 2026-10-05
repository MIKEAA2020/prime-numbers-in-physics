#!/usr/bin/env python3
"""Merge cover.pdf + main.pdf into the final deliverable, normalized to A4."""
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89  # A4 in points

def normalize_page_to_a4(page):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 2 or abs(h - A4_H) > 2:
        page.scale_to(A4_W, A4_H)
    return page

writer = PdfWriter()
cover_page = normalize_page_to_a4(PdfReader('cover.pdf').pages[0])
writer.add_page(cover_page)
for page in PdfReader('main.pdf').pages:
    writer.add_page(normalize_page_to_a4(page))
with open('final.pdf', 'wb') as f:
    writer.write(f)
print('merged: final.pdf,', len(PdfReader('final.pdf').pages), 'pages')
