# CASP template (`base.package`)

Este diretório deve conter `base.package`: um acessório CAS (CASP) plano,
categoria "Hats"/acessório de cabeça, preso ao osso `b__Head__`, com **N
swatches** (variações de cor/textura) reservados para as fotos dos Sims. A
companion tool (`companion/`) clona esse template e substitui a textura de
cada swatch pela foto convertida de cada Sim.

`base.package` **não é gerado automaticamente por padrão** (ver limitação
abaixo) — ele não está commitado neste diretório até que exista um build
válido. `.gitignore` do repo ignora `*.package` de propósito; se você gerar
um `base.package` válido, adicione uma exceção específica para este arquivo
ou commite-o via `git add -f`.

## Como é criado

Sims4Studio (ferramenta da comunidade, GUI-only, sem CLI/batch mode
documentado — ver `docs/base-de-conhecimento.html`) é usado para:

1. Novo projeto CAS Part → categoria acessório de cabeça (Hats/Accessory)
2. Import de uma geometria plana simples (um "quad"/plano) via mesh
   customizado (Blender → exportar, ou usar um plano já existente de algum
   template de acessório da comunidade como base)
3. Rig/vincular ao osso `b__Head__` (peso de vértice 100% nesse osso —
   nenhum outro osso deve influenciar, para o "tosco" ficar rígido e
   previsível)
4. Criar N swatches (recomendado: pelo menos 8-16 para começar) — cada
   swatch é só um placeholder de textura nesta etapa; a companion tool
   substitui a textura de cada swatch depois
5. Exportar como `.package`

## Limitação conhecida: automação via Wine no CI

O projeto tenta automatizar esse processo via Wine no CI (ver
`build/wine_casp/`), mas **isso é experimental e não está validado**: eu
(o agente que escreveu este código) não tenho acesso a Windows, Wine, nem
ao Sims4Studio real para testar a automação de UI (cliques/teclado) contra
a janela de verdade — escrever coordenadas/sequências de teclas "no escuro"
seria fingir precisão que não existe. O scaffold em `build/wine_casp/`
prepara o ambiente (Wine + .NET Desktop Runtime + download do instalador)
mas o passo final de automação de UI está deliberadamente marcado como
`NotImplementedError` com instruções do que falta.

**Alternativa recomendada (mais rápida e confiável): o Rafael faz esse
passo manualmente uma vez** no Windows (onde o jogo já roda para testes),
usando o Sims4Studio normalmente, e commita o `base.package` resultante
aqui. A partir daí, todo o resto do pipeline (re-texturizar por Sim via
companion tool) é 100% automatizado.

Se quiser tentar de qualquer forma terminar a automação via Wine, o job de
CI em `.github/workflows/ci.yml` (`casp-template-wine`, `continue-on-error:
true`) é o lugar para iterar — rode localmente com um VNC/X11 visível
(`Xvfb :99 -screen 0 1280x1024x24 &` + `x11vnc` ou `xdotool
getmouselocation`/`xdotool key`) para descobrir a sequência real de cliques
do Sims4Studio, e substitua o `NotImplementedError` em
`build/wine_casp/automate_casp.py` pela sequência validada.
