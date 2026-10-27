# FLUXOR — OS020 | Organização composta e acesso a pastas grandes/de rede

## Objetivo

Adicionar organização **por tipo e data juntos**, preservando modos anteriores e a importação incremental OS019. Mitigar a navegação repetitiva/em loop do seletor de origem relatada no MacBook Pro ao percorrer um atalho Downloads ou subpastas no HD Samsung conectado ao Mac Mini.

A identidade street bombing NÃO é alterada nesta OS: aguardamos a foto de referência que o usuário vai encaminhar.

## Classificação implementada

Os novos modos aparecem ao lado dos já existentes:

- **Por tipo e ano**: `Fluxor_Organizado/Imagens/2026/foto.jpg`; `Fluxor_Organizado/Videos/2026/video.mp4`
- **Por tipo, ano e mês**: `Fluxor_Organizado/Imagens/2026/10/foto.jpg`; `Fluxor_Organizado/Videos/2026/10/video.mp4`

A data usada é a data de **última modificação** do arquivo no sistema (`st_mtime`), não EXIF/data original da câmera. Classificador de categoria já existente é reutilizado.

No modo **Acrescentar à organização existente**, o usuário deve manter o modo de classificação desejado; a OS não migra nem muda automaticamente arquivos previamente organizados com outro critério. Escolher outro modo pode criar uma nova hierarquia paralela; não modifica arquivos antigos.

## Pasta de origem: mitigação de navegação

A seleção de pasta usa o QFileDialog Qt explicitamente não nativo com `DontUseNativeDialog`, `DontResolveSymlinks` e `QDir.Filter.NoSymLinks`, evitando navegar por atalhos simbólicos recursivos no diálogo.

Novo campo **Ou informe um caminho**, com botão **Usar caminho**:
- aceita `~/Downloads` e `/Volumes/COMPARTILHAMENTO/Pasta` (desde que estes caminhos estejam acessíveis no Mac que executa o Fluxor);
- permite saltar diretamente para uma pasta profunda num volume já montado, sem atravessar dezenas de pastas numa janela do Finder;
- não bloqueia a UI no clique para executar leitura, `stat` ou `resolve` em uma pasta de rede potencialmente indisponível: a verificação pesada é feita pela thread de prévia;
- recusa URL `sftp://`, `ssh://`, `smb://` e `afp://` no campo, explicando que **URL de rede não equivale a uma pasta macOS montada**.

O planejador da origem:
- mantém `followlinks=False`, ignora links internos e pacotes macOS especiais;
- detecta caminhos canônicos que se repetem e não percorre novamente esses diretórios;
- coleta avisos `os.walk(onerror=...)` para pastas inacessíveis em vez de entregar uma contagem incorreta sem indicação;
- emite observações periódicas de número de arquivos encontrados e pasta atual (não calcula porcentagem falsa) para que volumes grandes mostrem atividade;
- mantém cancelamento entre diretórios e arquivos. **Uma chamada ao filesystem que o próprio macOS mantém bloqueada pode não responder imediatamente ao cancelamento**.

## Limite de rede comprovado

A transferência de um arquivo do Samsung via SFTP do Mac Mini ao MacBook Pro foi validada anteriormente fora do aplicativo. Esta OS **não integra um cliente SFTP nem monta volumes de rede**. Para um arquivo remoto aparecer no navegador local, ele precisa estar numa pasta previamente montada/acessível no MacBook, ou ter sido transferido como cópia local. A correção do bug concreto do Finder/montagem precisa ser confirmada no MacBook real; não alegar resolução completa apenas pelo CI Linux.

## Testes

- `tests/test_os020.py`: pastas por tipo+ano/mês, hashes das cópias, funcionamento com importação incremental, ciclo simbólico e warnings de pasta inacessível, heartbeat da contagem.
- `tests/test_os020_gui.py`: contrato do controlador de origem e configuração do seletor não-nativo via *stub*, abrangendo `~/`, caminho absoluto e opções de não seguir links. **Não instancia uma janela Qt nessa regressão nova** porque o runner Linux offscreen apresentou falha de finalização de objetos Qt após as asserções. Os testes gráficos reais das versões OS014–OS019 continuam ativos na suíte; a interação do novo seletor precisa ser verificada no macOS.
- Regressões OS014–OS019, classificação, leitura, segurança e rollback.
- A navegação real de Finder/volumes no macOS Catalina **ainda exige validação pelo usuário**.

## Homologação MacBook Pro

Fechar o FLUXOR atual e nenhuma análise ou cópia em andamento. Executar no Terminal:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-os020 --track origin/dev/modos-combinados-navegacao-os020
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Se o Git sinalizar arquivos conflitantes, interromper; não executar `reset --hard`, `clean` ou apagar arquivos.

No FLUXOR: **Organização segura → Por tipo, ano e mês**. Selecionar uma **origem pequena de teste** e uma pasta de destino local diferente; rodar somente **Pré-visualizar** primeiro. Confirmar a hierarquia antes de autorizar cópia. Repetir, apenas em modo leitura, com `~/Downloads` por **Usar caminho**, e testar uma pasta de volume efetivamente montado em `/Volumes` — **não** usar `/Volumes/SAMSUNG` no MacBook se este só existir no Mac Mini.

## Governança

Branch isolada, PR em draft. Nenhum merge, deploy, publicação, acesso ao HD Samsung ou modificação de dados do usuário foi realizado por esta implementação.
