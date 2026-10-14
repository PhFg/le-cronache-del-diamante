extends Control

@onready var status_label: Label = $Center/VBox/Status

func _ready() -> void:
    $Center/VBox/VerddroButton.pressed.connect(_choose_verddro)
    $Center/VBox/TavorkoButton.pressed.connect(_choose_tavorko)

func _choose_verddro() -> void:
    GameState.choose_protagonist("verddro")
    status_label.text = "Verddro escolhido! História de origem em desenvolvimento."

func _choose_tavorko() -> void:
    GameState.choose_protagonist("tavorko")
    status_label.text = "Tavorko escolhido! História de origem em desenvolvimento."
