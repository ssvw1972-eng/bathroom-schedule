"""Render a short colour walk through the bathroom on the GPU. Does not save the blend."""
import os
import bpy
from mathutils import Vector

OUT = r"C:\Users\OFFICE\Downloads\bathroom-model\scroll"
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for dev in prefs.devices:
    dev.use = dev.type != "CPU"
    print("DEVICE", dev.name, dev.type, dev.use)
scene.cycles.device = "GPU"
scene.cycles.samples = 20
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_x = 1440
scene.render.resolution_y = 810
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("ScrollCam")
cam_data.lens = 22
cam_data.clip_start = 0.04
cam = bpy.data.objects.new("ScrollCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# loc, look-at. Interior is about x 0.15-3.10, y 0.15-2.70.
keys = [
    ((0.55, 1.35, 1.48), (1.85, 0.45, 1.00)),
    ((1.55, 1.15, 1.38), (1.55, 0.28, 1.02)),
    ((1.55, 0.95, 1.28), (1.55, 0.22, 1.15)),
    ((1.15, 1.35, 1.55), (0.45, 2.35, 1.70)),
    ((0.70, 1.95, 1.50), (0.40, 2.50, 1.85)),
    ((1.05, 2.15, 1.25), (0.22, 2.40, 1.15)),
    ((1.85, 1.70, 1.45), (2.70, 2.30, 0.70)),
    ((2.20, 1.85, 1.40), (2.85, 2.40, 0.65)),
    ((1.70, 1.95, 1.62), (1.20, 0.40, 0.95)),
]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


steps = 2
frames = []
for i in range(len(keys) - 1):
    for s in range(steps):
        t = s / steps
        frames.append((lerp(keys[i][0], keys[i + 1][0], t), lerp(keys[i][1], keys[i + 1][1], t)))
frames.append(keys[-1])

print("FRAMES", len(frames))
for n, (loc, target) in enumerate(frames):
    cam.location = loc
    look_at(cam, target)
    path = os.path.join(OUT, "f%02d.png" % n)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("WROTE", path, flush=True)

print("DONE", len(frames))
