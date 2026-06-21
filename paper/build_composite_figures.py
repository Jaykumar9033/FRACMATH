"""Build composite figures used by the JOSS paper.

The JOSS toolchain handles simple Markdown figures reliably, but not arbitrary
LaTeX subfigure blocks. This script creates clean multi-panel PNGs from the
source figures so `paper.md` can stay JOSS-friendly while the PDF keeps a
balanced panel layout.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
IMG = ROOT / "images"
WHITE = (255, 255, 255)
INK = (20, 20, 20)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["arialbd.ttf" if bold else "arial.ttf", "Arial Bold.ttf" if bold else "Arial.ttf"]
    for name in names:
        for base in [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]:
            path = base / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


LABEL_FONT = _font(30, bold=True)


def trim_white(im: Image.Image, pad: int = 18, threshold: int = 248) -> Image.Image:
    """Trim mostly white margins while preserving a small border."""
    rgb = im.convert("RGB")
    mask = Image.new("RGB", rgb.size, WHITE)
    diff = ImageChops.difference(rgb, mask).convert("L")
    diff = diff.point(lambda p: 255 if p > 255 - threshold else 0)
    box = diff.getbbox()
    if not box:
        return rgb
    left, top, right, bottom = box
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(rgb.width, right + pad)
    bottom = min(rgb.height, bottom + pad)
    return rgb.crop((left, top, right, bottom))


def load(name: str) -> Image.Image:
    return trim_white(Image.open(IMG / name))


def crop_fraction(im: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    left, top, right, bottom = box
    return im.crop(
        (
            int(left * im.width),
            int(top * im.height),
            int(right * im.width),
            int(bottom * im.height),
        )
    )


def fit(im: Image.Image, max_w: int, max_h: int) -> Image.Image:
    out = im.copy()
    out.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return out


def label_panel(canvas: Image.Image, xy: tuple[int, int], label: str) -> None:
    draw = ImageDraw.Draw(canvas)
    x, y = xy
    bbox = draw.textbbox((0, 0), label, font=LABEL_FONT)
    pad_x, pad_y = 12, 7
    rect = (x, y, x + bbox[2] + 2 * pad_x, y + bbox[3] + 2 * pad_y)
    draw.rounded_rectangle(rect, radius=8, fill=(255, 255, 255), outline=(210, 210, 210))
    draw.text((x + pad_x, y + pad_y), label, fill=INK, font=LABEL_FONT)


def stack_vertical(
    panels: list[tuple[str, str]],
    output: str,
    width: int = 1800,
    max_panel_h: int = 720,
    gap: int = 36,
    margin: int = 45,
) -> None:
    rendered = [(fit(load(name), width - 2 * margin, max_panel_h), label) for name, label in panels]
    height = 2 * margin + sum(im.height for im, _ in rendered) + gap * (len(rendered) - 1)
    canvas = Image.new("RGB", (width, height), WHITE)
    y = margin
    for im, label in rendered:
        x = (width - im.width) // 2
        canvas.paste(im, (x, y))
        label_panel(canvas, (x + 14, y + 14), label)
        y += im.height + gap
    canvas.save(IMG / output, optimize=True)


def row_equal_height(
    panels: list[tuple[str, str]],
    output: str,
    height: int = 560,
    gap: int = 34,
    margin: int = 45,
) -> None:
    rendered = []
    for name, label in panels:
        im = load(name)
        scale = height / im.height
        rendered.append((im.resize((int(im.width * scale), height), Image.Resampling.LANCZOS), label))
    width = 2 * margin + sum(im.width for im, _ in rendered) + gap * (len(rendered) - 1)
    canvas = Image.new("RGB", (width, height + 2 * margin), WHITE)
    x = margin
    for im, label in rendered:
        y = margin
        canvas.paste(im, (x, y))
        label_panel(canvas, (x + 12, y + 12), label)
        x += im.width + gap
    canvas.save(IMG / output, optimize=True)


def grid(
    panels: list[tuple[str, str]],
    output: str,
    cols: int,
    panel_w: int = 720,
    panel_h: int = 500,
    gap: int = 30,
    margin: int = 38,
) -> None:
    rows = (len(panels) + cols - 1) // cols
    width = 2 * margin + cols * panel_w + (cols - 1) * gap
    height = 2 * margin + rows * panel_h + (rows - 1) * gap
    canvas = Image.new("RGB", (width, height), WHITE)
    for row in range(rows):
        row_panels = panels[row * cols : (row + 1) * cols]
        row_width = len(row_panels) * panel_w + max(0, len(row_panels) - 1) * gap
        x0 = (width - row_width) // 2
        for col, (name, label) in enumerate(row_panels):
            x = x0 + col * (panel_w + gap)
            y = margin + row * (panel_h + gap)
            im = fit(load(name), panel_w, panel_h)
            canvas.paste(im, (x + (panel_w - im.width) // 2, y + (panel_h - im.height) // 2))
            label_panel(canvas, (x + 10, y + 10), label)
    canvas.save(IMG / output, optimize=True)


def nooru_mesh_layout(output: str) -> None:
    width = 1500
    margin = 34
    gap = 34
    top_h = 520
    bottom_h = 270

    panel_a = fit(load("nooru_BC_2D.png"), 520, top_h)
    panel_b = fit(load("nooru_mesh_3D.png"), 520, top_h)
    # The source experimental figure contains large blank specimen regions; crop
    # to the crack-path band so the panel is readable in the JOSS column.
    panel_c = fit(crop_fraction(load("Exp_noor.png"), (0.0, 0.15, 1.0, 0.75)), 900, bottom_h)

    height = 2 * margin + top_h + gap + bottom_h
    canvas = Image.new("RGB", (width, height), WHITE)

    top_width = panel_a.width + gap + panel_b.width
    x = (width - top_width) // 2
    y = margin + (top_h - max(panel_a.height, panel_b.height)) // 2
    canvas.paste(panel_a, (x, y + (max(panel_a.height, panel_b.height) - panel_a.height) // 2))
    label_panel(canvas, (x + 10, y + 10), "(a)")
    x += panel_a.width + gap
    canvas.paste(panel_b, (x, y + (max(panel_a.height, panel_b.height) - panel_b.height) // 2))
    label_panel(canvas, (x + 10, y + 10), "(b)")

    x = (width - panel_c.width) // 2
    y = margin + top_h + gap + (bottom_h - panel_c.height) // 2
    canvas.paste(panel_c, (x, y))
    label_panel(canvas, (x + 10, y + 10), "(c)")
    canvas.save(IMG / output, optimize=True)


def three_pb_layout(output: str) -> None:
    """Compact 3PB validation panel for the JOSS page width."""
    width = 1680
    margin = 34
    gap = 28

    damage = fit(load("abaqus_fig_damage_last_step.png"), width - 2 * margin, 470)
    response = fit(load("load_cmod_comparison.png"), 760, 470)
    timing = fit(load("time_comparison_bar.png"), 800, 470)

    bottom_h = max(response.height, timing.height)
    height = 2 * margin + damage.height + gap + bottom_h
    canvas = Image.new("RGB", (width, height), WHITE)

    x = (width - damage.width) // 2
    y = margin
    canvas.paste(damage, (x, y))
    label_panel(canvas, (x + 12, y + 12), "(a)")

    bottom_w = response.width + gap + timing.width
    x = (width - bottom_w) // 2
    y = margin + damage.height + gap
    canvas.paste(response, (x, y + (bottom_h - response.height) // 2))
    label_panel(canvas, (x + 12, y + 12), "(b)")
    x += response.width + gap
    canvas.paste(timing, (x, y + (bottom_h - timing.height) // 2))
    label_panel(canvas, (x + 12, y + 12), "(c)")

    canvas.save(IMG / output, optimize=True)


def main() -> None:
    stack_vertical(
        [
            ("fig_mesh.png", "(a)"),
            ("abaqus_fig_damage_last_step.png", "(b)"),
        ],
        "fig_b1_mesh_abq.png",
        width=1650,
        max_panel_h=520,
        gap=24,
        margin=30,
    )
    stack_vertical(
        [
            ("fig_damage_peak.png", "(a)"),
            ("fig_damage_postpeak.png", "(b)"),
        ],
        "fig_b1_damage.png",
        width=1650,
        max_panel_h=390,
        gap=22,
        margin=28,
    )
    stack_vertical(
        [
            ("load_cmod_comparison.png", "(a)"),
            ("time_comparison_bar.png", "(b)"),
        ],
        "fig_b1_results.png",
        width=1500,
        max_panel_h=520,
        gap=24,
        margin=30,
    )
    three_pb_layout("fig_b1_compact.png")
    nooru_mesh_layout("fig_b2_mesh.png")
    grid(
        [
            ("nooru_inc_0029.png", "(a)"),
            ("nooru_inc_0053.png", "(b)"),
            ("nooru_inc_0127.png", "(c)"),
            ("nooru_inc_0900.png", "(d)"),
        ],
        "nooru_damage_evolution_selected.png",
        cols=2,
        panel_w=730,
        panel_h=335,
        gap=20,
        margin=22,
    )
    row_equal_height(
        [
            ("torsion.png", "(a)"),
            ("Exp_torsion.png", "(b)"),
        ],
        "fig_b3_mesh.png",
        height=430,
        gap=32,
        margin=32,
    )
    grid(
        [
            ("Job-1_StaticFast_mod_vm_LIVE_snap_inc_0001_theta_2_143e-05.png", "(a)"),
            ("Job-1_StaticFast_mod_vm_LIVE_snap_inc_0041_theta_8_786e-04.png", "(b)"),
            ("Job-1_StaticFast_mod_vm_LIVE_snap_inc_0080_theta_1_714e-03.png", "(c)"),
            ("Job-1_StaticFast_mod_vm_LIVE_snap_inc_0140_theta_3_000e-03.png", "(d)"),
        ],
        "fig_b3_damage_evolution.png",
        cols=2,
        panel_w=760,
        panel_h=350,
        gap=22,
        margin=24,
    )


if __name__ == "__main__":
    main()
