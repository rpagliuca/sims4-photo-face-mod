# Roda no Blender (com o add-on do Sims4Studio) sobre o .blend exportado de um acessório de rosto
# (óculos): troca a geometria por um quad plano na frente do rosto, UV 0..1, 100% no osso b__Head__.
# Uso: blender.exe -b entrada.blend --python flat_quad.py -- saida.blend
import bpy, bmesh, sys
from mathutils import Vector

out = sys.argv[sys.argv.index('--') + 1]
try:
    import addon_utils
    addon_utils.enable('io_sims')  # registra Mesh.s4studio (o S4S instala o add-on ao exportar)
except Exception as e:
    print('add-on io_sims nao habilitado:', e)

def cut_of(o):
    try:
        return o.data.s4studio.cut
    except AttributeError:
        return (o.data.get('s4studio') or {}).get('cut', '')

meshes = [o for o in bpy.data.objects if o.type == 'MESH' and cut_of(o) != '']
print('objetos de malha:', [(o.name, cut_of(o)) for o in meshes])
assert meshes, 'nenhuma malha com cut do S4S'
# bbox de todas as partes dos óculos (aro, lentes)
pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
meshes.sort(key=lambda o: int(cut_of(o) or 0))
obj = meshes[0]
mw = obj.matrix_world
# as outras cuts viram um triângulo de 1 mm dentro da cabeça: se o objeto sumisse, o S4S
# manteria a geometria original delas, e malha vazia o S4S recusa
def tiny_triangle(o, center):
    bm = bmesh.new()
    bm.from_mesh(o.data)  # preserva as camadas de UV
    bmesh.ops.delete(bm, geom=list(bm.verts), context='VERTS')
    inv_o = o.matrix_world.inverted()
    d = 0.001
    offs = ((0, 0, 0), (d, 0, 0), (0, 0, d))  # UV num canto transparente do atlas
    vs_ = [bm.verts.new(inv_o @ (center + Vector(off))) for off in offs]
    f = bm.faces.new(vs_)
    for layer in bm.loops.layers.uv.values():
        for loop in f.loops:
            off = offs[vs_.index(loop.vert)]
            loop[layer].uv = (0.01 + off[0] * 10, 0.01 + off[2] * 10)
    bm.to_mesh(o.data)
    bm.free()
    for g in list(o.vertex_groups):
        if g.name != 'b__Head__':
            o.vertex_groups.remove(g)
    hg = o.vertex_groups.get('b__Head__') or o.vertex_groups.new(name='b__Head__')
    hg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
print('bbox oculos', tuple(mn), tuple(mx))
cx, cz = (mn.x + mx.x) / 2, (mn.z + mx.z) / 2
# frente do Sim = -Y no Blender (o S4S gira -90 graus em X ao gravar)
y = mn.y - 0.04  # 4 cm à frente dos óculos: com 1 cm o nariz atravessava a placa
W, H = 0.22, 0.28  # tamanho aproximado de um rosto adulto, em metros
cz -= 0.03         # óculos ficam na altura dos olhos; o centro do rosto é um pouco abaixo
for extra in meshes[1:]:
    tiny_triangle(extra, Vector((cx, (mn.y + mx.y) / 2 + 0.05, cz)))
    print('cut', cut_of(extra), 'virou triangulo de 1 mm')

inv = mw.inverted()
corners = [Vector((cx - W/2, y, cz - H/2)), Vector((cx + W/2, y, cz - H/2)),
           Vector((cx + W/2, y, cz + H/2)), Vector((cx - W/2, y, cz + H/2))]
uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

me = obj.data
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.delete(bm, geom=list(bm.verts), context='VERTS')
vs = [bm.verts.new(inv @ c) for c in corners]
face = bm.faces.new(vs)
bm.normal_update()
if (mw.to_3x3() @ face.normal).y > 0:
    face.normal_flip()
# UV pela posição no mundo: esquerda de quem olha o Sim (-X, o lado direito dele) = u 0;
# base = v 0 (no Blender v cresce para cima; o S4S grava 1 - v)
# O jogo compõe todas as peças do Sim num atlas 1024x2048; a região dos óculos é
# x 512..768, y 128..256 (uv_0: u 0.5..0.75, v 0.875..0.9375). A foto vai nesse retângulo.
# uv_1 recebe a faixa original dos óculos.
# 2 px para dentro do retângulo: na borda o filtro de textura puxava a vizinhança do atlas
IN_U, IN_V = 2 / 1024, 2 / 2048
UV_RECT = {'uv_0': (0.5 + IN_U, 0.75 - IN_U, 0.875 + IN_V, 0.9375 - IN_V), 'uv_1': (-0.867, 0.867, 0.867, 0.955)}
for name, layer in bm.loops.layers.uv.items():
    u0, u1, v0, v1 = UV_RECT.get(name, (0, 1, 0, 1))
    for loop in face.loops:
        w = mw @ loop.vert.co
        fx, fz = (w.x - (cx - W/2)) / W, (w.z - (cz - H/2)) / H
        loop[layer].uv = (u0 + (u1 - u0) * fx, v0 + (v1 - v0) * fz)
bm.to_mesh(me)
bm.free()

head = obj.vertex_groups.get('b__Head__') or obj.vertex_groups.new(name='b__Head__')
for g in list(obj.vertex_groups):
    if g.name != 'b__Head__':
        obj.vertex_groups.remove(g)
head.add(range(len(me.vertices)), 1.0, 'REPLACE')
me.update()
print('quad pronto:', len(me.vertices), 'vertices, uv layers', [l.name for l in me.uv_layers])
bpy.ops.wm.save_as_mainfile(filepath=out)
