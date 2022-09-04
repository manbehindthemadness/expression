import time
import board
import displayio
import terminalio
from adafruit_display_text import label
from display import Display


reset = board.D9

cs0 = board.D3
cs1 = board.D2

command0 = board.D0
command1 = board.D1


splash1 = displayio.Group()
splash2 = displayio.Group()


displays = Display(reset, command0, command1, cs0, cs1)

display0 = displays.displays[0]
display0.show(splash1)

display1 = displays.displays[1]
display1.show(splash2)

color_bitmap = displayio.Bitmap(96, 64, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF00 # Bright Green

bg_sprite = displayio.TileGrid(color_bitmap,
                               pixel_shader=color_palette,
                               x=0, y=0)
splash1.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(86, 54, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0xAA0088 # Purple
inner_sprite = displayio.TileGrid(inner_bitmap,
                                  pixel_shader=inner_palette,
                                  x=5, y=5)
splash1.append(inner_sprite)

# Draw a label
text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=12, y=32)
splash1.append(text_area)

time.sleep(1)

color_bitmap = displayio.Bitmap(96, 64, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF00 # Bright Green

bg_sprite = displayio.TileGrid(color_bitmap,
                               pixel_shader=color_palette,
                               x=0, y=0)
splash2.append(bg_sprite)

splash2.append(label.Label(terminalio.FONT, text='second display', color=0xFFFF00, x=12, y=32))
