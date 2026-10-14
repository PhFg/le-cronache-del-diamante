class_name CharacterVisual
extends AnimatedSprite2D

## Componente visual reutilizável para personagens de exploração.
## Não lê teclado nem mouse: recebe velocidade/estado de quem o controla
## (jogador local, rede ou IA).

signal facing_changed(direction: StringName)
signal action_finished(action: StringName)

const DIRECTIONS: Array[StringName] = [&"e", &"se", &"s", &"sw", &"w", &"nw", &"n", &"ne"]
const STATES: Array[StringName] = [&"idle", &"walk", &"run", &"interact"]
const FALLBACK_STATE := {&"run": &"walk", &"walk": &"idle", &"interact": &"idle"}
const DEFAULT_FRAMES_PATH := "res://assets/characters/%s/%s_exploration.tres"
const MOVE_THRESHOLD := 0.1

@export var character_id: StringName = &""
@export var frames_override: SpriteFrames
@export var foot_anchor := Vector2(128, 236)
@export var visual_scale := 0.45

var facing: StringName = &"s"
var state: StringName = &"idle"
var _action_playing := false

func _init() -> void:
    centered = false
    texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    animation_finished.connect(_on_animation_finished)

func _ready() -> void:
    if character_id != &"" and sprite_frames == null:
        setup(character_id, frames_override)

## Configura o personagem. Sem `frames`, procura o SpriteFrames padrão em
## DEFAULT_FRAMES_PATH. Retorna false quando não há arte (usar fallback).
func setup(id: StringName, frames: SpriteFrames = null) -> bool:
    character_id = id
    if frames == null:
        var path := DEFAULT_FRAMES_PATH % [id, id]
        if ResourceLoader.exists(path):
            frames = load(path) as SpriteFrames
    sprite_frames = frames
    centered = false
    offset = -foot_anchor
    scale = Vector2.ONE * visual_scale
    visible = has_frames()
    _refresh()
    return visible

func has_frames() -> bool:
    return sprite_frames != null and sprite_frames.has_animation(&"idle_s")

## Atualiza estado e direção a partir da velocidade. Parado, mantém o facing.
func update_movement(velocity: Vector2, moving_state: StringName = &"walk") -> void:
    if velocity.length() > MOVE_THRESHOLD:
        _action_playing = false
        _apply_facing(direction_from_vector(velocity))
        _set_state(moving_state)
    elif not _action_playing:
        _set_state(&"idle")

## Executa uma ação única (ex.: interact). Movimento a interrompe.
func play_action(action: StringName = &"interact") -> bool:
    if not has_frames() or _resolve_animation(action, facing) == &"":
        return false
    _action_playing = true
    _set_state(action)
    return true

func set_facing(direction: StringName) -> void:
    if direction in DIRECTIONS:
        _apply_facing(direction)

func is_action_playing() -> bool:
    return _action_playing

## 0=E, 1=SE, 2=S, 3=SW, 4=W, 5=NW, 6=N, 7=NE (eixo Y da Godot aponta para baixo).
static func direction_from_vector(v: Vector2) -> StringName:
    return DIRECTIONS[wrapi(roundi(v.angle() / (PI / 4.0)), 0, DIRECTIONS.size())]

static func animation_name(anim_state: StringName, direction: StringName) -> StringName:
    return StringName("%s_%s" % [anim_state, direction])

func _apply_facing(direction: StringName) -> void:
    if direction == facing:
        return
    facing = direction
    facing_changed.emit(facing)
    _refresh()

func _set_state(new_state: StringName) -> void:
    state = new_state
    _refresh()

func _resolve_animation(anim_state: StringName, direction: StringName) -> StringName:
    if sprite_frames == null:
        return &""
    var current: StringName = anim_state
    while current != &"":
        var anim_name := animation_name(current, direction)
        if sprite_frames.has_animation(anim_name):
            return anim_name
        current = FALLBACK_STATE.get(current, &"")
    return &""

func _refresh() -> void:
    if not has_frames():
        return
    var anim := _resolve_animation(state, facing)
    if anim == &"" or (anim == animation and is_playing()):
        return
    var keep_cycle := String(animation).get_slice("_", 0) == String(anim).get_slice("_", 0)
    var previous_frame := frame
    var previous_progress := frame_progress
    play(anim)
    if keep_cycle:
        set_frame_and_progress(mini(previous_frame, sprite_frames.get_frame_count(anim) - 1), previous_progress)

func _on_animation_finished() -> void:
    if not _action_playing:
        return
    _action_playing = false
    var finished := state
    _set_state(&"idle")
    action_finished.emit(finished)
