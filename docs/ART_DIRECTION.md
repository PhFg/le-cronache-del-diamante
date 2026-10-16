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

## Decisão oficial de exploração (V0.2)
Aprovada por Pedro e Gustavo após os estudos A/B/C e o teste A/B de resolução na Godot 4.7.

- **Look oficial: C — Híbrido.** Superfície pintada (pós-processo Kuwahara leve), cel shading de 3 tons com sombras coloridas, luz cinematográfica com foco em rosto e peito, contraluz menta, contornos verde-escuros hierarquizados e cristais esmeralda como únicos pontos com brilho/bloom.
- **Resolução oficial dos protagonistas: 384 × 384 px**, escala 0.30, âncora dos pés (192, 354).
- Motivo: em 1280 × 720 a 384 é equivalente à 256; em 1920 × 1080 e em telas de tablet é visivelmente mais nítida (a 256 precisaria ser ampliada em telas de ~2560 × 1600).
- Pipeline e referências: `art_3d/tools/setup_style_study.py` (`--style C`), `art_3d/verddro/renders/verddro_style_C_hybrid.png`, relatório `art_3d/verddro/renders/resolution_tests/`.
- O sprite-protótipo anterior (256 px, arte pré-Look C) está guardado em `art_3d/verddro/backups/v0.2_prototype_256/`, fora do jogo (pasta com `.gdignore`).

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
| Tamanho do quadro | **384 × 384 px** (protagonistas) |
| Fundo | Transparente (PNG RGBA, sRGB) |
| Altura do personagem no quadro | ~300–320 px |
| Ponto dos pés (âncora) | **(192, 354)** — fixo em todos os quadros, direções e estados. Em vista três quartos, é o ponto do chão entre os dois pés |
| Margem de segurança | ≥ 12 px em todos os lados (asas, cauda, arco) |
| Arte mestre | Render 1024 × 1024 do Look C, guardado em `art_3d/<personagem>/renders/` para reexportação |
| Personagens secundários | 256 × 256 px, âncora (128, 236), escala 0.45 (mesma altura na tela) |

### Escala na tela
- Altura visual-alvo: **~100–110 px** na tela base de 1280 × 720 (medido: ~107 px).
- Com o zoom da câmera (1.12), isso corresponde a ~90–98 px no mundo.
- Escala oficial do sprite: **0.30** (`visual_scale`, padrão do `CharacterVisual`).
- A âncora dos pés coincide com a origem do `CharacterBody2D` (`offset = -foot_anchor`, `centered = false`).

### Memória estimada (224 quadros por personagem, com mipmaps)
| | Sem compressão | Com compressão de VRAM (~8 bpp) |
|---|---|---|
| Por quadro 384 px | 768 KB | 192 KB |
| Por protagonista | ~168 MB | ~42 MB |
- Compressão de textura (VRAM) obrigatória nas exportações para tablet.

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
assets/characters/<personagem>/exploration/<estado>/<personagem>_<estado>_<direção>.png   (tira horizontal de quadros 384 px)
assets/characters/<personagem>/<personagem>_exploration.tres                              (SpriteFrames)
```
Exemplo: `assets/characters/verddro/exploration/walk/verddro_walk_ne.png` (8 quadros → 3072 × 384).

### Importação
- Filtro **Linear** com **mipmaps** ativados nas texturas de personagem (evita serrilhado na redução); o `CharacterVisual` usa `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS`.
- Importação sem perdas e `fix_alpha_border` ligado (sem halo nas bordas transparentes).
- Espelhamento horizontal (W/NW/SW a partir de E/NE/SE) **não** é usado para Tavorko (o arco trocaria de mão); para Verddro, avaliar caso a caso.

### Etapas futuras da V0.2
- Corrida com Shift, após validação de idle e walk.
- Y-Sort entre personagem e objetos do cenário.
