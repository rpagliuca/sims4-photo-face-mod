# Photo Face Mod — The Sims 4

[![CI](https://github.com/rpagliuca/sims4-photo-face-mod/actions/workflows/ci.yml/badge.svg)](https://github.com/rpagliuca/sims4-photo-face-mod/actions/workflows/ci.yml)

Atribui uma foto de perfil a um Sim específico no The Sims 4. A foto aparece
**sempre sobreposta ao rosto do Sim**, de um jeito **deliberadamente
tosco**: um acessório 2D plano preso à cabeça, sem nenhuma tentativa de
perspectiva 3D. O tosco é feature, não bug — é a única abordagem
tecnicamente viável no engine do TS4 para esse efeito (billboard real
"sempre de frente pra câmera" não existe para nada anexado ao Sim; ver
[`docs/base-de-conhecimento.html`](docs/base-de-conhecimento.html)).

## Como funciona (visão rápida)

1. Um acessório CAS (`.package`, formato DBPF) plano, preso ao osso da
   cabeça, no slot de óculos: o template `packages/casp_template/base.package`.
2. Uma **companion tool** (Node.js + [Sims4Toolkit](https://github.com/sims4toolkit))
   clona esse acessório para cada foto (CASP novo + textura RLE2 com a foto)
   e acumula tudo num único `.package`.
3. Um **script mod** Python (`.ts4script`) guarda qual acessório pertence a
   qual Sim (persistente entre save/load), o põe em todas as roupas e o
   reaplica quando um lote termina de carregar. Um comando de console
   (`photofacemod.assign <foto>`) atribui a foto ao Sim selecionado.

**História do projeto, com prints:** https://rpagliuca.github.io/sims4-photo-face-mod/historia/

Documentação completa (arquitetura, build, instalação, testes) em
[`docs/`](docs/index.html).

## Estrutura do repositório

```
src/                 # script mod Python (.ts4script)
companion/           # companion tool Node.js+S4TK (injeção de foto no .package)
packages/            # fontes/templates dos .package (CASP)
build/               # scripts de build (Linux → artefatos prontos p/ Windows)
tests/               # pytest (mod) + node:test (companion tool)
docs/                # documentação HTML: base de conhecimento, compilação, instalação, testes
.github/workflows/   # CI
```

## Quickstart

```bash
# testes do mod Python
pip install -r requirements-dev.txt && pytest -q

# testes da companion tool
cd companion && npm install && npm test

# build do .ts4script
python build/build_ts4script.py
```

Veja [`docs/compilacao.html`](docs/compilacao.html) para o build completo e
[`docs/instalacao.html`](docs/instalacao.html) para instalar no jogo
(Windows).

## Status

Projeto em desenvolvimento ativo. Validação final in-game (Windows) é
manual — ver [`docs/testes.html`](docs/testes.html) para o que é e não é
testável automaticamente.

## Licença

MIT — ver [`LICENSE`](LICENSE).
