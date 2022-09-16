"""
Lets give a drone some eyes...
"""
import math
import board
import displayio
import asyncio
import random
import adafruit_imageload
from adafruit_bitmap_font import bitmap_font  # noqa
from adafruit_display_text import label  # noqa
try:
    from display import Display, waits
except ImportError:
    from .display import Display, waits

SIDES = ['left', 'right']
VERTICALS = ['both', 'top', 'bottom']
HORIZONTALS = ['both', 'left', 'right']
BUGS = ['none', 'left', 'right', 'both']
OPENS = ['open', 'close', 'both']
font = bitmap_font.load_font("expression/img/ldr.bdf", displayio.Bitmap)
ICONS = list('abcdefghijklmnopqrstuvwx123456789')
BL = ['both', 'left']
BR = ['both', 'right']
NL = ['none', 'left']
NR = ['none', 'right']
BT = ['both', 'top']
BB = ['both', 'bottom']
BC = ['both', 'close']
BO = ['both', 'open']


class Eyes:
    """
    This is our fancy eye-control class.
    """
    wait_1 = wait_2 = 0

    def __init__(
            self,
            reset=board.D9,
            cs0=board.D7,
            cs1=board.D3,
            command0=board.D4,
            command1=board.D5,
            clock0=board.SCK,
            mosi0=board.MOSI,
            clock1=None,
            mosi1=None
    ):
        self.waits = waits

        self.reset = reset

        self.cs0 = cs0
        self.cs1 = cs1

        self.command0 = command0
        self.command1 = command1

        self.displays = Display(
            self.reset, self.command0, self.command1, self.cs0, self.cs1,
            clock0, mosi0, clock1, mosi1
        )
        self.displays.reset()

        self.dw, self.dh = 96, 64
        self.iris_w, self.iris_h = 48, 50

        self.iris_l_cy = self.iris_r_cx = self.dh // 2 - self.iris_h // 2
        self.iris_l_cx = self.iris_r_cy = self.dw // 2 - self.iris_w // 2

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
        self.transparent(self.exp_top_left_pal)

        self.exp_bottom_left, self.exp_bottom_left_pal = adafruit_imageload.load(
            "expression/img/exp_bottom_left.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.transparent(self.exp_bottom_left_pal)

        self.exp_top_right, self.exp_top_right_pal = adafruit_imageload.load(
            "expression/img/exp_top_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.transparent(self.exp_top_right_pal)

        self.exp_bottom_right, self.exp_bottom_right_pal = adafruit_imageload.load(
            "expression/img/exp_bottom_right.bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.transparent(self.exp_bottom_right_pal)

        self.group_L, self.display_L, self.eyeball_L, self.iris_L, self.exp_up_LL, \
            self.exp_down_LL, self.exp_up_LR, self.exp_down_LR, \
            self.blink_L, self.blink_pal_L, self.bg_L, self.text_L, self.iris_icon_L \
            = self.display_eye_init(self.displays.displays[1], 'left')
        self.group_R, self.display_R, self.eyeball_R, self.iris_R, self.exp_up_RL, \
            self.exp_down_RL, self.exp_up_RR, self.exp_down_RR, \
            self.blink_R, self.blink_pal_R, self.bg_R, self.text_R, self.iris_icon_R \
            = self.display_eye_init(self.displays.displays[0], 'right')

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

        self.left_icon = self.right_icon = None

        self.transitioning = False
        self.screen_saving = False

    async def wait(self):
        """
        Waits for a transition to complete.
        """
        while self.transitioning:
            await asyncio.sleep(0.0001)

    def transparent(self, palette: displayio.Palette):
        """
        This will remove everything but the black.
        """
        for i in range(len(palette)):
            if i > 0:
                palette.make_transparent(i)
        return self

    def display_eye_init(
            self,
            display: displayio.Display,
            side: SIDES
    ) -> tuple[
        displayio.Group,
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
        label,
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
        blink_palette[0] = 0x000000

        eyeball_bitmap, eyeball_pal = adafruit_imageload.load(
            "expression/img/eye_" + side + ".bmp",
            bitmap=displayio.Bitmap,
            palette=displayio.Palette
        )
        self.transparent(eyeball_pal)
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

        text = label.Label(font, text='')
        text.x = -100
        text.y = 30

        iris_icon = label.Label(font, text='')

        main.append(bg)
        main.append(iris)
        main.append(eyeball)
        main.append(exp_up_left)
        main.append(exp_down_left)
        main.append(exp_up_right)
        main.append(exp_down_right)
        main.append(bnk)
        main.append(text)
        return main, display, eyeball, iris, exp_up_left, exp_down_left, exp_up_right, exp_down_right, \
            bnk, blink_palette, bg_palette, text, iris_icon

    @staticmethod
    async def _range_x(item, des, speed, rng):
        """
        Calculate individual transition.
        """
        result = True
        cur = item.x
        if cur not in rng:
            if des < cur:
                item.x -= speed
                result = False
            if des > cur:
                item.x += speed
                result = False
        return result

    @staticmethod
    async def _range_y(item, des, speed, rng):
        """
        Calculate individual transition.
        """
        result = True
        cur = item.y
        if cur not in rng:
            if des < cur:
                item.y -= speed
                result = False
            if des > cur:
                item.y += speed
                result = False
        return result

    async def transition(self, des_x: int, des_y: int, rng_x: range, rng_y: range, item: displayio.TileGrid, speed: int) -> bool:
        """
        Calculates transition.
        """
        result = await self._range_x(item, des_x, speed, rng_x)  # noqa
        result = await self._range_y(item, des_y, speed, rng_y)
        return result

    async def eye_position(self, x: int, y: int, left_right: HORIZONTALS = 'both', rate: int = 1) -> tuple[int, int]:
        """
        Updates the direction that our eyes are looking.
        """

        await self.wait()
        desired_x, desired_y = x - self.iris_mid_x, y - self.iris_mid_y
        rng_x = range(desired_x - rate, desired_x + rate)
        rng_y = range(desired_y - rate, desired_y + rate)
        self.transitioning = True
        criteria = [True]
        if left_right == 'both':
            criteria = [False, False]
        if left_right == 'left':
            criteria = [False, True]
        if left_right == 'right':
            criteria = [True, False]
        if rate:
            while False in criteria:
                if left_right in BL:
                    criteria[0] = await self.transition(desired_x, desired_y, rng_x, rng_y, self.iris_L, rate)
                    self.iris_icon_L.x = self.iris_L.x
                    self.iris_icon_L.y = self.iris_L.y + 20
                if left_right in BR:
                    criteria[1] = await self.transition(desired_x, desired_y, rng_x, rng_y, self.iris_R, rate)
                    self.iris_icon_R.x = self.iris_R.x
                    self.iris_icon_R.y = self.iris_R.y + 20
                await self.displays.refresh()
                self.wait_1 = await self.waits.wait(self.wait_1)
        else:
            if left_right in BL:
                self.iris_L.x = x
                self.iris_L.y = y
                self.iris_icon_L.x = self.iris_L.x
                self.iris_icon_L.y = self.iris_L.y + 20
            if left_right in BR:
                self.iris_R.x = x
                self.iris_R.y = y
                self.iris_icon_R.x = self.iris_R.x
                self.iris_icon_R.y = self.iris_R.y + 20
        self.left_anchor = self.iris_L.x, self.iris_L.y
        self.right_anchor = self.iris_R.x, self.iris_R.y
        self.transitioning = False
        return int(self.iris_L.x), int(self.iris_R.y)

    async def iris_to_icon(
            self,
            left_right: BUGS = 'none',
            icon_l: ICONS = None,
            icon_r: ICONS = None,
            color_l: int = 0x000000,
            color_r: int = 0x000000
    ):
        """
        This will swap an iris for an icon.
        """
        if left_right in BL:
            if icon_l is None:
                icon_l = random.choice(ICONS)
            self.iris_icon_L.text = icon_l
            self.iris_icon_L.color = color_l
            self.group_L.pop(1)
            self.group_L.insert(1, self.iris_icon_L)
        if left_right in BR:
            if icon_r is None:
                icon_r = random.choice(ICONS)
            self.iris_icon_R.text = icon_r
            self.iris_icon_R.color = color_r
            self.group_R.pop(1)
            self.group_R.insert(1, self.iris_icon_R)
        if left_right in NL:
            self.group_R.pop(1)
            self.group_R.insert(1, self.iris_R)
            self.iris_icon_R.text = ''
        if left_right in NR:
            self.group_L.pop(1)
            self.group_L.insert(1, self.iris_L)
            self.iris_icon_L.text = ''
        await self.displays.refresh()
        return self

    async def eye_roll(self, rad: int, direction: SIDES, iterations: int, left_right: HORIZONTALS = 'both'):
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
                if left_right in BL:
                    self.theta_L -= self.d_theta_L
                if left_right in BR:
                    self.theta_R -= self.d_theta_R
            if direction == 'left':
                if left_right in BL:
                    self.theta_L += self.d_theta_L
                if left_right in BR:
                    self.theta_R += self.d_theta_R
            await self.displays.refresh()
            self.wait_2 = await self.waits.wait(self.wait_2)
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
        self.iris_icon_L.x = self.iris_L.x
        self.iris_icon_L.y = self.iris_L.y + 20
        self.iris_icon_R.x = self.iris_R.x
        self.iris_icon_R.y = self.iris_R.y + 20
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
        if top_bottom in BT:
            if left_right in BL:
                self.exp_up_LL.y = self.u_ref + amount
                self.exp_up_LR.y = self.u_ref + amount
            if left_right in BR:
                self.exp_up_RL.y = self.u_ref + amount
                self.exp_up_RR.y = self.u_ref + amount
            await self.displays.refresh()
        if top_bottom in BB:
            if left_right in BL:
                self.exp_down_LL.y = self.d_ref - amount
                self.exp_down_LR.y = self.d_ref - amount
            if left_right in BR:
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
        if mask:
            await self.blink('close')
        if amount > 0:
            amount += 25
        if amount < 0:
            amount -= 25
        if top_bottom in BT:
            if left_right in BL:
                if right_left in BL:
                    self.exp_up_LL.x = self.l_ref + amount
                if right_left in BR:
                    self.exp_up_LR.x = self.r_ref + amount
            if left_right in BR:
                if right_left in BL:
                    self.exp_up_RL.x = self.l_ref + amount
                if right_left in BR:
                    self.exp_up_RR.x = self.r_ref + amount
            await self.displays.refresh()
        if top_bottom in BB:
            if left_right in BL:
                if right_left in BL:
                    self.exp_down_LL.x = self.l_ref + amount
                if right_left in BR:
                    self.exp_down_LR.x = self.r_ref + amount
            if left_right in BR:
                if right_left in BL:
                    self.exp_down_RL.x = self.l_ref + amount
                if right_left in BR:
                    self.exp_down_RR.x = self.r_ref + amount
            await self.displays.refresh()
        if bug == 'none' and self.eyeball_L.x and self.eyeball_R.x:
            self.eyeball_L.x = 0
            self.eyeball_R.x = 0
        if bug in BL:
            self.eyeball_L.x = 200
        if bug in BR:
            self.eyeball_R.x = 200
        await self.displays.refresh()
        if mask:
            await self.blink('open')
        return self

    async def blink(self, open_close: OPENS = 'both', left_right: HORIZONTALS = 'both'):
        """
        Aptly named.
        """
        if open_close in BC:
            if left_right in BL:
                self.blink_L.x = 0
            if left_right in BR:
                self.blink_R.x = 0
            await self.displays.refresh()
        if open_close in BO:
            if left_right in BL:
                self.blink_L.x = -200
            if left_right in BR:
                self.blink_R.x = -200
            await self.displays.refresh()
        return self

    async def background_fill(self, fill: int = 0xffffff, left_right: HORIZONTALS = 'both'):
        """
        Changes the background color of the eyes.
        """
        if left_right in BL:
            self.bg_L[0] = self.bg_l_fill = fill
        if left_right in BR:
            self.bg_R[0] = self.bg_r_fill = fill
        await self.displays.refresh()
        return self

    async def foreground_fill(self, fill: int = 0xffffff, left_right: HORIZONTALS = 'both'):
        """
        Changes the foreground blink color of the eyes.
        """
        if left_right in BL:
            self.blink_pal_L[0] = fill
        if left_right in BR:
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
        """
        self.transitioning = True
        await self.blink('close', left_right)
        if left_right in BL:
            if icon_left is None:
                icon_left = random.choice(ICONS)
            self.text_L.text = icon_left
            self.text_L.color = self.bg_l_fill
            self.text_L.x = self.iris_L.x
            self.text_L.y = self.iris_L.y + 20
        if left_right in BR:
            if icon_right is None:
                icon_right = random.choice(ICONS)
            self.text_R.text = icon_right
            self.text_R.color = self.bg_r_fill
            self.text_R.x = self.iris_R.x
            self.text_R.y = self.iris_R.y + 20
        await self.displays.refresh()
        await asyncio.sleep(length)
        if _open:
            if left_right in BL:
                self.text_L.text = ''
                self.text_L.x = -100
                self.text_L.y = 0
            if left_right in BR:
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
            await self.screensaver()
            await self.screensaver()
            await self.screensaver(end=True)
        else:
            await self.blink('open')
        return self

    async def screensaver(self, end: bool = False):
        """
        A cool screen-saver because why not?
        """
        if not self.screen_saving:
            self.screen_saving = True
            self.left_icon = random.choice(ICONS)
            self.right_icon = random.choice(ICONS)
            await self.blink('closed')
            await self.background_fill(0x000000)
            await self.squint(0)
            await self.glance(0, bug='both')
            await self.eye_position(x=46, y=-70, rate=0)
            await self.iris_to_icon(left_right='both', color_l=0xffffff, color_r=0xffffff, icon_l=self.left_icon, icon_r=self.right_icon)
            await self.blink('open')
        if self.iris_L.y == 92:
            await self.eye_position(x=46, y=-70, left_right='left', rate=0)
            self.left_icon = random.choice(ICONS)
        if self.iris_R.y == 92:
            await self.eye_position(x=46, y=-70, left_right='right', rate=0)
            self.right_icon = random.choice(ICONS)
        await self.iris_to_icon(left_right='both', color_l=0xffffff, color_r=0xffffff, icon_l=self.left_icon, icon_r=self.right_icon)
        await self.eye_position(x=46, y=35, rate=3)
        await asyncio.sleep(2)
        await self.eye_position(x=46, y=120, left_right=random.choice(HORIZONTALS), rate=3)
        await asyncio.sleep(0.5)
        if end:
            self.screen_saving = False
            await self.blink('closed')
            await self.background_fill()
            await self.glance(0)
            await self.iris_to_icon()
            await self.eye_position(x=self.iris_l_cx, y=self.iris_l_cy, rate=0)
            await self.blink('open')
        return self
