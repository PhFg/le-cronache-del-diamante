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
