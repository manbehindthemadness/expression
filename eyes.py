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


iris_bitmap, iris_pal = adafruit_imageload.load("img/iris.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
iris_pal.make_transparent(0)

exp_top_left, exp_top_left_pal = adafruit_imageload.load("img/exp_top_left.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_top_left_pal.make_transparent(0)

exp_bottom_left, exp_bottom_left_pal = adafruit_imageload.load("img/exp_bottom_left.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_bottom_left_pal.make_transparent(0)

exp_top_right, exp_top_right_pal = adafruit_imageload.load("img/exp_top_right.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_top_right_pal.make_transparent(0)

exp_bottom_right, exp_bottom_right_pal = adafruit_imageload.load("img/exp_bottom_right.bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
exp_bottom_right_pal.make_transparent(0)

reset = board.D9

cs0 = board.D3
cs1 = board.D2

command0 = board.D0
command1 = board.D1


def display_eye_init(display, side):  # noqa
    """
    Experiment.

    """
    background = displayio.Bitmap(96, 64, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0xffffff

    blink = displayio.Bitmap(96, 64, 1)
    blink_palette = displayio.Palette(1)
    blink_palette[0] = 0x080808

    eyeball_bitmap, eyeball_pal = adafruit_imageload.load("img/eye_" + side + ".bmp", bitmap=displayio.Bitmap, palette=displayio.Palette)
    eyeball_pal.make_transparent(0)
    main = displayio.Group()
    display.show(main)
    bg = displayio.TileGrid(background, pixel_shader=bg_palette)
    eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal)
    iris = displayio.TileGrid(iris_bitmap, pixel_shader=iris_pal, x=iris_cx, y=iris_cy)

    exp_up_left = displayio.TileGrid(exp_top_left, pixel_shader=exp_top_left_pal, x=-60, y=-26)
    exp_down_left = displayio.TileGrid(exp_bottom_left, pixel_shader=exp_bottom_left_pal, x=-60, y=-5)

    exp_up_right = displayio.TileGrid(exp_top_right, pixel_shader=exp_top_right_pal, x=-6, y=-26)
    exp_down_right = displayio.TileGrid(exp_bottom_right, pixel_shader=exp_bottom_right_pal, x=-6, y=-5)

    bnk = displayio.TileGrid(blink, pixel_shader=blink_palette, x=-200)
    main.append(bg)
    main.append(iris)
    main.append(eyeball)  # add eyeball & iris to main group
    main.append(exp_up_left)
    main.append(exp_down_left)
    main.append(exp_up_right)
    main.append(exp_down_right)
    main.append(bnk)
    return display, eyeball, iris, exp_up_left, exp_down_left, exp_up_right, exp_down_right, bnk, bg


displays = Display(reset, command0, command1, cs0, cs1)
display_L, eyeball_L, iris_L, exp_up_LL, exp_down_LL, exp_up_LR, exp_down_LR, blink_L, bg_L = display_eye_init(displays.displays[1], 'left')
display_R, eyeball_R, iris_R, exp_up_RL, exp_down_RL, exp_up_RR, exp_down_RR, blink_R, bg_R = display_eye_init(displays.displays[0], 'right')

left_anchor = iris_L.x, iris_L.y
right_anchor = iris_R.x, iris_R.y


def eye_position(x, y, left_right='both'):
    """
    Updates the direction that our eyes are looking.
    """
    global left_anchor
    global right_anchor
    x, y = x - iris_mid_x, y - iris_mid_y
    if left_right in ['both', 'left']:
        iris_L.x = x
        iris_L.y = y
    if left_right in ['both', 'right']:
        iris_R.x = x
        iris_R.y = y
    left_anchor = iris_L.x, iris_L.y
    right_anchor = iris_R.x, iris_R.y
    return int(iris_L.x), int(iris_R.y)


def eye_roll(x_anchor, y_anchor, rad):  # noqa
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


def saccades(x, y):
    """
    Performs Saccadic Eye Movements
    """
    global left_anchor
    global right_anchor
    lx_anchor, ly_anchor = left_anchor
    rx_anchor, ry_anchor = right_anchor
    x_variant = int(x / 2)
    y_variant = int(y / 2)
    x_variant = random.randint(-x_variant, x_variant)
    y_variant = random.randint(-y_variant, y_variant)
    new_lx_pos = x_variant + lx_anchor
    new_ly_pos = y_variant + ly_anchor
    new_rx_pos = x_variant + rx_anchor
    new_ry_pos = y_variant + ry_anchor
    iris_L.x = new_lx_pos
    iris_L.y = new_ly_pos
    iris_R.x = new_rx_pos
    iris_R.y = new_ry_pos


def squint(amount, top_bottom='both', left_right='both'):
    """
    Makes a squint expression.
    """
    u_ref = -26
    d_ref = -5
    if top_bottom in ['both', 'top']:
        if left_right in ['both', 'left']:
            exp_up_LL.y = u_ref + amount
            exp_up_LR.y = u_ref + amount
        if left_right in ['both', 'right']:
            exp_up_RL.y = u_ref + amount
            exp_up_RR.y = u_ref + amount
    if top_bottom in ['both', 'bottom']:
        if left_right in ['both', 'left']:
            exp_down_LL.y = d_ref - amount
            exp_down_LR.y = d_ref - amount
        if left_right in ['both', 'right']:
            exp_down_RL.y = d_ref - amount
            exp_down_RR.y = d_ref - amount


def glance(amount, top_bottom='both', left_right='both', right_left='both', bug='none'):
    """
    Like squint but for diagonal expressions.
    """
    l_ref = -60
    r_ref = -6
    if amount > 0:
        amount += 25
    else:
        amount -= 25
    if top_bottom in ['both', 'top']:
        if left_right in ['both', 'left']:
            if right_left in ['both', 'left']:
                exp_up_LL.x = l_ref + amount
            if right_left in ['both', 'right']:
                exp_up_LR.x = r_ref + amount
        if left_right in ['both', 'right']:
            if right_left in ['both', 'left']:
                exp_up_RL.x = l_ref + amount
            if right_left in ['both', 'right']:
                exp_up_RR.x = r_ref + amount
    if top_bottom in ['both', 'bottom']:
        if left_right in ['both', 'left']:
            if right_left in ['both', 'left']:
                exp_down_LL.x = l_ref + amount
            if right_left in ['both', 'right']:
                exp_down_LR.x = r_ref + amount
        if left_right in ['both', 'right']:
            if right_left in ['both', 'left']:
                exp_down_RL.x = l_ref + amount
            if right_left in ['both', 'right']:
                exp_down_RR.x = r_ref + amount
    if bug == 'none' and eyeball_L.x and eyeball_R.x:
        eyeball_L.x = 0
        eyeball_R.x = 0
    if bug in ['both', 'left']:
        eyeball_L.x = 200
    if bug in ['both', 'right']:
        eyeball_R.x = 200


eye_position(48, 32)


verticals = ['both', 'top', 'bottom']
horizontals = ['both', 'left', 'right']
bugs = ['none', 'left', 'none', 'right', 'none', 'both', 'none']
eyes = ['both', 'both', 'left', 'both', 'both', 'right', 'both', 'both']

gc.collect()
print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
print("MEMORY FREE", gc.mem_free())  # noqa

displays = [display_L, display_R]
shut = False
refresh = True
while True:
    if shut:  # If eyes are shut, open them.
        blink_L.x = -200
        blink_R.x = -200
        shut = False
        refresh = True

    if not random.randint(0, 10):
        squint(random.randint(0, 20), random.choice(verticals), random.choice(horizontals))
        refresh = True

    if not random.randint(0, 10):
        glance(
            random.randint(-30, 30),
            random.choice(verticals),
            random.choice(horizontals),
            random.choice(horizontals),
            random.choice(bugs)
        )
        refresh = True

    if not random.randint(0, 25):
        eye_position(
            random.randint(25, 71),
            random.randint(25, 39),
            random.choice(eyes)
        )
        refresh = True

    if not random.randint(0, 2):
        saccades(7, 7)
        refresh = True

    if not random.randint(0, 50):  # Blink randomly.
        blink_L.x = 0
        blink_R.x = 0
        shut = True
        refresh = True

    if refresh:
        displays.reverse()
        for display in displays:
            display.refresh()
    delay = random.randint(125, 500) / 1000
    refresh = False
    time.sleep(delay)
