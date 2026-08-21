#!/usr/bin/env python3
"""Regenerate the monochrome B&W badge SVGs in this directory.

For each entry in BADGES, pulls the official brand icon from the
`simple-icons` npm package (or `@vscode/codicons` for VS Code, which
simple-icons doesn't ship due to brand guidelines) and embeds it in a
chamfered (cyberpunk-style) badge: pure-black hexagonal background, thin
white outline, and white label text.

Run from anywhere with Python 3 + Node/npm:
    python3 _generate.py
"""
import os
import re
import subprocess
import sys
import tempfile
import textwrap

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_MODULES = os.path.join(tempfile.gettempdir(), "si", "node_modules")
SI_DIR = os.path.join(NODE_MODULES, "simple-icons", "icons")
VSCODE_SVG = os.path.join(NODE_MODULES, "@vscode", "codicons", "src",
                          "icons", "vscode.svg")

# (slug, label, simple-icons-slug | "__vscode__", height)
# height=None uses the default (28).  Used for the support button.
DEFAULT_HEIGHT = 28
BADGES = [
    ("html5",         "HTML5",          "html5",         None),
    ("css",           "CSS",            "css",           None),
    ("javascript",    "JavaScript",     "javascript",    None),
    ("typescript",    "TypeScript",     "typescript",    None),
    ("nodejs",        "Node.js",        "nodedotjs",     None),
    ("java",          "Java",           "openjdk",       None),
    ("kotlin",        "Kotlin",         "kotlin",        None),
    ("git",           "Git",            "git",           None),
    ("github",        "GitHub",         "github",        None),
    ("vscode",        "VS Code",        "__vscode__",    None),
    ("androidstudio", "Android Studio", "androidstudio", None),
    ("kofi",          "Support me",     "kofi",          44),
]

# Visual proportions are computed from HEIGHT so badges look consistent
# regardless of size.  These are all expressed as fractions of HEIGHT.
BADGE_STROKE_FRAC = 1.5 / 28
CHAMFER_PX = 9                  # size of the diagonal corner cut
ICON_SIZE_FRAC = 18 / 28
ICON_PAD_FRAC = 6 / 28
TEXT_PAD_LEFT_FRAC = 10 / 28
TEXT_PAD_RIGHT_FRAC = 12 / 28
FONT_SIZE = 11
FONT_WEIGHT = 700
CHAR_W = 7.4

FONT_FAMILY = ", ".join(
    f"'{name}'" if " " in name or "-" in name else name
    for name in ["Inter", "Helvetica Neue", "Helvetica", "Arial",
                 "Segoe UI", "system-ui", "sans-serif"]
)


def ensure_icon_sources() -> None:
    """Make sure simple-icons + @vscode/codicons are installed in NODE_MODULES."""
    need_simple = not os.path.isdir(SI_DIR)
    need_vscode = not os.path.isfile(VSCODE_SVG)
    if not need_simple and not need_vscode:
        return

    print("Installing icon source packages via npm (one-time)…", file=sys.stderr)
    tmp_root = os.path.dirname(NODE_MODULES)
    os.makedirs(tmp_root, exist_ok=True)
    pkg_dir = os.path.join(tempfile.gettempdir(), "si")
    if not os.path.isfile(os.path.join(pkg_dir, "package.json")):
        subprocess.check_call(["npm", "init", "-y"], cwd=pkg_dir,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    subprocess.check_call(
        ["npm", "install", "--silent", "--no-audit", "--no-fund",
         "simple-icons", "@vscode/codicons"],
        cwd=pkg_dir,
    )


def load_icon_inner(slug: str) -> tuple[str, str]:
    """Return (viewBox, inner_content) for a simple-icons / codicons SVG."""
    if slug == "__vscode__":
        with open(VSCODE_SVG) as f:
            svg = f.read()
    else:
        with open(os.path.join(SI_DIR, f"{slug}.svg")) as f:
            svg = f.read()
    m = re.search(r'<svg([^>]*)>', svg)
    attrs = m.group(1)
    inner = svg[m.end():svg.rfind("</svg>")]
    vb = re.search(r'viewBox="([^"]+)"', attrs)
    viewbox = vb.group(1) if vb else "0 0 24 24"
    inner = re.sub(r'<title>.*?</title>', '', inner, flags=re.DOTALL)
    inner = re.sub(
        r'<path\b(?![^>]*fill=)',
        '<path fill="#ffffff"',
        inner,
    )
    return viewbox, inner.strip()


def estimate_text_width(label: str) -> float:
    return len(label) * CHAR_W


def hex_path(x: float, y: float, w: float, h: float, c: float) -> str:
    """Return an SVG `d` string for a horizontally-stretched hexagon.

    The 4 corners are clipped at 45 degrees by c pixels, AND the top and
    bottom edges each get a small diagonal cut in the middle for a more
    cyberpunk/tactical feel.

      x, y: top-left of the bounding box
      w, h: width and height of the bounding box
      c:    chamfer (corner cut) in pixels
    """
    c = min(c, w / 2, h / 2)
    # Cut a small notch on the top and bottom edges too — sized so the
    # notch is a triangle, smaller than the corner cuts.
    notch = c * 0.45
    cx = x + w / 2
    return (
        f"M{x + c},{y} "
        f"L{cx - notch},{y} "
        f"L{cx},{y + notch} "
        f"L{cx + notch},{y} "
        f"L{x + w - c},{y} "
        f"L{x + w},{y + c} "
        f"L{x + w},{y + h - c} "
        f"L{x + w - c},{y + h} "
        f"L{cx + notch},{y + h} "
        f"L{cx},{y + h - notch} "
        f"L{cx - notch},{y + h} "
        f"L{x + c},{y + h} "
        f"L{x},{y + h - c} "
        f"L{x},{y + c} Z"
    )


def make_svg(label: str, viewbox: str, icon_inner: str,
             height: int = DEFAULT_HEIGHT) -> str:
    icon_size = round(ICON_SIZE_FRAC * height, 2)
    icon_pad = round(ICON_PAD_FRAC * height, 2)
    text_pad_l = round(TEXT_PAD_LEFT_FRAC * height, 2)
    text_pad_r = round(TEXT_PAD_RIGHT_FRAC * height, 2)
    stroke = round(BADGE_STROKE_FRAC * height, 2)

    text_w = estimate_text_width(label)
    icon_x = icon_pad
    icon_y = (height - icon_size) / 2
    text_x = icon_x + icon_size + text_pad_l
    text_y = height / 2 + FONT_SIZE * 0.36
    width = text_x + text_w + text_pad_r

    chamfer = min(CHAMFER_PX, width / 2 - stroke, height / 2 - stroke)
    d = hex_path(0, 0, width, height, chamfer)

    return textwrap.dedent(f"""\
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{width:.2f}" height="{height}"
         viewBox="0 0 {width:.2f} {height}"
         role="img" aria-label="{label}">
      <title>{label}</title>
      <path d="{d}"
            fill="#000000" stroke="#ffffff"
            stroke-width="{stroke}" stroke-linejoin="miter"/>
      <svg x="{icon_x}" y="{icon_y:.2f}"
           width="{icon_size}" height="{icon_size}"
           viewBox="{viewbox}" fill="#ffffff">
        {icon_inner}
      </svg>
      <text x="{text_x:.2f}" y="{text_y:.2f}"
            font-family="{FONT_FAMILY}"
            font-size="{FONT_SIZE}" font-weight="{FONT_WEIGHT}"
            fill="#ffffff" text-anchor="start">{label}</text>
    </svg>
    """)


def main() -> None:
    ensure_icon_sources()
    for slug, label, si_slug, height in BADGES:
        viewbox, inner = load_icon_inner(si_slug)
        out = make_svg(label, viewbox, inner,
                       height if height is not None else DEFAULT_HEIGHT)
        path = os.path.join(OUT_DIR, f"{slug}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {path}  ({len(out)} bytes)")


if __name__ == "__main__":
    main()
