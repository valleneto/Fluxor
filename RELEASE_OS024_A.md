# FLUXOR — RELEASE OS024-A | Cópia segura e recuperação idempotente

**Emissão:** 18/11/2026 · **Classificação:** motor Linux aprovado; homologação macOS Ventura pendente.
**Repositório:** valleneto/Fluxor · **Base imutável:** aa2dc2cd225bcee2eaab7befb31c4608363c5512.
**PR de referência:** #11, OS022; branch dev/os022-restauro-visual-referencia-20261027.
**Branch isolada:** dev/os024a-copia-atomica-recuperacao.
**PR draft OS024-A:** https://github.com/valleneto/Fluxor/pull/12, base na branch da PR #11, não master.
**Evidência de CI GREEN:** https://github.com/valleneto/Fluxor/actions/runs/44354128230 — SHA 89bf29e6862572239a33cd1ac1ecd109b7b88be5.
**Orçamento:** R$0; nenhuma publicação, merge, instalação, teste SMB real ou manipulação de acervo pessoal.

## 1. Análise e governança

O commit-base e o HEAD da PR #11 coincidiram exatamente. A nova branch nasceu diretamente desse SHA. A inspeção do worktree local do Mac não foi possível pela API GitHub e **não** se afirma que esteja limpo. Nenhum checkout local ou comando de limpeza foi executado.

Arquivos alterados versus OS022:
- fluxor_core/atomic_copy.py — motor de publicação exclusiva + journal/recovery.
- fluxor_core/plan.py — integração à cópia, preservando prévia e modos.
- fluxor_core/merge.py — exclui temporários gerenciados da deduplicação incremental.
- tests/test_os024a.py — T01 a T22; todos sintéticos.
- tests/test_os005.py — reposiciona a injeção de SHA-256 para o novo módulo, preservando sua intenção de segurança.
- .github/workflows/mvp-checks.yml — inclui OS024-A, fixa runner Ubuntu 24.04 e PySide6 6.8.3.
- RELEASE_OS024_A.md — este relatório.

Nenhum arquivo de interface, identidade visual, logotipo, animação japonesa, seletor de pastas ou componentes Qt da OS022 foi alterado.

## 2. Antes e depois da transferência

Antes: destino com nome definitivo aberto em modo exclusivo e preenchido progressivamente. Se o processo morresse durante a transferência, o arquivo definitivo poderia ficar parcial.

OS024-A:
1. Validar origem, destino, capacidade, política de critérios e prévia completa.
2. Gerar UUID, criar journal JSONL exclusivo e sincronizado em .fluxor-journal; registrar PLANNED.
3. Registrar TRANSFERRING; criar temporário oculto exclusivo .fluxor-tmp-UUID.part na própria pasta de categoria.
4. Transferir blocos de 1 MiB; sincronizar arquivo e diretório; comparar tamanho, identidade da origem e SHA-256 da origem versus temporário.
5. Registrar VERIFIED persistentemente; só então publicar com os.link (POSIX link(2)), que cria nome atomicamente e retorna EEXIST quando já ocupado.
6. Em colisão, registrar a nova intenção e tentar nome alternativo sem sobrescrever.
7. Sincronizar diretório, registrar PUBLISHED, verificar o nome definitivo, desvincular somente o nome temporário **da própria transação** após comprovar mesmo inode, e registrar CONFIRMED.

Não há os.replace, rename com substituição nem escrita direta no nome definitivo. Falha de hardlink ou fsync implica erro sem fallback inseguro.

Garantia formal da primitiva Apple link(2): https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/link.2.html

## 3. Journal e recuperação idempotente

API: fluxor_core.atomic_copy.recover_transactions(base).

- PLANNED / TRANSFERRING: incompleto; sem publicação nem limpeza automática; retorna incomplete.
- VERIFIED / COLLISION: temporário deve estar íntegro; origem ainda idêntica; tenta link exclusivo. Se nome ocupado, bloqueia em vez de substituir.
- Arquivo publicado antes do journal final: confirma somente quando hash e propriedade (inode temporário/definitivo) forem demonstráveis.
- PUBLISHED com temporário já ausente e destino íntegro: confirma sem republicar.
- CONFIRMED: terminal, evita rehash de toda a coleção em cada nova operação.
- Registros truncados, incorretos, ambíguos, symlinks ou temporários alterados: blocked, sem mudança destrutiva.
- Temporários gerenciados de padrão UUID nunca são interpretados como duplicatas da coleção ou arquivos normais de origem.

A recuperação três vezes seguida foi testada; a segunda e a terceira não modificaram arquivos nem repetiram alterações no journal confirmado. Restos de transações incompletas são preservados para revisão; não há botão de limpeza automática nesta OS.

## 4. Matriz T01–T22 e regressão

A execução https://github.com/valleneto/Fluxor/actions/runs/44354128230 confirmou todos os passos:

| Teste | Cenário | Resultado Linux |
|---|---|---|
| T01–T03 | Cópia normal, cancelamento antes/durante transferência | PASS |
| T04 | Processo auxiliar encerrado abruptamente por os._exit(77) durante cópia | PASS |
| T05–T08 | Falhas entre transferência, verificação, publicação, journal; recuperar 3 vezes | PASS |
| T09–T11 | Nome ocupado, bytes diferentes, SHA-256 incremental, temporários ignorados | PASS |
| T12–T14 | Origem mutável, erro de leitura e ENOSPC sintéticos | PASS |
| T15–T17 | Journal truncado, temporário adulterado, symlink | PASS |
| T18–T21 | Concorrência, critérios combinados, incompatibilidade de política, link indisponível | PASS |
| T22 | Regressões de sintaxe, motor, SQLite, segurança e UI OS005–OS022 | PASS |

A primeira rodada do CI acusou falhas legítimas de regressão/injeção SHA-256 e falhas nativas Qt decorrentes da mudança de versão do runner/Qt. O ponto de injeção foi atualizado, e Ubuntu 24.04/PySide6 6.8.3 foram fixados para obter reprodutibilidade. O CI verde acima inclui testes gráficos OS022 preservados.

## 5. Limitações importantes

- **macOS Ventura 13**: alvo da beta, mas **não testado fisicamente** nesta OS. Não houve build nem instalação .app/.dmg, nem validação macOS/APFS. Catalina explicitamente fora de escopo.
- **Linux CI**: Ubuntu 24.04, Python 3.11, PySide6 6.8.3, Qt offscreen e arquivos em TemporaryDirectory. O teste de encerramento foi os._exit, não queda de energia ou simulação de falha de controladora.
- **Filesystem**: os.link oferece publicação exclusiva no filesystem compatível; não prova durabilidade absoluta após desligamento físico ou garantias de SMB/NTFS/exFAT. Se não houver suporte a hardlink/fsync, falha controlada.
- **Samsung/SMB**: nenhum acesso ou teste. Conexão de rede real depende de homologação posterior.
- **Journal e resíduos**: temporários incompletos permanecem para revisão; não há interface de limpeza. Hashes de arquivos confirmados não são recalculados automaticamente a cada execução; verificação periódica de arquivo alterado externamente não integra o escopo.
- **Desempenho**: append-only/fsync por operação adiciona I/O; benchmark real de dezenas de milhares de arquivos em Ventura permanece pendente.
- **Acervos legados**: sem migração automática de critérios preexistentes.

## 6. Classificação e reversão

**Resultado da OS024-A:** APROVADO em Linux sintético + regressões; **APROVADO COM RESTRIÇÕES** como candidato a homologação real. Beta externa ou uso comercial ainda não liberados.

Reversão segura: preservar OS022 no SHA aa2dc2cd225bcee2eaab7befb31c4608363c5512 e manter a PR #12 sem merge. Não executar reset destrutivo, force-push ou exclusão de arquivos.

**Não houve execução no projeto CICLO nem em dispositivos/arquivos pessoais.**
