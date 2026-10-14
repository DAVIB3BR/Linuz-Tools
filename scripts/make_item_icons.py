#!/usr/bin/env python3
"""Gera todos os PNGs de ícone em lunuz/icons/.

1. sec-*.svg  -> sec-*.png   (ícones coloridos das seções, estilo LinuxToys)
2. item-*.svg -> item-*.png  (ícones de marca: nvidia, docker, vscode...)
3. distro-*.svg -> distro-*.png (logos de distros: debian, ubuntu, fedora...)
3. demais itens -> PNG genérico: quadrado arredondado na cor da categoria
                   + glifo simbólico branco do tema (ITEM_ICONS)

Aliases: repo-git<-git, run-python<-lang-python, run-java<-lang-java,
         run-node<-lang-node, run-cpp<-lang-cpp.

Uso: python3 scripts/make_item_icons.py
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "icons")
OUT = os.path.join(ROOT, "lunuz", "icons")
SIZE_SVG = 128          # tamanho de renderização dos SVGs
SIZE_GENERIC = 96       # tamanho dos PNGs genéricos
GLYPH_SCALE = 0.56      # proporção do glifo dentro do quadrado

sys.path.insert(0, ROOT)

ALIASES = {
    "repo-git": "git",
    "run-python": "lang-python",
    "run-java": "lang-java",
    "run-node": "lang-node",
    "run-cpp": "lang-cpp",
}


def rsvg(svg_path, png_path, size=SIZE_SVG):
    subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), svg_path, "-o", png_path],
        check=True,
    )


def load_glyph(symbolic, size):
    """Carrega o glifo simbólico do tema como imagem RGBA monocromática."""
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GdkPixbuf
    theme = Gtk.IconTheme.get_default()
    if not theme.has_icon(symbolic):
        return None
    pb = theme.load_icon(symbolic, size, 0)
    tmp = os.path.join(OUT, ".glyph-tmp.png")
    pb.savev(tmp, "png", [], [])
    from PIL import Image
    im = Image.open(tmp).convert("RGBA")
    os.unlink(tmp)
    # força branco usando o alfa do glifo
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(im.split()[3])
    return white


def generic_icon(item_id, symbolic, color, size=SIZE_GENERIC):
    from PIL import Image, ImageDraw
    hexcolor = color.lstrip("#")
    rgb = tuple(int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 5, fill=rgb + (255,))
    glyph = load_glyph(symbolic, int(size * GLYPH_SCALE))
    if glyph is not None:
        gx = (size - glyph.width) // 2
        gy = (size - glyph.height) // 2
        im.alpha_composite(glyph, (gx, gy))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    from lunuz.actions import CATEGORIES, ITEM_ICONS

    cat_of, color_of = {}, {}
    for cat in CATEGORIES:
        color_of[cat["id"]] = cat["color"]
        for it in cat["items"]:
            cat_of[it["id"]] = cat["id"]

    n_sec = n_brand = n_gen = 0

    # 1) seções (SVGs sem prefixo "item-", ex.: system.svg -> sec-system.png)
    #    e logos de distro (distro-*.svg -> distro-*.png, nome preservado)
    n_distro = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".svg"):
            continue
        if f.startswith("distro-"):
            rsvg(os.path.join(SRC, f), os.path.join(OUT, f[:-4] + ".png"))
            n_distro += 1
        elif not f.startswith("item-"):
            rsvg(os.path.join(SRC, f), os.path.join(OUT, "sec-" + f[:-4] + ".png"))
            n_sec += 1

    # 2) marcas
    brands = {}
    for f in sorted(os.listdir(SRC)):
        if f.startswith("item-") and f.endswith(".svg"):
            item_id = f[len("item-"):-len(".svg")]
            rsvg(os.path.join(SRC, f), os.path.join(OUT, f"item-{item_id}.png"))
            brands[item_id] = True
            n_brand += 1

    # 3) genéricos + aliases
    for item_id, symbolic in ITEM_ICONS.items():
        dst = os.path.join(OUT, f"item-{item_id}.png")
        if item_id in brands or os.path.exists(dst):
            continue
        if item_id in ALIASES:
            src = os.path.join(OUT, f"item-{ALIASES[item_id]}.png")
            if os.path.exists(src):
                shutil.copyfile(src, dst)
                n_gen += 1
                continue
        color = color_of.get(cat_of.get(item_id, ""), "#555555")
        generic_icon(item_id, symbolic, color).save(dst)
        n_gen += 1

    total = len([f for f in os.listdir(OUT) if f.endswith(".png")])
    print(f"secoes: {n_sec} | distros: {n_distro} | marcas: {n_brand} | "
          f"genericos+aliases: {n_gen} | total em icons/: {total}")


if __name__ == "__main__":
    main()
