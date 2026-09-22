"""Render a homework list as a simple printable A4 JPEG page.

Used by the webuntis.print_homework service, which hands the resulting
JPEG bytes to the ipp_printing integration's ipp_printing.print action
(image/jpeg is the format that has been confirmed to work against the
printer this was built for - a Kyocera ECOSYS M2035dn that only
advertises PCLXL/PostScript/PCL5E/PJL, not text/plain, over IPP).
"""

from __future__ import annotations

import io
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .homework import GROUP_LABELS_DE

# ~A4 at 150 DPI
_PAGE_WIDTH = 1240
_PAGE_HEIGHT = 1754
_MARGIN = 60
_LINE_HEIGHT = 26
_GROUP_GAP = 20
_TEXT_WRAP_WIDTH = 42

_COL_SUBJECT_X = _MARGIN
_COL_TEACHER_X = _MARGIN + 90
_COL_ASSIGNED_X = _MARGIN + 260
_COL_DUE_X = _MARGIN + 430
_COL_TEXT_X = _MARGIN + 600


_UMLAUT_MAP = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
)


def _ascii_safe(text: str) -> str:
    """Transliterate German umlauts.

    Pillow's built-in default font doesn't reliably include the Latin-1
    Supplement glyphs (ä/ö/ü/ß render as a missing-glyph box), and bundling
    or locating a full Unicode TTF isn't worth it for this personal-use
    print button.
    """
    return text.translate(_UMLAUT_MAP)


def _load_fonts():
    try:
        return (
            ImageFont.load_default(size=32),
            ImageFont.load_default(size=20),
            ImageFont.load_default(size=18),
        )
    except TypeError:
        # Pillow < 10.1 doesn't support the size= argument.
        font = ImageFont.load_default()
        return font, font, font


def render_homework_jpeg(
    homeworks,
    title="Hausaufgaben",
    include_groups=("due_soon", "open", "overdue"),
) -> bytes:
    """Render a homework list to a single-page JPEG and return its bytes."""
    title_font, header_font, body_font = _load_fonts()

    image = Image.new("RGB", (_PAGE_WIDTH, _PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    y = _MARGIN
    draw.text((_MARGIN, y), _ascii_safe(title), font=title_font, fill="black")
    y += 50

    by_group = {key: [] for key in include_groups}
    for homework in homeworks:
        if homework.get("group") in by_group:
            by_group[homework["group"]].append(homework)

    any_rows = False
    for group in include_groups:
        items = by_group[group]
        if not items:
            continue
        any_rows = True

        y += _GROUP_GAP
        header = GROUP_LABELS_DE.get(group, group)
        draw.text((_MARGIN, y), _ascii_safe(header), font=header_font, fill="black")
        y += _LINE_HEIGHT
        draw.line([(_MARGIN, y), (_PAGE_WIDTH - _MARGIN, y)], fill="black", width=1)
        y += 8

        for homework in items:
            if y > _PAGE_HEIGHT - _MARGIN - _LINE_HEIGHT:
                break  # single page for now

            subject = _ascii_safe(homework.get("subject") or "")
            teacher = _ascii_safe(homework.get("teacher") or "")
            assigned = homework.get("date_assigned") or ""
            due = homework.get("due_date") or ""
            wrapped = textwrap.wrap(
                _ascii_safe(homework.get("text") or ""), width=_TEXT_WRAP_WIDTH
            ) or [""]

            draw.text((_COL_SUBJECT_X, y), subject, font=body_font, fill="black")
            draw.text((_COL_TEACHER_X, y), teacher, font=body_font, fill="black")
            draw.text((_COL_ASSIGNED_X, y), assigned, font=body_font, fill="black")
            draw.text((_COL_DUE_X, y), due, font=body_font, fill="black")
            draw.text((_COL_TEXT_X, y), wrapped[0], font=body_font, fill="black")
            y += _LINE_HEIGHT

            for extra_line in wrapped[1:]:
                draw.text((_COL_TEXT_X, y), extra_line, font=body_font, fill="black")
                y += _LINE_HEIGHT

            y += 6

    if not any_rows:
        draw.text((_MARGIN, y), "Keine Hausaufgaben.", font=body_font, fill="black")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()
