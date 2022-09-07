"""
Lets give a drone some eyes...
"""
import math
import random
import board
import displayio
import asyncio
import random
import adafruit_imageload
from adafruit_bitmap_font import bitmap_font  # noqa
from adafruit_display_text import label  # noqa
try:
    from display import Display
except ImportError:
    from .display import Display

SIDES = ['left', 'right']
VERTICALS = ['both', 'top', 'bottom']
HORIZONTALS = ['both', 'left', 'right']
BUGS = ['none', 'left', 'right', 'both']
OPENS = ['open', 'close', 'both']
font = bitmap_font.load_font("expression/img/ldr.bdf", displayio.Bitmap)
ICONS = list('abcdefghijklmnopqrstuvwx123456789')


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
        self.displays.reset()

        self.dw, self.dh = 96, 64
        self.iris_w, self.iris_h = 48, 50

        self.iris_l_cy = self.iris_r_cx = self.dh // 2 - self.iris_h // 2
        self.iris_l_cx = self.iris_r_cy = self.dw // 2 - self.iris_w // 2

        print(self.iris_l_cx, self.iris_r_cy)

        self.iris_mid_x, self.iris_mid_y = int(self.iris_w / 2), int(self.iris_h / 2)

        self.iris_bitmap, self.iris_pal = adafruit_imageload.load(
            "expression/img/iris.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.iris_pal.make_transparent(0)

        self.exp_top_left, self.exp_top_left_pal = adafruit_imageload.load(
            "expression/img/exp_top_left.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_top_left_pal.make_transparent(0)

        self.exp_bottom_left, self.exp_bottom_left_pal = adafruit_imageload.load(
            "expression/img/exp_bottom_left.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_bottom_left_pal.make_transparent(0)

        self.exp_top_right, self.exp_top_right_pal = adafruit_imageload.load(
            "expression/img/exp_top_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_top_right_pal.make_transparent(0)

        self.exp_bottom_right, self.exp_bottom_right_pal = adafruit_imageload.load(
            "expression/img/exp_bottom_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.exp_bottom_right_pal.make_transparent(0)

        self.display_L, self.eyeball_L, self.iris_L, self.exp_up_LL, self.exp_down_LL, self.exp_up_LR, self.exp_down_LR, \
            self.blink_L, self.blink_pal_L, self.bg_L, self.text_L = self.display_eye_init(self.displays.displays[1], 'left')
        self.display_R, self.eyeball_R, self.iris_R, self.exp_up_RL, self.exp_down_RL, self.exp_up_RR, self.exp_down_RR, \
            self.blink_R, self.blink_pal_R, self.bg_R, self.text_R = self.display_eye_init(self.displays.displays[0], 'right')

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

        self.bg_l_fill = 0xffffff
        self.bg_r_fill = 0xffffff

        self.transitioning = False

    async def wait(self):
        """
        Waits for a transition to complete.
        """
        while self.transitioning:
            await asyncio.sleep(0.0001)

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
        displayio.Palette,
        displayio.Palette,
        label
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

        eyeball_bitmap, eyeball_pal = adafruit_imageload.load(
            "expression/img/eye_" + side + ".bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        eyeball_pal.make_transparent(0)
        main = displayio.Group()
        display.show(main)
        bg = displayio.TileGrid(background, pixel_shader=bg_palette)
        eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal)
        iris = displayio.TileGrid(self.iris_bitmap, pixel_shader=self.iris_pal, x=self.iris_l_cx, y=self.iris_l_cy)

        exp_up_left = displayio.TileGrid(self.exp_top_left, pixel_shader=self.exp_top_left_pal, x=-60, y=-26)
        exp_down_left = displayio.TileGrid(self.exp_bottom_left, pixel_shader=self.exp_bottom_left_pal, x=-60, y=-5)

        exp_up_right = displayio.TileGrid(self.exp_top_right, pixel_shader=self.exp_top_right_pal, x=-6, y=-26)
        exp_down_right = displayio.TileGrid(self.exp_bottom_right, pixel_shader=self.exp_bottom_right_pal, x=-6, y=-5)

        bnk = displayio.TileGrid(blink, pixel_shader=blink_palette)

        text = label.Label(font, text='a')
        text.x = -100
        text.y = 30
        main.append(bg)
        main.append(iris)
        main.append(eyeball)
        main.append(exp_up_left)
        main.append(exp_down_left)
        main.append(exp_up_right)
        main.append(exp_down_right)
        main.append(bnk)
        main.append(text)
        return display, eyeball, iris, exp_up_left, exp_down_left, exp_up_right, exp_down_right, bnk, blink_palette, bg_palette, text

    async def eye_position(self, x: int, y: int, left_right: HORIZONTALS = 'both', rate: int = 1) -> tuple[int, int]:
        """
        Updates the direction that our eyes are looking.
        """

        def transition(des_x: int, des_y: int, item: displayio.TileGrid, speed: int) -> bool:
            """
            Calculates transition.
            """
            result = True
            cur_x = item.x
            if cur_x not in range(des_x - speed, des_x + speed):
                if des_x < cur_x:
                    item.x -= speed
                    result = False
                if des_x > cur_x:
                    item.x += speed
                    result = False
            cur_y = item.y
            if cur_y not in range(des_y - speed, des_y + speed):
                if des_y < cur_y:
                    item.y -= speed
                    result = False
                if des_y > cur_y:
                    item.y += speed
                    result = False
            return result

        await self.wait()
        desired_x, desired_y = x - self.iris_mid_x, y - self.iris_mid_y
        self.transitioning = True
        criteria = [True]
        if left_right == 'both':
            criteria = [False, False]
        if left_right == 'left':
            criteria = [False, True]
        if left_right == 'right':
            criteria = [True, False]
        while False in criteria:
            if left_right in ['both', 'left']:
                criteria[0] = transition(desired_x, desired_y, self.iris_L, rate)
            if left_right in ['both', 'right']:
                criteria[1] = transition(desired_x, desired_y, self.iris_R, rate)
            await self.displays.refresh()
            await asyncio.sleep(0.0001)
        self.left_anchor = self.iris_L.x, self.iris_L.y
        self.right_anchor = self.iris_R.x, self.iris_R.y
        self.transitioning = False
        return int(self.iris_L.x), int(self.iris_R.y)

    async def eye_roll(self, rad: int, direction: SIDES, iterations: int, left_right: HORIZONTALS = 'both'):  # noqa
        """
        Adds some radial movements.
        """
        await self.wait()
        self.transitioning = True
        self.iris_l_cx = (self.dw // 2 - self.iris_w // 2) - self.iris_L.x
        self.iris_l_cy = (self.dh // 2 - self.iris_h // 2) - self.iris_L.y
        self.iris_r_cx = (self.dw // 2 - self.iris_w // 2) - self.iris_R.x
        self.iris_r_cy = (self.dh // 2 - self.iris_h // 2) - self.iris_R.y
        while iterations:
            self.iris_L.x = self.iris_l_cx + int(rad * math.sin(self.theta_L))
            self.iris_L.y = self.iris_l_cy + int(rad * math.cos(self.theta_L))
            self.iris_R.x = self.iris_r_cx + int(rad * math.sin(self.theta_L))
            self.iris_R.y = self.iris_r_cy + int(rad * math.cos(self.theta_L))
            if direction == 'right':
                if left_right in ['both', 'left']:
                    self.theta_L -= self.d_theta_L
                if left_right in ['both', 'right']:
                    self.theta_R -= self.d_theta_R
            if direction == 'left':
                if left_right in ['both', 'left']:
                    self.theta_L += self.d_theta_L
                if left_right in ['both', 'right']:
                    self.theta_R += self.d_theta_R
            await self.displays.refresh()
            await asyncio.sleep(0.0001)
            iterations -= 1
        self.transitioning = False
        return self

    async def saccades(self, x: int, y: int):
        """
        Performs Saccadic Eye Movements
        """
        await self.wait()
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
            left_right: HORIZONTALS = 'both',
            mask: bool = False
    ):
        """
        Makes a squint expression.
        """
        if mask:
            await self.blink('close')
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
        if mask:
            await self.blink('open')
        return self

    async def glance(
            self,
            amount: int,
            top_bottom: VERTICALS = 'both',
            left_right: HORIZONTALS = 'both',
            right_left: HORIZONTALS = 'both',
            bug: BUGS = 'none',
            mask: bool = False
    ):
        """
        Like squint but for diagonal expressions.
        """
        if amount > 0:
            amount += 25
        else:
            amount -= 25
        if mask:
            await self.blink('close')
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
        if mask:
            await self.blink('open')
        return self

    async def blink(self, open_close: OPENS = 'both', left_right: HORIZONTALS = 'both'):
        """
        Aptly named.
        """
        if open_close in ['both', 'close']:
            if left_right in ['both', 'left']:
                self.blink_L.x = 0
            if left_right in ['both', 'right']:
                self.blink_R.x = 0
            await self.displays.refresh()
        if open_close in ['both', 'open']:
            if left_right in ['both', 'left']:
                self.blink_L.x = -200
            if left_right in ['both', 'right']:
                self.blink_R.x = -200
            await self.displays.refresh()
        return self

    async def background_fill(self, fill: int = 0xffffff, left_right: HORIZONTALS = 'both'):
        """
        Changes the background color of the eyes.
        """
        if left_right in ['both', 'left']:
            self.bg_L[0] = self.bg_l_fill = fill
        if left_right in ['both', 'right']:
            self.bg_R[0] = self.bg_r_fill = fill
        await self.displays.refresh()
        return self

    async def foreground_fill(self, fill: int = 0xffffff, left_right: HORIZONTALS = 'both'):
        """
        Changes the foreground blink color of the eyes.
        """
        if left_right in ['both', 'left']:
            self.blink_pal_L[0] = fill
        if left_right in ['both', 'right']:
            self.blink_pal_R[0] = fill
        await self.displays.refresh()
        return self

    async def text_icon(
            self,
            icon_left: ICONS = None,
            icon_right: ICONS = None,
            length: int = 1,
            left_right: HORIZONTALS = 'both',
            _open: bool = True
    ):
        """
        Displays a cool icon instead of the eyeball graphic.
        :return:
        """
        self.transitioning = True
        await self.blink('close', left_right)
        if left_right in ['both', 'left']:
            if icon_left is None:
                icon_left = random.choice(ICONS)
            self.text_L.text = icon_left
            self.text_L.color = self.bg_l_fill
            self.text_L.x = self.iris_L.x
            self.text_L.y = self.iris_L.y + 20
        if left_right in ['both', 'right']:
            if icon_right is None:
                icon_right = random.choice(ICONS)
            self.text_R.text = icon_right
            self.text_R.color = self.bg_r_fill
            self.text_R.x = self.iris_R.x
            self.text_R.y = self.iris_R.y + 20
        await self.displays.refresh()
        await asyncio.sleep(length)
        if _open:
            if left_right in ['both', 'left']:
                self.text_L.text = ''
                self.text_L.x = -100
                self.text_L.y = 0
            if left_right in ['both', 'right']:
                self.text_R.text = ''
                self.text_R.x = -100
                self.text_R.y = 0
            await self.displays.refresh()
            await self.blink('open', left_right)
            self.transitioning = False
        return self

    async def start(self, show: bool = True):
        """
        Gets us started :)
        """
        if show:
            await self.text_icon(left_right='right', _open=False)
            await self.text_icon(left_right='left', _open=False)
            await self.text_icon(left_right='right', _open=False)
            await self.text_icon(length=2)
        else:
            await self.blink('open')
        return self
