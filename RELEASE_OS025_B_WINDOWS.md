# FLUXOR — OS025-B Windows/NTFS | Diagnóstico controlado
**Base aprovada OS024-C:** `9f0a109d9adb52bc4fc469327a5fc4c56ba07a45`.
**Base PR14:** `e70ece689e681cba1687e6b70995c4487ea819ab`.
**Branch OS025-B:** `dev/os025b-windows-ntfs-isolado-20261120`.

## Hipóteses e alterações mínimas
1. `fluxor_core/library.py`: três consultas SQLite usavam contexto transacional que NÃO fecha conexão. Aplicado `contextlib.closing` para liberar arquivo no Windows; indexação já usava `closing`. A função não altera SQL nem o catálogo.
2. GUI014/015: fixtures isoladas usam `HOME`, mas `Path.home()` em Windows prefere `USERPROFILE`. Fix de teste restrito ao início da janela com `unittest.mock.patch`.
3. GUI020: o seletor retorna caminho canônico, enquanto teste comparava o caminho original, que pode conter nomes Windows 8.3. Expectativa corrigida para `str(path.resolve())`; nenhum relaxamento de segurança.
4. Teste de primitiva Windows: hardlink exclusivo sem overwrite + tentativa de flush de diretório usando `CreateFileW`/`FlushFileBuffers` em arquivo **sintético descartável**. Prova de chamada de API não equivale a garantia de persistência após queda de energia; falhar de modo controlado quando não suportado.

## Gates obrigatórios
- Regressão UI Windows, SQLite e motor em CI nativo Windows Server 2022.
- NÃO alterar `fluxor_core/atomic_copy.py` antes de confirmação da primitiva NTFS. Não criar fallback inseguro.
- Sem repetir T01–T22 integralmente; sem testes SMB reais, arquivos pessoais, distribuições ou instalador.
- Sem merge ou alteração de `master` e PRs #12/#13/#14.
- **Status:** diagnóstico pendente de CI; NO-GO para beta externa.
