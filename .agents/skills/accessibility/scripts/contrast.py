#!/usr/bin/env python3
"""The WCAG 2 contrast ratio of colour pairs, against the floors in the accessibility skill: 4.5:1 for text, 3:1 for
large text and for non-text (icons, control borders, focus indicators, chart marks).

    python3 .agents/skills/accessibility/scripts/contrast.py "#5f6368" "#ffffff"            # text on a surface
    python3 .agents/skills/accessibility/scripts/contrast.py --min 3 "#1a73e8" "#ffffff"    # non-text or large text
    python3 .agents/skills/accessibility/scripts/contrast.py fg1 bg1 fg2 bg2 …              # several pairs
    python3 .agents/skills/accessibility/scripts/contrast.py --test

Colours are hex: #rgb, #rrggbb, or #rrggbbaa over the background (alpha is composited onto it first, as the screen
paints it). Measure against the colour actually painted under the text — a translucent fill composited over its own
background, not the token's name. Exit 0 when every pair meets the floor, 1 when one does not, 2 on bad input.
"""

from __future__ import annotations

import sys


def parse(hex_colour: str) -> tuple[float, float, float, float]:
    h = hex_colour.strip().lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    if len(h) not in (6, 8) or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"not a hex colour: {hex_colour!r}")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return r, g, b, a


def over(fg: tuple[float, float, float, float], bg: tuple[float, float, float, float]) -> tuple[float, float, float]:
    """The foreground composited over an opaque background."""
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def luminance(rgb: tuple[float, float, float]) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg_hex: str, bg_hex: str) -> float:
    bg = parse(bg_hex)
    if bg[3] < 1:
        raise ValueError(f"the background must be opaque — composite it over what is behind it first: {bg_hex!r}")
    fg = over(parse(fg_hex), bg)
    l1, l2 = sorted((luminance(fg), luminance(bg[:3])), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def self_test() -> int:
    cases = [("#000000", "#ffffff", 21.0), ("#ffffff", "#ffffff", 1.0), ("#777777", "#ffffff", 4.48),
             ("#767676", "#ffffff", 4.54), ("#000", "#fff", 21.0), ("#00000080", "#ffffff", 4.0)]
    bad = 0
    for fg, bg, want in cases:
        got = round(ratio(fg, bg), 2)
        if abs(got - want) > 0.01:
            bad += 1
            print(f"FAIL  {fg} on {bg}: want {want}, got {got}")
    print(f"contrast self-test: {len(cases) - bad}/{len(cases)} cases pass")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--test" in argv:
        return self_test()
    floor = 4.5
    if "--min" in argv:
        i = argv.index("--min")
        floor = float(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if not argv or len(argv) % 2:
        print(__doc__, file=sys.stderr)
        return 2
    failed = 0
    try:
        for fg, bg in zip(argv[::2], argv[1::2]):
            r = ratio(fg, bg)
            ok = r >= floor
            failed += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {fg} on {bg}: {r:.2f}:1 (floor {floor:g}:1)")
    except ValueError as e:
        print(f"contrast: {e}", file=sys.stderr)
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
