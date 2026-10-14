extends Node2D

const PlayerScript = preload("res://scripts/player.gd")
const WORLD_SIZE := Vector2(1800, 1200)
const INTERACTION_RANGE := 105.0

var player: CharacterBody2D
var info_label: Label
var hint_label: Label
var near_target := -1
var objects: Array[Dictionary] = []
var is_tavorko := false

func _ready() -> void:
    is_tavorko = GameState.protagonist_id == "tavorko"
    if GameState.protagonist_id == "":
        get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
        return
    _make_objects()
    _make_player()
    _make_hud()
    queue_redraw()

func _make_objects() -> void:
    if is_tavorko:
        objects = [
            {"pos": Vector2(370,350), "type":"tree", "text":"Árvore Ancestral: suas raízes sustentam a Vila das Trocas."},
            {"pos": Vector2(670,260), "type":"tree", "text":"Ninhos abandonados: as famílias deixaram o mercado após o decreto."},
            {"pos": Vector2(1050,390), "type":"stall", "text":"Mercador: antes trocávamos frutas por ferramentas. O Conselho proibiu as trocas."},
            {"pos": Vector2(1370,600), "type":"guard", "text":"Soldado do Conselho: circulação restrita! O primeiro combate chega na V0.2."},
            {"pos": Vector2(430,860), "type":"tree", "text":"Uma passagem entre as copas parece levar para outra região."},
            {"pos": Vector2(1050,910), "type":"crystal", "text":"Cristal do vento: parece reagir ao arco de Tavorko."}
        ]
    else:
        objects = [
            {"pos": Vector2(360,340), "type":"tree", "text":"Bosque Esmeralda: um dos poucos lugares ainda livres do Conselho."},
            {"pos": Vector2(720,280), "type":"crystal", "text":"Cristal Esmeralda: pertence aos artesãos da vila. Foi marcado para confisco."},
            {"pos": Vector2(1050,430), "type":"stall", "text":"Artesão: querem tomar todos os cristais, inclusive os que nós extraímos!"},
            {"pos": Vector2(1390,620), "type":"guard", "text":"Soldado do Conselho: entregue seus cristais! O primeiro combate chega na V0.2."},
            {"pos": Vector2(410,860), "type":"tree", "text":"Esta floresta guarda antigos caminhos entre as regiões."},
            {"pos": Vector2(1040,910), "type":"crystal", "text":"O cristal vibra: talvez Verddro possa despertar a Fúria Esmeralda."}
        ]
    for obj in objects:
        if obj["type"] == "guard" or obj["type"] == "tree" or obj["type"] == "stall":
            var body := StaticBody2D.new()
            body.position = obj["pos"]
            var shape := CollisionShape2D.new()
            var circle := CircleShape2D.new()
            circle.radius = 37.0 if obj["type"] == "tree" else 32.0
            shape.shape = circle
            body.add_child(shape)
            add_child(body)
    for side in range(4):
        var wall := StaticBody2D.new()
        var collider := CollisionShape2D.new()
        var rect := RectangleShape2D.new()
        if side < 2:
            rect.size = Vector2(WORLD_SIZE.x + 60, 60)
            wall.position = Vector2(WORLD_SIZE.x / 2.0, -30 if side == 0 else WORLD_SIZE.y + 30)
        else:
            rect.size = Vector2(60, WORLD_SIZE.y + 60)
            wall.position = Vector2(-30 if side == 2 else WORLD_SIZE.x + 30, WORLD_SIZE.y / 2.0)
        collider.shape = rect
        wall.add_child(collider)
        add_child(wall)

func _make_player() -> void:
    player = CharacterBody2D.new()
    player.set_script(PlayerScript)
    player.set("hero_id", GameState.protagonist_id)
    player.position = Vector2(250, 620)
    var collider := CollisionShape2D.new()
    var shape := CircleShape2D.new()
    shape.radius = 16
    collider.shape = shape
    player.add_child(collider)
    add_child(player)
    var camera := Camera2D.new()
    camera.zoom = Vector2(1.12, 1.12)
    camera.position_smoothing_enabled = true
    camera.position_smoothing_speed = 6.0
    camera.limit_left = 0
    camera.limit_top = 0
    camera.limit_right = int(WORLD_SIZE.x)
    camera.limit_bottom = int(WORLD_SIZE.y)
    player.add_child(camera)
    camera.make_current()

func _make_hud() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var ui := Control.new()
    ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(ui)
    ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var top := PanelContainer.new()
    top.position = Vector2(18,18)
    top.custom_minimum_size = Vector2(580,80)
    ui.add_child(top)
    var head := Label.new()
    head.text = ("TAVORKO  •  Vila das Trocas" if is_tavorko else "VERDDRO  •  Bosque Esmeralda") + "\nWASD / setas: mover   •   E: interagir   •   ESC: menu"
    head.add_theme_font_size_override("font_size", 19)
    top.add_child(head)
    var panel := PanelContainer.new()
    panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
    panel.offset_left = 24
    panel.offset_right = -24
    panel.offset_top = -125
    panel.offset_bottom = -24
    ui.add_child(panel)
    info_label = Label.new()
    info_label.text = "Explore a região e aproxime-se dos locais marcados. Protótipo V0.1."
    info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    info_label.add_theme_font_size_override("font_size", 19)
    panel.add_child(info_label)
    hint_label = Label.new()
    hint_label.position = Vector2(24,104)
    hint_label.add_theme_font_size_override("font_size", 18)
    ui.add_child(hint_label)

func _process(_delta: float) -> void:
    near_target = -1
    var closest := INTERACTION_RANGE
    for i in range(objects.size()):
        var dist: float = player.position.distance_to(objects[i]["pos"])
        if dist < closest:
            near_target = i
            closest = dist
    hint_label.text = "[E] Examinar: " + _object_name(objects[near_target]["type"]) if near_target >= 0 else ""

func _unhandled_key_input(event: InputEvent) -> void:
    if not (event is InputEventKey) or not event.pressed or event.echo:
        return
    if event.keycode == KEY_ESCAPE:
        get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
    elif event.keycode == KEY_E and near_target >= 0:
        info_label.text = objects[near_target]["text"]

func _object_name(kind: String) -> String:
    match kind:
        "tree": return "Árvore"
        "crystal": return "Cristal"
        "stall": return "Habitante"
        "guard": return "Soldado"
    return "Objeto"

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO,WORLD_SIZE), Color("547f69") if is_tavorko else Color("638563"))
    for y in range(0, 1200, 120):
        for x in range(0, 1800, 120):
            draw_colored_polygon(PackedVector2Array([Vector2(x,y+54),Vector2(x+70,y+10),Vector2(x+122,y+54),Vector2(x+52,y+98)]), Color(0.32,0.48,0.37,0.17))
    var road := PackedVector2Array([Vector2(100,560),Vector2(450,510),Vector2(840,560),Vector2(1160,530),Vector2(1680,670),Vector2(1680,790),Vector2(1140,635),Vector2(840,660),Vector2(460,610),Vector2(100,675)])
    draw_colored_polygon(road,Color("bea77a") if is_tavorko else Color("a9a17c"))
    for i in range(objects.size()):
        var obj := objects[i]
        var p: Vector2 = obj["pos"]
        match obj["type"]:
            "tree":
                draw_circle(p+Vector2(0,18),42,Color(0.08,0.2,0.14,0.35))
                draw_rect(Rect2(p+Vector2(-8,-44),Vector2(16,50)),Color("654a35"))
                draw_circle(p+Vector2(0,-48),45,Color("244e3d"))
                draw_circle(p+Vector2(-15,-68),25,Color("49876a"))
            "crystal":
                draw_colored_polygon(PackedVector2Array([p+Vector2(0,-55),p+Vector2(26,-20),p+Vector2(14,8),p+Vector2(-16,10),p+Vector2(-28,-20)]), Color("66e5a6") if not is_tavorko else Color("71d7ef"))
                draw_line(p+Vector2(0,-53),p+Vector2(0,5),Color("e4ffca"),2)
            "stall":
                draw_rect(Rect2(p+Vector2(-31,-24),Vector2(62,45)),Color("805741"))
                draw_colored_polygon(PackedVector2Array([p+Vector2(-41,-24),p+Vector2(0,-53),p+Vector2(41,-24)]),Color("e4bc70"))
            "guard":
                draw_circle(p+Vector2(0,-14),21,Color("ad4f49"))
                draw_rect(Rect2(p+Vector2(-17,-13),Vector2(34,31)),Color("5a303b"))
                draw_line(p+Vector2(25,-40),p+Vector2(25,16),Color("dfd4ac"),4)
                draw_colored_polygon(PackedVector2Array([p+Vector2(18,-43),p+Vector2(32,-43),p+Vector2(25,-59)]),Color("c7d0c7"))
