#!/usr/bin/env python3
"""Compose the YouTube thumbnail (1280x720) from a generated base image and big title lines.

episode.json:
  "thumbnail": {
    "image": "<image id in images>",          # base picture (generate it with gen_images.py)
    "lines": ["三洋電機", "なぜ消えた？", "倒産してないのに…"]  # 2-3 short lines
  }
Line 1 is white, the middle line(s) are the large gold hook, the last line sits on a red band.
Writes episodes/<slug>/out/thumbnail.png.

Usage: make_thumbnail.py <slug>
"""
from __future__ import annotations

import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from episode_lib import CHANNEL, ROOT, episode_dir, load_episode

W, H = 1280, 720
FONT = ROOT / "channel" / "fonts" / "DelaGothicOne-Regular.ttf"
SEAL_FONT = ROOT / "channel" / "fonts" / "NotoSansJP-VariableFont.ttf"


def cover(im: Image.Image) -> Image.Image:
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def fit_font(text: str, max_w: int, max_size: int) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > 30:
        f = ImageFont.truetype(str(FONT), size)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(FONT), size)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    ep = load_episode(slug)
    d = episode_dir(slug)
    spec = ep["thumbnail"]
    base = cover(Image.open(d / "assets" / "images" / f"{spec['image']}.png").convert("RGB"))

    # darken the left side so the title reads at phone size
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for x in range(W):
        t = max(0.0, 1 - x / (W * 0.72))
        sd.line([(x, 0), (x, H)], fill=int(205 * t ** 1.3))
    base = Image.composite(Image.new("RGB", (W, H), (8, 8, 10)), base, shade)

    lines = spec["lines"]
    max_w = int(W * 0.62)
    canvas = base.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    y = 46
    gold = (255, 210, 63)
    for i, text in enumerate(lines):
        last = i == len(lines) - 1 and len(lines) >= 3
        hook = 0 < i < len(lines) - (1 if len(lines) >= 3 else 0)
        f = fit_font(text, max_w, 200 if hook else 120)
        bbox = f.getbbox(text)
        th = bbox[3] - bbox[1]
        if last:
            pad = 18
            band = (30, y - 6, 30 + f.getlength(text) + pad * 2, y + th + pad * 2 - 6)
            dr.rectangle(band, fill=CHANNEL["colors"]["seal"])
            dr.text((30 + pad, y + pad - bbox[1] - 6), text, font=f, fill="white", stroke_width=6, stroke_fill="black")
            y = band[3] + 14
        else:
            dr.text((36, y - bbox[1]), text, font=f, fill=gold if hook else "white",
                    stroke_width=14 if hook else 10, stroke_fill="black")
            y += th + 26
    glow = layer.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas, Image.eval(glow, lambda v: v // 3))
    canvas = Image.alpha_composite(canvas, layer)

    # channel seal (top-right)
    seal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    sf = ImageFont.truetype(str(SEAL_FONT), 40)
    sf.set_variation_by_name("Black")
    a, b = CHANNEL["logo"]["lines"]
    box = (W - 132, 24, W - 24, 132)
    sd.rounded_rectangle(box, radius=10, fill=CHANNEL["colors"]["seal"], outline="white", width=4)
    sd.text(((box[0] + box[2]) / 2, box[1] + 30), a, font=sf, fill="white", anchor="mm")
    sd.text(((box[0] + box[2]) / 2, box[1] + 78), b, font=sf, fill="white", anchor="mm")
    canvas = Image.alpha_composite(canvas, seal)

    out = d / "out"
    out.mkdir(exist_ok=True)
    canvas.convert("RGB").save(out / "thumbnail.png")
    print(out / "thumbnail.png")


if __name__ == "__main__":
    main()
