# OS025-C — Preparação Windows / Microsoft Store (auditoria)
**Data inicial:** 20/11/2026
**Base imutável OS025-B:** `8d8e59acfe8a308c37338d4487cbbe3e889bf5c4`
**Branch isolada:** `dev/os025c-windows-store-private-staging-20261120`
**Escopo:** Windows 10/11 desktop (x64) e Store privada, sem dados pessoais.

## Segurança
- Windows: bloquear junctions, symlinks e qualquer caminho com atributo reparse (inclusive ancestrais), antes de `Path.resolve()`.
- Windows beta: operações de escrita restritas a discos locais FIXED com filesystem NTFS. UNC/SMB, USB/FAT, ReFS e outras unidades indisponíveis até homologação separada.
- Preservar regras de no-overwrite, SHA256, temporários, journal e fsync. Nenhuma remoção automática de arquivos.
- POSIX macOS/Linux: comportamento preservado; não altera visual OS022.
- Segurança residual: verificações baseadas em caminhos são sujeitas a TOCTOU sob atacante concorrente; não classificar como auditado para adversários, rede ou falha de energia.

## Microsoft Store
- Caminho pretendido: MSIX, `Private audience` com contas Microsoft de testadores, certificado e hosting providos pelo Store após certificação.
- Requer conta verificada no Partner Center e reserva do nome/identidade exata; não inventar `Publisher` real.
- Empacotamento CI somente com identificador **provisório de desenvolvimento** até usuário fornecer identidades do Partner Center.
- MSIX de CI sem assinatura não representa instalação homologada nem pode ser enviado publicamente.
- Sem submissão, distribuição, merge, release, instalador público ou modificação de master sem nova autorização.

Referências:
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/visibility-options
- https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
- https://learn.microsoft.com/en-us/windows/apps/publish/prepare-developer-account

## Empacotamento automatizado — OS025-C
- scripts/package_msix_stage.py prepara uma copia **nao assinada** do binario em um MSIX com nome e Publisher PROVISORIOS. Bloqueado para uso em Partner Center como esta.
- scripts/windows_binary_smoke.py testa somente inicializacao headless do FLUXOR.exe dentro de perfil descartavel, nao prova instalacao nem interacao fisica.
- CI .github/workflows/os025c-msix-staging.yml executa primeiro tres gates: seguranca Windows (inclusive junction), UI OS022/Inspector e regressao Linux/POSIX. Build interno somente apos todos PASS.
- Artefatos de CI mantidos tres dias, sem GitHub Release e sem upload ou publicacao na Microsoft Store.
- Para envio verdadeiro: reservar identidade do pacote no Partner Center, substituir Name/Publisher pelo resultado oficial e fazer testes humanos de Windows 10/11 e instalacao/desinstalacao. Politica de privacidade e listagem pendentes.

## Execucao inicial OS025-C (SHA 13d4f2c5977ba1f7d6c5427b5a3383f0e476b0a4)
- Windows reparse/junction/UNC PASS; NTFS primitivas PASS; recuperacao 8/8 PASS.
- Teste legado OS020 falhou: symlink comum no conjunto sintetico passou a marcar previa como incompleta.
- Correcao minima: symlink identificado continua ignorado como na OS020; junction e reparse nao-symlink continuam bloqueando a previa.
- Nova execucao CI obrigatoria; nao publicar ate todos os gates PASS.
