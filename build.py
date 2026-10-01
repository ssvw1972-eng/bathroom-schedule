# Bathroom model. Clear size 10 ft 8 in x 9 ft 4 in x 9 ft 0 in.
# Finish: Brodware Weathered Brass Organic (unlacquered living bronze).
import math
import bpy
import bmesh
from mathutils import Vector

L = 10 * 0.3048 + 8 * 0.0254   # 3.2512 m
W = 9 * 0.3048 + 4 * 0.0254    # 2.8448 m
H = 9 * 0.3048                 # 2.7432 m ceiling, assumed
T = 0.10                       # wall thickness outside the clear size

OUT = r"C:\Users\OFFICE\Downloads\bathroom-model"

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
    for d in list(block):
        if d.users == 0:
            block.remove(d)

scene = bpy.context.scene
col = scene.collection

def link(obj):
    col.objects.link(obj)
    return obj

def new_mesh(name, bm):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    link(obj)
    return obj

def box(name, cx, cy, cz, sx, sy, sz, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    obj = new_mesh(name, bm)
    obj.location = (cx, cy, cz)
    obj.scale = (sx, sy, sz)
    if mat:
        obj.data.materials.append(mat)
    return obj

def cyl(name, cx, cy, cz, r, depth, mat, rot=(0, 0, 0), segs=28):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segs,
        radius1=r, radius2=r, depth=depth,
    )
    obj = new_mesh(name, bm)
    obj.location = (cx, cy, cz)
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    return obj

def ico(name, cx, cy, cz, r, mat, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    obj = new_mesh(name, bm)
    obj.location = (cx, cy, cz)
    if mat:
        obj.data.materials.append(mat)
    return obj

def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def make_mat(name, color, rough=0.45, metal=0.0, emit=0.0, emit_color=None, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.45
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m

def travertine(name, base, scale=18.0, strength=0.18):
    m = make_mat(name, base, rough=0.72, metal=0.0)
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.55
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = (base[0] * 0.82, base[1] * 0.84, base[2] * 0.80, 1)
    mix.inputs["B"].default_value = (min(base[0] * 1.12, 1), min(base[1] * 1.08, 1), min(base[2] * 1.05, 1), 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    nt.links.new(noise.outputs["Fac"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m

def oak(name):
    m = make_mat(name, (0.32, 0.20, 0.11), rough=0.55, metal=0.0)
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = 'BANDS'
    wave.inputs["Scale"].default_value = 8.0
    wave.inputs["Distortion"].default_value = 1.2
    wave.inputs["Detail"].default_value = 4.0
    mapping = nt.nodes.new("ShaderNodeMapping")
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping.inputs["Scale"].default_value = (0.35, 3.5, 1.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs["A"].default_value = (0.28, 0.17, 0.09, 1)
    mix.inputs["B"].default_value = (0.40, 0.26, 0.14, 1)
    nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m

trav = travertine("Travertine", (0.72, 0.64, 0.50), 14.0, 0.22)
trav_dark = travertine("TravertineTrough", (0.55, 0.48, 0.36), 22.0, 0.12)
plaster = travertine("Plaster", (0.86, 0.80, 0.70), 6.0, 0.04)
wood = oak("SmokedOak")
bronze = make_mat("Bronze", (0.52, 0.30, 0.13), rough=0.38, metal=1.0)
bronze_dark = make_mat("BronzeDark", (0.32, 0.18, 0.08), rough=0.46, metal=1.0)
ceramic = make_mat("Ceramic", (0.92, 0.91, 0.88), rough=0.18, metal=0.0)
mirror_mat = make_mat("Mirror", (0.85, 0.84, 0.80), rough=0.02, metal=1.0)
leaf = make_mat("Leaf", (0.28, 0.38, 0.20), rough=0.55)
leaf_dark = make_mat("LeafDark", (0.16, 0.24, 0.12), rough=0.6)
clay = travertine("Clay", (0.45, 0.32, 0.22), 30.0, 0.08)
water = make_mat("Water", (0.55, 0.58, 0.55), rough=0.04, metal=0.0, transmission=0.85)
glow = make_mat("Glow", (1.0, 0.78, 0.50), rough=0.4, emit=2.2, emit_color=(1.0, 0.72, 0.42))
gap = make_mat("ShadowGap", (0.08, 0.07, 0.06), rough=0.8)
metal_soft = make_mat("SoftMetal", (0.55, 0.52, 0.46), rough=0.35, metal=1.0)

# ---------- shell ----------
box("Floor", L / 2, W / 2, -0.04, L, W, 0.08, trav)
box("Ceiling", L / 2, W / 2, H + 0.04, L, W, 0.08, plaster)

# south wall, vanity side, solid
box("WallS", L / 2, -T / 2, H / 2, L + 2 * T, T, H, plaster)
# north wall
box("WallN", L / 2, W + T / 2, H / 2, L + 2 * T, T, H, plaster)
# east wall
box("WallE", L + T / 2, W / 2, H / 2, T, W, H, plaster)
# west wall with a door. Opening starts 1 ft 4 in from the south corner.
door_y0 = 0.406
door_y1 = door_y0 + 0.86
door_h = 2.10
box("WallW_low", -T / 2, door_y0 / 2, H / 2, T, door_y0, H, plaster)
box("WallW_high", -T / 2, (door_y1 + W) / 2, H / 2, T, W - door_y1, H, plaster)
box("WallW_head", -T / 2, (door_y0 + door_y1) / 2, (door_h + H) / 2, T, door_y1 - door_y0, H - door_h, plaster)
# door slab, ajar into the room
box("Door", 0.03, (door_y0 + door_y1) / 2 - 0.18, door_h / 2, 0.04, 0.82, door_h, wood)
box("DoorFrameL", 0.0, door_y0 - 0.02, door_h / 2, 0.06, 0.04, door_h, wood)
box("DoorFrameR", 0.0, door_y1 + 0.02, door_h / 2, 0.06, 0.04, door_h, wood)

# skirting on dry walls
box("SkirtS", L / 2, 0.012, 0.04, L, 0.024, 0.08, wood)
box("SkirtE", L - 0.012, W / 2, 0.04, 0.024, W, 0.08, wood)

# ---------- vanity: south wall ----------
# Counter almost the full 10 ft 8 in. Trough centred. Plants on the two ends.
vx0, vx1 = 0.10, L - 0.10
vy0, vy1 = 0.0, 0.52
counter_z = 0.90
top_t = 0.045
box("VanityCarcass", (vx0 + vx1) / 2, 0.20, 0.42, vx1 - vx0 - 0.06, 0.32, 0.78, wood)
# toe kick shadow
box("ToeKick", (vx0 + vx1) / 2, 0.06, 0.04, vx1 - vx0 - 0.08, 0.06, 0.08, gap)
# two cabinet breaks
box("VanityRail", (vx0 + vx1) / 2, vy1 - 0.02, 0.46, 0.012, 0.02, 0.70, bronze_dark)

# stone top as a frame around the trough so the spout lands in the channel
tx0, tx1 = 0.72, 2.54          # trough 1.82 m, clear of the plant ends
ty0, ty1 = 0.14, 0.46
tz_floor = 0.78
# left, right, front, back lips, and the trough floor
box("TopLeft", (vx0 + tx0) / 2, (vy0 + vy1) / 2 + 0.01, counter_z + top_t / 2, tx0 - vx0, vy1 - vy0, top_t, trav)
box("TopRight", (tx1 + vx1) / 2, (vy0 + vy1) / 2 + 0.01, counter_z + top_t / 2, vx1 - tx1, vy1 - vy0, top_t, trav)
box("TopBack", (tx0 + tx1) / 2, (vy0 + ty0) / 2, counter_z + top_t / 2, tx1 - tx0, ty0 - vy0, top_t, trav)
box("TopFront", (tx0 + tx1) / 2, (ty1 + vy1) / 2, counter_z + top_t / 2, tx1 - tx0, vy1 - ty1, top_t, trav)
box("TroughFloor", (tx0 + tx1) / 2, (ty0 + ty1) / 2, tz_floor, tx1 - tx0 - 0.04, ty1 - ty0 - 0.04, 0.025, trav_dark)
box("TroughWallL", tx0 + 0.012, (ty0 + ty1) / 2, (tz_floor + counter_z) / 2, 0.02, ty1 - ty0, counter_z - tz_floor, trav)
box("TroughWallR", tx1 - 0.012, (ty0 + ty1) / 2, (tz_floor + counter_z) / 2, 0.02, ty1 - ty0, counter_z - tz_floor, trav)
box("TroughWallB", (tx0 + tx1) / 2, ty0 + 0.012, (tz_floor + counter_z) / 2, tx1 - tx0, 0.02, counter_z - tz_floor, trav)
box("TroughWallF", (tx0 + tx1) / 2, ty1 - 0.012, (tz_floor + counter_z) / 2, tx1 - tx0, 0.02, counter_z - tz_floor, trav)
box("Water", (tx0 + tx1) / 2, (ty0 + ty1) / 2, tz_floor + 0.03, tx1 - tx0 - 0.08, ty1 - ty0 - 0.06, 0.006, water)
# waste
cyl("Waste", (tx0 + tx1) / 2, (ty0 + ty1) / 2, tz_floor + 0.02, 0.028, 0.01, bronze, rot=(0, 0, 0))

# wall spout, 200 mm projection, pin lever of a City Stik mixer
spout_x = (tx0 + tx1) / 2
spout_z = 1.02
cyl("Spout", spout_x, 0.10, spout_z, 0.014, 0.20, bronze, rot=(math.pi / 2, 0, 0))
cyl("SpoutRose", spout_x, 0.012, spout_z, 0.028, 0.012, bronze, rot=(math.pi / 2, 0, 0))
cyl("SpoutTip", spout_x, 0.20, spout_z, 0.011, 0.02, bronze, rot=(math.pi / 2, 0, 0))
cyl("MixerPin", spout_x - 0.09, 0.045, spout_z + 0.02, 0.008, 0.07, bronze, rot=(math.pi / 2, 0, 0))
cyl("MixerRosette", spout_x - 0.09, 0.008, spout_z, 0.022, 0.01, bronze, rot=(math.pi / 2, 0, 0))

# mirror, full width of the counter, warm halo in the shadow gap
mx0, mx1 = vx0, vx1
mz0, mz1 = 1.20, 2.28
box("MirrorGap", (mx0 + mx1) / 2, 0.004, (mz0 + mz1) / 2, mx1 - mx0 + 0.02, 0.008, mz1 - mz0 + 0.02, gap)
box("MirrorGlow", (mx0 + mx1) / 2, 0.006, (mz0 + mz1) / 2, mx1 - mx0 + 0.012, 0.004, mz1 - mz0 + 0.012, glow)
box("Mirror", (mx0 + mx1) / 2, 0.012, (mz0 + mz1) / 2, mx1 - mx0, 0.008, mz1 - mz0, mirror_mat)

# plants: low pot at the left end, taller vase at the right, both outside the trough
def foliage(x, y, z, height, count, spread):
    for i in range(count):
        ang = i * 2.399
        rad = spread * (0.25 + 0.75 * ((i * 3) % 5) / 5)
        px = x + rad * math.cos(ang)
        py = y + rad * math.sin(ang)
        h = height * (0.55 + 0.45 * ((i * 5) % 7) / 7)
        cyl(f"Stem_{x:.2f}_{i}", px, py, z + h / 2, 0.0035, h, leaf_dark, segs=6)
        ico(f"Leaf_{x:.2f}_{i}", px, py, z + h, 0.045 + 0.01 * (i % 3), leaf if i % 2 == 0 else leaf_dark, sub=1)

pot_x, pot_y = 0.38, 0.28
cyl("SaucerL", pot_x, pot_y, counter_z + top_t + 0.006, 0.105, 0.012, clay)
cyl("Pot", pot_x, pot_y, counter_z + top_t + 0.07, 0.085, 0.11, clay)
cyl("PotRim", pot_x, pot_y, counter_z + top_t + 0.125, 0.092, 0.018, clay)
foliage(pot_x, pot_y, counter_z + top_t + 0.12, 0.28, 9, 0.07)

vase_x, vase_y = L - 0.38, 0.27
cyl("SaucerR", vase_x, vase_y, counter_z + top_t + 0.006, 0.075, 0.01, clay)
cyl("Vase", vase_x, vase_y, counter_z + top_t + 0.16, 0.055, 0.30, clay)
cyl("VaseNeck", vase_x, vase_y, counter_z + top_t + 0.33, 0.032, 0.06, clay)
foliage(vase_x, vase_y, counter_z + top_t + 0.34, 0.42, 7, 0.05)

# ---------- shower, north-west ----------
# Clear shower 5 ft 6 in wide by 4 ft 5 in deep, open to the walkway.
sx0, sx1 = 0.0, 1.68
sy0, sy1 = 1.50, W
box("ShowerFloor", (sx0 + sx1) / 2, (sy0 + sy1) / 2, 0.005, sx1 - sx0, sy1 - sy0, 0.01, trav)
# linear drain at the open edge
box("LinearDrain", (sx0 + sx1) / 2, sy0 + 0.04, 0.012, sx1 - sx0 - 0.12, 0.018, 0.008, bronze_dark)
# divider between shower and WC, stops at 2.10 so the ceiling reads as one room
box("Divider", 1.74, (sy0 + W) / 2, 1.05, 0.08, W - sy0, 2.10, trav)

# ceiling rose, 300 mm, one head with normal / rain / waterfall modes
rose_x, rose_y = (sx0 + sx1) / 2, (sy0 + 0.25 + W) / 2
cyl("RoseArm", rose_x, rose_y, H - 0.04, 0.018, 0.08, bronze)
cyl("Rose", rose_x, rose_y, H - 0.085, 0.15, 0.018, bronze)
cyl("RoseFace", rose_x, rose_y, H - 0.096, 0.135, 0.006, bronze_dark)

# hand shower on the west wall
bar_y = 1.95
cyl("SlideBar", 0.025, bar_y, 1.25, 0.008, 0.70, bronze)
cyl("HandHolder", 0.05, bar_y, 1.40, 0.012, 0.04, bronze, rot=(0, math.pi / 2, 0))
cyl("HandHead", 0.09, bar_y, 1.36, 0.028, 0.09, bronze, rot=(math.pi / 2, 0, 0.4))
cyl("Hose", 0.06, bar_y + 0.02, 1.05, 0.006, 0.40, bronze_dark)

# four body jets on the north wall: shoulders and hips, 300 mm apart
jet_xs = (rose_x - 0.15, rose_x + 0.15)
jet_zs = (1.40, 0.90)
for i, jx in enumerate(jet_xs):
    for j, jz in enumerate(jet_zs):
        cyl(f"Jet_{i}{j}", jx, W - 0.015, jz, 0.022, 0.03, bronze, rot=(math.pi / 2, 0, 0))
        cyl(f"JetFace_{i}{j}", jx, W - 0.032, jz, 0.012, 0.006, bronze_dark, rot=(math.pi / 2, 0, 0))

# thermostatic trim on the west wall, reached from the walkway
cyl("ThermoPlate", 0.02, 1.62, 1.15, 0.045, 0.012, bronze, rot=(0, math.pi / 2, 0))
cyl("ThermoLever", 0.055, 1.62, 1.15, 0.007, 0.09, bronze, rot=(0, math.pi / 2, 0))
cyl("Diverter", 0.02, 1.78, 1.15, 0.028, 0.012, bronze, rot=(0, math.pi / 2, 0))

# ---------- WC, north-east ----------
wc_x = 2.52
# TOTO RP roughly 380 x 490 x 330, wall-hung
box("WCBowl", wc_x, W - 0.26, 0.40, 0.38, 0.50, 0.28, ceramic)
box("WCSeat", wc_x, W - 0.27, 0.55, 0.36, 0.46, 0.04, ceramic)
cyl("WCHole", wc_x, W - 0.30, 0.555, 0.10, 0.02, gap)
# flush plate
box("FlushPlate", wc_x, W - 0.008, 1.05, 0.22, 0.008, 0.14, bronze)
box("FlushButton", wc_x, W - 0.014, 1.05, 0.08, 0.006, 0.05, bronze_dark)
# health faucet on the east wall of the alcove
cyl("HealthRose", L - 0.012, W - 0.55, 0.70, 0.022, 0.01, bronze, rot=(0, math.pi / 2, 0))
cyl("HealthHead", L - 0.08, W - 0.55, 0.66, 0.018, 0.08, bronze, rot=(math.pi / 2, 0, 0))
cyl("HealthHose", L - 0.05, W - 0.50, 0.55, 0.005, 0.22, bronze_dark)
# paper holder and a hook inside the alcove
cyl("PaperArm", L - 0.04, W - 0.95, 0.72, 0.006, 0.08, bronze, rot=(0, math.pi / 2, 0))
cyl("PaperRoll", L - 0.07, W - 0.95, 0.72, 0.028, 0.11, make_mat("Paper", (0.9, 0.88, 0.82), 0.7), rot=(0, math.pi / 2, 0))
cyl("HookWC", 1.90, W - 0.35, 1.55, 0.008, 0.04, bronze, rot=(math.pi / 2, 0, 0))

# towel bar on the east wall of the dry zone, and a hook by the door
cyl("TowelBar", L - 0.04, 1.05, 1.20, 0.01, 0.60, bronze)
cyl("TowelRoseA", L - 0.02, 0.76, 1.20, 0.016, 0.02, bronze, rot=(0, math.pi / 2, 0))
cyl("TowelRoseB", L - 0.02, 1.34, 1.20, 0.016, 0.02, bronze, rot=(0, math.pi / 2, 0))
cyl("HookDoor", 0.08, door_y1 + 0.12, 1.55, 0.008, 0.045, bronze, rot=(0, math.pi / 2, 0))

# ---------- lights ----------
def area(name, loc, target, energy, size, color=(1.0, 0.82, 0.62)):
    light_data = bpy.data.lights.new(name, 'AREA')
    light_data.energy = energy
    light_data.size = size
    light_data.color = color
    obj = bpy.data.objects.new(name, light_data)
    obj.location = loc
    link(obj)
    look_at(obj, target)
    return obj

area("Fill", (L / 2, W / 2, H - 0.15), (L / 2, W / 2, 0.8), 40, 1.6)
area("SpotVanity", (L / 2, 0.85, H - 0.05), (L / 2, 0.3, 1.2), 18, 0.18)
area("SpotWalk", (1.55, 1.15, H - 0.05), (1.55, 1.15, 0.5), 14, 0.16)
area("SpotShower", (rose_x, rose_y, H - 0.02), (rose_x, rose_y, 1.0), 16, 0.16)
area("SpotWC", (wc_x, W - 0.6, H - 0.05), (wc_x, W - 0.4, 0.6), 10, 0.14)
area("FromDressing", (-0.55, (door_y0 + door_y1) / 2, 1.5), (1.2, 1.2, 1.1), 80, 0.9, (1.0, 0.86, 0.70))

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.45, 0.35, 1)
bg.inputs["Strength"].default_value = 0.015

# ---------- cameras ----------
def camera(name, loc, target, lens=28, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 0.05
    cam.clip_end = 40
    if ortho:
        cam.type = 'ORTHO'
        cam.ortho_scale = ortho
    obj = bpy.data.objects.new(name, cam)
    obj.location = loc
    link(obj)
    if not ortho:
        look_at(obj, target)
    else:
        obj.rotation_euler = (0, 0, 0)
    return obj

cam_wide = camera("CamWide", (1.50, 1.62, 1.48), (1.62, 0.22, 0.92), lens=15)
cam_vanity = camera("CamVanity", (1.62, 1.35, 1.52), (1.62, 0.22, 1.05), lens=32)
cam_shower = camera("CamShower", (1.20, 1.05, 1.50), (0.82, 2.40, 1.30), lens=28)
cam_plan = camera("CamPlan", (L / 2, W / 2, 8.0), (L / 2, W / 2, 0), ortho=3.9)

# plan labels, hidden for the perspective renders
labels = []
def add_label(text, x, y, size=0.09):
    curve = bpy.data.curves.new("Label_" + text, 'FONT')
    curve.body = text
    curve.size = size
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    obj = bpy.data.objects.new("Label_" + text, curve)
    obj.location = (x, y, 0.05)
    link(obj)
    mat = make_mat("Ink_" + text, (0.22, 0.16, 0.10), 0.8)
    obj.data.materials.append(mat)
    labels.append(obj)
    return obj

add_label("WASH BASIN", L / 2, 0.28, 0.07)
add_label("SHOWER", (sx0 + sx1) / 2, sy0 + 0.28, 0.07)
add_label("EWC", wc_x, W - 0.85, 0.08)
add_label("10 ft 8 in", L / 2, -0.18, 0.06)
add_label("9 ft 4 in", -0.22, W / 2, 0.06)

ceiling = bpy.data.objects["Ceiling"]
for obj in labels:
    obj.hide_render = True

# ---------- render ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 80
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0.15
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

prefs = bpy.context.preferences.addons['cycles'].preferences
used = 'CPU'
for device_type in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = device_type
        prefs.get_devices()
        gpu = False
        for d in prefs.devices:
            if d.type == 'CPU':
                d.use = False
            else:
                d.use = True
                gpu = True
            print('DEVICE', d.name, d.type, d.use)
        if gpu:
            scene.cycles.device = 'GPU'
            used = device_type
            break
    except Exception as exc:
        print('DEVICE_FAIL', device_type, exc)
print('RENDER_DEVICE', used)

def shoot(cam, path, rx, ry, samples, hide_ceiling=False):
    scene.camera = cam
    scene.render.resolution_x = rx
    scene.render.resolution_y = ry
    scene.cycles.samples = samples
    scene.render.filepath = path
    ceiling.hide_render = hide_ceiling
    for obj in labels:
        obj.hide_render = not hide_ceiling
    bpy.ops.render.render(write_still=True)
    print('WROTE', path)

shoot(cam_wide, OUT + r"\render-wide.png", 1920, 1080, 64, False)
shoot(cam_vanity, OUT + r"\render-vanity.png", 1920, 1080, 48, False)
shoot(cam_shower, OUT + r"\render-shower.png", 1920, 1080, 48, False)
shoot(cam_plan, OUT + r"\render-plan.png", 1600, 1400, 16, True)

bpy.ops.wm.save_as_mainfile(filepath=OUT + r"\bathroom.blend")
print('SAVED', OUT + r"\bathroom.blend")
