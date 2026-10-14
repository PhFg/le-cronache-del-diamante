extends Node

var protagonist_id: String = ""

func choose_protagonist(id: String) -> void:
    if id not in ["verddro", "tavorko"]:
        push_warning("Protagonista desconhecido: " + id)
        return
    protagonist_id = id
