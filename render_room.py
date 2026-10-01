import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=r"C:\Users\OFFICE\Downloads\bathroom-model\bathroom.blend")

# The oak leaf stays in the opening. Hiding it left a black void.
bpy.data.objects["Door"].hide_render = False

cam = bpy.data.objects["CamWide"]
# East side of the walkway, looking along the basin wall so both plants fit.
# Shower threshold, looking straight at the basin so both plants and the door fit.
cam.location = (1.50, 1.62, 1.48)
target = Vector((1.62, 0.22, 0.92))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 15
cam.data.clip_start = 0.05

scene = bpy.context.scene
scene.camera = cam
scene.cycles.samples = 48
scene.cycles.device = "GPU"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type != "CPU"
scene.render.filepath = r"C:\Users\OFFICE\Downloads\bathroom-model\render-room.png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile(filepath=r"C:\Users\OFFICE\Downloads\bathroom-model\bathroom.blend")
print("WROTE room")
