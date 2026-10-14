extends CharacterBody2D

const SPEED := 220.0
var hero_id := "verddro"
var walk_time := 0.0

func _physics_process(delta: float) -> void:
    var direction := Vector2.ZERO
    if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): direction.x -= 1.0
    if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): direction.x += 1.0
    if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): direction.y -= 1.0
    if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): direction.y += 1.0
    velocity = direction.normalized() * SPEED
    move_and_slide()
    if velocity.length() > 0.1:
        walk_time += delta * 12.0
    queue_redraw()

func _draw() -> void:
    var bob := sin(walk_time) * 2.0 if velocity.length() > 0.1 else 0.0
    draw_ellipse_shadow()
    if hero_id == "tavorko":
        draw_colored_polygon(PackedVector2Array([Vector2(-21,-26+bob),Vector2(-7,-42+bob),Vector2(17,-37+bob),Vector2(25,-17+bob),Vector2(0,-6+bob)]), Color("e9ae3e"))
        draw_circle(Vector2(0,-25+bob), 17, Color("df453b"))
        draw_circle(Vector2(-4,-30+bob), 7, Color("f7ecb6"))
        draw_circle(Vector2(-6,-31+bob), 2, Color("142629"))
        draw_colored_polygon(PackedVector2Array([Vector2(9,-24+bob),Vector2(29,-18+bob),Vector2(10,-13+bob)]), Color("f4c64b"))
        draw_line(Vector2(18,-48+bob),Vector2(29,-1+bob), Color("5d3527"), 3.0)
        draw_line(Vector2(18,-48+bob),Vector2(34,-25+bob), Color("fbf0cc"), 1.5)
        draw_line(Vector2(34,-25+bob),Vector2(29,-1+bob), Color("fbf0cc"), 1.5)
    else:
        draw_colored_polygon(PackedVector2Array([Vector2(-13,-9+bob),Vector2(-24,-31+bob),Vector2(-9,-52+bob),Vector2(15,-44+bob),Vector2(21,-16+bob),Vector2(8,-7+bob)]), Color("329765"))
        draw_colored_polygon(PackedVector2Array([Vector2(-10,-41+bob),Vector2(-15,-58+bob),Vector2(0,-47+bob),Vector2(12,-59+bob),Vector2(13,-39+bob)]), Color("a8db78"))
        draw_circle(Vector2(7,-36+bob), 3.5, Color("f9edbd"))
        draw_circle(Vector2(8,-36+bob), 1.7, Color("102a25"))
        draw_colored_polygon(PackedVector2Array([Vector2(15,-30+bob),Vector2(30,-23+bob),Vector2(11,-19+bob)]), Color("b0d46e"))
        draw_colored_polygon(PackedVector2Array([Vector2(-17,-22+bob),Vector2(-31,-36+bob),Vector2(-28,-12+bob)]), Color("58bc81"))

func draw_ellipse_shadow() -> void:
    draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0,0.38))
    draw_circle(Vector2(0,4), 22, Color(0.04,0.12,0.10,0.32))
    draw_set_transform(Vector2.ZERO)
