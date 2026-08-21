#!/usr/bin/env python3
"""Generate monochrome black & white 'for-the-badge'-style SVG badges.

Style:
  - Solid black background (#000), 8px rounded corners
  - White text, small white square "icon" block on the left
  - 28px tall, width sized to text
"""
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Each entry: (slug, label, icon_glyph, glyph_size)
# glyph_size is the icon's font size.  Use 12 for single chars, 10 for 2 chars
# so 2-char monograms don't get clipped by the icon square.
BADGES = [
    ("html5",         "HTML5",          "H",  12),
    ("css",           "CSS",            "C",  12),
    ("javascript",    "JavaScript",     "Js", 10),
    ("typescript",    "TypeScript",     "Ts", 10),
    ("nodejs",        "Node.js",        "N",  12),
    ("java",          "Java",           "Jv", 10),
    ("kotlin",        "Kotlin",         "Kt", 10),
    ("git",           "Git",            "G",  12),
    ("github",        "GitHub",         "Gh", 10),
    ("vscode",        "VS Code",        "Vs", 10),
    ("androidstudio", "Android Studio", "As", 10),
]

HEIGHT = 28
ICON_SIZE = 20
CORNER = 8
TEXT_PAD_LEFT = 12
TEXT_PAD_RIGHT = 12
LEFT_MARGIN = 5
FONT_SIZE = 11
FONT_WEIGHT = 700
CHAR_W = 7.4

FONT_FAMILY = ", ".join(
    f"'{name}'" if " " in name or "-" in name else name
    for name in ["Inter", "Helvetica Neue", "Helvetica", "Arial",
                 "Segoe UI", "system-ui", "sans-serif"]
)


def estimate_text_width(label: str) -> float:
    return len(label) * CHAR_W


def make_svg(label: str, icon_glyph: str, glyph_size: int) -> str:
    text_w = estimate_text_width(label)
    text_section_w = TEXT_PAD_LEFT + text_w + TEXT_PAD_RIGHT
    width = LEFT_MARGIN + ICON_SIZE + text_section_w

    icon_x = LEFT_MARGIN
    icon_y = (HEIGHT - ICON_SIZE) / 2
    icon_cx = icon_x + ICON_SIZE / 2
    icon_cy = HEIGHT / 2

    text_x = icon_x + ICON_SIZE + TEXT_PAD_LEFT
    text_y = HEIGHT / 2 + FONT_SIZE * 0.36

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width:.2f}" height="{HEIGHT}" '
        f'viewBox="0 0 {width:.2f} {HEIGHT}" '
        f'role="img" aria-label="{label}">\n'
        f'  <title>{label}</title>\n'
        f'  <rect x="0" y="0" width="{width:.2f}" height="{HEIGHT}" '
        f'rx="{CORNER}" ry="{CORNER}" fill="#000000"/>\n'
        f'  <rect x="{icon_x}" y="{icon_y:.2f}" '
        f'width="{ICON_SIZE}" height="{ICON_SIZE}" '
        f'rx="3" ry="3" fill="#ffffff"/>\n'
        f'  <text x="{icon_cx:.2f}" y="{icon_cy + glyph_size * 0.36:.2f}" '
        f'font-family="{FONT_FAMILY}" '
        f'font-size="{glyph_size}" font-weight="{FONT_WEIGHT}" '
        f'fill="#000000" text-anchor="middle">{icon_glyph}</text>\n'
        f'  <text x="{text_x:.2f}" y="{text_y:.2f}" '
        f'font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}" font-weight="{FONT_WEIGHT}" '
        f'fill="#ffffff" text-anchor="start">{label}</text>\n'
        f'</svg>\n'
    )


def main() -> None:
    for slug, label, glyph, glyph_size in BADGES:
        path = os.path.join(OUT_DIR, f"{slug}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(make_svg(label, glyph, glyph_size))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
