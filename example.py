"""
Lets give a drone some eyes...
"""
import gc
import random
import time
from eyes import Eyes

e = Eyes()


verticals = ['both', 'top', 'bottom']
horizontals = ['both', 'left', 'right']
bugs = ['none', 'left', 'none', 'right', 'none', 'both', 'none']
eyes = ['both', 'both', 'left', 'both', 'both', 'right', 'both', 'both']

gc.collect()
print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
print("MEMORY FREE", gc.mem_free())  # noqa

displays = [e.display_L, e.display_R]
shut = False
refresh = True
while True:
    if shut:  # If eyes are shut, open them.
        e.blink_L.x = -200
        e.blink_R.x = -200
        shut = False
        refresh = True

    if not random.randint(0, 10):
        e.squint(random.randint(0, 20), random.choice(verticals), random.choice(horizontals))
        refresh = True

    if not random.randint(0, 10):
        e.glance(
            random.randint(-30, 30),
            random.choice(verticals),
            random.choice(horizontals),
            random.choice(horizontals),
            random.choice(bugs)
        )
        refresh = True

    if not random.randint(0, 25):
        e.eye_position(
            random.randint(25, 71),
            random.randint(25, 39),
            random.choice(eyes)
        )
        refresh = True

    if not random.randint(0, 2):
        e.saccades(7, 7)
        refresh = True

    if not random.randint(0, 50):  # Blink randomly.
        e.blink_L.x = 0
        e.blink_R.x = 0
        shut = True
        refresh = True

    if refresh:
        displays.reverse()
        for display in displays:
            display.refresh()
    delay = random.randint(125, 500) / 1000
    refresh = False
    time.sleep(delay)
