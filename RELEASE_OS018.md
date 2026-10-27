# FLUXOR — OS018 | Black / Silver / Gold · Zen Sand

## Por que esta versão existe

O usuário determinou substituir a direção fluorescente e o lettering central por uma identidade de **preto fosco / preto brilhante / grafite / prata / dourado**. O logotipo, apenas no painel esquerdo, é horizontal, de duas tintas e influenciado por throw-up/bombe. O centro não deve ter logotipo, fotografia ou ferramenta 3D: deve funcionar como uma **animação de proteção de tela** inspirada nos sulcos deixados por um rastelo num jardim japonês.

## Implementado

- `fluxor_brand.py`: wordmark FLUXOR horizontal, vetorial e escalável, com face prata e segunda camada dourada; ícone de janela transparente com signo F, sem o antigo quadrado.
- `fluxor_mural.py`: motor procedural de sulcos na areia, renderizado com QPainter, faixas horizontais progressivas, deslocamento esquerda→direita e direita→esquerda, 7 faixas, troca de passe/cor com reescrita sobre as linhas anteriores. Traços quase retos, curvas discretas apenas nas transições de segmentos e pequenos indicadores direcionais. Sem vídeo, WebEngine, arquivo em nuvem, stock media ou renderização fotográfica.
- `fluxor_design.py`: tema completo preto/prata/dourado suave, sem neon.
- `fluxor_iniciar.py`: só mantém marca na esquerda; motor zen central, comandos úteis de Biblioteca/Organização e resumo real de acervo. Corrigidos singular/plural e a exibição inadequada de acervos pequenos como 0,00 GB.

## Segurança

- Branch isolada: `dev/zen-sand-luxury-os018`.
- PR em rascunho, **sem merge ou publicação**.
- Motor de indexação e cópia segura preservado. Originais nunca são apagados automaticamente.
- O teste utiliza dados sintéticos em diretórios temporários. O disco SAMSUNG e a rede não são acessados pelo CI.
- O navegador SFTP interno do FLUXOR permanece como OS separada.

## CI

Workflow: `.github/workflows/mvp-checks.yml`.
- Regressões de arquivos, integridade, catálogos, rollback, desempenho e segurança continuam.
- GUI OS014/015/016/017/018 testam navegação, animação, pausa, estados e integração.
- Os primeiros jobs OS018 reproduziram uma falha de **finalização do interpretador Python/PySide6 no Linux offscreen** após testes gráficos que capturavam QPixmap/screenshot. A captura foi isolada/removida do teste funcional; as asserções de pintura de versões anteriores permanecem, além das regressões de estado da animação OS018. Com essa separação a suíte terminou em sucesso.
- Essa resolução **não comprova** que o bug do backend gráfico Linux foi corrigido: o fluxo de screenshots automatizadas continua pendente de investigação isolada. Não esconder essa limitação, não alegar 100% de compatibilidade entre todos os hosts Qt.

## Homologação local (MacBook Pro macOS Catalina)

1. Fechar o Fluxor atual e garantir que nenhuma análise/cópia esteja em andamento.
2. No terminal:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-zen-os018 --track origin/dev/zen-sand-luxury-os018
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Se houver conflito local, **parar**. Não usar `git reset --hard`, `git clean` nem apagar os dados.

### Verificar

1. Topo da sidebar: logo horizontal FLUXOR, prata e dourado; não existe logo central nem bloco quadrado.
2. Centro: linhas de areia surgem em passadas por faixas, da esquerda para a direita e de volta, descendo ao longo da animação; depois uma segunda tonalidade redesenha o cenário.
3. Pausar animação: o fluxo para imediatamente, sem prejudicar o restante do software.
4. Biblioteca: sem seleção, lista usa a largura total; clicar num arquivo abre Inspector; fechar devolve espaço à lista.
5. Organização: seleção de origem/destino, prévia obrigatória e relatório visível, sem alterar originais.
6. Em MacBook antigo: verificar suavidade real, uso de CPU, alinhamento do wordmark, ausência de efeitos neon e presença de contraste adequado.

A implementação é uma **candidata à homologação visual** e não um instalador final assinado.
