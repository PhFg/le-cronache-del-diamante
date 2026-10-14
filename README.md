# Le Cronache del Diamante
## Il Risveglio della Libertà

Jogo RPG original em desenvolvimento com Godot 4.7 e GDScript. Direção artística: 2.25D ilustrado — exploração pictórica e batalhas expressivas.

## Primeira execução
1. Instale a Godot 4.7 (versão oficial de desenvolvimento do projeto).
2. Extraia este projeto e importe o arquivo `project.godot` pelo Project Manager.
3. Abra o projeto e pressione F6 na cena `scenes/main_menu.tscn` ou F5 para executar o projeto.
4. Clique em Verddro ou Tavorko. A escolha será registrada em `GameState` nesta sessão.

Não há dependências externas nem downloads de assets.

### Controles
- **WASD / setas:** mover (oito direções)
- **E:** interagir quando próximo de um objeto
- **Esc:** voltar ao menu

## Estado do desenvolvimento

| Versão | Escopo | Situação |
|---|---|---|
| V0.0 | Fundação do projeto | ✅ Concluída |
| V0.1 | Seleção dos protagonistas, exploração e interação | ✅ Concluída e validada |
| V0.2 | Produção artística e animação dos personagens | 🚧 Em desenvolvimento |
| V0.3 | **Il Primo Scontro** — primeiro sistema de batalha por turnos interativos | Planejada |
| Futuro | Multiplayer cooperativo | Expansão futura, não implementada |

### V0.1 — Il Primo Decreto (protótipo)
Após escolher Verddro ou Tavorko, o jogo leva a uma região de origem jogável própria: Bosque Esmeralda (Verddro) ou Vila das Trocas (Tavorko). Inclui movimentação, colisões, câmera que acompanha o personagem e interação com objetos e habitantes. Os cenários ainda são provisórios, desenhados por código.

### V0.2 — em andamento
- **Verddro** já possui o primeiro sprite ilustrado integrado e validado visualmente.
- **Tavorko** ainda utiliza temporariamente seu desenho geométrico.
- A movimentação em oito direções já está implementada; as animações ilustradas (idle, walk, run e interact) ainda estão sendo produzidas.
- Especificações de arte em `docs/ART_DIRECTION.md`; roteiro de testes em `docs/V0.2_TEST_PLAN.md`.

Ainda não implementados: batalha, missões, salvamento e multiplayer.

Consultar `docs/` antes de ampliar a implementação.
