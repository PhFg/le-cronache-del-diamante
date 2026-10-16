"""Estudos de direção artística A/B/C — Le Cronache del Diamante (Blender 5.2 LTS, Eevee).

A — PICTÓRICO: textura arrastada em pinceladas, sombra por mudança de cor, Kuwahara forte, tela.
B — GRÁFICO:   cor chapada posterizada, cel de 2 tons, contornos grossos hierarquizados.
C — HÍBRIDO:   superfície pintada + cel de 3 tons, luz cinematográfica, cristais como destaque.

Uso (sempre a partir da fonte texturizada, que NUNCA é salva):
  blender -b --factory-startup --disable-autoexec art_3d/verddro/blender/verddro_textured_v1.blend \
      --python art_3d/tools/setup_style_study.py -- --style A

Mesma câmera, enquadramento e posição de luzes nos três estilos; muda apenas o tratamento.
Geometria, UV e materiais originais preservados (cópia de material ligada ao slot do objeto;
texturas simplificadas são imagens novas derivadas da original).
"""
import argparse
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setup_exploration_look as v1  # noqa: E402

SOURCE = "verddro_textured_v1.blend"
PREFIX = "STYLE_"
FRAME_FILL = 0.85
AZIMUTH, ELEVATION = 35.0, 25.0

STYLES = {
    "A": {
        "name": "painterly",
        "lights": {"KEY": 2.6, "FILL": 80.0, "RIM": 2.0, "FOCUS": 100.0},
        "albedo_size": 512, "albedo_palette": None, "albedo_interp": "Cubic",
        "smear": 0.004, "stroke_scale": (3.0, 3.0, 14.0),
        "normal_strength": 0.0,
        "ramp_interp": "EASE", "wobble": 0.30,
        "ramp": [(0.10, (0.36, 0.40, 0.70)), (0.42, (0.80, 0.74, 0.80)), (0.70, (1.05, 0.95, 0.80))],
        "ao": 0.75, "leg_darken": 0.88,
        "rim": (1.0, 0.86, 0.66), "rim_strength": 0.30, "rim_hard": False,
        "crystal": (1.25, 0.6, 0.0),
        "kuwahara": 9.0, "kuwahara_mix": 1.0, "canvas": 0.10,
        "lines": {"color": (0.03, 0.035, 0.06), "sil": 0.4, "depth": 0.0, "crease": 0.0, "sil_dilate": 0,
                  "crease_range": (1.4, 2.6)},
        "bloom": 0.0,
    },
    "B": {
        "name": "graphic",
        "lights": {"KEY": 3.2, "FILL": 30.0, "RIM": 3.0, "FOCUS": 120.0},
        "albedo_size": 256, "albedo_palette": 8, "albedo_interp": "Linear",
        "smear": 0.0, "stroke_scale": (1.0, 1.0, 1.0),
        "normal_strength": 0.0,
        "ramp_interp": "CONSTANT", "wobble": 0.0,
        "ramp": [(0.0, (0.30, 0.33, 0.60)), (0.46, (1.0, 1.0, 1.0))],
        "ao": 1.0, "leg_darken": 1.0,
        "rim": (0.85, 1.0, 0.95), "rim_strength": 0.75, "rim_hard": True,
        "crystal": (1.15, 0.0, 0.0),
        "kuwahara": 0.0, "kuwahara_mix": 0.0, "canvas": 0.0,
        "lines": {"color": (0.02, 0.025, 0.035), "sil": 1.0, "depth": 1.0, "crease": 0.9, "sil_dilate": 2,
                  "crease_range": (0.6, 1.2)},
        "bloom": 0.0,
    },
    "C": {
        "name": "hybrid",
        "lights": {"KEY": 3.4, "FILL": 30.0, "RIM": 3.6, "FOCUS": 200.0},
        "albedo_size": 512, "albedo_palette": None, "albedo_interp": "Linear",
        "smear": 0.0025, "stroke_scale": (3.0, 3.0, 12.0),
        "normal_strength": 0.4,
        "ramp_interp": "CONSTANT", "wobble": 0.08,
        "ramp": [(0.0, (0.28, 0.32, 0.60)), (0.30, (0.68, 0.69, 0.82)), (0.58, (0.94, 0.88, 0.76)),
                 (0.86, (1.0, 0.97, 0.88))],
        "ao": 0.6, "leg_darken": 0.74,
        "rim": (0.62, 1.0, 0.84), "rim_strength": 0.65, "rim_hard": True,
        "crystal": (1.3, 2.4, 1.8),
        "kuwahara": 6.0, "kuwahara_mix": 0.85, "canvas": 0.04,
        "lines": {"color": (0.012, 0.025, 0.018), "sil": 0.9, "depth": 0.65, "crease": 0.3, "sil_dilate": 1,
                  "crease_range": (1.1, 2.2)},
        "bloom": 0.6, "bloom_threshold": 1.12,
    },
}

LIGHT_RIG = {  # posições fixas (relativas a centro/altura), iguais nos três estilos
    "KEY": ("SUN", Vector((-1.6, -2.4, 3.2)), (1.0, 0.93, 0.82), {"angle": math.radians(2), "use_shadow": True}),
    "FILL": ("AREA", Vector((2.4, -1.6, 0.4)), (0.62, 0.74, 1.0), {"use_shadow": False}),
    "RIM": ("SUN", Vector((1.3, 2.6, 1.6)), (0.78, 1.0, 0.90), {"angle": math.radians(2), "use_shadow": True}),
    "FOCUS": ("SPOT", Vector((-0.4, -1.6, 0.9)), (1.0, 0.94, 0.84),
              {"spot_size": math.radians(38), "spot_blend": 0.7, "use_shadow": True}),
}
RIM_DIRECTION = Vector((0.78, 0.55, 0.15)).normalized()


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--style", required=True, choices=sorted(STYLES))
    p.add_argument("--output")
    p.add_argument("--resolution", type=int, default=1024)
    p.add_argument("--no-save", action="store_true")
    return p.parse_args(argv)


def setup_camera(coll, pts, center):
    az, el = math.radians(AZIMUTH), math.radians(ELEVATION)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    data = bpy.data.cameras.new(PREFIX + "CAMERA")
    data.type = "ORTHO"
    cam = bpy.data.objects.new(PREFIX + "CAMERA", data)
    coll.objects.link(cam)
    cam.location = center + direction * 10.0
    v1.look_at(cam, center)
    bpy.context.view_layer.update()
    rot = cam.matrix_world.to_3x3()
    right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
    xs = [(p - center).dot(right) for p in pts]
    ys = [(p - center).dot(up) for p in pts]
    depths = [(p - cam.location).dot(fwd) for p in pts]
    cam.location += right * ((max(xs) + min(xs)) / 2) + up * ((max(ys) + min(ys)) / 2)
    data.ortho_scale = max((max(ys) - min(ys)) / FRAME_FILL, (max(xs) - min(xs)) / 0.9)
    data.clip_start, data.clip_end = 0.1, 30.0
    bpy.context.scene.camera = cam
    return min(depths), max(depths)


def setup_lights(coll, center, height, energies):
    chest = center + Vector((0, 0, 0.28 * height))
    for name, (kind, offset, color, props) in LIGHT_RIG.items():
        extra = dict(props)
        if kind == "AREA":
            extra["size"] = 2.5 * height
        base = chest if name == "FOCUS" else center
        target = chest if name in ("KEY", "FOCUS") else center
        obj = v1.add_light(coll, name, kind, base + offset * height, target, energies[name], color, **extra)
        obj.name = obj.data.name = PREFIX + name


def palette_quantize(rgb, colors, iterations=15):
    """K-means em RGB: cores chapadas sem desvio de matiz (ao contrário de posterizar por canal)."""
    rng = np.random.default_rng(3)
    centers = rgb[rng.choice(len(rgb), colors, replace=False)]
    for _ in range(iterations):
        labels = np.argmin(((rgb[:, None, :] - centers[None]) ** 2).sum(-1), axis=1)
        for k in range(colors):
            members = rgb[labels == k]
            if len(members):
                centers[k] = members.mean(0)
    return centers[labels]


def derived_texture(src, name, size, palette):
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = src.copy()
    img.name = name
    img.scale(size, size)
    if palette:
        px = np.empty(size * size * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        px[:, :3] = palette_quantize(px[:, :3].copy(), palette)
        img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


class Graph:
    def __init__(self, nt, origin):
        self.nt, self.ox, self.oy = nt, origin.x, origin.y

    def node(self, kind, x, y, **attrs):
        n = self.nt.nodes.new(kind)
        n.location = (self.ox + x, self.oy + y)
        n.label = PREFIX + kind.replace("ShaderNode", "")
        for k, v in attrs.items():
            setattr(n, k, v)
        return n

    def connect(self, value, socket):
        if isinstance(value, bpy.types.NodeSocket):
            self.nt.links.new(value, socket)
        else:
            socket.default_value = value

    def math(self, op, a, b, x, y):
        n = self.node("ShaderNodeMath", x, y, operation=op)
        self.connect(a, n.inputs[0])
        self.connect(b, n.inputs[1])
        return n.outputs[0]

    def map_range(self, value, fmin, fmax, tmin, tmax, x, y):
        n = self.node("ShaderNodeMapRange", x, y, clamp=True)
        for key, v in (("From Min", fmin), ("From Max", fmax), ("To Min", tmin), ("To Max", tmax)):
            n.inputs[key].default_value = v
        self.connect(value, n.inputs["Value"])
        return n.outputs["Result"]

    def mix(self, blend, a, b, x, y, fac=1.0):
        n = self.node("ShaderNodeMix", x, y, data_type="RGBA", blend_type=blend)
        self.connect(fac, n.inputs["Factor"])
        self.connect(a, n.inputs["A"])
        self.connect(b, n.inputs["B"])
        return n.outputs["Result"]

    def gray(self, value, x, y):
        n = self.node("ShaderNodeCombineColor", x, y)
        for ch in ("Red", "Green", "Blue"):
            self.connect(value, n.inputs[ch])
        return n.outputs["Color"]


def build_material(src, cfg, key, z_min, height):
    name = f"{src.name}_{PREFIX}{key}"
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    mat = src.copy()
    mat.name = name
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    base_link = bsdf.inputs["Base Color"].links[0]
    base_tex = base_link.from_node
    normal_node = bsdf.inputs["Normal"].links[0].from_node if bsdf.inputs["Normal"].links else None
    g = Graph(nt, bsdf.location)

    coord = g.node("ShaderNodeTexCoord", 200, 900)
    geo = g.node("ShaderNodeNewGeometry", 200, 700)
    uv = g.node("ShaderNodeUVMap", 200, 1100)

    tex_vector = uv.outputs["UV"]
    if cfg["smear"]:
        mapping = g.node("ShaderNodeMapping", 350, 1000)
        mapping.inputs["Scale"].default_value = cfg["stroke_scale"]
        g.connect(coord.outputs["Object"], mapping.inputs["Vector"])
        strokes = g.node("ShaderNodeTexNoise", 500, 1000)
        strokes.inputs["Scale"].default_value = 6.0
        strokes.inputs["Detail"].default_value = 2.0
        g.connect(mapping.outputs["Vector"], strokes.inputs["Vector"])
        centered = g.node("ShaderNodeVectorMath", 650, 1000, operation="SUBTRACT")
        g.connect(strokes.outputs["Color"], centered.inputs[0])
        centered.inputs[1].default_value = (0.5, 0.5, 0.5)
        scaled = g.node("ShaderNodeVectorMath", 800, 1000, operation="SCALE")
        g.connect(centered.outputs["Vector"], scaled.inputs[0])
        scaled.inputs["Scale"].default_value = cfg["smear"]
        moved = g.node("ShaderNodeVectorMath", 950, 1050, operation="ADD")
        g.connect(uv.outputs["UV"], moved.inputs[0])
        g.connect(scaled.outputs["Vector"], moved.inputs[1])
        tex_vector = moved.outputs["Vector"]
        stroke_value = strokes.outputs["Fac"]
    else:
        stroke_value = None

    simple = derived_texture(base_tex.image, f"{base_tex.image.name}_{PREFIX}{key}", cfg["albedo_size"],
                             cfg["albedo_palette"])
    albedo_node = g.node("ShaderNodeTexImage", 1100, 1000, image=simple, interpolation=cfg["albedo_interp"])
    g.connect(tex_vector, albedo_node.inputs["Vector"])
    albedo = albedo_node.outputs["Color"]

    diffuse = g.node("ShaderNodeBsdfDiffuse", 300, 400)
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    if normal_node and cfg["normal_strength"] > 0:
        nmap = g.node("ShaderNodeNormalMap", 150, 300)
        nmap.inputs["Strength"].default_value = cfg["normal_strength"]
        g.connect(normal_node.inputs["Color"].links[0].from_socket, nmap.inputs["Color"])
        g.connect(nmap.outputs["Normal"], diffuse.inputs["Normal"])
    to_rgb = g.node("ShaderNodeShaderToRGB", 450, 400)
    g.connect(diffuse.outputs["BSDF"], to_rgb.inputs["Shader"])
    shade = to_rgb.outputs["Color"]
    if cfg["ao"] < 1.0:
        ao = g.node("ShaderNodeAmbientOcclusion", 450, 250)
        ao.inputs["Distance"].default_value = 0.06 * height
        shade = g.math("MULTIPLY", shade, g.map_range(ao.outputs["AO"], 0, 1, cfg["ao"], 1.0, 600, 250), 750, 350)
    if cfg["wobble"]:
        wob_src = stroke_value
        if wob_src is None:
            wob = g.node("ShaderNodeTexNoise", 450, 600)
            wob.inputs["Scale"].default_value = 14.0
            wob.inputs["Detail"].default_value = 4.0
            g.connect(coord.outputs["Object"], wob.inputs["Vector"])
            wob_src = wob.outputs["Fac"]
        shade = g.math("ADD", shade, g.map_range(wob_src, 0.3, 0.7, -cfg["wobble"] / 2, cfg["wobble"] / 2,
                                                 600, 550), 900, 400)

    ramp = g.node("ShaderNodeValToRGB", 1050, 400)
    cr = ramp.color_ramp
    cr.interpolation = cfg["ramp_interp"]
    stops = cfg["ramp"]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], stops[0][1] + (1.0,)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], stops[-1][1] + (1.0,)
    for pos, col in stops[1:-1]:
        cr.elements.new(pos).color = col + (1.0,)
    g.connect(shade, ramp.inputs["Fac"])
    color = g.mix("MULTIPLY", albedo, ramp.outputs["Color"], 1300, 500)

    if cfg["leg_darken"] < 1.0:
        pos = g.node("ShaderNodeSeparateXYZ", 400, -100)
        g.connect(geo.outputs["Position"], pos.inputs["Vector"])
        focus = g.map_range(pos.outputs["Z"], z_min, z_min + 0.55 * height, cfg["leg_darken"], 1.0, 600, -100)
        color = g.mix("MULTIPLY", color, g.gray(focus, 750, -100), 1450, 400)

    layer = g.node("ShaderNodeLayerWeight", 900, -300)
    layer.inputs["Blend"].default_value = 0.35
    edge_lo, edge_hi = (0.62, 0.66) if cfg["rim_hard"] else (0.5, 0.8)
    rim_edge = g.map_range(layer.outputs["Facing"], edge_lo, edge_hi, 0, 1, 1050, -300)
    rim_dot = g.node("ShaderNodeVectorMath", 900, -450, operation="DOT_PRODUCT")
    g.connect(geo.outputs["Normal"], rim_dot.inputs[0])
    rim_dot.inputs[1].default_value = RIM_DIRECTION
    side_lo, side_hi = (0.40, 0.45) if cfg["rim_hard"] else (0.2, 0.6)
    rim_side = g.map_range(rim_dot.outputs["Value"], side_lo, side_hi, 0, 1, 1050, -450)
    rim = g.math("MULTIPLY", g.math("MULTIPLY", rim_edge, rim_side, 1200, -350), cfg["rim_strength"], 1350, -350)
    color = g.mix("ADD", color, cfg["rim"] + (1.0,), 1600, 400, fac=rim)

    base_c, facet_c, sparkle_c = cfg["crystal"]
    sharp = base_tex.outputs["Color"]
    hsv = g.node("ShaderNodeSeparateColor", 300, -700, mode="HSV")
    g.connect(sharp, hsv.inputs["Color"])
    hue = g.math("MULTIPLY", g.math("GREATER_THAN", hsv.outputs["Red"], 0.36, 500, -650),
                 g.math("LESS_THAN", hsv.outputs["Red"], 0.55, 500, -730), 650, -700)
    sv = g.math("MULTIPLY", g.map_range(hsv.outputs["Green"], 0.45, 0.7, 0, 1, 500, -820),
                g.map_range(hsv.outputs["Blue"], 0.6, 0.85, 0, 1, 500, -920), 650, -860)
    crystal = g.math("MULTIPLY", hue, sv, 800, -780)
    strength = base_c
    if facet_c or sparkle_c:
        facet = g.node("ShaderNodeLayerWeight", 650, -1050)
        facet.inputs["Blend"].default_value = 0.5
        if normal_node:
            g.connect(normal_node.outputs["Normal"], facet.inputs["Normal"])
        sparkle_tex = g.node("ShaderNodeTexNoise", 650, -1200)
        sparkle_tex.inputs["Scale"].default_value = 45.0
        g.connect(coord.outputs["Object"], sparkle_tex.inputs["Vector"])
        sparkle = g.map_range(sparkle_tex.outputs["Fac"], 0.62, 0.74, 0, 1, 800, -1200)
        strength = g.math("ADD", base_c, g.math("ADD", g.math("MULTIPLY", facet.outputs["Fresnel"], facet_c, 950, -1050),
                                               g.math("MULTIPLY", sparkle, sparkle_c, 950, -1200), 1100, -1100),
                          1250, -1000)
    glow = g.mix("MULTIPLY", sharp, g.gray(strength, 1350, -900), 1500, -800)
    color = g.mix("MIX", color, glow, 1750, 300, fac=crystal)

    emit = g.node("ShaderNodeEmission", 1950, 300)
    g.connect(color, emit.inputs["Color"])
    for l in list(out.inputs["Surface"].links):
        nt.links.remove(l)
    g.connect(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def canvas_image(resolution):
    name = PREFIX + "CANVAS"
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    rng = np.random.default_rng(7)
    small = rng.random((resolution // 4, resolution // 4)).astype(np.float32)
    grain = np.kron(small, np.ones((4, 4), dtype=np.float32))
    weave = 0.5 + 0.25 * (np.sin(np.arange(resolution) * 0.9)[None, :] + np.sin(np.arange(resolution) * 0.9)[:, None])
    value = np.clip(0.55 * grain + 0.45 * weave, 0, 1)
    img = bpy.data.images.new(name, resolution, resolution, alpha=False, float_buffer=True)
    px = np.ones((resolution, resolution, 4), dtype=np.float32)
    px[..., :3] = value[..., None]
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def setup_compositor(cfg, key, depth_min, depth_max, resolution):
    sc = bpy.context.scene
    name = PREFIX + "COMPOSITOR_" + key
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    tree = bpy.data.node_groups.new(name, "CompositorNodeTree")
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n = tree.nodes
    link = tree.links.new

    def new(kind, x, y, **inputs):
        node = n.new(kind)
        node.location = (x, y)
        for k, v in inputs.items():
            node.inputs[k].default_value = v
        return node

    def math(op, a, b, x, y):
        m = new("ShaderNodeMath", x, y)
        m.operation = op
        for sock, val in ((m.inputs[0], a), (m.inputs[1], b)):
            if isinstance(val, bpy.types.NodeSocket):
                link(val, sock)
            else:
                sock.default_value = val
        return m.outputs[0]

    def edge(src, lo, hi, weight, dilate, x, y):
        f = new("CompositorNodeFilter", x, y, Type="Sobel")
        link(src, f.inputs["Image"])
        m = new("ShaderNodeMapRange", x + 180, y)
        m.clamp = True
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = lo, hi
        link(f.outputs["Image"], m.inputs["Value"])
        result = m.outputs["Result"]
        if dilate:
            d = new("CompositorNodeDilateErode", x + 360, y, Size=dilate, Type="Steps")
            link(result, d.inputs["Mask"])
            result = d.outputs["Mask"]
        return math("MULTIPLY", result, weight, x + 520, y)

    rl = new("CompositorNodeRLayers", -1400, 0)
    image = rl.outputs["Image"]

    if cfg["kuwahara"]:
        kuwa = new("CompositorNodeKuwahara", -1100, 400, Size=cfg["kuwahara"], Type="Anisotropic",
                   Sharpness=0.5 if key == "A" else 0.7, Eccentricity=1.6 if key == "A" else 1.0)
        link(image, kuwa.inputs["Image"])
        interior = new("CompositorNodeDilateErode", -1100, 200, Size=-2, Type="Steps")
        link(rl.outputs["Alpha"], interior.inputs["Mask"])
        mixed = new("ShaderNodeMix", -850, 350)
        mixed.data_type = "RGBA"
        link(math("MULTIPLY", interior.outputs["Mask"], cfg["kuwahara_mix"], -950, 200), mixed.inputs["Factor"])
        link(image, mixed.inputs["A"])
        link(kuwa.outputs["Image"], mixed.inputs["B"])
        keep = new("CompositorNodeSetAlpha", -650, 350, Type="Replace Alpha")
        link(mixed.outputs["Result"], keep.inputs["Image"])
        link(rl.outputs["Alpha"], keep.inputs["Alpha"])
        image = keep.outputs["Image"]

    if cfg["canvas"]:
        tex = n.new("CompositorNodeImage")
        tex.location = (-650, 600)
        tex.image = canvas_image(resolution)
        grain = new("ShaderNodeMapRange", -450, 600)
        grain.inputs["To Min"].default_value = 1 - cfg["canvas"]
        grain.inputs["To Max"].default_value = 1 + cfg["canvas"] / 2
        link(tex.outputs["Image"], grain.inputs["Value"])
        textured = new("ShaderNodeMix", -250, 400)
        textured.data_type = "RGBA"
        textured.blend_type = "MULTIPLY"
        textured.inputs["Factor"].default_value = 1.0
        link(image, textured.inputs["A"])
        gray = new("CompositorNodeCombineColor", -300, 600)
        for ch in ("Red", "Green", "Blue"):
            link(grain.outputs["Result"], gray.inputs[ch])
        link(gray.outputs["Image"], textured.inputs["B"])
        keep = new("CompositorNodeSetAlpha", -100, 400, Type="Replace Alpha")
        link(textured.outputs["Result"], keep.inputs["Image"])
        link(rl.outputs["Alpha"], keep.inputs["Alpha"])
        image = keep.outputs["Image"]

    if cfg["bloom"]:
        glare = new("CompositorNodeGlare", 100, 400, Type="Bloom", Strength=cfg["bloom"], Size=0.55)
        glare.inputs["Highlights Threshold"].default_value = cfg.get("bloom_threshold", 1.05)
        link(image, glare.inputs["Image"])
        image = glare.outputs["Image"]

    lc = cfg["lines"]
    depth = new("ShaderNodeMapRange", -1200, -300)
    depth.clamp = True
    depth.inputs["From Min"].default_value = depth_min - 0.05
    depth.inputs["From Max"].default_value = depth_max + 0.05
    link(rl.outputs["Depth"], depth.inputs["Value"])
    edges = edge(rl.outputs["Alpha"], 0.3, 1.2, lc["sil"], lc["sil_dilate"], -1000, -650)
    if lc["depth"]:
        edges = math("MAXIMUM", edges, edge(depth.outputs["Result"], 0.05, 0.18, lc["depth"],
                                            1 if key == "B" else 0, -1000, -400), -300, -450)
    if lc["crease"]:
        lo, hi = lc["crease_range"]
        edges = math("MAXIMUM", edges, edge(rl.outputs["Normal"], lo, hi, lc["crease"], 0, -1000, -150), -150, -350)
    lines = new("CompositorNodeSetAlpha", 100, -200, Type="Apply Mask")
    lines.inputs["Image"].default_value = lc["color"] + (1.0,)
    link(edges, lines.inputs["Alpha"])
    over = new("CompositorNodeAlphaOver", 350, 150)
    link(image, over.inputs["Background"])
    link(lines.outputs["Image"], over.inputs["Foreground"])
    out = new("NodeGroupOutput", 550, 150)
    link(over.outputs["Image"], out.inputs["Image"])
    sc.compositing_node_group = tree


def main():
    args = parse_args()
    if os.path.basename(bpy.data.filepath) != SOURCE:
        raise SystemExit(f"[style] Abra a fonte {SOURCE} (aberto: {os.path.basename(bpy.data.filepath)}).")
    key, cfg = args.style, STYLES[args.style]
    folder = os.path.dirname(bpy.data.filepath)
    blend_out = os.path.join(folder, f"verddro_style_{key}_{cfg['name']}.blend")
    png_out = os.path.abspath(args.output or os.path.join(folder, "..", "renders", f"verddro_style_{key}_{cfg['name']}.png"))

    obj = v1.character_object()
    polys, uvs = len(obj.data.polygons), [u.name for u in obj.data.uv_layers]
    mesh_mats = [m.name if m else None for m in obj.data.materials]
    original = obj.material_slots[0].material

    coll = bpy.data.collections.new(PREFIX + "LOOK")
    bpy.context.scene.collection.children.link(coll)
    pts, mn, mx = v1.world_points(obj)
    center, height = (mn + mx) / 2, mx.z - mn.z
    dmin, dmax = setup_camera(coll, pts, center)
    setup_lights(coll, center, height, cfg["lights"])
    mat = build_material(original, cfg, key, mn.z, height)
    slot = obj.material_slots[0]
    slot.link = "OBJECT"
    slot.material = mat
    v1.setup_render(args.resolution)
    setup_compositor(cfg, key, dmin, dmax, args.resolution)

    assert len(obj.data.polygons) == polys and [u.name for u in obj.data.uv_layers] == uvs
    assert [m.name if m else None for m in obj.data.materials] == mesh_mats
    print(f"[style] {key} ({cfg['name']}) material={mat.name}")

    os.makedirs(os.path.dirname(png_out), exist_ok=True)
    bpy.context.scene.render.filepath = png_out
    bpy.ops.render.render(write_still=True)
    print(f"[style] render: {png_out}")
    if not args.no_save:
        bpy.ops.wm.save_as_mainfile(filepath=blend_out, copy=True)
        print(f"[style] blend: {blend_out}")


if __name__ == "__main__":
    main()
