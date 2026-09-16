"""Inline SVG chart primitives for the printed dashboard.

WeasyPrint runs no JavaScript, so every mark is emitted as SVG from Python. The
dashboard is a print artifact and deliberately commits to a single light palette;
there is no dark variant to keep in step.

Palette validated with the dataviz six-checks validator (light, surface #FBF9F7):
lightness band, chroma floor, CVD separation (worst adjacent dE 24.7), normal-vision
floor, and contrast all pass. Status colors are reserved and never reused as a series.
"""

from __future__ import annotations

from html import escape

# Categorical — identity. Fixed order, never cycled.
SERIES = ["#2a78d6", "#eb6834", "#4a3aa7"]
# Status — reserved, never a series slot.
ACTIVE = "#0F5F63"
IDLE = "#C3BBB2"
WARNING = "#8A5A12"
# Ink and furniture.
INK = "#12171A"
MUTED = "#6E6862"
FAINT = "#9A938B"
RULE = "#E2DCD5"
SURFACE = "#FBF9F7"

BAR_H = 15
BAR_GAP = 11
SEG_GAP = 2  # surface-colored gap between stacked fills
RADIUS = 4   # rounded data-end only; the baseline end stays square


def _t(x, y, text, *, size=10, fill=MUTED, anchor="start", weight=400, mono=False):
    family = (
        "'SF Mono', Menlo, 'Liberation Mono', 'DejaVu Sans Mono', monospace" if mono
        else "'Helvetica Neue', Helvetica, 'Liberation Sans', Arial, sans-serif"
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}" font-family="{family}">'
        f"{escape(str(text))}</text>"
    )


def _rounded_right(x, y, w, h, r):
    """A bar anchored square at the baseline with a rounded data-end."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (
        f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} "
        f"H{x:.1f} Z"
    )


def _svg(width, height, body) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'role="img" xmlns="http://www.w3.org/2000/svg" '
        f'style="display:block;max-width:100%">{body}</svg>'
    )


def legend(labels: list[tuple[str, str]]) -> str:
    """Swatch + label pairs. Present whenever a chart carries two or more series."""
    out = ['<div class="legend">']
    for color, label in labels:
        out.append(
            f'<span class="lg"><span class="sw" style="background:{color}"></span>'
            f"{escape(label)}</span>"
        )
    out.append("</div>")
    return "".join(out)


def stacked_bars(
    rows: list[tuple[str, list[int]]],
    colors: list[str],
    *,
    width: int = 620,
    label_w: int = 176,
    value_fmt=lambda total: str(total),
    max_total: int | None = None,
) -> str:
    """Horizontal stacked bars, one row per category, with a direct total label.

    `rows` is [(label, [seg1, seg2, ...])]. Segments are separated by a 2px gap in
    the surface color so adjacent fills never read as one mark.
    """
    if not rows:
        return ""
    value_w = 46
    plot_w = width - label_w - value_w
    top = 6
    height = top + len(rows) * (BAR_H + BAR_GAP)
    ceiling = max_total or max((sum(v) for _, v in rows), default=0) or 1

    parts = []
    y = top
    for label, values in rows:
        total = sum(values)
        parts.append(_t(label_w - 10, y + BAR_H - 3.5, _clip(label, 30), anchor="end", fill=INK))
        x = label_w
        full = (total / ceiling) * plot_w
        if total == 0:
            parts.append(
                f'<rect x="{label_w}" y="{y + BAR_H / 2 - 1:.1f}" width="10" height="2" fill="{RULE}"/>'
            )
        for i, value in enumerate(values):
            if value <= 0:
                continue
            seg_w = (value / total) * full if total else 0
            is_last = i == max(j for j, v in enumerate(values) if v > 0)
            draw_w = seg_w if is_last else max(seg_w - SEG_GAP, 0.5)
            color = colors[i % len(colors)]
            if is_last:
                parts.append(
                    f'<path d="{_rounded_right(x, y, draw_w, BAR_H, RADIUS)}" fill="{color}"/>'
                )
            else:
                parts.append(
                    f'<rect x="{x:.1f}" y="{y}" width="{draw_w:.1f}" height="{BAR_H}" fill="{color}"/>'
                )
            x += seg_w
        parts.append(
            _t(width - 4, y + BAR_H - 3.5, value_fmt(total), anchor="end", fill=INK, mono=True)
        )
        y += BAR_H + BAR_GAP

    return _svg(width, height, "".join(parts))


def column_bars(
    buckets: list[tuple[str, int]],
    *,
    width: int = 620,
    height: int = 150,
    color: str = ACTIVE,
    highlight_from: int | None = None,
    highlight_color: str = WARNING,
) -> str:
    """Vertical bars for an ordered distribution (time buckets, score bands).

    `highlight_from` switches the fill for that index onward — used to mark the
    stale end of a recency distribution without introducing a second series.
    """
    if not buckets:
        return ""
    pad_l, pad_b, pad_t = 30, 30, 14
    plot_w = width - pad_l - 8
    plot_h = height - pad_b - pad_t
    ceiling = max((v for _, v in buckets), default=0) or 1
    slot = plot_w / len(buckets)
    bar_w = min(slot * 0.62, 54)

    parts = []
    # Recessive gridlines, drawn under the marks.
    for frac in (0, 0.5, 1):
        gy = pad_t + plot_h * (1 - frac)
        parts.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - 8}" y2="{gy:.1f}" '
            f'stroke="{RULE}" stroke-width="1"/>'
        )
        parts.append(_t(pad_l - 7, gy + 3, round(ceiling * frac), size=9, anchor="end", fill=FAINT, mono=True))

    for i, (label, value) in enumerate(buckets):
        bh = (value / ceiling) * plot_h
        bx = pad_l + i * slot + (slot - bar_w) / 2
        by = pad_t + plot_h - bh
        fill = highlight_color if (highlight_from is not None and i >= highlight_from) else color
        if bh > 0:
            parts.append(f'<path d="{_rounded_up(bx, by, bar_w, bh, RADIUS)}" fill="{fill}"/>')
            parts.append(_t(bx + bar_w / 2, by - 5, value, size=9.5, anchor="middle", fill=INK, mono=True))
        parts.append(
            _t(bx + bar_w / 2, pad_t + plot_h + 14, label, size=9, anchor="middle", fill=MUTED)
        )
    return _svg(width, height, "".join(parts))


def _rounded_up(x, y, w, h, r):
    """A column anchored square at the baseline with a rounded top."""
    r = min(r, w / 2, h)
    return (
        f"M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"V{y + h:.1f} Z"
    )


def donut_share(part: int, whole: int, *, size: int = 92, color: str = WARNING) -> str:
    """A single-proportion dial. Used only where one share is the headline."""
    whole = whole or 1
    frac = max(0.0, min(1.0, part / whole))
    r, sw = size / 2 - 8, 9
    cx = cy = size / 2
    circ = 2 * 3.141592653589793 * r
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{RULE}" stroke-width="{sw}"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-dasharray="{circ * frac:.2f} {circ:.2f}" '
        f'transform="rotate(-90 {cx} {cy})"/>',
        _t(cx, cy + 5, f"{round(frac * 100)}%", size=17, anchor="middle", fill=INK, weight=600, mono=True),
    ]
    return _svg(size, size, "".join(parts))


GRADE_COLORS = {"A": "#2E6B3F", "B": "#2E6B3F", "C": "#0F5F63", "D": "#8A5A12", "F": "#A03028"}


def gauge(pct: int, grade: str, *, size: int = 96) -> str:
    """An open-arc dial for a 0–100 score, coloured by its grade band.

    The arc stops short of a full circle so the gap reads as a scale with a start
    and an end, rather than as a pie with a missing slice.
    """
    r = size / 2 - 10
    circumference = 2 * 3.141592653589793 * r
    track = circumference * 0.72
    filled = track * max(0, min(100, pct)) / 100
    cx = cy = size / 2
    colour = GRADE_COLORS.get(grade, ACTIVE)
    return _svg(size, size, "".join([
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{RULE}" stroke-width="9" '
        f'stroke-linecap="round" stroke-dasharray="{track:.1f} {circumference:.1f}" '
        f'transform="rotate(129 {cx} {cy})"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" stroke-width="9" '
        f'stroke-linecap="round" stroke-dasharray="{filled:.1f} {circumference:.1f}" '
        f'transform="rotate(129 {cx} {cy})"/>',
        _t(cx, cy + 6, f"{pct}%", size=17, anchor="middle", fill=INK, weight=600, mono=True),
    ]))


def _clip(text: str, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"
