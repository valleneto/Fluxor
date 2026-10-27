# FLUXOR — apresentação OS019 restaurada sobre base OS021

- **27/10/2026, referência de aceitação:** a mensagem original de entrega OS019 (PR #6) foi fornecida pelo usuário; a interface OS021 foi rejeitada.
- **Branch de revisão visual:** `dev/os021-apresentacao-os019-20261027`, partindo da OS021 `69e53f3be64836670a39018bab0b51cbf4208c7c`.
- **Restaurado de forma idêntica:** arquivo `fluxor_brand.py` da PR #6, com lettering FLUXOR em prata/dourado original daquela entrega.
- **Organizador:** volta a exibir apenas os dois botões OS019 **Escolher origem** e **Escolher destino**, preservando o menu de acrescentar à organização existente.
- **Biblioteca:** linha de ações original, sem botão SMB extra.
- **Rede:** botão **Conectar SMB (Finder)…** agora somente dentro do seletor de pasta; scanner assíncrono, paginação por cursor e navegação por caminhos montados permanecem da OS021.
- **Critérios avançados:** permanecem disponíveis sob escolha explícita **Combinar critérios (ordenar)** no seletor de modo, sem ocupar espaço da tela de organização por padrão.
- **Sem regressão intencional:** arquivos `fluxor_core`, proteção de prévia incompleta, índices SQL, deduplicação SHA-256 e política de critérios da OS021 mantidos. Animação central e `fluxor_design.py` eram byte a byte idênticos em OS019 e OS021.
- **Limites:** sem acesso físico ao MacBook ou Samsung; nenhum merge/deploy/release; apenas PR draft. Testes automatizados são sintéticos.
- **Visual:** a referência validada é exatamente o código da OS019, não as fotos de grafite originais; se houver diferença entre código e imagens locais, homologar com a tela do Mac.
