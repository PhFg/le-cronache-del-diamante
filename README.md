# Le Cronache del Diamante
## Il Risveglio della Libertà

Jogo RPG original em desenvolvimento com Godot 4 e GDScript. Direção artística proposta: 2.25D — exploração pictórica e batalhas expressivas.

## Primeira execução
1. Instale a versão estável da Godot 4.x (recomendado 4.3 ou mais recente).
2. Extraia este projeto e importe o arquivo `project.godot` pelo Project Manager.
3. Abra o projeto e pressione F6 na cena `scenes/main_menu.tscn` ou F5 para executar o projeto.
4. Clique em Verddro ou Tavorko. A escolha será registrada em `GameState` nesta sessão.

**Estado atual:** V0.0 — tela funcional de seleção; ainda sem mapa, arte final, batalha ou salvamento. Os textos são temporários. 

## Próximos marcos
- V0.1: cena de exploração 2.25D, duas origens e movimentação
- V0.2: protótipo do sistema de batalha por turnos
- V0.3: missão inicial `Il Primo Decreto`

Consultar `docs/` antes de ampliar a implementação.

## V0.1 — Il Primo Decreto (prototype)

After choosing Verddro or Tavorko, the game transitions to a distinct playable origin region. Move with WASD or arrows, interact with E when close to an object, and return to the menu with Escape. Scenery and characters are procedural placeholders for validating exploration, collisions and camera behavior before final 2.25D artwork. Battle, quests and multiplayer are not implemented yet.

To run: import `project.godot` in Godot 4.3+ and press F5. No external dependencies or asset downloads are needed.
