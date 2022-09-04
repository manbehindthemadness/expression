# eyeballs_dual_gc9a01.py - dual display GC9A01 round TFT LCDs with creepy eyeball animation
# 17 May 2022 - @todbot / Tod Kurt
#
# requires recompiled CircuitPython with "#define CIRCUITPY_DISPLAY_LIMIT  (2)" in "mpconfigboard.h"
#
import math, random
import board
import displayio
from display import Display

dw, dh = 96, 64  # display dimensions
iris_w, iris_h = 50, 50  # iris image is 110x110
iris_cx, iris_cy = dw // 2 - iris_w // 2, dh // 2 - iris_h // 2  # "center" of iris image

background = displayio.Bitmap(96, 64, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xffffff  # White I hope...

iris_bitmap = displayio.OnDiskBitmap(open("img/iris.bmp", "rb"))
iris_pal = iris_bitmap.pixel_shader
iris_pal.make_transparent(0)

exp_top = displayio.OnDiskBitmap(open("img/exp_top.bmp", "rb"))
exp_top_pal = exp_top.pixel_shader
exp_top_pal.make_transparent(0)

exp_bottom = displayio.OnDiskBitmap(open("img/exp_bottom.bmp", "rb"))
exp_top_bottom = exp_bottom.pixel_shader
exp_top_bottom.make_transparent(0)

reset = board.D9

cs0 = board.D3
cs1 = board.D2

command0 = board.D0
command1 = board.D1


def display_eye_init(display, side):
    """
    Experiment.

    """
    eyeball_bitmap = displayio.OnDiskBitmap(open("img/eye_" + side + ".bmp", "rb"))
    eyeball_pal = eyeball_bitmap.pixel_shader
    eyeball_pal.make_transparent(0)
    main = displayio.Group()
    display.show(main)
    bg = displayio.TileGrid(background, pixel_shader=bg_palette)
    eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_bitmap.pixel_shader)
    iris = displayio.TileGrid(iris_bitmap, pixel_shader=iris_pal, x=iris_cx, y=iris_cy)

    exp_up = displayio.TileGrid(exp_top, pixel_shader=exp_top_pal, x=-108, y=-48)
    exp_down = displayio.TileGrid(exp_top, pixel_shader=exp_top_pal, x=-108, y=48)
    main.append(bg)
    main.append(iris)
    main.append(eyeball)  # add eyeball & iris to main group
    main.append(exp_up)
    return display, eyeball, iris, exp_up, exp_down


displays = Display(reset, command0, command1, cs0, cs1)
display_L, eyeball_L, iris_L, exp_up_L, exp_down_L = display_eye_init(displays.displays[0], 'left')
display_R, eyeball_R, iris_R, exp_up_R, exp_down_R = display_eye_init(displays.displays[1], 'right')

thetaL, thetaR = 0, 0  # left & right eye rotational position
dthetaL, dthetaR = 0.25, 0.25  # how fast left & right eyes spins
r = 17  # size of eye spin

while True:
    iris_L.x = iris_cx + int(r * math.sin(thetaL))  # update iris positions based on angle
    iris_L.y = iris_cy + int(r * math.cos(thetaL))
    iris_R.x = iris_cx + int(r * math.sin(thetaL))
    iris_R.y = iris_cy + int(r * math.cos(thetaL))

    if random.randint(0, 20) == 0:
        dthetaR = -dthetaR  # randomly change right eye spin direction

    thetaL -= dthetaL  # update angles (negative for clockwise motion)
    thetaR -= dthetaR

    display_L.refresh(target_frames_per_second=20)
    display_R.refresh(target_frames_per_second=20)
