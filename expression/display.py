"""
This is a custom method of using two spi screens with a single reset.
"""
import board
import busio
import digitalio
import displayio
from adafruit_ssd1331 import SSD1331
from equalizer import Equalizer  # noqa
from microcontroller import Pin


waits = Equalizer()
wait = 0


class Display:
    """
    Experiments...
    """
    displays = list()

    def __init__(self,
                 rst: Pin,
                 cmd0: Pin,
                 cmd1: Pin,
                 cs0: Pin,
                 cs1: Pin,
                 clock0: Pin = board.SCK,
                 mosi0: Pin = board.MOSI,
                 clock1: Pin = None,
                 mosi1: Pin = None
                 ):
        self.commands = [cmd0, cmd1]
        self.cable_selects = [cs0, cs1]
        self.release()
        displayio.release_displays()
        bus_1 = busio.SPI(clock=clock0, MOSI=mosi0)
        self.busses = [bus_1]
        if None in [clock1, mosi1]:
            self.busses.append(bus_1)
        else:
            self.busses.append(busio.SPI(clock=clock1, MOSI=mosi1))
        for bus in self.busses:
            bus.try_lock()
            bus.unlock()

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

        for bus, cmd, cs in zip(self.busses, self.commands, self.cable_selects):
            bus = displayio.FourWire(
                bus,
                command=cmd,  # noqa
                chip_select=cs,
                baudrate=80_000_000
            )
            display = SSD1331(
                bus,
                width=96,
                height=64,
                auto_refresh=True,
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
        global wait
        self.displays.reverse()
        for display in self.displays:
            await self._refresh(display)
            wait = await waits.wait(wait)
        return self
