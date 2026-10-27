# FLUXOR — OS021 | Consolidação, critérios ordenáveis e integridade

**Emissão:** 27/10/2026 · **Autorização:** usuário aprovou fases A–F após retomada de emergência.  
**Branch:** \`dev/os021-consolidacao-integridade-20261027\`  
**PR draft:** https://github.com/valleneto/Fluxor/pull/9  
**Branch principal:** \`master\` no SHA \`2d165c94a0e2d1ac2122f4e932a49afa68bbc7cf\`; **não modificada**.  
**Ponto de origem:** PR #8 / \`dev/combinacao-navegacao-os020\`, \`965ba3d16c72951fe6b70582c5711e58d9e09b2e\`.  
**Orçamento:** R$ 0. **Não houve** merge, deploy, publicação, instalação local ou acesso a arquivos pessoais.

## 1. Fontes e decisão de consolidação (fase A)

- PR #7 (\`dev/modos-combinados-navegacao-os020\`) e PR #8 são duas implementações divergentes da OS020, ambas derivadas da OS019. Não foram mescladas cegamente.
- Base adotada: PR #8, com \`SafeFolderPicker\` em worker assíncrono e a hierarquia OS019. Da branch \`dev/fluxor-ui-rede-20261026\` foi recuperada somente a ação de conexão **SMB via Finder**, sem incorporar o seletor nativo antigo que ocasionava dificuldades.
- Preservados \`fluxor_mural.py\` (areia japonesa procedural 20 fps e opção reduzir movimento), \`fluxor_brand.py\` (wordmark existente) e \`fluxor_design.py\` (preto/cinza/prata/dourado).
- **Atenção visual:** a referência exata em fotografia para grafite/bombing não foi recuperada de modo verificável. Por segurança de identidade, nenhuma nova arte foi inventada nem o logo redesenhado. A aceitação visual segue pendente.

## 2. Organização multicritério (fase C)

- \`fluxor_core/criteria.py\` centraliza validação e composição de até três critérios, **na ordem selecionada**: Tipo, Extensão, Ano, Ano/mês, Ano/mês/dia.
- Ex.: \`Combinar: Tipo > Ano/mês\` produz \`Imagens/2024/05/foto.jpg\` e \`Videos/2024/05/video.mp4\`. Inverter para \`Ano/mês > Tipo\` produz \`2024/05/Imagens/foto.jpg\`. Também é possível \`Extensão > Tipo > Ano\`.
- UI expõe **Combinar critérios (ordenar)** e três seletores posicionais na tela de Organização. Modos anteriores são preservados, inclusive ano/mês/dia.
- Seleção duplicada ou sobreposição de granularidades de data é rejeitada em vez de gerar hierarquias inválidas.
- Data considerada: **última modificação** (\`mtime\`) no sistema de arquivos, NÃO EXIF nem data de gravação QuickTime. Sem alterar arquivos para recuperar metadata original.
- O arquivo auxiliar oculto \`.fluxor-organizacao.json\` registra a ordem dos critérios na própria coleção **após o usuário autorizar a cópia e antes do primeiro arquivo**. Modo diferente é bloqueado em coleções já registradas. Coleções antigas sem registro são mantidas e exigem revisão visual da prévia; não são migradas automaticamente.

## 3. Motor e integridade (fase B)

- Prévia com erros de leitura de arquivo, pasta inacessível, profundidade não percorrida ou ciclo inesperado recebe \`completa=False\` e \`bloqueios\`; o botão de copiar fica indisponível e \`executar_plano\` recusa execução mesmo quando chamado diretamente.
- O scanner testa \`stat()\` explicitamente, evitando tratar erro de permissão transitório como simples arquivo inexistente por \`Path.is_file()\` devolver falso.
- A indexação SQLite já tinha transação com rollback em falha de rede; agora falhas de stat e profundidade excedida também abortam a transação, evitando substituir o catálogo válido por resultado parcial.
- Mantidos os controles OS019: cópia exclusiva \`xb\` sem sobrescrever arquivos, SHA-256, prevenção de destinos sobrepostos, detecção de colisões, prévia obrigatória e recusa de destino somente leitura.
- **Limite remanescente:** em encerramento abrupto/processo morto durante uma escrita, ainda pode permanecer um arquivo de destino parcial. A organização continua NÃO homologada para uso massivo sobre dados críticos sem uma política posterior de journal/atomicidade que preserve os arquivos anteriores. Não executar limpeza automática de dados pessoais.

## 4. Navegação, Downloads, Samsung e rede (fase D)

- \`SafeFolderPicker\` enumera apenas diretórios em worker daemon separado da GUI, 140 por página. Paginação agora ordena nomes e usa cursor alfabético (keyset), impedindo duplicação por ordem instável do \`os.scandir\`. Mudanças no diretório durante paginação podem exigir recarregamento.
- Colar endereço \`smb://\`, \`afp://\`, \`ssh://\` ou \`sftp://\` exibe explicação de rede não montada e **invalida seleção anterior**, prevenindo copiar do diretório errado.
- O usuário pode abrir \`~/Downloads\` e volumes previamente montados em \`/Volumes\`; caminhos remotos inexistentes são erro controlado. O botão **Conectar SMB (Finder)** solicita ao sistema que abra o servidor e faça a autenticação, sem guardar senhas no Fluxor.
- A conexão por \`sftp://\` e montagem remota nativa no Fluxor **não foram implementadas**. Uma chamada bloqueada pelo macOS/servidor em \`scandir/stat\` pode permanecer pendente apesar da thread e do aviso de lentidão.
- Nenhuma pasta Samsung, nenhum compartilhamento real e nenhum arquivo local do usuário foram acessados. A causa exata do erro original no MacBook/SMB não é considerada resolvida apenas pelo CI.

## 5. Identidade visual (fase E)

Paleta preservada: preto fosco/brilhante, cinza, prata e detalhes de ouro envelhecido, sem fluorescência. Animação central independente com sulcos de jardim japonês, direções alternadas, padrões transformativos e opção de movimento reduzido. O logo continua à esquerda. Revisão do grafite/bombing está **bloqueada por falta das fotografias originais**; reenvio exigido antes de redesenho, sem bloquear a correção técnica.

## 6. Validação (fase F)

CI GitHub Actions: \`Fluxor MVP checks\`, usando Python 3.11 em Ubuntu e PySide6 Qt offscreen. Executa regressões históricas e os novos testes:

- \`tests/test_os021.py\`: ordem Tipo→Data, Data→Tipo e três níveis; integridade por hash; política persistida; rejeição de critérios duplicados e coleção incompatível; prévia profunda incompleta e cópia recusada. Fixtures temporárias.
- \`tests/test_os021_gui.py\`: seletores posicionais, botão SMB, paginação estável de mais de 140 pastas, endereço inválido limpa seleção. Qt offscreen e HOME temporário.
- Regressões OS014–OS020 e motor continuam ativas. Testes históricos foram atualizados quando esperavam misturar modos no mesmo destino ou aceitar árvore incompleta.

Execução de CI comprovadamente aprovada em commit intermediário: https://github.com/valleneto/Fluxor/actions/runs/40558500732 (SHA \`d4f6ee7503b0be14c4710d8145bb0bfb1cbf588d\`). **Após o commit de registro antecipado de política, o CI final do HEAD deve ser conferido de novo.**

### Critérios para homologação manual no macOS

1. **Sem substituir a instalação atual**: verificar \`git status\` antes de qualquer checkout/worktree; se houver alterações locais, parar. Preservar o bundle anterior.
2. Abrir a versão candidata no Mac com ambiente Python já existente, sem instalação automática. Testar janela em resolução do MacBook Pro, navegação entre abas, Inspector e controles.
3. Usar **apenas pasta sintética local**, com imagem e vídeo, como origem; testar critério Tipo→Ano/mês e Ano/mês→Tipo, primeiro prévia, depois cópia pequena em destino descartável. Confirmar SHA-256 e política de modo.
4. Testar \`Downloads\` somente em leitura e o caminho real \`/Volumes/...\` montado no próprio MacBook. Registrar existência, permissões de leitura, tamanho do diretório, tempo de resposta, tipo do volume e mensagem de erro. **Não escolher o Samsung montado somente leitura como destino de escrita.**
5. Validar desconexão/retorno de SMB e pastas de milhares de subpastas, sem copiar arquivos reais.
6. Verificar imagem do jardim japonês em movimento real, pausa/minimização, consumo CPU/memória e legibilidade do logo. Confrontar bombing com as fotos após reenvio.

## 7. Reversão e limites

Todas as alterações permanecem na branch isolada/PR draft; a \`master\` e as PRs #1–#8 não foram mescladas nem reescritas. A reversão segura consiste em não instalar/incorporar a OS021 e, se necessário, preparar commits de reversão revisados na própria branch. Não executar \`reset --hard\`, \`git clean\`, force-push ou exclusão de acervo pessoal. Sem deploy, release, serviços pagos, contratação ou alteração de HDs reais.

## 8. Estado final declarado

**Código implementado e testes automatizados em CI:** candidato. **Testes reais de MacBook/SMB/Samsung:** pendentes. **Qualidade do grafite comparada às fotografias:** pendente. **Pronto para merge/publicação:** NÃO. **Pronto para revisão e homologação controlada:** SIM, após conferir CI do HEAD.
