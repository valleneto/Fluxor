# Fluxor Control — OS 008: beta experimental

## Executar no macOS (ambiente de desenvolvimento)
```bash
cd ~/Projetos/google-fotos-lab
source .venv/bin/activate
python3 fluxor_iniciar.py
```

## O que existe nesta beta
- Janela única com navegação entre Biblioteca e Organizar.
- Biblioteca local SQLite com indexação de pastas escolhidas pelo usuário, busca, categoria, extensão, ordenação e páginas de até 100 arquivos.
- Diagnóstico de armazenamento baseado no índice.
- Busca de duplicados exatos por tamanho e SHA-256, sem exclusão, com solicitação de cancelamento.
- Inspector textual com informações do índice; duplo clique abre no aplicativo padrão.
- Barra de espaço solicita prévia pelo Quick Look do macOS (componente externo, não integra player ao app).
- Organizador que copia com prévia e SHA-256 após a operação.

## Limitações e segurança
- Beta de desenvolvimento; não pronta para loja ou distribuição pública.
- Não executar testes de duplicados em pastas grandes do Google Drive: SHA-256 pode baixar arquivos disponíveis apenas na nuvem.
- Não há integração nativa ao Quick Look testada em todos os formatos; o comando `qlmanage` é um fallback macOS e pode exibir uma janela externa.
- Cancelamento dos duplicados ocorre entre blocos de leitura; pode haver demora em armazenamento lento.
- Páginas de 100 resultados; ordenação clicando na tabela atua na página exibida. Ordenação global via consulta SQL está disponível no motor, mas ainda não está conectada ao cabeçalho.
- Há processos de hashing que reabrem arquivos: conteúdo mutável durante a cópia exige tratamento adicional.
- A indexação é apenas dos locais autorizados, armazena caminhos e metadados localmente. A versão atual não protege contra todas as mudanças simultâneas de diretório e erros de disco.
- Não há instalador assinado/notarizado, nem testes de GUI macOS em CI.
- O histórico de operações, desfazer e memória avançada ainda não estão implementados.

## Plano de homologação
1. Confirmar `git status --short` sem alterações antes de atualizar a branch local.
2. Testar navegação Início / Biblioteca / Organizar, voltar e avançar.
3. Indexar somente pasta sintética pequena; conferir filtro e 3 páginas de listagem com >200 arquivos.
4. Selecionar imagem, pressionar Espaço e observar Quick Look; fechar prévia.
5. Testar duplicados sintéticos e botão de interromper.
6. Testar organizar usando origem e destino temporários distintos, conferir arquivos com hashes.
7. Medir inicialização e memória no Monitor de Atividade do macOS antes de autorizar distribuição.

## Empacotamento
Empacotamento com PyInstaller é candidato para uma fase específica de QA macOS, **não** está homologado nem automatizado aqui. É necessário testar versão do Python/PySide6, dependências, ícone, permissões, codesign, notarização e funcionamento em máquina limpa. Não contratar serviços nem publicar sem aprovação.

## Referência
`master` deve permanecer intacta. Mudanças nesta fase somente na branch `dev/seguranca-mvp`.
