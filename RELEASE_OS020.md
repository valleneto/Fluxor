# FLUXOR OS020 — Organizar por tipo + data, pastas de rede e wildstyle

**Status:** desenvolvimento concluído em branch isolada, aguardando homologação no MacBook Pro. Sem merge/deploy/publicação/instalação automática. Sem acesso ou escrita em arquivos do HD Samsung.

## Solicitações do usuário

1. Organizar fotos e vídeos por **tipo e data juntos**, em vez de escolher apenas um critério.
2. Evitar loop de pastas ou janela travada ao navegar no origem dentro de downloads/links de compartilhamentos de rede, especialmente pastas grandes no HD Samsung conectado ao Mac Mini.
3. Refazer o wordmark FLUXOR a partir de fotos reais de letras grafite **wildstyle** (formas angulares, sobreposição geométrica, linhas que entram/saem do corpo das letras, setas incorporadas), preservando a paleta aprovada preto fosco, prata, dourado. A animação central zen areia permanece independente.

## Implementação

- Modos adicionais no motor e UI: `Por tipo e ano`, `Por tipo, ano e mês`. Saída, por exemplo: `Fluxor_Organizado/Imagens/2026/10/arquivo.jpg`, `Fluxor_Organizado/Videos/2026/10/filme.mp4`. Compatível com o modo de acrescentar pastas da OS019. Modos antigos preservados.
- **Critério temporal = última modificação do arquivo**, não data EXIF/fotografia ou gravação. Tooltip do aplicativo explica. Para EXIF/QuickTime haverá uma implementação distinta, com datas conflitantes e timezones cuidadosamente analisados.
- Seletor não nativo `SafeFolderPicker` substitui o diálogo macOS no Organizador e na Biblioteca: percorre **apenas diretórios**, não segue symlinks, atalhos/aliases, não lista arquivos para navegação, apresenta em páginas de 140 pastas, aceita endereço absoluto colado ou atalhos Início/Downloads/Rede montada (`/Volumes`). Consulta em thread daemon para não bloquear o Qt; mensagem após 9 segundos em rede lenta. Caminho inacessível/atalho recusado; seleção antiga é desabilitada após erro.
- Não pressupõe que `sftp://` seja uma pasta local. **Não monta** SMB, AFP ou SFTP nativamente: a conexão precisa estar montada pelo macOS (por exemplo `/Volumes/Share`). Aviso claro para esquemas `sftp://`, `smb://`, `afp://`. Rede desconectada pode manter uma chamada do sistema operacional pendurada numa thread daemon; a GUI permanece utilizável, mas o navegador SFTP direto ainda exige outro módulo.
- Leitura `planejar` em worker em segundo plano com contagem parcial (total desconhecido, barra indeterminada, sem falsa porcentagem), verificações de symlink/ciclo e limite prudente de 42 níveis para interromper travessias potencialmente ilimitadas, com avisos; desconexões detectadas pelo `os.walk` **abortam** prévia ao invés de validar inventário incompleto.
- Indexação `index_folder` utiliza proteções equivalentes e aborta transação de SQLite em erro de rede (preserva acervo catalogado anterior).
- Preflight detecta volume destino marcado como **somente leitura**, prevenindo tentativas de gravação em volumes Samsung NTFS montados RO. Originais preservados e nenhuma cópia executada durante testes.
- Wordmark `fluxor_brand.py` foi refeito como formas vetoriais **criadas letra por letra** de F, L, U, X, O, R: linhas geométricas próprias, extrusão dourada, face prata, setas integradas e trilhos sobrepostos/clipped. Não é mais apenas Arial Black com flechas coladas. Continua apenas na barra lateral sem fundo quadrado; o centro continua a animação japonesa de areia já testada na OS018.
- Segurança OS019 (prévia, hash, colisões sem sobrescrita, cópia exclusiva, SHA-256, nenhuma exclusão) intacta.

## Testes

- `tests/test_os020.py`: hierarquia data+tipo, inclusão incremental posterior, symlink cycle, diretório com 84 arquivos e barra indeterminada, recursão profunda, falha simulada de rede, rollback SQLite e volume read-only simulado.
- `tests/test_os020_gui.py`: seletor em diretório sintético com mais de 140 pastas, paginação, symlink loop recusado, URL de rede não montada com orientação e modos da UI.
- Regressões OS014–OS019 e testes de motor mantidos no workflow.
- Essas simulações não comprovam a compatibilidade e a responsividade de **todas** as configurações SMB/AFP/NTFS macOS. Homologar no hardware real, nunca executar uma primeira cópia grande em destino sensível.

## Como homologar no MacBook Pro

Fechar o Fluxor e verificar que nenhuma cópia está ativa:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-combinado-os020 --track origin/dev/combinacao-navegacao-os020
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Caso o Git indique arquivos locais conflitantes, PARAR; não fazer `reset --hard` ou `git clean`.

### Teste manual 80/20

1. Organização segura → origem: abrir **Downloads** (local). O novo navegador deve mostrar somente pastas, permitir entrar/voltar, ignorar atalhos simbólicos e responder com grandes listas; para compartilhamentos montados, ir a **Rede montada** (`/Volumes`).
2. Fonte de teste contendo foto e vídeo (cópias sintéticas ou isoladas), destino local gravável, modo **Por tipo, ano e mês**. Fazer prévia e conferir caminhos, **sem autorizar cópia até conferir**.
3. Se houver rede montada via macOS, navegar ao diretório real do compartilhamento. Se aparecer apenas link simbólico ou `sftp://`, isso é diagnosticado, não suportado como caminho direto nessa versão.
4. Só depois executar com pequeno lote, confirmar destino organizado e SHA-256. Nenhuma escrita no Samsung se montado read-only.
5. Conferir na lateral lettering wildstyle prata/dourado com setas e no meio a animação zen, sem blocos coloridos. Registrar foto/captura para comparar referências fornecidas.

**Não implementado:** SFTP interno, data EXIF real, resolução universal de links Finder/DFS e timeout forçado de syscalls de rede bloqueadas no kernel. Estão mapeados como requisitos de desenvolvimento posteriores e não devem ser anunciados como resolvidos.
