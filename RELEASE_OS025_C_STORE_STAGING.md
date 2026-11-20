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
