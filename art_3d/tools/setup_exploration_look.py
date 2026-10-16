"""Look ilustrado de exploração para Le Cronache del Diamante (Blender 5.2 LTS, Eevee).

Uso (Blender em modo background, abrindo o ARQUIVO DE TRABALHO):
  blender -b --factory-startup --disable-autoexec art_3d/verddro/blender/verddro_exploration_look_v1.blend \
      --python art_3d/tools/setup_exploration_look.py -- \
      --output art_3d/verddro/renders/verddro_exploration_look_test_v1.png

Opções: --no-render, --no-save, --azimuth <graus>, --elevation <graus>, --resolution <px>.

Garantias:
- Recusa rodar em arquivos protegidos (ex.: verddro_textured_v1.blend) ou fora do arquivo de trabalho esperado.
- Não altera malha, UV, modificadores nem materiais originais: o material estilizado é uma CÓPIA,
  ligada ao slot no nível do OBJETO (a malha continua apontando para o material original).
- Contornos via compositor (passes de normal/profundidade/alpha): nenhuma geometria duplicada.
- Reexecutável: remove e recria apenas os elementos com prefixo EXPLORE_.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

WORK_FILE = "verddro_exploration_look_v1.blend"
PROTECTED_FILES = {"verddro_textured_v1.blend", "verddro_model_working_v2.blend", "verddro_model_v1.blend"}
PREFIX = "EXPLORE_"
COLLECTION = PREFIX + "LOOK"
MAT_SUFFIX = "_" + PREFIX.rstrip("_")
COMPOSITOR = PREFIX + "COMPOSITOR"

LINE_COLOR = (0.035, 0.06, 0.045, 1.0)
LINE_OPACITY = 0.7
SHADOW_TINT = (0.40, 0.44, 0.62, 1.0)
MID_TINT = (0.80, 0.82, 0.84, 1.0)
LIGHT_TINT = (1.0, 0.97, 0.90, 1.0)
CRYSTAL_EMISSION = 2.4


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="art_3d/verddro/renders/verddro_exploration_look_test_v1.png")
    p.add_argument("--azimuth", type=float, default=35.0, help="Graus a partir da frente do personagem (-Y).")
    p.add_argument("--elevation", type=float, default=25.0)
    p.add_argument("--resolution", type=int, default=1024)
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--no-save", action="store_true")
    return p.parse_args(argv)


def check_file():
    name = os.path.basename(bpy.data.filepath)
    if name in PROTECTED_FILES:
        raise SystemExit(f"[explore] Recusado: {name} é um arquivo protegido.")
    if name != WORK_FILE:
        raise SystemExit(f"[explore] Abra o arquivo de trabalho {WORK_FILE} (aberto: {name or 'nenhum'}).")


def character_object():
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.name.startswith(PREFIX)]
    if not meshes:
        raise SystemExit("[explore] Nenhuma malha encontrada.")
    return max(meshes, key=lambda o: len(o.data.polygons))


def world_points(obj, max_points=60000):
    """Amostra de vértices em espaço de mundo (somente leitura) para enquadrar pela silhueta real."""
    verts = obj.data.vertices
    step = max(1, len(verts) // max_points)
    mw = obj.matrix_world
    pts = [mw @ verts[i].co for i in range(0, len(verts), step)]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return pts, mn, mx


def cleanup():
    coll = bpy.data.collections.get(COLLECTION)
    if coll:
        for o in list(coll.objects):
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data and data.users == 0:
                (bpy.data.cameras if isinstance(data, bpy.types.Camera) else bpy.data.lights).remove(data)
        bpy.data.collections.remove(coll)
    group = bpy.data.node_groups.get(COMPOSITOR)
    if group:
        bpy.data.node_groups.remove(group)


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def new_collection():
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    return coll


def setup_camera(coll, pts, center, azimuth, elevation, resolution):
    az, el = math.radians(azimuth), math.radians(elevation)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam_data = bpy.data.cameras.new(PREFIX + "CAMERA")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new(PREFIX + "CAMERA", cam_data)
    coll.objects.link(cam)
    distance = 10.0
    cam.location = center + direction * distance
    look_at(cam, center)
    bpy.context.view_layer.update()
    rot = cam.matrix_world.to_3x3()
    right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
    xs = [(p - center).dot(right) for p in pts]
    ys = [(p - center).dot(up) for p in pts]
    depths = [(p - cam.location).dot(fwd) for p in pts]
    cam.location += right * ((max(xs) + min(xs)) / 2) + up * ((max(ys) + min(ys)) / 2)
    cam_data.ortho_scale = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.06
    cam_data.clip_start, cam_data.clip_end = 0.1, distance * 3
    bpy.context.scene.camera = cam
    return cam, min(depths), max(depths)


def add_light(coll, name, kind, location, target, energy, color, **props):
    data = bpy.data.lights.new(PREFIX + name, kind)
    data.energy, data.color = energy, color
    for k, v in props.items():
        setattr(data, k, v)
    obj = bpy.data.objects.new(PREFIX + name, data)
    obj.location = location
    coll.objects.link(obj)
    look_at(obj, target)
    return obj


def setup_lights(coll, center, height):
    h = height
    add_light(coll, "KEY", "SUN", center + Vector((-2.4, -2.0, 3.0)) * h, center, 2.6, (1.0, 0.94, 0.84),
              angle=math.radians(4), use_shadow=True)
    add_light(coll, "FILL", "AREA", center + Vector((2.2, -1.8, 0.6)) * h, center, 90.0, (0.70, 0.80, 1.0),
              size=2.5 * h, use_shadow=False)
    add_light(coll, "RIM", "SUN", center + Vector((1.2, 2.6, 1.4)) * h, center, 2.2, (0.80, 1.0, 0.90),
              angle=math.radians(3), use_shadow=True)


def link(tree, a, b):
    tree.links.new(a, b)


def stylize_material(src):
    """Cópia estilizada: toon em 3 faixas (Shader to RGB), sombra fria, cristais emissivos. Original intacto."""
    name = src.name + MAT_SUFFIX
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    mat = src.copy()
    mat.name = name
    nt = mat.node_tree
    nodes = nt.nodes
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None) or \
        next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not bsdf or not out:
        return None
    base_link = bsdf.inputs["Base Color"].links
    normal_link = bsdf.inputs["Normal"].links
    base_socket = base_link[0].from_socket if base_link else None

    def node(kind, x, y, **attrs):
        n = nodes.new(kind)
        n.location = (bsdf.location.x + x, bsdf.location.y + y)
        n.label = PREFIX + kind.replace("ShaderNode", "")
        for k, v in attrs.items():
            setattr(n, k, v)
        return n

    diffuse = node("ShaderNodeBsdfDiffuse", 300, 300)
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    if normal_link:
        link(nt, normal_link[0].from_socket, diffuse.inputs["Normal"])
    to_rgb = node("ShaderNodeShaderToRGB", 500, 300)
    link(nt, diffuse.outputs["BSDF"], to_rgb.inputs["Shader"])
    ramp = node("ShaderNodeValToRGB", 700, 300)
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].position, cr.elements[0].color = 0.18, SHADOW_TINT
    cr.elements[1].position, cr.elements[1].color = 0.75, LIGHT_TINT
    mid = cr.elements.new(0.42)
    mid.color = MID_TINT
    link(nt, to_rgb.outputs["Color"], ramp.inputs["Fac"])

    toon = node("ShaderNodeMix", 1000, 200, data_type="RGBA", blend_type="MULTIPLY")
    toon.inputs["Factor"].default_value = 1.0
    if base_socket:
        link(nt, base_socket, toon.inputs["A"])
    else:
        toon.inputs["A"].default_value = bsdf.inputs["Base Color"].default_value
    link(nt, ramp.outputs["Color"], toon.inputs["B"])

    emission_color = toon.outputs["Result"]
    if base_socket:
        hsv = node("ShaderNodeSeparateColor", 300, -100, mode="HSV")
        link(nt, base_socket, hsv.inputs["Color"])
        hue_lo = node("ShaderNodeMath", 500, -40, operation="GREATER_THAN")
        hue_lo.inputs[1].default_value = 0.36
        hue_hi = node("ShaderNodeMath", 500, -120, operation="LESS_THAN")
        hue_hi.inputs[1].default_value = 0.55
        sat = node("ShaderNodeMapRange", 500, -200)
        sat.inputs["From Min"].default_value, sat.inputs["From Max"].default_value = 0.45, 0.7
        val = node("ShaderNodeMapRange", 500, -380)
        val.inputs["From Min"].default_value, val.inputs["From Max"].default_value = 0.6, 0.85
        link(nt, hsv.outputs["Red"], hue_lo.inputs[0])
        link(nt, hsv.outputs["Red"], hue_hi.inputs[0])
        link(nt, hsv.outputs["Green"], sat.inputs["Value"])
        link(nt, hsv.outputs["Blue"], val.inputs["Value"])
        m1 = node("ShaderNodeMath", 700, -80, operation="MULTIPLY")
        m2 = node("ShaderNodeMath", 700, -200, operation="MULTIPLY")
        mask = node("ShaderNodeMath", 850, -140, operation="MULTIPLY")
        link(nt, hue_lo.outputs[0], m1.inputs[0])
        link(nt, hue_hi.outputs[0], m1.inputs[1])
        link(nt, sat.outputs["Result"], m2.inputs[0])
        link(nt, val.outputs["Result"], m2.inputs[1])
        link(nt, m1.outputs[0], mask.inputs[0])
        link(nt, m2.outputs[0], mask.inputs[1])
        glow = node("ShaderNodeMix", 1000, -60, data_type="RGBA", blend_type="MULTIPLY")
        link(nt, mask.outputs[0], glow.inputs["Factor"])
        link(nt, base_socket, glow.inputs["A"])
        glow.inputs["B"].default_value = (CRYSTAL_EMISSION,) * 3 + (1.0,)
        add = node("ShaderNodeMix", 1200, 100, data_type="RGBA", blend_type="ADD")
        add.inputs["Factor"].default_value = 1.0
        link(nt, toon.outputs["Result"], add.inputs["A"])
        crystal_only = node("ShaderNodeMix", 1100, -60, data_type="RGBA", blend_type="MIX")
        link(nt, mask.outputs[0], crystal_only.inputs["Factor"])
        crystal_only.inputs["A"].default_value = (0, 0, 0, 1)
        link(nt, glow.outputs["Result"], crystal_only.inputs["B"])
        link(nt, crystal_only.outputs["Result"], add.inputs["B"])
        emission_color = add.outputs["Result"]

    emit = node("ShaderNodeEmission", 1400, 100)
    emit.inputs["Strength"].default_value = 1.0
    link(nt, emission_color, emit.inputs["Color"])
    for l in list(out.inputs["Surface"].links):
        nt.links.remove(l)
    link(nt, emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def assign_materials(obj):
    created = []
    for slot in obj.material_slots:
        src = slot.material
        if not src or src.name.endswith(MAT_SUFFIX):
            src = bpy.data.materials.get(src.name[: -len(MAT_SUFFIX)]) if src else None
        if not src or not src.node_tree:
            continue
        styl = stylize_material(src)
        if styl:
            slot.link = "OBJECT"
            slot.material = styl
            created.append((src.name, styl.name))
    return created


def setup_render(resolution):
    sc = bpy.context.scene
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x = r.resolution_y = resolution
    r.resolution_percentage = 100
    r.film_transparent = True
    r.use_compositing = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    sc.eevee.taa_render_samples = 64
    sc.eevee.use_shadows = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    if sc.world is None:
        sc.world = bpy.data.worlds.new(PREFIX + "WORLD")
    vl = bpy.context.view_layer
    vl.use_pass_z = True
    vl.use_pass_normal = True


def setup_compositor(depth_min, depth_max):
    """Contornos discretos: Sobel sobre normal, profundidade e alpha; bloom suave nos cristais."""
    sc = bpy.context.scene
    tree = bpy.data.node_groups.new(COMPOSITOR, "CompositorNodeTree")
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n = tree.nodes
    rl = n.new("CompositorNodeRLayers")
    rl.location = (-900, 0)

    def sobel(src, x, y):
        f = n.new("CompositorNodeFilter")
        f.location = (x, y)
        f.inputs["Type"].default_value = "Sobel"
        link(tree, src, f.inputs["Image"])
        return f

    def threshold(src, lo, hi, x, y):
        m = n.new("ShaderNodeMapRange")
        m.location = (x, y)
        m.clamp = True
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = lo, hi
        link(tree, src, m.inputs["Value"])
        return m.outputs["Result"]

    def maximum(a, b, x, y):
        m = n.new("ShaderNodeMath")
        m.location = (x, y)
        m.operation = "MAXIMUM"
        link(tree, a, m.inputs[0])
        link(tree, b, m.inputs[1])
        return m.outputs[0]

    depth_norm = n.new("ShaderNodeMapRange")
    depth_norm.location = (-700, -250)
    depth_norm.clamp = True
    depth_norm.inputs["From Min"].default_value = depth_min - 0.05
    depth_norm.inputs["From Max"].default_value = depth_max + 0.05
    link(tree, rl.outputs["Depth"], depth_norm.inputs["Value"])

    e_normal = threshold(sobel(rl.outputs["Normal"], -500, 100).outputs["Image"], 1.6, 3.2, -300, 100)
    e_depth = threshold(sobel(depth_norm.outputs["Result"], -500, -250).outputs["Image"], 0.10, 0.30, -300, -250)
    e_alpha = threshold(sobel(rl.outputs["Alpha"], -500, -450).outputs["Image"], 0.4, 1.6, -300, -450)
    edges = maximum(maximum(e_normal, e_depth, -100, 0), e_alpha, 50, -150)
    opacity = n.new("ShaderNodeMath")
    opacity.location = (200, -150)
    opacity.operation = "MULTIPLY"
    opacity.inputs[1].default_value = LINE_OPACITY
    link(tree, edges, opacity.inputs[0])

    glare = n.new("CompositorNodeGlare")
    glare.location = (-500, 350)
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Highlights Threshold"].default_value = 1.0
    glare.inputs["Strength"].default_value = 0.35
    glare.inputs["Size"].default_value = 0.45
    link(tree, rl.outputs["Image"], glare.inputs["Image"])

    lines = n.new("CompositorNodeSetAlpha")
    lines.location = (400, -100)
    lines.inputs["Type"].default_value = "Apply Mask"
    lines.inputs["Image"].default_value = LINE_COLOR
    link(tree, opacity.outputs[0], lines.inputs["Alpha"])

    over = n.new("CompositorNodeAlphaOver")
    over.location = (600, 150)
    link(tree, glare.outputs["Image"], over.inputs["Background"])
    link(tree, lines.outputs["Image"], over.inputs["Foreground"])
    out = n.new("NodeGroupOutput")
    out.location = (800, 150)
    link(tree, over.outputs["Image"], out.inputs["Image"])
    sc.compositing_node_group = tree


def main():
    args = parse_args()
    check_file()
    obj = character_object()
    polys_before = len(obj.data.polygons)
    uv_before = [uv.name for uv in obj.data.uv_layers]
    mesh_mats_before = [m.name if m else None for m in obj.data.materials]

    cleanup()
    coll = new_collection()
    pts, mn, mx = world_points(obj)
    center = (mn + mx) / 2
    height = mx.z - mn.z
    _, dmin, dmax = setup_camera(coll, pts, center, args.azimuth, args.elevation, args.resolution)
    setup_lights(coll, center, height)
    created = assign_materials(obj)
    setup_render(args.resolution)
    setup_compositor(dmin, dmax)

    assert len(obj.data.polygons) == polys_before, "malha alterada"
    assert [uv.name for uv in obj.data.uv_layers] == uv_before, "UV alterado"
    assert [m.name if m else None for m in obj.data.materials] == mesh_mats_before, "materiais da malha alterados"
    print(f"[explore] objeto={obj.name} faces={polys_before} materiais={created}")

    if not args.no_render:
        out = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print(f"[explore] render salvo em {out}")
    if not args.no_save:
        bpy.ops.wm.save_mainfile()
        print(f"[explore] arquivo de trabalho salvo: {bpy.data.filepath}")


if __name__ == "__main__":
    main()
