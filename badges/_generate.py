#!/usr/bin/env python3
"""Regenerate the monochrome B&W badge SVGs in this directory.

For each tech in BADGES, pulls the official brand icon from the
`simple-icons` npm package (or `@vscode/codicons` for VS Code, which
simple-icons doesn't ship due to brand guidelines) and embeds it in a
28px-tall rounded badge with a pure-black background, thin white outline,
and white label text.

Run from anywhere with Python 3 + Node/npm:
    python3 _generate.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_MODULES = os.path.join(tempfile.gettempdir(), "si", "node_modules")
SI_DIR = os.path.join(NODE_MODULES, "simple-icons", "icons")
VSCODE_SVG = os.path.join(NODE_MODULES, "@vscode", "codicons", "src",
                          "icons", "vscode.svg")

# (slug, label, simple-icons-slug | "__vscode__")
BADGES = [
    ("html5",         "HTML5",          "html5"),
    ("css",           "CSS",            "css"),
    ("javascript",    "JavaScript",     "javascript"),
    ("typescript",    "TypeScript",     "typescript"),
    ("nodejs",        "Node.js",        "nodedotjs"),
    ("java",          "Java",           "openjdk"),
    ("kotlin",        "Kotlin",         "kotlin"),
    ("git",           "Git",            "git"),
    ("github",        "GitHub",         "github"),
    ("vscode",        "VS Code",        "__vscode__"),
    ("androidstudio", "Android Studio", "androidstudio"),
]

HEIGHT = 28
ICON_SIZE = 18
ICON_PAD = 6
BADGE_RADIUS = 8
BADGE_STROKE = 1.5
TEXT_PAD_LEFT = 10
TEXT_PAD_RIGHT = 12
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


def make_svg(label: str, viewbox: str, icon_inner: str) -> str:
    text_w = estimate_text_width(label)
    icon_x = ICON_PAD
    icon_y = (HEIGHT - ICON_SIZE) / 2
    text_x = icon_x + ICON_SIZE + TEXT_PAD_LEFT
    text_y = HEIGHT / 2 + FONT_SIZE * 0.36
    width = text_x + text_w + TEXT_PAD_RIGHT

    inset = BADGE_STROKE / 2
    return textwrap.dedent(f"""\
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{width:.2f}" height="{HEIGHT}"
         viewBox="0 0 {width:.2f} {HEIGHT}"
         role="img" aria-label="{label}">
      <title>{label}</title>
      <rect x="{inset}" y="{inset}"
            width="{width - 2*inset:.2f}" height="{HEIGHT - 2*inset:.2f}"
            rx="{BADGE_RADIUS}" ry="{BADGE_RADIUS}"
            fill="#000000" stroke="#ffffff" stroke-width="{BADGE_STROKE}"/>
      <svg x="{icon_x}" y="{icon_y:.2f}"
           width="{ICON_SIZE}" height="{ICON_SIZE}"
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
    for slug, label, si_slug in BADGES:
        viewbox, inner = load_icon_inner(si_slug)
        out = make_svg(label, viewbox, inner)
        path = os.path.join(OUT_DIR, f"{slug}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {path}  ({len(out)} bytes)")


if __name__ == "__main__":
    main()
