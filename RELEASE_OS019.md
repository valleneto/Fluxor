# FLUXOR OS019 — Mesclar novas pastas na organização existente

## O problema observado

O usuário testou com sucesso copiar e organizar arquivos vindos do HD conectado ao Mac Mini para o MacBook Pro, mas precisa adicionar outra origem à **mesma** estrutura previamente organizada. Até a OS018 o fluxo gerava `Fluxor_Organizado` sob um diretório pai e renomeava qualquer colisão. Isso poderia produzir `video (1).mp4` mesmo para cópias byte-a-byte idênticas.

## Comportamento novo

Na tela **Organização segura → ACERVO**, escolher entre:

1. `Criar ou usar Fluxor_Organizado no destino` — fluxo histórico, escolhido a partir da pasta pai.
2. `Acrescentar a uma organização existente` — selecionar a própria pasta **Fluxor_Organizado**, com a estrutura já criada. O aplicativo **não** cria outra pasta Fluxor_Organizado dentro dela.

Para preservar a estrutura, selecionar **o mesmo critério** de organização da primeira operação (tipo, extensão, ano ou ano e mês). A detecção automática do critério histórico ainda não existe; a interface orienta o usuário a manter a escolha coerente.

Após escolher nova origem:

- **NOVO:** prevê e copia no grupo correspondente.
- **IGNORAR IDÊNTICO:** verifica tamanho e SHA-256 dentro da categoria de destino e não copia conteúdo já presente, mesmo com nome diferente. Também considera arquivos idênticos dentro do mesmo lote.
- **RENOMEAR:** nomes iguais com bytes diferentes recebem sufixo numerado, sem sobrescrever o anterior.
- **PRÉVIA OBRIGATÓRIA:** lista arquivo/origem/destino e resumo de quantos serão adicionados, ignorados ou renomeados antes de habilitar a cópia.
- **REVALIDAÇÃO:** tamanho/mtime da origem, conteúdo SHA-256 e caminhos de destino revisados no momento da execução; colisões criadas no intervalo são tratadas com criação exclusiva `xb`.
- **RELATÓRIO:** mostra quantidade copiada, ignorada e renomeada, além de avisos/erros. Após a conclusão, o destino continua selecionado para um próximo lote.

### Segurança e limites

- Não muda/move/apaga arquivos anteriores ou originais; apenas cria novos arquivos em subpastas de categoria.
- Recusa destino organizado ausente, raiz simbólica, subpasta de categoria simbólica, origem sobreposta ao destino e planos cujo destino foi adulterado.
- Impede selecionar a própria `Fluxor_Organizado` no modo de nova organização, para evitar criar uma segunda aninhada.
- Compara duplicatas **na mesma categoria**, não faz auditoria de duplicatas entre todas as categorias da coleção. Verificação SHA-256 pode consumir tempo de leitura em arquivos grandes de mesmo tamanho, inclusive em discos montados pela rede.
- Não altera o motor de rede; acesso ao Mac Mini depende do compartilhamento/volume já disponível no sistema. Navegador SFTP integrado continua pendente.
- O motor não deduz ou altera o modo histórico de classificação. Escolher outro modo poderá resultar em grupos paralelos, sem mover os grupos existentes.

## Nova identidade FLUXOR

- `fluxor_brand.py`: wordmark vetorial mais expressivo com setas em direções diferentes, linhas angulares cruzando o corpo do lettering com clip e níveis à frente/atrás (referência wildstyle/bomb); paleta conservadora em prata e dourado.
- Continua somente na barra lateral, sem quadro quadrado.
- A animação de areia zen da OS018 no centro permanece inalterada.
- Identidade sujeita à aprovação visual no MacBook.

## Evidência técnica

- `tests/test_os019.py` testa acréscimo, idempotência, duplicatas por conteúdo inclusive nomes diferentes e lote único, nomes alternativos em colisão, plano obsoleto, destino inválido/aninhado, symlink e integridade SHA-256.
- `tests/test_os019_gui.py` confirma controles Qt, troca explícita de modo, limpeza da seleção antiga e preservação da exigência de prévia.
- GitHub Actions verifica também OS014–OS018 e demais regressões. Testes usam apenas pastas temporárias e arquivos sintéticos, sem acesso ao Samsung.

## Homologação no MacBook Pro

Fechar a janela atual e confirmar que nenhuma análise está sendo executada. No Terminal:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-merge-os019 --track origin/dev/merge-safe-brand-os019
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Se Git sinalizar conflito com arquivos locais, **parar** e preservar tudo; não usar `reset --hard`, `clean` ou excluir arquivos.

No app, selecionar **Organização segura**, escolher **Acrescentar a uma organização existente**, selecionar uma nova pasta de origem, selecionar a própria `Fluxor_Organizado` usada na execução anterior como destino, manter o mesmo modo (por exemplo `Por ano e mês`), clicar **Pré-visualizar**, ler o resumo e somente então **Copiar com segurança**.

Usar primeiro duas cópias sintéticas ou uma pasta de teste pequena. Não executar primeira homologação num diretório inteiro de vídeos importantes.

## Governança

Branch isolada `dev/merge-safe-brand-os019`, PR draft. Sem merge, deploy, publicação, acesso ativo ao HD Samsung ou manipulação de arquivos pessoais.
