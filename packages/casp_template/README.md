# CASP template (`base.package`)

`base.package` é o acessório CAS (CASP) da placa da foto: um quad plano de 22 x 28 cm, 1 cm à frente do
rosto, preso 100% ao osso `b__Head__`. Foi criado em 2026-10-23 no Sims4Studio 3.2.6.5 (Star), num
Windows com o jogo instalado, clonando uns óculos do jogo base. Ocupa o slot de **óculos**: um Sim com a
foto não usa óculos ao mesmo tempo.

| Recurso | Tipo | Instance |
|---|---|---|
| CASP | `0x034AEECB` | `0xC4A9939F6D089983` |
| GEOM (6: LODs 0-3, cuts 0 e 1) | `0x015A1849` | `0x7A74B38D1DBA4523` |
| RegionMap | `0xAC16FBEC` | `0x7A74B38D1DBA4523` |
| Diffuse (RLE2) | `0x3453CF95` | `0xE9AE743A020F1D1E` |

## Onde a foto fica na textura

O jogo compõe todas as peças do Sim num atlas único de **1024 x 2048**. A região dos óculos, e portanto a
da foto, é o retângulo **x 512..768, y 128..256** (256 x 128 px). Fora dele a textura deve ser transparente.
`placeholder_atlas.png` é o exemplo: uma carinha amarela nesse retângulo. A foto é esticada para 256 x 128
e aparece de novo esticada no quad retrato. É tosco de propósito.

## Como foi criado (para refazer)

1. Sims4Studio → CAS → Create CAS Standalone → buscar `glasses` → escolher os óculos de aro preto do jogo
   base → Next → salvar como `PhotoFace_base.package`.
2. Aba Meshes → LOD 0 → Export Mesh → `glasses_lod0.blend`.
3. Gerar o quad com o Blender 3.6 (o mesmo que o Sims4Studio usa, configurado em Settings → Blender Path):

   ```
   blender.exe -b glasses_lod0.blend --python flat_quad.py -- photoface_quad.blend
   ```

   O script troca a cut 0 pelo quad, com o UV no retângulo acima, e reduz a cut 1 (as lentes) a um triângulo de
   1 mm dentro da cabeça. Se o objeto sumisse, o Sims4Studio manteria a geometria original dessa cut, e
   malha vazia ele recusa.
4. Aba Meshes → Import Mesh com `photoface_quad.blend` em **cada uma** das LODs 0 a 3.
5. Aba Texture → Diffuse → Import → `placeholder_atlas.png` → Save.

O Sims4Studio é só GUI. Esse passo é raro: só se repete se a placa mudar. O dia a dia (uma foto por Sim)
passa só pela companion tool.
