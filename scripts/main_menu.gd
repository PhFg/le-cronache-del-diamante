extends Control

@onready var status_label: Label = $Center/VBox/Status

func _ready() -> void:
    $Center/VBox/VerddroButton.pressed.connect(_choose_verddro)
    $Center/VBox/TavorkoButton.pressed.connect(_choose_tavorko)

func _choose_verddro() -> void:
    GameState.choose_protagonist("verddro")
    get_tree().change_scene_to_file("res://scenes/world.tscn")

func _choose_tavorko() -> void:
    GameState.choose_protagonist("tavorko")
    get_tree().change_scene_to_file("res://scenes/world.tscn")
