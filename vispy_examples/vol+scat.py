# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
# vispy: gallery 2

"""
Example volume rendering

Controls:

* 1  - toggle camera between first person (fly), regular 3D (turntable) and
       arcball
* 2  - toggle between volume rendering methods
* 3  - toggle between stent-CT / brain-MRI image
* 4  - toggle between colormaps
* 0  - reset cameras
* [] - decrease/increase isosurface threshold

With fly camera:

* WASD or arrow keys - move around
* SPACE - brake
* FC - move up-down
* IJKL or mouse - look around
"""

from itertools import cycle

import numpy as np

from vispy import app, scene, io
from vispy.scene import visuals
import vispy.visuals as impl_visuals
from vispy.color import get_colormaps, BaseColormap

# Read volume
vol1 = np.load(io.load_data_file('volume/stent.npz'))['arr_0']
vol2 = np.load(io.load_data_file('brain/mri.npz'))['data']
vol2 = np.flipud(np.rollaxis(vol2, 1))

# Prepare canvas
canvas = scene.SceneCanvas(keys='interactive', size=(800, 600), show=True)
canvas.measure_fps()

# Set up a viewbox to display the image with interactive pan/zoom
view = canvas.central_widget.add_view()

# Set whether we are emulating a 3D texture
emulate_texture = False

# Create the volume visuals, only one is visible
volume1 = scene.visuals.Volume(vol1, parent=view.scene, threshold=0.225,
                               emulate_texture=emulate_texture)
volume1.transform = scene.STTransform(translate=(64, 64, 0))
volume2 = scene.visuals.Volume(vol2, parent=view.scene, threshold=0.2,
                               emulate_texture=emulate_texture)
volume2.visible = False

# Create three cameras (Fly, Turntable and Arcball)
fov = 60.
cam1 = scene.cameras.FlyCamera(parent=view.scene, fov=fov, name='Fly')
cam2 = scene.cameras.TurntableCamera(parent=view.scene, fov=fov,
                                     name='Turntable')
cam3 = scene.cameras.ArcballCamera(parent=view.scene, fov=fov, name='Arcball')
view.camera = cam2  # Select turntable at first

# Add scatter plots here
canvas.unfreeze()
n = 100
P = np.random.rand(n, 3)
s = vol1.shape
X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
X = X*s[2]
Y = Y*s[1]
Z = Z*s[0]
pos = np.zeros((n, 3), dtype=np.float32)
pos[:, 0], pos[:, 1], pos[:, 2] = X, Y, Z

# xmin, xmax =  "%.4g" % np.nanmin(vol1[])
scatter = scene.visuals.Markers()
scatter.set_data(pos, face_color=(0, 1, 0), scaling=False)
index = 1
# scatter.symbol = 'star'
scatter.symbol = impl_visuals.marker_types[index]

scatter.transform = scene.STTransform(translate=(s[2]/2.0, s[1]/2.0, 0))

view.add(scatter)

# Add text visual here
text = visuals.Text(impl_visuals.marker_types[index],
                                 pos=(80, 15), font_size=14,
                                 color='white', parent=canvas.scene)
canvas.freeze()
# canvas.update()

# create colormaps that work well for translucent and additive volume rendering
class TransFire(BaseColormap):
    glsl_map = """
    vec4 translucent_fire(float t) {
        return vec4(pow(t, 0.5), t, t*t, max(0, t*1.05 - 0.05));
    }
    """


class TransGrays(BaseColormap):
    glsl_map = """
    vec4 translucent_grays(float t) {
        return vec4(t, t, t, t*0.05);
    }
    """

# Setup colormap iterators
opaque_cmaps = cycle(get_colormaps())
translucent_cmaps = cycle([TransFire(), TransGrays()])
opaque_cmap = next(opaque_cmaps)
translucent_cmap = next(translucent_cmaps)


# Implement key presses
@canvas.events.key_press.connect
def on_key_press(event):
    global opaque_cmap, translucent_cmap
    if event.text == '1':
        cam_toggle = {cam1: cam2, cam2: cam3, cam3: cam1}
        view.camera = cam_toggle.get(view.camera, cam2)
        print(view.camera.name + ' camera')
    elif event.text == '2':
        methods = ['mip', 'translucent', 'iso', 'additive']
        method = methods[(methods.index(volume1.method) + 1) % 4]
        print("Volume render method: %s" % method)
        cmap = opaque_cmap if method in ['mip', 'iso'] else translucent_cmap
        volume1.method = method
        volume1.cmap = cmap
        volume2.method = method
        volume2.cmap = cmap
    elif event.text == '3':
        volume1.visible = not volume1.visible
        volume2.visible = not volume1.visible
    elif event.text == '4':
        if volume1.method in ['mip', 'iso']:
            cmap = opaque_cmap = next(opaque_cmaps)
        else:
            cmap = translucent_cmap = next(translucent_cmaps)
        volume1.cmap = cmap
        volume2.cmap = cmap
    elif event.text == '0':
        cam1.set_range()
        cam3.set_range()
    elif event.text != '' and event.text in '[]':
        s = -0.025 if event.text == '[' else 0.025
        volume1.threshold += s
        volume2.threshold += s
        th = volume1.threshold if volume1.visible else volume2.threshold
        print("Isosurface threshold: %0.3f" % th)


# for testing performance
# @canvas.connect
# def on_draw(ev):
# canvas.update()

if __name__ == '__main__':
    print(__doc__)
    app.run()
