"""
Lets give a drone some eyes...
"""
import gc
import math
import random
import time
import board
import displayio
import adafruit_imageload
from display import Display

dw, dh = 96, 64
iris_w, iris_h = 48, 50
iris_cx, iris_cy = dw // 2 - iris_w // 2, dh // 2 - iris_h // 2  # "center" of iris image
iris_mid_x, iris_mid_y = int(iris_w / 2), int(iris_h / 2)


background = displayio.Bitmap(96, 64, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xffffff

blink = displayio.Bitmap(96, 64, 1)
blink_palette = displayio.Palette(1)
blink_palette[0] = 0x000000


iris_bitmap, iris_pal = adafruit_imageload.load("img/iris.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
iris_pal.make_transparent(0)

exp_top, exp_top_pal = adafruit_imageload.load("img/exp_top.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_top_pal.make_transparent(0)

exp_bottom, exp_bottom_pal = adafruit_imageload.load("img/exp_bottom.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_bottom_pal.make_transparent(0)

reset = board.D9

cs0 = board.D3
cs1 = board.D2

command0 = board.D0
command1 = board.D1


def display_eye_init(display, side):
    """
    Experiment.

    """
    eyeball_bitmap, eyeball_pal = adafruit_imageload.load("img/eye_" + side + ".bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
    eyeball_pal.make_transparent(0)
    main = displayio.Group()
    display.show(main)
    bg = displayio.TileGrid(background, pixel_shader=bg_palette)
    eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal)
    iris = displayio.TileGrid(iris_bitmap, pixel_shader=iris_pal, x=iris_cx, y=iris_cy)

    exp_up = displayio.TileGrid(exp_top, pixel_shader=exp_top_pal, x=-108, y=-48)
    exp_down = displayio.TileGrid(exp_top, pixel_shader=exp_top_pal, x=-108, y=144)

    bnk = displayio.TileGrid(blink, pixel_shader=blink_palette, x=-200)
    main.append(bg)
    main.append(iris)
    main.append(eyeball)  # add eyeball & iris to main group
    main.append(exp_up)
    main.append(exp_down)
    main.append(bnk)
    return display, eyeball, iris, exp_up, exp_down, bnk


displays = Display(reset, command0, command1, cs0, cs1)
display_L, eyeball_L, iris_L, exp_up_L, exp_down_L, blink_L = display_eye_init(displays.displays[0], 'left')
display_R, eyeball_R, iris_R, exp_up_R, exp_down_R, blink_R = display_eye_init(displays.displays[1], 'right')


def eye_position(x, y):
    """
    Updates the direction that our eyes are looking.
    """
    x, y = x - iris_mid_x, y - iris_mid_y
    iris_L.x = x
    iris_L.y = y
    iris_R.x = x
    iris_R.y = y

    return int(iris_L.x), int(iris_R.y)


def eye_roll(x_anchor, y_anchor, rad):
    """
    Adds some radial movements.
    """
    thetaL, thetaR = 0, 0  # left & right eye rotational position
    dthetaL, dthetaR = 0.25, 0.25  # how fast left & right eyes spins

    iris_L.x = iris_cx + int(rad * math.sin(thetaL))
    iris_L.y = iris_cy + int(rad * math.cos(thetaL))
    iris_R.x = iris_cx + int(rad * math.sin(thetaL))
    iris_R.y = iris_cy + int(rad * math.cos(thetaL))
    thetaL -= dthetaL  # update angles (negative for clockwise motion)
    thetaR -= dthetaR


def saccades(x, y, x_anchor, y_anchor):
    """
    Performs Saccadic Eye Movements
    """
    x_variant = int(x / 2)
    y_variant = int(y / 2)
    new_x_pos = random.randint(-x_variant, x_variant) + x_anchor
    new_y_pos = random.randint(-y_variant, y_variant) + y_anchor
    iris_L.x = new_x_pos
    iris_L.y = new_y_pos
    iris_R.x = new_x_pos
    iris_R.y = new_y_pos


xx, yy = eye_position(48, 32)


print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
print("MEMORY FREE", gc.mem_free())  # noqa
shut = False
refresh = True
while True:
    if shut:  # If eyes are shut, open them.
        blink_L.x = -200
        blink_R.x = -200
        shut = False
        refresh = True

    if not random.randint(0, 2):
        saccades(7, 7, xx, yy)
        refresh = True

    if not random.randint(0, 50):  # Blink randomly.
        blink_L.x = 0
        blink_R.x = 0
        shut = True
        refresh = True

    if refresh:
        display_L.refresh(target_frames_per_second=20)
        display_R.refresh(target_frames_per_second=20)
    delay = random.randint(250, 750) / 1000
    refresh = False
    time.sleep(delay)
