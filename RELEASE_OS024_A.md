# FLUXOR OS024-A — Cópia segura e recuperação idempotente

**Referência base imutável:** `aa2dc2cd225bcee2eaab7befb31c4608363c5512` (OS022, PR #11, branch `dev/os022-restauro-visual-referencia-20261027`).
**Branch isolada:** `dev/os024a-copia-atomica-recuperacao`.
**Estado:** implementação técnica em validação. PR draft; sem merge, publicação, instalação ou arquivos pessoais. R$0.

## Mapa do fluxo

- Antes: `planejar` -> validar capacidade/modo -> criar destino definitivo com `open('xb')` -> transferir bytes -> verificar SHA -> remover na exceção tratada. Um SIGKILL/crash podia deixar nome definitivo parcial.
- Agora: plano e revalidação -> transação journal append-only (.fluxor-journal/UUID.jsonl) -> temporário exclusivo na própria pasta de categoria -> transferência em blocos -> fsync -> SHA de fonte e temporário/identidade -> registro VERIFIED -> `os.link(temporario, destino)` exclusivo (sem sobrescrita) -> fsync pasta -> registro PUBLISHED -> remover **somente** o nome provisório de propriedade comprovada (mesmo inode do definitivo) -> registro CONFIRMED.
- Uma colisão concorrente `EEXIST` tenta nome alternativo, registrando a nova intenção antes de publicar.
- Recuperação verifica journals, publica apenas temporários completos e validados, confirma publicações feitas antes do registro final e recusa inconsistências.
- Estados incompletos não publicam nada e são preservados para revisão, sem limpeza automática.

## Garantia e limites

A chamada `link(2)` cria um novo nome atomicamente e retorna `EEXIST` quando o destino existe, conforme documentação oficial Apple: https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/link.2.html

`os.replace` / rename com substituição não é usado para o nome final. Sem fallback destrutivo caso o volume não suporte hard links ou sincronização de diretório.
Journal e temporário são arquivos exclusivos controlados pelo Fluxor, sem exclusão de dados preexistentes.
O journal não equivale a uma prova de durabilidade absoluta perante falha física de hardware, controladora ou filesystem não homologado; `fsync` e testes sintéticos estabelecem o limite.
Não executa nem promete testes reais em Ventura, APFS externo, NTFS, exFAT ou SMB. O macOS Ventura é a plataforma-alvo futura; Catalina está fora do escopo.
O método de recuperação está disponível em `fluxor_core.atomic_copy.recover_transactions(base)`; não há novo botão nem interface.
A recuperação incompleta reporta `incomplete` sem limpar arquivos provisórios; registros suspeitos retornam `blocked`.

## Matriz de validação

`tests/test_os024a.py`: T01–T21 cobrindo cópia, cancelamentos, SIGKILL em subprocesso sintético, interrupção antes/depois de verificação e publicação, recuperação três vezes, colisão, integridade, origem mutável, EIO, ENOSPC, journal truncado, temporário adulterado, symlink, disputa concorrente, critérios combinados, política de coleção e link indisponível.
T22: execução das regressões OS005–OS022 no mesmo fluxo `.github/workflows/mvp-checks.yml`.
**Preencher CI final e testes individuais após validação.**
