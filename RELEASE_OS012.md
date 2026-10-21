# OS 012 — Fluxor Evolution (desenvolvimento, NÃO homologado)

## Entregas verificáveis no código
- Navegação lateral e identidade grafite/aqua, home revisada.
- Filtro por tamanho (10 MB, 100 MB, 1 GB); filtros de nome, categoria e extensão existentes.
- Revisão persistente em `~/.fluxor/workspace.db` (SQLite), independente do catálogo.
- Coleções virtuais com nomes e referências de caminhos da lista de revisão; não movem nem copiam os originais.
- Duplicate Center: SHA-256 exato pelo motor anterior, janela de resultados selecionáveis e adição à fila persistente, sem exclusão.
- Quick Look pop-up pela barra de espaço preservado; painel de mídia embutido opcional.
- Radar, Versions, diagnóstico e organização com prévia permanecem disponíveis.

## Pendências assumidas
- Visão de projetos ainda é uma coleção de referências, não tela completa de gestão.
- Safe Actions mantém a prévia de cópia anterior; não há sistema geral de desfazer, exclusão ou plano de ações encadeadas.
- Smart Search tem filtro de tamanho básico; intervalo de datas, filtros avançados por projeto e contagem total da busca ficam para evolução.
- Algumas operações de consulta e agrupamento ainda são síncronas e podem ocupar a interface em bases muito grandes.
- A fila persistente guarda caminhos e pode conter referências antigas; não significa que o arquivo ainda exista.
- Operações SHA-256 podem hidratar arquivos só na nuvem; NÃO executar varredura grande em CloudStorage.
- A identidade visual e o diálogo de duplicados precisam ser testados no macOS com escalonamento, acessibilidade, navegação por teclado, tamanho mínimo e vídeos.
- GitHub Actions no Linux valida sintaxe/testes de núcleo, não a GUI macOS.
- Código e `.app` não estão assinados/notarizados nem aprovados para distribuição.

## Homologação local
1. Feche o app e confira `git status --short`; resolva qualquer modificação local antes de atualizar.
2. `git fetch origin && git merge --ff-only origin/dev/seguranca-mvp`.
3. `source .venv/bin/activate && python3 fluxor_iniciar.py`.
4. Teste navegação lateral, voltar/avançar, Biblioteca e organizar.
5. Com arquivos sintéticos locais, verifique busca por tamanho, índice e pop-up Quick Look.
6. Adicione arquivos à fila de revisão; reinicie e confira persistência.
7. Salve coleção virtual; confirme conteúdo e que os originais não mudaram.
8. Gere duplicados sintéticos com bytes iguais; compare e selecione no Duplicate Center.
9. Confirme aparência, responsividade e RAM.
10. Depois de validar, `zsh scripts/build_macos.sh` para reconstruir o aplicativo.

Branch de trabalho: dev/seguranca-mvp. master preservada. Sem publicação.
