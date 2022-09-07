"""
This is a custom method of using two spi screens with a single reset.
"""
import board
import busio
import digitalio
import displayio
from adafruit_ssd1331 import SSD1331


class Display:
    """
    Experiments...
    """
    displays = list()

    def __init__(self, rst, cmd0, cmd1, cs0, cs1, clock=board.SCK, mosi=board.MOSI):
        self.commands = [cmd0, cmd1]
        self.cable_selects = [cs0, cs1]
        self.release()
        displayio.release_displays()
        self.spi = busio.SPI(clock=clock, MOSI=mosi)
        self.spi.try_lock()
        self.spi.configure(baudrate=100000000)
        self.spi.unlock()
        self.rst = rst
        self.activate()

    def activate(self):
        """
        Activates the current display.
        """
        rst = digitalio.DigitalInOut(self.rst)
        rst.direction = digitalio.Direction.OUTPUT
        rst.value = True
        self.rst = rst
        for cmd, cs in zip(self.commands, self.cable_selects):
            bus = displayio.FourWire(
                self.spi,
                command=cmd,
                chip_select=cs,
            )
            display = SSD1331(
                bus,
                width=96,
                height=64,
                auto_refresh=False
            )
            self.displays.append(display)
        return self

    async def reset(self):
        """
        reset.
        """
        self.rst.value = False
        self.rst.value = True

    async def release(self):
        """
        Resets all displays.

        This is to be used to free resources BEFORE init, not during the program.
        :return:
        """
        try:
            await self.reset()
        except AttributeError:
            pass
        displayio.release_displays()

    async def _refresh(self, display: displayio.Display):
        """
        Refreshes a screen.
        """
        display.refresh()
        return self

    async def refresh(self):
        """
        Refreshes our screens.
        :return:
        """
        self.displays.reverse()
        for display in self.displays:
            await self._refresh(display)
        return self