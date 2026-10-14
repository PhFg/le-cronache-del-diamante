# Direção de Arte — V0.2

## Estilo visual oficial
- **2.25D ilustrado** (nome interno da direção de arte, não uma classificação técnica do motor).
- **Exploração:** composição pictórica, com cenários de profundidade e iluminação.
- **Batalhas:** linguagem gráfica expressiva e efeitos cinematográficos.

## Personagens
Os personagens são baseados nas construções originais de LEGO, reinterpretados como criaturas de animação.

| Personagem | Espécie | Personalidade |
|---|---|---|
| **Verddro** | Dragão esmeralda | Valente e impulsivo |
| **Tavorko** | Papagaio arqueiro | Sério e determinado |

### Referência de qualidade
A primeira ficha individual de **Tavorko** é a referência principal de maturidade e acabamento visual. Toda nova arte de personagem deve ser comparada a ela.

## Animação de exploração

### Direções
Movimentação em oito direções: **N, NE, E, SE, S, SW, W, NW**.

### Estados previstos
| Estado | Pasta |
|---|---|
| idle | `exploration/idle/` |
| walk | `exploration/walk/` |
| run | `exploration/run/` |
| interact | `exploration/interact/` |

### Consistência
Manter consistência de **escala, proporções, cores e silhueta** entre todos os frames, direções e estados.

## Organização dos assets
```
assets/characters/<personagem>/
  concept/        # artes conceituais e fichas
  exploration/
    idle/
    walk/
    run/
    interact/
  portraits/      # retratos para diálogos e menus
```

## Especificações técnicas dos sprites de exploração

### Arquitetura na Godot
- O jogador continua sendo o `CharacterBody2D` criado por `world.gd` com `scripts/player.gd`.
- O componente visual é um `AnimatedSprite2D` controlado por `scripts/characters/character_visual.gd` (`CharacterVisual`).
- O componente não lê teclado nem mouse: recebe velocidade e ações de quem o controla (jogador local, rede ou IA).
- **Fallback:** se o personagem não tiver `SpriteFrames` válido (sem a animação `idle_s`), o desenho geométrico da V0.1 continua sendo usado.
- Colisão (círculo de raio 16), velocidade, câmera e interação não mudam.

### Quadros PNG
| Item | Especificação |
|---|---|
| Tamanho do quadro | **256 × 256 px** |
| Fundo | Transparente (PNG RGBA, sRGB) |
| Altura do personagem no quadro | ~200–220 px |
| Ponto dos pés (âncora) | **(128, 236)** — fixo em todos os quadros, direções e estados |
| Margem de segurança | ≥ 8 px em todos os lados (asas, cauda, arco) |
| Arte mestre | 1024 px, guardada em `concept/` para reexportação |

### Escala na tela
- Altura visual-alvo: **~100–110 px** na tela base de 1280 × 720.
- Com o zoom da câmera (1.12), isso corresponde a ~90–98 px no mundo.
- Escala inicial do sprite: **0.45** (`visual_scale`), ajustável após validação no Bosque Esmeralda.
- A âncora dos pés coincide com a origem do `CharacterBody2D` (`offset = -foot_anchor`, `centered = false`).

### Convenção de animações
- Nome: `estado_direção`, em minúsculas: `idle_n`, `walk_ne`, `run_sw`, `interact_w`.
- Direções: `n`, `ne`, `e`, `se`, `s`, `sw`, `w`, `nw` (8 setores de 45°).
- Ao parar, o personagem mantém a última direção.
- Animação ausente: `run` → `walk` → `idle`; `interact` → `idle`.

| Estado | Quadros sugeridos | FPS | Loop |
|---|---|---|---|
| idle | 6 | 6 | sim |
| walk | 8 | 10–12 | sim |
| run | 8 | 14–16 | sim |
| interact | 6 | 10 | **não** |

### Arquivos
```
assets/characters/<personagem>/exploration/<estado>/<personagem>_<estado>_<direção>.png   (tira horizontal de quadros 256 px)
assets/characters/<personagem>/<personagem>_exploration.tres                              (SpriteFrames)
```
Exemplo: `assets/characters/verddro/exploration/walk/verddro_walk_ne.png` (8 quadros → 2048 × 256).

### Importação
- Filtro **Linear** com **mipmaps** ativados nas texturas de personagem (evita serrilhado na redução).
- Espelhamento horizontal (W/NW/SW a partir de E/NE/SE) **não** é usado para Tavorko (o arco trocaria de mão); para Verddro, avaliar caso a caso.

### Etapas futuras da V0.2
- Corrida com Shift, após validação de idle e walk.
- Y-Sort entre personagem e objetos do cenário.
