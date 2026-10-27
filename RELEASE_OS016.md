# FLUXOR OS016 — Design premium aprovado: implementação isolada

## Objetivo

Aplicar o design anteriormente combinado **antes** de iniciar a integração de rede: premium Apple-like / Arc / Linear, grafite profundo + azul-gelo discreto, visual limpo, tipografia nativa, microanimação leve e utilidade em cada elemento. Sem fotografia central, sem gráfico arbitrário, sem visual gamer/neon, sem novas dependências ou fontes externas.

## Alterações concretas

1. **Design system** em `fluxor_design.py`: tokens de cor, estados de foco, ações primárias, botões de navegação, tabelas, painéis, barras de progresso e rolagem.
2. **Visão geral** em `fluxor_iniciar.py`: nome FLUXOR e logo local preservados; navegação lateral com estado ativo; hierarquia editorial; painel Zen procedural no centro, ações reais de Biblioteca/Organização e estatística do acervo existente. Texto supérfluo sobre animação removido.
3. **Zen Core** em `fluxor_zen.py`: campo de linhas vetoriais fluidas, no máximo 20 fps, apenas quando visível; opção de reduzir movimento; diferencia estados reais, não simula porcentagem.
4. **Biblioteca**: seletores úteis em primeiro plano; filtros secundários recolhidos; lista priorizada. Inspector contextual da OS015 preservado (não aparece sem seleção).
5. **Organização segura**: painéis ACERVO, ORGANIZAÇÃO e RELATÓRIO; escolher origem/destino; prévia antes de copiar; nenhum arquivo apagado. Relatório permanece fora da rolagem de controles em telas menores; progresso e logs visíveis. Estimativa aproximada somente durante cópia, calculada a partir do tempo observado por arquivo, com ressalva de variabilidade.

## Segurança

- Branch: `dev/design-premium-os016`, baseada em `dev/inspector-contextual-20261026`.
- PR draft, sem merge, deploy, release ou instalação automática.
- Não toca no HD Samsung, nem nas pastas pessoais do usuário.
- A OS016 não implementa SFTP integrado ao Fluxor; o protocolo segue disponível externamente à aplicação.

## Testes

- Workflow `.github/workflows/mvp-checks.yml` — sintaxe, testes funcionais existentes, GUI Qt offscreen OS014, OS015 e OS016.
- `tests/test_os016_gui.py` valida identidade, estado da navegação, redução de movimento, lista/Inspector inicial, três etapas e visibilidade do relatório inclusive a 900×580.
- Linux CI não substitui homologação visual real no macOS Catalina.

## Homologação no MacBook Pro

**Fechar antes a janela do Fluxor atualmente em execução** para não misturar operações. Depois:

```bash
cd ~/Projetos/google-fotos-lab
git status --short
git fetch origin
git switch -c homologacao-design-os016 --track origin/dev/design-premium-os016
source .venv/bin/activate
python3 fluxor_iniciar.py
```

Se o Git indicar arquivos locais conflitantes, **não executar** `git reset --hard`, `git clean` ou deleção de pastas: interromper e rever o estado.

### Critérios manuais
1. Tela inicial mostra marca FLUXOR e centro animado discreto, sem fotografia e sem gráfico de progresso fictício.
2. Alternância Voltar/Avançar/Início e barra lateral indicam a seção ativa.
3. Checkbox Reduzir movimento pausa a animação.
4. Biblioteca sem seleção utiliza toda a área, seleção mostra Inspector, Fechar × devolve a área; filtros ficam recolhidos.
5. Organização apresenta origem, destino, modo e prévia; RELATÓRIO visível inclusive em tela menor.
6. Para testar motor de cópia, usar apenas arquivos sintéticos ou cópias e **destino distinto**, nunca o Samsung.
