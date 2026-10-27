# FLUXOR — OS015 | Biblioteca contextual (homologação)

## Status

Alterações implementadas exclusivamente na branch `dev/inspector-contextual-20261026`.
Merge, deploy e instalação no computador do usuário **não realizados**.

## Experiência revisada

- Sem arquivo selecionado: a Biblioteca ocupa toda a largura do painel.
- Seleção simples: Inspector aparece à direita com metadados do arquivo selecionado.
- O botão **Fechar ×** recolhe o Inspector e limpa a seleção, devolvendo a largura à lista.
- Não há **Escolher arquivo** no Inspector embutido na Biblioteca.
- Imagens locais: prévia sob demanda ao selecionar, sem cache persistente.
- PDF e DOC/DOCX/RTF/ODT/PAGES locais: prévia de miniatura pelo Quick Look **no macOS**, sujeita à disponibilidade do gerador de miniaturas do sistema.
- Vídeo: não reproduz automaticamente; ações de quadro e prévia curta disponíveis sob demanda.
- Outras extensões: exibição de metadados, sem forçar uma prévia.
- Arquivos detectados em pastas típicas de nuvem: prévias bloqueadas.
- Ferramentas de análise secundárias: recolhidas por padrão.
- **Interromper análise**: botão visível durante indexação/comparação, mesmo com ferramentas recolhidas.

## Testes automáticos

Workflow: `.github/workflows/mvp-checks.yml`.

- Sintaxe Python e suíte existente: classificação, scanner, organização, indexação SQLite, SHA-256, rollback e desempenho sintético.
- Qt offscreen OS014: navegação, botões numa janela pequena, mídia.
- Qt offscreen OS015: Inspector oculto inicialmente, seleção e fechamento, documento e imagem, nuvem, filtro e ferramentas recolhidas.
- Fixtures sintéticas em diretórios temporários, sem utilizar dados pessoais.

Os testes Linux CI **não comprovam** a compatibilidade visual e do Quick Look com macOS Catalina; esta etapa depende de homologação local.

## Homologação no MacBook Pro, sem alterar a branch anterior

No Terminal:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-os015 --track origin/dev/inspector-contextual-20261026
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Se `git switch` apontar arquivos locais conflitantes, **não faça reset/clean**: interrompa e preserve os arquivos locais.

Na Biblioteca, selecionar apenas `~/Downloads/FLUXOR_TESTE_ORIGEM` (cópia local de teste validada por SHA-256). Verificar:
1. Lista em toda a largura sem seleção.
2. Um clique no DOCX abre Inspector; não existe botão Escolher arquivo no Inspector.
3. Fechar × recolhe o Inspector.
4. Buscar nome de arquivo não exige nova seleção pelo Finder.
5. Ferramentas secundárias recolhidas; cancelamento acessível enquanto análise estiver em curso.
6. Não mover, excluir ou modificar originais.

## Limites conhecidos / escopo futuro

- Acesso direto a volumes remotos SMB/AFP e navegador SFTP integrado **não fazem parte da OS015**. Foi validada uma transferência **externa ao Fluxor** por SFTP do Samsung para uma pasta local, com conferência SHA-256.
- A prévia documental depende de `qlmanage` do macOS e pode não ter miniatura para todo formato.
- Não há pacote `.app` assinado/notarizado desta branch; execução atual é pelo ambiente Python existente.
- Segurança de arquivos: continuar com origem separada do destino, prévia antes de organizar, sem exclusão automática.
