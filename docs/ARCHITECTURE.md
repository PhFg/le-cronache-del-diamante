# Arquitetura inicial

- Engine: Godot 4.x; linguagem: GDScript; repositório Git; edição via Windsurf.
- Scene principal: `scenes/main_menu.tscn`; controlador: `scripts/main_menu.gd`.
- Autoload `GameState`: escolha do personagem desacoplada da interface.
- Representação gráfica e regras de combate devem permanecer separadas.
- IDs estáveis (`verddro`, `tavorko`) para personagens, itens, missões e regiões.
- Dados estáticos podem usar Resources/JSON versionados; salvamentos locais em `user://` serão adicionados futuramente.
- Futuro cooperativo requer transição para estado de jogo validado por host/servidor e sincronização de ações. Não considerar o cliente como fonte autoritativa de progresso compartilhado.
- 2.25D: experimentar sprites 2D em ambiente 3D simplificado e câmera isométrica, validando legibilidade e desempenho antes de expandir mapas.
- NÃO adicionar multiplayer, base de dados externa ou serviços em nuvem à V0.0.
