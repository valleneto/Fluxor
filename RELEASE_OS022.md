# FLUXOR OS022 — Restauro do visual aprovado nas fotografias

Data: 27/10/2026. Estado: **PR draft / candidato à homologação visual**.

## Referência
Três fotos fornecidas pelo usuário, mostrando Início, Biblioteca e Organizar no MacBook Pro. A referência funcional corresponde à apresentação pré-OS021, com identidade preta/prata/ouro e jardim japonês procedural.

## Mudanças
- `fluxor_iniciar.py`, `fluxor_design.py`, `fluxor_brand.py` e `fluxor_mural.py` **não foram alterados** nesta fase; a estrutura de Início, navegação, estilo, logo e animação permanecem.
- Biblioteca: linha principal novamente com **+ Adicionar pasta / Busca / Categorias**, sem botão adicional SMB, como fotografado.
- Organizar: linha principal novamente **Escolher origem / Escolher destino**, sem terceiro botão.
- Conexão SMB permanece funcional, mas está no navegador de pastas (`SafeFolderPicker`) via **Conectar SMB (Finder)**, junto aos atalhos Início, Downloads e Rede montada.
- `tests/test_os022_gui.py`: cobre interface principal, disposição exata dos botões e acionamento SMB no navegador usando simulação, sem rede real.
- `tests/test_os021_gui.py`: atualizado para verificar a localização intencional do botão SMB.
- Motor OS021 não foi revertido: critérios em ordem livre, exclusividade de cópia, SHA-256, proteção contra prévia incompleta e política persistida mantidos.

## Limites
- Sem merge na master, sem deploy, sem lançamento/instalação de produção.
- Não executar operações em arquivos pessoais ou unidades de rede reais sem confirmação específica.
- Capturas de tela do usuário provam preferência de layout, **não equivalência pixel-a-pixel** nem execução em macOS. Homologação no MacBook permanece necessária.
- O logo wildstyle atual foi mantido, sem alegar que corresponde exatamente às referências de grafite ainda não recuperadas.
- CI automatizado deve ser conferido no head mais recente antes de recomendar uso em dados não sintéticos.
- A OS021 original permanece preservada na PR #9; a OS022 usa branch independente e é candidata à substituição visual.

## Teste no Mac
Abrir **apenas uma cópia isolada** da branch `dev/os022-restauro-visual-referencia-20261027` e inspecionar as três telas antes de testar qualquer cópia. Usar arquivos sintéticos se decidir testar organização.
