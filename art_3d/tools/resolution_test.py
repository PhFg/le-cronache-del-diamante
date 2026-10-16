"""Teste de resolução de sprites (256 vs 384) para Le Cronache del Diamante.

Uso:
  python art_3d/tools/resolution_test.py

Lê o render do Look C (somente leitura), gera quadros de 256 e 384 px com a âncora dos pés
proporcional a (128, 236) e simula a exibição na Godot 4.7:
  - viewport base 1280x720, stretch canvas_items, zoom da câmera 1.12;
  - escala do sprite ajustada para ~106 px de altura em 720p;
  - filtro linear com mipmaps (emulação trilinear), como TEXTURE_FILTER_LINEAR_WITH_MIPMAPS.
Sem nitidez artificial nem upscaling. Saídas em art_3d/verddro/renders/resolution_tests/.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verddro", "renders")
SOURCE = os.path.join(ROOT, "verddro_style_C_hybrid.png")
OUT = os.path.join(ROOT, "resolution_tests")

BASE_FRAME, BASE_ANCHOR, BASE_CHAR_HEIGHT = 256, (128, 236), 210
SIZES = (256, 384)
CAMERA_ZOOM = 1.12
TARGET_SCREEN_HEIGHT_720 = 106
WINDOWS = {"720p": 1.0, "1080p": 1.5}
FRAMES_PER_CHARACTER = 8 * (6 + 8 + 8 + 6)

GRASS = (0x63, 0x85, 0x63)
DIAMOND = (0.32, 0.48, 0.37, 0.17)
ROAD = (0xA9, 0xA1, 0x7C)
SHADOW = (0.04, 0.12, 0.10, 0.32)
PANEL_BG = (30, 33, 33)
TEXT = (232, 234, 228)


def font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def ground_anchor(alpha):
    """Ponto do chão entre os pés: média das bases dos dois grupos de colunas mais baixos."""
    solid = alpha >= 128
    ys, _ = np.nonzero(solid)
    top, bottom = ys.min(), ys.max()
    band = solid[bottom - int((bottom - top) * 0.18): bottom + 1]
    cols = np.nonzero(band.any(0))[0]
    groups = np.split(cols, np.where(np.diff(cols) > 3)[0] + 1)
    feet = sorted(groups, key=len, reverse=True)[:2]
    xs = [(g[0] + g[-1]) / 2 for g in feet]
    bases = [max(np.nonzero(solid[:, x])[0].max() for x in g) for g in feet]
    return (sum(xs) / len(xs), sum(bases) / len(bases)), (top, bottom)


def src_height_total(src):
    bb = src.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    return bb[3] - bb[1]


def trilinear(img, s):
    """Emula filtro linear + mipmaps da GPU para um fator de redução s (< 1)."""
    w, h = round(img.width * s), round(img.height * s)
    pm = img.convert("RGBa")
    lod = max(0.0, math.log2(1 / s))
    lo = int(math.floor(lod))
    frac = lod - lo
    levels = [pm]
    for _ in range(lo + 1):
        prev = levels[-1]
        levels.append(prev.resize((max(1, prev.width // 2), max(1, prev.height // 2)), Image.BOX))
    a = np.asarray(levels[lo].resize((w, h), Image.BILINEAR), dtype=np.float32)
    b = np.asarray(levels[lo + 1].resize((w, h), Image.BILINEAR), dtype=np.float32)
    mixed = np.clip(a * (1 - frac) + b * frac, 0, 255).astype(np.uint8)
    return Image.fromarray(mixed, "RGBa").convert("RGBA")


def forest_background(w, h, px_per_world, ground_y):
    img = Image.new("RGBA", (w, h), GRASS + (255,))
    over = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    tile = 120 * px_per_world
    col = tuple(int(c * 255) for c in DIAMOND[:3]) + (int(DIAMOND[3] * 255),)
    for ty in np.arange(-tile, h + tile, tile):
        for tx in np.arange(-tile, w + tile, tile):
            pts = [(tx, ty + 54 / 120 * tile), (tx + 70 / 120 * tile, ty + 10 / 120 * tile),
                   (tx + 122 / 120 * tile, ty + 54 / 120 * tile), (tx + 52 / 120 * tile, ty + 98 / 120 * tile)]
            d.polygon(pts, fill=col)
    road_top = ground_y - 30 * px_per_world
    d.polygon([(0, road_top), (w, road_top - 18 * px_per_world), (w, h), (0, h)], fill=ROAD + (255,))
    img.alpha_composite(over)
    return img


def draw_shadow(img, cx, cy, px_per_world):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    r = 22 * px_per_world
    ry = r * 0.38
    oy = 4 * 0.38 * px_per_world
    col = tuple(int(c * 255) for c in SHADOW[:3]) + (int(SHADOW[3] * 255),)
    ImageDraw.Draw(layer).ellipse((cx - r, cy + oy - ry, cx + r, cy + oy + ry), fill=col)
    img.alpha_composite(layer)


def simulate(frame, size, window_factor, scene_w, scene_h):
    k = size / BASE_FRAME
    visual_scale = TARGET_SCREEN_HEIGHT_720 / CAMERA_ZOOM / (BASE_CHAR_HEIGHT * k)
    px_per_world = CAMERA_ZOOM * window_factor
    s = visual_scale * px_per_world
    sprite = trilinear(frame, s)
    ground = (scene_w / 2, scene_h * 0.84)
    scene = forest_background(scene_w, scene_h, px_per_world, ground[1])
    draw_shadow(scene, ground[0], ground[1], px_per_world)
    ax, ay = BASE_ANCHOR[0] * k * s, BASE_ANCHOR[1] * k * s
    scene.alpha_composite(sprite, (round(ground[0] - ax), round(ground[1] - ay)))
    bb = sprite.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    return scene, sprite, {"visual_scale": round(visual_scale, 4), "screen_scale": round(s, 4),
                           "screen_char_height_px": bb[3] - bb[1], "sprite_px": list(sprite.size)}


def sharpness(sprite):
    arr = np.asarray(sprite, dtype=np.float32)
    lum = arr[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mask = arr[..., 3] > 250
    gx, gy = np.zeros_like(lum), np.zeros_like(lum)
    gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    gy[1:-1] = lum[2:] - lum[:-2]
    return float(np.hypot(gx, gy)[mask].mean())


def compare(a, b):
    w, h = max(a.width, b.width), max(a.height, b.height)
    pa, pb = Image.new("RGBA", (w, h)), Image.new("RGBA", (w, h))
    pa.paste(a, (0, 0))
    pb.paste(b, (0, 0))
    da = np.abs(np.asarray(pa, dtype=np.int16) - np.asarray(pb, dtype=np.int16))
    return {"mean_abs_diff": round(float(da.mean()), 2), "pixels_diff_gt_16_pct": round(float((da.max(-1) > 16).mean() * 100), 2)}


def alpha_report(frame):
    a = np.asarray(frame.getchannel("A"))
    rgb = np.asarray(frame, dtype=np.int16)[..., :3]
    edge = (a > 0) & (a < 255)
    return {"alpha_min": int(a.min()), "alpha_max": int(a.max()), "edge_pixels_semitransparent": int(edge.sum()),
            "transparent_pixels_with_color": int(((a == 0) & (rgb.sum(-1) > 0)).sum()),
            "bbox": list(frame.getchannel("A").getbbox())}


def memory(size):
    raw = size * size * 4
    return {"frame_rgba8_kb": round(raw / 1024, 1), "frame_with_mipmaps_kb": round(raw * 4 / 3 / 1024, 1),
            "character_frames": FRAMES_PER_CHARACTER,
            "character_uncompressed_mb": round(raw * 4 / 3 * FRAMES_PER_CHARACTER / 2**20, 1),
            "character_vram_compressed_8bpp_mb": round(size * size * 4 / 3 * FRAMES_PER_CHARACTER / 2**20, 1)}


def board(results, scenes):
    f_title, f_head, f_small = font(34), font(24), font(17)
    zoom = {"720p": 3, "1080p": 2}
    cells = []
    for win in WINDOWS:
        row = []
        for size in SIZES:
            scene, sprite = scenes[(win, size)]
            bb = sprite.getchannel("A").getbbox()
            sx = scene.width // 2 - sprite.width // 2
            crop_box = (scene.width // 2 - sprite.width // 2 - 6, int(scene.height * 0.84) - sprite.height,
                        scene.width // 2 + sprite.width // 2 + 6, int(scene.height * 0.84) + sprite.height // 8)
            crop = scene.crop(crop_box)
            row.append((scene, crop.resize((crop.width * zoom[win], crop.height * zoom[win]), Image.NEAREST)))
        cells.append(row)
    pad, label_h = 24, 34
    col_w = max(max(s.width, z.width) for row in cells for s, z in row)
    row_h = [max(s.height + label_h + z.height + label_h for s, z in row) for row in cells]
    title = "Verddro — Look C Híbrido · teste de resolução (256 vs 384)"
    subtitle = ("Simulação Godot 4.7: viewport 1280×720, stretch canvas_items, zoom 1.12, "
                "filtro linear + mipmaps. Sem nitidez artificial.")
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text_w = max(measure.textlength(title, font=f_title), measure.textlength(subtitle, font=f_small))
    width = int(max(pad + len(SIZES) * (col_w + pad), text_w + 2 * pad))
    height = 110 + sum(h + 70 for h in row_h) + 40
    out = Image.new("RGB", (width, height), PANEL_BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 20), title, font=f_title, fill=TEXT)
    d.text((pad, 66), subtitle, font=f_small, fill=TEXT)
    y = 110
    for win, row, rh in zip(WINDOWS, cells, row_h):
        d.text((pad, y), f"Janela {win}", font=f_head, fill=TEXT)
        y += 40
        for i, ((scene, zoomed), size) in enumerate(zip(row, SIZES)):
            x = pad + i * (col_w + pad)
            info = results["simulation"][win][str(size)]
            d.text((x, y), f"Quadro {size}×{size} · tamanho real · personagem {info['screen_char_height_px']} px",
                   font=f_small, fill=TEXT)
            out.paste(scene.convert("RGB"), (x, y + label_h - 8))
            zy = y + label_h + scene.height
            d.text((x, zy), f"ampliado {zoom[win]}× (vizinho mais próximo, só para inspeção)", font=f_small, fill=TEXT)
            out.paste(zoomed.convert("RGB"), (x, zy + label_h - 8))
        y += rh + 30
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    src = Image.open(SOURCE).convert("RGBA")
    alpha = np.asarray(src.getchannel("A"))
    anchor, (top, bottom) = ground_anchor(alpha)
    results = {"source": {"file": os.path.relpath(SOURCE, ROOT), "size": list(src.size), "mode": src.mode,
                          "alpha_min": int(alpha.min()), "alpha_max": int(alpha.max()),
                          "char_bbox_alpha_ge_128": [int(v) for v in src.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()],
                          "ground_anchor": [round(anchor[0], 1), round(anchor[1], 1)]},
               "frames": {}, "simulation": {w: {} for w in WINDOWS}, "comparison": {}, "memory": {}}
    frames, scenes, sprites = {}, {}, {}
    total_h = src_height_total(src)
    for size in SIZES:
        k = size / BASE_FRAME
        scale = BASE_CHAR_HEIGHT * k / total_h
        fx, fy = BASE_ANCHOR[0] * k, BASE_ANCHOR[1] * k
        left, upper = anchor[0] - fx / scale, anchor[1] - fy / scale
        pad = int(size / scale)
        padded = Image.new("RGBA", (src.width + 2 * pad, src.height + 2 * pad), (0, 0, 0, 0))
        padded.paste(src, (pad, pad))
        box = (left + pad, upper + pad, left + pad + size / scale, upper + pad + size / scale)
        frame = padded.convert("RGBa").resize((size, size), Image.LANCZOS, box=box).convert("RGBA")
        path = os.path.join(OUT, f"verddro_hybrid_{size}.png")
        frame.save(path, optimize=True)
        frames[size] = frame
        bb = frame.getchannel("A").getbbox()
        results["frames"][str(size)] = {"file": os.path.basename(path), "scale_from_source": round(scale, 5),
                                        "anchor": [fx, fy], "char_height_px": bb[3] - bb[1],
                                        "margins_px": {"left": bb[0], "top": bb[1], "right": size - bb[2], "bottom": size - bb[3]},
                                        "png_kb": round(os.path.getsize(path) / 1024, 1), **alpha_report(frame)}
        results["memory"][str(size)] = memory(size)
        for win, factor in WINDOWS.items():
            scene_w, scene_h = round(300 * factor), round(170 * factor)
            scene, sprite, info = simulate(frame, size, factor, scene_w, scene_h)
            info["sharpness_mean_gradient"] = round(sharpness(sprite), 2)
            results["simulation"][win][str(size)] = info
            scenes[(win, size)] = (scene, sprite)
            sprites[(win, size)] = sprite
            scene.save(os.path.join(OUT, f"sim_{win}_{size}.png"))
    for win in WINDOWS:
        results["comparison"][win] = compare(sprites[(win, 256)], sprites[(win, 384)])
    board(results, scenes).save(os.path.join(OUT, "verddro_resolution_comparison.png"))
    with open(os.path.join(OUT, "resolution_test_report.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
