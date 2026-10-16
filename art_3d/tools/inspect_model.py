"""Diagnóstico técnico de malhas para Le Cronache del Diamante (somente leitura).

Uso (Blender em modo background):
  blender -b --factory-startup --disable-autoexec <arquivo.blend> --python art_3d/tools/inspect_model.py -- --output <relatorio.json>
  blender -b --factory-startup --disable-autoexec --python art_3d/tools/inspect_model.py -- --input <modelo.glb> --output <relatorio.json>

O script nunca salva o .blend nem aplica modificadores: lê cópias da malha via bmesh.
"""
import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

GAME_TRI_BUDGET = 30000
HIGH_TRI_WARNING = 100000
TINY_ISLAND_VERTS = 50
MERGE_DISTANCE = 1e-5
DEGENERATE_AREA = 1e-10
MIRROR_TOLERANCE_RATIO = 0.005


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Arquivo .glb/.gltf/.fbx/.obj a importar. Omitir para usar o .blend aberto.")
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def load_input(path):
    if not path:
        return bpy.data.filepath
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise SystemExit(f"Formato não suportado: {ext}")
    return path


def r(v, n=4):
    return round(float(v), n)


def vec(v):
    return [r(c) for c in v]


def islands(bm):
    parent = list(range(len(bm.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    return sorted(Counter(find(i) for i in range(len(bm.verts))).values(), reverse=True)


def duplicate_vertices(bm):
    kd = KDTree(len(bm.verts))
    for v in bm.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    dup = 0
    for v in bm.verts:
        if any(idx < v.index for _, idx, _ in kd.find_range(v.co, MERGE_DISTANCE)):
            dup += 1
    return dup


def mirror_symmetry(world_verts, world_polys, size_x, height):
    """Espelha uma amostra de vértices no plano X central e mede a distância até a superfície."""
    if not world_verts:
        return None
    center_x = sum(v.x for v in world_verts) / len(world_verts)
    bvh = BVHTree.FromPolygons(world_verts, world_polys)
    step = max(1, len(world_verts) // 20000)
    sample = world_verts[::step]
    dists = sorted(bvh.find_nearest(Vector((2 * center_x - v.x, v.y, v.z)))[3] for v in sample)
    result = {"center_x": r(center_x), "sampled_vertices": len(sample),
              "median_distance": r(dists[len(dists) // 2], 5), "p90_distance": r(dists[int(len(dists) * 0.9)], 5)}
    for label, ratio in (("ratio_within_0_5pct_width", MIRROR_TOLERANCE_RATIO), ("ratio_within_2pct_height", None)):
        tol = max(size_x, 1e-6) * ratio if ratio else height * 0.02
        result[label] = r(sum(1 for d in dists if d <= tol) / len(dists), 3)
    result["mirrored_ratio"] = result["ratio_within_0_5pct_width"]
    return result


def material_info(mat):
    images = []
    if mat and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                img = node.image
                images.append({"name": img.name, "size": list(img.size), "packed": img.packed_file is not None, "filepath": img.filepath})
    return {"name": mat.name if mat else None, "images": images}


def analyze_mesh(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    face_sizes = Counter("tri" if len(f.verts) == 3 else "quad" if len(f.verts) == 4 else "ngon" for f in bm.faces)
    isl = islands(bm)
    nm_edges = [e for e in bm.edges if not e.is_manifold]
    result = {
        "name": obj.name,
        "mesh_data": me.name,
        "counts": {"vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces), "triangles": tris,
                   "tris": face_sizes["tri"], "quads": face_sizes["quad"], "ngons": face_sizes["ngon"]},
        "transform": {"location": vec(obj.location), "rotation_euler_deg": [r(math.degrees(a), 2) for a in obj.rotation_euler],
                      "scale": vec(obj.scale), "parent": obj.parent.name if obj.parent else None},
        "materials": [material_info(s.material) for s in obj.material_slots],
        "uv_maps": [uv.name for uv in me.uv_layers],
        "color_attributes": [c.name for c in me.color_attributes],
        "modifiers": [{"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render} for m in obj.modifiers],
        "shape_keys": [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
        "vertex_groups": len(obj.vertex_groups),
        "components": {"count": len(isl), "largest_vertices": isl[:10],
                       "tiny_islands": sum(1 for s in isl if s <= TINY_ISLAND_VERTS), "tiny_threshold_vertices": TINY_ISLAND_VERTS},
        "manifold": {
            "non_manifold_edges": len(nm_edges),
            "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
            "edges_more_than_2_faces": sum(1 for e in bm.edges if len(e.link_faces) > 2),
            "wire_edges": sum(1 for e in bm.edges if e.is_wire),
            "non_manifold_vertices": sum(1 for v in bm.verts if not v.is_manifold),
            "loose_vertices": sum(1 for v in bm.verts if not v.link_edges),
            "inconsistent_normal_edges": sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous),
            "zero_area_faces": sum(1 for f in bm.faces if f.calc_area() < DEGENERATE_AREA),
            "zero_length_edges": sum(1 for e in bm.edges if e.calc_length() < MERGE_DISTANCE),
            "duplicate_vertices": duplicate_vertices(bm),
            "merge_distance": MERGE_DISTANCE,
        },
    }
    world = [obj.matrix_world @ v.co for v in bm.verts]
    polys = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return result, world, polys


def build_issues(report):
    issues = []

    def add(severity, area, message):
        issues.append({"severity": severity, "area": area, "message": message})

    t = report["totals"]
    if t["triangles"] > HIGH_TRI_WARNING:
        add("high", "retopology", f"{t['triangles']} triângulos: muito acima do orçamento de jogo (~{GAME_TRI_BUDGET}). Retopologia necessária.")
    elif t["triangles"] > GAME_TRI_BUDGET:
        add("medium", "retopology", f"{t['triangles']} triângulos: acima do orçamento sugerido (~{GAME_TRI_BUDGET}).")
    if t["faces"] and t["tris"] / t["faces"] > 0.9:
        add("high", "retopology", "Malha quase toda triangulada (típico de IA/fotogrametria): sem fluxo de arestas para deformação; refazer em quads.")
    if t["ngons"]:
        add("medium", "retopology", f"{t['ngons']} n-gons: deformam mal e triangulam de forma imprevisível.")
    if t["components"] > 1:
        add("medium", "rigging", f"{t['components']} componentes desconectados ({t['tiny_islands']} pequenos): peças soltas precisam ser unidas, removidas ou parentadas ao osso correto.")
    if t["non_manifold_edges"] or t["non_manifold_vertices"]:
        add("high" if t["edges_more_than_2_faces"] else "medium", "geometry",
            f"Geometria não manifold: {t['non_manifold_edges']} arestas ({t['boundary_edges']} de borda, {t['edges_more_than_2_faces']} com >2 faces), {t['non_manifold_vertices']} vértices.")
    if t["inconsistent_normal_edges"]:
        add("medium", "geometry", f"{t['inconsistent_normal_edges']} arestas com normais inconsistentes (faces invertidas).")
    if t["duplicate_vertices"]:
        add("medium", "geometry", f"{t['duplicate_vertices']} vértices duplicados (distância < {MERGE_DISTANCE}).")
    if t["zero_area_faces"] or t["zero_length_edges"]:
        add("low", "geometry", f"Geometria degenerada: {t['zero_area_faces']} faces de área zero, {t['zero_length_edges']} arestas de comprimento zero.")
    if t["loose_vertices"] or t["wire_edges"]:
        add("low", "geometry", f"{t['loose_vertices']} vértices soltos e {t['wire_edges']} arestas sem face.")
    for m in report["meshes"]:
        n = m["name"]
        if not m["uv_maps"]:
            add("high", "uv", f"{n}: sem UV Map.")
        elif len(m["uv_maps"]) > 1:
            add("low", "uv", f"{n}: {len(m['uv_maps'])} UV Maps ({', '.join(m['uv_maps'])}).")
        if m["modifiers"]:
            add("info", "modifiers", f"{n}: modificadores não aplicados: {', '.join(x['type'] for x in m['modifiers'])}.")
        s, rot = m["transform"]["scale"], m["transform"]["rotation_euler_deg"]
        if any(abs(c - 1) > 1e-4 for c in s) or any(abs(a) > 1e-3 for a in rot):
            add("medium", "rigging", f"{n}: transformações não aplicadas (escala {s}, rotação {rot}°). Aplicar antes do rigging.")
        if not m["materials"]:
            add("low", "materials", f"{n}: sem material.")
    d = report["dimensions"]
    if d:
        if abs(d["min"][2]) > 0.01 * max(d["size"][2], 1e-6):
            add("low", "rigging", f"Base do personagem em Z={d['min'][2]}: idealmente os pés ficam em Z=0.")
        if not 0.3 < d["size"][2] < 5:
            add("medium", "scale", f"Altura {d['size'][2]} m fora da faixa plausível; conferir unidade/escala.")
        sym = report.get("symmetry")
        if sym and sym["ratio_within_2pct_height"] < 0.8:
            add("medium", "rigging", f"Pose/forma assimétrica no eixo X (só {sym['ratio_within_2pct_height']:.0%} da superfície espelhada a menos de 2% da altura): dificulta Symmetrize, pesos espelhados e retopologia simétrica.")
    used_images = {i["name"] for m in report["meshes"] for mt in m["materials"] for i in mt["images"]}
    texture_images = [i for i in report["images"] if i["source"] != "VIEWER"]
    if texture_images and not used_images:
        add("medium", "materials", f"{len(texture_images)} textura(s) no arquivo, mas nenhuma ligada ao material da malha.")
    if not used_images:
        add("high", "materials", "Nenhuma textura ligada à malha: as cores da referência não estão no modelo (o GLB do Meshy foi exportado sem textura/UV).")
    unused = [m["name"] for m in report["materials"] if m["users"] == 0]
    if unused:
        add("low", "materials", f"Materiais sem uso no arquivo: {', '.join(unused)}.")
    if not report["armatures"]:
        add("info", "rigging", "Nenhuma armature na cena: rigging ainda não iniciado.")
    return issues


def main():
    args = parse_args()
    source = load_input(args.input)
    objects = list(bpy.data.objects)
    mesh_objs = [o for o in objects if o.type == "MESH"]
    meshes, world_verts, world_polys = [], [], []
    for obj in mesh_objs:
        data, world, polys = analyze_mesh(obj)
        meshes.append(data)
        base = len(world_verts)
        world_polys.extend([[i + base for i in p] for p in polys])
        world_verts.extend(world)

    totals = Counter()
    for m in meshes:
        totals.update(m["counts"])
        totals.update({k: v for k, v in m["manifold"].items() if isinstance(v, int)})
        totals["components"] += m["components"]["count"]
        totals["tiny_islands"] += m["components"]["tiny_islands"]

    dims = None
    if world_verts:
        mn = Vector((min(v.x for v in world_verts), min(v.y for v in world_verts), min(v.z for v in world_verts)))
        mx = Vector((max(v.x for v in world_verts), max(v.y for v in world_verts), max(v.z for v in world_verts)))
        size = mx - mn
        dims = {"min": vec(mn), "max": vec(mx), "size": vec(size), "unit": bpy.context.scene.unit_settings.system,
                "scale_length": r(bpy.context.scene.unit_settings.scale_length),
                "width_to_height": r(size.x / size.z, 3) if size.z else None}

    all_mats = {s.material.name for o in mesh_objs for s in o.material_slots if s.material}
    report = {
        "tool": "art_3d/tools/inspect_model.py",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "source": os.path.relpath(source, os.getcwd()) if source else None,
        "scene": {
            "objects": len(objects),
            "objects_by_type": dict(Counter(o.type for o in objects)),
            "mesh_objects": len(mesh_objs),
            "mesh_datablocks": len(bpy.data.meshes),
            "materials_in_file": len(bpy.data.materials),
            "materials_used_by_meshes": len(all_mats),
            "images": len(bpy.data.images),
        },
        "armatures": [o.name for o in objects if o.type == "ARMATURE"],
        "totals": dict(totals),
        "dimensions": dims,
        "symmetry": mirror_symmetry(world_verts, world_polys, dims["size"][0], dims["size"][2]) if dims else None,
        "materials": [{"name": m.name, "users": m.users, "fake_user": m.use_fake_user} for m in bpy.data.materials],
        "images": [{"name": i.name, "size": list(i.size), "packed": i.packed_file is not None, "filepath": i.filepath,
                    "users": i.users, "source": i.source} for i in bpy.data.images],
        "meshes": meshes,
    }
    report["issues"] = build_issues(report)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[inspect_model] relatório salvo em {args.output}")


if __name__ == "__main__":
    main()
