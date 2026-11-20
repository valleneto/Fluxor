# FLUXOR OS025 — Windows compatibility gate (diagnóstico)
**Data:** 2026-11-20
**Base imutável:** `9f0a109d9adb52bc4fc469327a5fc4c56ba07a45` (OS024-C, PR #13)
**Branch:** `dev/os025-windows-diagnostico-20261120`
**Estado inicial:** diagnóstico criado; sem resultado Windows até confirmação de GitHub Actions.

## Objetivo
Verificar compatibilidade do aplicativo PySide6 e do motor de cópia em `windows-2022` (Windows Server 2022, não substitui validação final Windows 10/11). Os testes usam somente fixtures sintéticas em diretórios temporários do runner descartável.

## Testes
- Interface: OS024-C miniatura; GUI014/015/020/021/022.
- Motor: OS005, OS009, OS014, OS020, OS021.
- Diagnóstico explícito de `os.O_DIRECTORY`, `os.O_NOFOLLOW` e `os.link`; falha inesperada bloqueia liberação.
- **Não executa T01–T22 integralmente**, nem SMB, nem acervo pessoal.
- Workflow com permissões `contents: read` e sem publicação de artefatos.

## Riscos conhecidos a investigar
- `fluxor_core/atomic_copy.py` usa semântica POSIX de `os.link`, `os.open(directory)` e `os.fsync(directory_fd)`. Isso requer análise específica de Windows/NTFS: não remover checagens de integridade ou substituir operações por fallback inseguro.
- `fluxor_network.py` delega conexões SMB ao Windows Explorer; `fluxor_folder_picker.py` tem textos/caminhos com premissas de macOS.
- Ainda não existe build Windows assinado/testado; `scripts/build_macos.sh` é exclusivo de macOS.

## Gate
Sem GO de beta Windows ou Microsoft Store até testes Windows, correções de segurança, build, instalação, desinstalação, e autorização explícita. Sem merge, release, instalador, publicação e sem alteração de `master`, OS022 ou OS024-A/B/C.
