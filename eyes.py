"""
Lets give a drone some eyes...
"""
import math
import random
import board
import displayio
import adafruit_imageload
from display import Display


SIDES = ['left', 'right']
VERTICALS = ['both', 'top', 'bottom']
HORIZONTALS = ['both', 'left', 'right']
BUGS = ['none', 'left', 'right', 'both']


class Eyes:
    """
    This is our fancy eye-control class
    """

    def __init__(
            self,
            reset=board.D9,
            cs0=board.D3,
            cs1=board.D2,
            command0=board.D0,
            command1=board.D1,
    ):
        self.reset = reset

        self.cs0 = cs0
        self.cs1 = cs1

        self.command0 = command0
        self.command1 = command1

        self.displays = Display(self.reset, self.command0, self.command1, self.cs0, self.cs1)

        self.dw, self.dh = 96, 64
        self.iris_w, self.iris_h = 48, 50
        self.iris_cx, self.iris_cy = self.dw // 2 - self.iris_w // 2, self.dh // 2 - self.iris_h // 2
        self.iris_mid_x, self.iris_mid_y = int(self.iris_w / 2), int(self.iris_h / 2)

        self.iris_bitmap, self.iris_pal = adafruit_imageload.load(
            "img/iris.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.iris_pal.make_transparent(0)

        self.exp_top_left, self.exp_top_left_pal = adafruit_imageload.load(
            "img/exp_top_left.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_top_left_pal.make_transparent(0)

        self.exp_bottom_left, self.exp_bottom_left_pal = adafruit_imageload.load(
            "img/exp_bottom_left.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_bottom_left_pal.make_transparent(0)

        self.exp_top_right, self.exp_top_right_pal = adafruit_imageload.load(
            "img/exp_top_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_top_right_pal.make_transparent(0)

        self.exp_bottom_right, self.exp_bottom_right_pal = adafruit_imageload.load(
            "img/exp_bottom_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_bottom_right_pal.make_transparent(0)

        self.display_L, self.eyeball_L, self.iris_L, self.exp_up_LL, self.exp_down_LL, self.exp_up_LR, self.exp_down_LR, \
            self.blink_L, self.bg_L = self.display_eye_init(self.displays.displays[1], 'left')
        self.display_R, self.eyeball_R, self.iris_R, self.exp_up_RL, self.exp_down_RL, self.exp_up_RR, self.exp_down_RR, \
            self.blink_R, self.bg_R = self.display_eye_init(self.displays.displays[0], 'right')

        self.left_anchor = self.iris_L.x, self.iris_L.y
        self.right_anchor = self.iris_R.x, self.iris_R.y

        self.lx_anchor, self.ly_anchor = self.left_anchor
        self.rx_anchor, self.ry_anchor = self.right_anchor

        self.theta_L, self.theta_R = 0, 0  # left & right eye rotational position
        self.d_theta_L, self.d_theta_R = 0.25, 0.25  # how fast left & right eyes spins

        self.u_ref = -26
        self.d_ref = -5
        self.l_ref = -60
        self.r_ref = -6

    def display_eye_init(
            self,
            display: displayio.Display,
            side: SIDES
    ) -> tuple[
        displayio.Display,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
        displayio.TileGrid,
    ]:
        """
        Fires up the displays.

        """
        background = displayio.Bitmap(96, 64, 1)
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0xffffff

        blink = displayio.Bitmap(96, 64, 1)
        blink_palette = displayio.Palette(1)
        blink_palette[0] = 0x080808

        eyeball_bitmap, eyeball_pal = adafruit_imageload.load("img/eye_" + side + ".bmp", bitmap=displayio.Bitmap,
                                                              palette=displayio.Palette)
        eyeball_pal.make_transparent(0)
        main = displayio.Group()
        display.show(main)
        bg = displayio.TileGrid(background, pixel_shader=bg_palette)
        eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal)
        iris = displayio.TileGrid(self.iris_bitmap, pixel_shader=self.iris_pal, x=self.iris_cx, y=self.iris_cy)

        exp_up_left = displayio.TileGrid(self.exp_top_left, pixel_shader=self.exp_top_left_pal, x=-60, y=-26)
        exp_down_left = displayio.TileGrid(self.exp_bottom_left, pixel_shader=self.exp_bottom_left_pal, x=-60, y=-5)

        exp_up_right = displayio.TileGrid(self.exp_top_right, pixel_shader=self.exp_top_right_pal, x=-6, y=-26)
        exp_down_right = displayio.TileGrid(self.exp_bottom_right, pixel_shader=self.exp_bottom_right_pal, x=-6, y=-5)

        bnk = displayio.TileGrid(blink, pixel_shader=blink_palette, x=-200)
        main.append(bg)
        main.append(iris)
        main.append(eyeball)
        main.append(exp_up_left)
        main.append(exp_down_left)
        main.append(exp_up_right)
        main.append(exp_down_right)
        main.append(bnk)
        return display, eyeball, iris, exp_up_left, exp_down_left, exp_up_right, exp_down_right, bnk, bg

    async def eye_position(self, x: int, y: int, left_right: HORIZONTALS = 'both') -> tuple[int, int]:
        """
        Updates the direction that our eyes are looking.
        """
        x, y = x - self.iris_mid_x, y - self.iris_mid_y
        if left_right in ['both', 'left']:
            self.iris_L.x = x
            self.iris_L.y = y
        if left_right in ['both', 'right']:
            self.iris_R.x = x
            self.iris_R.y = y
        await self.displays.refresh()
        self.left_anchor = self.iris_L.x, self.iris_L.y
        self.right_anchor = self.iris_R.x, self.iris_R.y
        return int(self.iris_L.x), int(self.iris_R.y)


    async def eye_roll(self, x_anchor: int, y_anchor: int, rad: int):  # noqa
        """
        Adds some radial movements.
        """
        self.iris_L.x = self.iris_cx + int(rad * math.sin(self.theta_L))
        self.iris_L.y = self.iris_cy + int(rad * math.cos(self.theta_L))
        self.iris_R.x = self.iris_cx + int(rad * math.sin(self.theta_L))
        self.iris_R.y = self.iris_cy + int(rad * math.cos(self.theta_L))
        self.theta_L -= self.d_theta_L  # update angles (negative for clockwise motion)
        self.theta_R -= self.d_theta_R
        await self.displays.refresh()
        return self

    async def saccades(self, x: int, y: int):
        """
        Performs Saccadic Eye Movements
        """
        self.lx_anchor, self.ly_anchor = self.left_anchor
        self.rx_anchor, self.ry_anchor = self.right_anchor
        x_variant = int(x / 2)
        y_variant = int(y / 2)
        x_variant = random.randint(-x_variant, x_variant)
        y_variant = random.randint(-y_variant, y_variant)
        new_lx_pos = x_variant + self.lx_anchor
        new_ly_pos = y_variant + self.ly_anchor
        new_rx_pos = x_variant + self.rx_anchor
        new_ry_pos = y_variant + self.ry_anchor
        self.iris_L.x = new_lx_pos
        self.iris_L.y = new_ly_pos
        self.iris_R.x = new_rx_pos
        self.iris_R.y = new_ry_pos
        await self.displays.refresh()
        return self

    async def squint(
            self,
            amount: int,
            top_bottom: VERTICALS = 'both',
            left_right: HORIZONTALS = 'both'
    ):
        """
        Makes a squint expression.
        """
        if top_bottom in ['both', 'top']:
            if left_right in ['both', 'left']:
                self.exp_up_LL.y = self.u_ref + amount
                self.exp_up_LR.y = self.u_ref + amount
            if left_right in ['both', 'right']:
                self.exp_up_RL.y = self.u_ref + amount
                self.exp_up_RR.y = self.u_ref + amount
            await self.displays.refresh()
        if top_bottom in ['both', 'bottom']:
            if left_right in ['both', 'left']:
                self.exp_down_LL.y = self.d_ref - amount
                self.exp_down_LR.y = self.d_ref - amount
            if left_right in ['both', 'right']:
                self.exp_down_RL.y = self.d_ref - amount
                self.exp_down_RR.y = self.d_ref - amount
            await self.displays.refresh()
        return self

    async def glance(
            self,
            amount: int,
            top_bottom: VERTICALS = 'both',
            left_right: HORIZONTALS = 'both',
            right_left: HORIZONTALS = 'both',
            bug: BUGS = 'none'
    ):
        """
        Like squint but for diagonal expressions.
        """
        if amount > 0:
            amount += 25
        else:
            amount -= 25
        if top_bottom in ['both', 'top']:
            if left_right in ['both', 'left']:
                if right_left in ['both', 'left']:
                    self.exp_up_LL.x = self.l_ref + amount
                if right_left in ['both', 'right']:
                    self.exp_up_LR.x = self.r_ref + amount
            if left_right in ['both', 'right']:
                if right_left in ['both', 'left']:
                    self.exp_up_RL.x = self.l_ref + amount
                if right_left in ['both', 'right']:
                    self.exp_up_RR.x = self.r_ref + amount
            await self.displays.refresh()
        if top_bottom in ['both', 'bottom']:
            if left_right in ['both', 'left']:
                if right_left in ['both', 'left']:
                    self.exp_down_LL.x = self.l_ref + amount
                if right_left in ['both', 'right']:
                    self.exp_down_LR.x = self.r_ref + amount
            if left_right in ['both', 'right']:
                if right_left in ['both', 'left']:
                    self.exp_down_RL.x = self.l_ref + amount
                if right_left in ['both', 'right']:
                    self.exp_down_RR.x = self.r_ref + amount
            await self.displays.refresh()
        if bug == 'none' and self.eyeball_L.x and self.eyeball_R.x:
            self.eyeball_L.x = 0
            self.eyeball_R.x = 0
        if bug in ['both', 'left']:
            self.eyeball_L.x = 200
        if bug in ['both', 'right']:
            self.eyeball_R.x = 200
        await self.displays.refresh()
        return self

    async def blink(self):
        """
        Aptly named.
        """
        self.blink_L.x = 0
        self.blink_R.x = 0
        await self.displays.refresh()
        self.blink_L.x = -200
        self.blink_R.x = -200
        await self.displays.refresh()
        return self
