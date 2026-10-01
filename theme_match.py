import bpy

# Palette chips from the bedroom board (sRGB):
# smoked oak #5A3F27, travertine #C9B8A7, warm plaster #AC9985.
# Lights are warm-white. The previous amber lights (1.00, 0.82, 0.62)
# pushed every surface to caramel and crushed the oak.

def s2l(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def rgba(rgb):
    return (s2l(rgb[0]), s2l(rgb[1]), s2l(rgb[2]), 1.0)

SURFACES = {
    "SmokedOak": ((0.33, 0.23, 0.15), (0.40, 0.28, 0.18), 0.58),
    "Travertine": ((0.72, 0.64, 0.56), (0.90, 0.83, 0.75), 0.92),
    "TravertineTrough": ((0.55, 0.48, 0.40), (0.72, 0.64, 0.56), 0.90),
    "Plaster": ((0.62, 0.55, 0.47), (0.76, 0.68, 0.60), 0.95),
    "Clay": ((0.52, 0.38, 0.28), (0.68, 0.52, 0.40), 0.78),
}
BUMP = {
    "Travertine": 0.0,
    "TravertineTrough": 0.0,
    "Plaster": 0.0,
    "Clay": 0.02,
}
METAL = {
    "Bronze": ((0.58, 0.40, 0.24), 0.46),
    "BronzeDark": ((0.36, 0.24, 0.14), 0.55),
}
LEAF = {
    "Leaf": ((0.30, 0.36, 0.20), 0.62),
    "LeafDark": ((0.18, 0.24, 0.12), 0.68),
}

bpy.ops.wm.open_mainfile(filepath=r"C:\Users\OFFICE\Downloads\bathroom-model\bathroom.blend")

for name, (dark, light, rough) in SURFACES.items():
    m = bpy.data.materials[name]
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(light)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0
    for node in m.node_tree.nodes:
        if node.type == "MIX" and "A" in node.inputs:
            node.inputs["A"].default_value = rgba(dark)
            node.inputs["B"].default_value = rgba(light)
        if node.type == "BUMP":
            node.inputs["Strength"].default_value = BUMP.get(name, 0.02)
        if node.type == "TEX_NOISE" and name in ("Travertine", "TravertineTrough", "Plaster"):
            node.inputs["Scale"].default_value = 2.2
            node.inputs["Detail"].default_value = 2.0

# Flat smoked oak with a soft vertical mottling. Wave bands were reading as flutes.
oak = bpy.data.materials["SmokedOak"]
nt = oak.node_tree
mix = next(n for n in nt.nodes if n.type == "MIX")
for link in list(nt.links):
    if link.to_node == mix and link.to_socket.name == "Factor":
        nt.links.remove(link)
grain = nt.nodes.get("OakGrain")
if grain is None:
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.name = "OakGrain"
grain.inputs["Scale"].default_value = 5.0
grain.inputs["Detail"].default_value = 6.0
grain.inputs["Roughness"].default_value = 0.55
mapping = next(n for n in nt.nodes if n.type == "MAPPING")
mapping.inputs["Scale"].default_value = (1.4, 1.4, 8.0)
nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])
nt.links.new(grain.outputs["Fac"], mix.inputs["Factor"])

for name, (color, rough) in {**METAL, **LEAF}.items():
    m = bpy.data.materials[name]
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 1.0 if name.startswith("Bronze") else 0.0

glow = bpy.data.materials["Glow"].node_tree.nodes.get("Principled BSDF")
glow.inputs["Emission Color"].default_value = rgba((1.0, 0.90, 0.78))
glow.inputs["Emission Strength"].default_value = 1.3

# Absolute energies. The blend had already been halved once.
LIGHTS = {
    "Fill": (36, (1.0, 0.96, 0.91)),
    "FromDressing": (62, (1.0, 0.97, 0.93)),
    "SpotVanity": (11, (1.0, 0.93, 0.84)),
    "SpotWalk": (9, (1.0, 0.93, 0.84)),
    "SpotShower": (9, (1.0, 0.93, 0.84)),
    "SpotWC": (6, (1.0, 0.93, 0.84)),
}
for obj in bpy.data.objects:
    if obj.type != "LIGHT":
        continue
    energy, color = LIGHTS[obj.name]
    obj.data.energy = energy
    obj.data.color = color
    print("LIGHT", obj.name, energy, tuple(round(c, 3) for c in color))

world = bpy.context.scene.world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = rgba((0.80, 0.76, 0.70))
bg.inputs["Strength"].default_value = 0.045

scene = bpy.context.scene
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.30

prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type != "CPU"
scene.cycles.device = "GPU"
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_percentage = 100

shots = [("CamWide", "render-room.png", 40, 1920, 1080), ("CamVanity", "render-vanity.png", 32, 1920, 1080), ("CamShower", "render-shower.png", 32, 1920, 1080)]
for cam_name, filename, samples, rx, ry in shots:
    scene.camera = bpy.data.objects[cam_name]
    scene.cycles.samples = samples
    scene.render.resolution_x = rx
    scene.render.resolution_y = ry
    scene.render.filepath = r"C:\Users\OFFICE\Downloads\bathroom-model\\" + filename
    bpy.ops.render.render(write_still=True)
    print("WROTE", filename)

ceiling = bpy.data.objects["Ceiling"]
ceiling.hide_render = True
for obj in bpy.data.objects:
    if obj.name.startswith("Label_"):
        obj.hide_render = False
scene.camera = bpy.data.objects["CamPlan"]
scene.cycles.samples = 16
scene.render.resolution_x = 1600
scene.render.resolution_y = 1400
scene.render.filepath = r"C:\Users\OFFICE\Downloads\bathroom-model\render-plan.png"
bpy.ops.render.render(write_still=True)
print("WROTE", "render-plan.png")

bpy.ops.wm.save_mainfile(filepath=r"C:\Users\OFFICE\Downloads\bathroom-model\bathroom.blend")
print("SAVED")
