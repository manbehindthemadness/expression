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
ICONS = list('abcdefghijklmnopqrstuvwx123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ{}|~!"#%&\'()*+_-/0[]^`;:,.<>?')
BL = ['both', 'left']
BR = ['both', 'right']
NL = ['none', 'left']
NR = ['none', 'right']
BT = ['both', 'top']
BB = ['both', 'bottom']
BC = ['both', 'close']
BO = ['both', 'open']


def percent_of(percent, whole, use_float=False):
    """
    Generic math method
    """
    result = (percent * whole) / 100
    # result = np.divide(np.multiply(percent, whole), 100.0)
    if not use_float:
        result = int(result)
    return result


def percent_in(part, whole, use_float=False):
    """
    Generic math method
    """
    result = 100 * (part / whole)
    if not use_float:
        result = int(result)
    return result


def percentage_center(scaler: int, constant: int) -> int:
    """
    Offsets a zero position to be in the center of the constant.
    """
    scaler = (percent_of(scaler, constant, True) / 2) + (constant / 2)
    return int(scaler)


def center_percentage(scaler: int, constant: int) -> int:
    """
    reverses the above.
    """
    scaler = (percent_in(scaler, constant, True) * 2) - (constant / 2)
    return int(scaler)


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

        self.u_ref = -28
        self.d_ref = -5
        self.l_ref = -56
        self.r_ref = -10

        self.bg_l_fill = 0xffffff
        self.bg_r_fill = 0xffffff

        self.ilr_min_y = -15
        self.ilr_min_y_ref = int(self.ilr_min_y)
        self.ilr_max_y = 25
        self.ilr_max_y_ref = int(self.ilr_max_y)
        self.ilr_min_x = -15
        self.ilr_min_x_ref = int(self.ilr_min_x)
        self.ilr_max_x = 61
        self.ilr_max_x_ref = int(self.ilr_max_x)

        self.irr_min_y = -15
        self.irr_min_y_ref = int(self.irr_min_y)
        self.irr_max_y = 25
        self.irr_max_y_ref = int(self.irr_max_y)
        self.irr_min_x = -15
        self.irr_min_x_ref = int(self.irr_min_x)
        self.irr_max_x = 61
        self.irr_max_x_ref = int(self.irr_max_x)

        self.left_icon = self.right_icon = None

        self.transitioning = False
        self.screen_saving = False

        self.last_ir_l_x = (0, 0)
        self.last_ir_l_y = (0, 0)
        self.last_ir_r_x = (0, 0)
        self.last_ir_r_y = (0, 0)

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

        exp_up_left = displayio.TileGrid(self.exp_top_left, pixel_shader=self.exp_top_left_pal, x=-60, y=-27)
        exp_down_left = displayio.TileGrid(self.exp_bottom_left, pixel_shader=self.exp_bottom_left_pal, x=-60, y=-5)

        exp_up_right = displayio.TileGrid(self.exp_top_right, pixel_shader=self.exp_top_right_pal, x=-6, y=-27)
        exp_down_right = displayio.TileGrid(self.exp_bottom_right, pixel_shader=self.exp_bottom_right_pal, x=-6, y=-4)

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

    async def eye_position(self, x: int, y: int, left_right: HORIZONTALS = 'both', rate: int = 1, const: bool = True) -> tuple[int, int]:
        """
        Updates the direction that our eyes are looking.
        """
        x = percentage_center(x, self.dw)
        y = percentage_center(y, self.dh)
        await self.wait()
        desired_x, desired_y = x - self.iris_mid_x, y - self.iris_mid_y
        des_l_x = des_r_x = desired_x
        des_l_y = des_r_y = desired_y
        if const:  # Handle position restrictions.
            if des_l_x < self.ilr_min_x:
                des_l_x = self.ilr_min_x
            if des_l_x > self.ilr_max_x:
                des_l_x = self.ilr_max_x
            if des_l_y < self.ilr_min_y:
                des_l_y = self.ilr_min_y
            if des_l_y > self.ilr_max_y:
                des_l_y = self.ilr_max_y

            if des_r_x < self.irr_min_x:
                des_r_x = self.irr_min_x
            if des_r_x > self.irr_max_x:
                des_r_x = self.irr_max_x
            if des_r_y < self.irr_min_y:
                des_r_y = self.irr_min_y
            if des_r_y > self.irr_max_y:
                des_r_y = self.irr_max_y

        rng_l_x = range(des_l_x - rate, des_l_x + rate)
        rng_l_y = range(des_l_y - rate, des_l_y + rate)
        rng_r_x = range(des_r_x - rate, des_r_x + rate)
        rng_r_y = range(des_r_y - rate, des_r_y + rate)
        self.transitioning = True
        criteria = [True]
        if left_right == 'both':
            criteria = [False, False]
        if left_right == 'left':
            criteria = [False, True]
        if left_right == 'right':
            criteria = [True, False]
        change = False
        if rate:
            while False in criteria:
                if left_right in BL:
                    criteria[0] = True
                    if des_l_x != self.last_ir_l_x[0] or des_l_y != self.last_ir_l_y[0]:
                        change = True
                        criteria[0] = await self.transition(des_l_x, des_l_y, rng_l_x, rng_l_y, self.iris_L, rate)
                        self.iris_icon_L.x = self.iris_L.x
                        self.iris_icon_L.y = self.iris_L.y + 20
                if left_right in BR:
                    criteria[1] = True
                    if des_r_x != self.last_ir_r_x[0] or des_r_y != self.last_ir_r_y[0]:
                        change = True
                        criteria[1] = await self.transition(des_r_x, des_r_y, rng_r_x, rng_r_y, self.iris_R, rate)
                        self.iris_icon_R.x = self.iris_R.x
                        self.iris_icon_R.y = self.iris_R.y + 20
                await self.displays.refresh()
                self.wait_1 = await self.waits.wait(self.wait_1)
        else:
            if left_right in BL:
                if des_l_x != self.last_ir_l_x[0] or des_l_y != self.last_ir_l_y[0]:
                    change = True
                    self.iris_L.x = des_l_x
                    self.iris_L.y = des_l_y
                    self.iris_icon_L.x = self.iris_L.x
                    self.iris_icon_L.y = self.iris_L.y + 20
            if left_right in BR:
                if des_r_x != self.last_ir_r_x[0] or des_r_y != self.last_ir_r_y[0]:
                    change = True
                    self.iris_R.x = des_r_x
                    self.iris_R.y = des_r_y
                    self.iris_icon_R.x = self.iris_R.x
                    self.iris_icon_R.y = self.iris_R.y + 20
        if change:
            self.left_anchor = self.iris_L.x, self.iris_L.y
            self.right_anchor = self.iris_R.x, self.iris_R.y
        self.transitioning = False

        if left_right in BL:
            self.last_ir_l_x = (des_l_x, x)
            self.last_ir_l_y = (des_l_y, y)
        if left_right in BR:
            self.last_ir_r_x = (des_r_x, x)
            self.last_ir_r_y = (des_r_y, y)

        return int(self.iris_L.x), int(self.iris_R.y)

    async def correct_eye_position(self):
        """
        Checks and confirms that the pupils are in the viewable area
        """
        await self.eye_position(self.last_ir_l_x[1], self.last_ir_l_y[1], 'left', rate=0)
        await self.eye_position(self.last_ir_r_x[1], self.last_ir_r_y[1], 'right', rate=0)
        return self

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
        amount = percent_of(amount, 27)
        if mask:
            await self.blink('close')
        ada = self.u_ref + amount
        adb = self.d_ref - amount
        if top_bottom in BT:
            if left_right in BL:
                self.exp_up_LL.y = ada
                self.exp_up_LR.y = ada
                if amount > 0:
                    self.ilr_min_y = int(self.ilr_min_y_ref + amount)
                else:
                    self.ilr_min_y = self.ilr_min_y_ref
            if left_right in BR:
                self.exp_up_RL.y = ada
                self.exp_up_RR.y = ada
                if amount > 0:
                    self.irr_min_y = int(self.irr_min_y_ref + amount)
                else:
                    self.irr_min_y = self.irr_min_y_ref
            await self.displays.refresh()
        if top_bottom in BB:
            if left_right in BL:
                self.exp_down_LL.y = adb
                self.exp_down_LR.y = adb
                if amount > 0:
                    self.ilr_max_y = int(self.ilr_max_y_ref - amount)
                else:
                    self.ilr_max_y = self.ilr_max_y_ref
            if left_right in BR:
                self.exp_down_RL.y = adb
                self.exp_down_RR.y = adb
                if amount > 0:
                    self.irr_max_y = int(self.irr_max_y_ref - amount)
                else:
                    self.irr_max_y = self.irr_max_y_ref
            await self.displays.refresh()
        await self.correct_eye_position()
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
        amount = percent_of(amount, 56)
        if mask:
            await self.blink('close')
        if top_bottom in BT:  # noqa
            if left_right in BL:
                if right_left in BL:
                    self.exp_up_LL.x = self.l_ref + amount
                    if amount > 0:
                        self.ilr_min_x = int(self.ilr_min_x_ref + amount)
                    else:
                        self.ilr_min_x = self.ilr_min_x_ref
                if right_left in BR:
                    self.exp_up_LR.x = self.r_ref - amount
                    if amount > 0:
                        self.ilr_max_x = int(self.ilr_max_x_ref - amount)
                    else:
                        self.ilr_max_x = self.ilr_max_x_ref
            if left_right in BR:
                if right_left in BL:
                    self.exp_up_RL.x = self.l_ref + amount
                    if amount > 0:
                        self.irr_min_x = int(self.irr_min_x_ref + amount)
                    else:
                        self.irr_min_x = self.irr_min_x_ref
                if right_left in BR:
                    self.exp_up_RR.x = self.r_ref - amount
                    if amount > 0:
                        self.irr_max_x = int(self.irr_max_x_ref - amount)
                    else:
                        self.irr_max_x = self.irr_max_x_ref
            await self.displays.refresh()
        if top_bottom in BB:  # noqa
            if left_right in BL:
                if right_left in BL:
                    self.exp_down_LL.x = self.l_ref + amount
                    if amount > 0:
                        self.ilr_min_x = int(self.ilr_min_x_ref + amount)
                    else:
                        self.ilr_min_x = self.ilr_min_x_ref
                if right_left in BR:
                    self.exp_down_LR.x = self.r_ref - amount
                    if amount > 0:
                        self.ilr_max_x = int(self.ilr_max_x_ref - amount)
                    else:
                        self.ilr_max_x = self.ilr_max_x_ref
            if left_right in BR:
                if right_left in BL:
                    self.exp_down_RL.x = self.l_ref + amount
                    if amount > 0:
                        self.irr_min_x = int(self.irr_min_x_ref + amount)
                    else:
                        self.irr_min_x = self.irr_min_x_ref
                if right_left in BR:
                    self.exp_down_RR.x = self.r_ref - amount
                    if amount > 0:
                        self.irr_max_x = int(self.irr_max_x_ref - amount)
                    else:
                        self.irr_max_x = self.irr_max_x_ref
            await self.displays.refresh()
        if bug == 'none' and self.eyeball_L.x and self.eyeball_R.x:
            self.eyeball_L.x = 0
            self.eyeball_R.x = 0
        if bug in BL:
            self.eyeball_L.x = 200
        if bug in BR:
            self.eyeball_R.x = 200
        await self.displays.refresh()
        await self.correct_eye_position()
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
            await self.eye_position(x=0, y=-185, rate=0, const=False)
            await self.iris_to_icon(left_right='both', color_l=0xffffff, color_r=0xffffff, icon_l=self.left_icon, icon_r=self.right_icon)
            await self.blink('open')
        if self.iris_L.y == 65:
            await self.eye_position(x=0, y=-185, left_right='left', rate=0, const=False)
            self.left_icon = random.choice(ICONS)
        if self.iris_R.y == 65:
            await self.eye_position(x=0, y=-185, left_right='right', rate=0, const=False)
            self.right_icon = random.choice(ICONS)
        await self.iris_to_icon(left_right='both', color_l=0xffffff, color_r=0xffffff, icon_l=self.left_icon, icon_r=self.right_icon)
        await self.eye_position(x=0, y=104, rate=3, const=False)
        await asyncio.sleep(2)
        await self.eye_position(x=0, y=185, left_right=random.choice(HORIZONTALS), rate=3, const=False)
        await asyncio.sleep(0.5)
        if end:
            await self.blink('closed')
            await self.background_fill()
            await self.glance(0)
            await self.iris_to_icon()
            await self.eye_position(x=0, y=0, rate=0, const=False)
            await self.blink('open')
            self.screen_saving = False
        return self
