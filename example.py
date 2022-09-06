"""
Lets give a drone some eyes...
"""
import gc
import random
import asyncio
from eyes import Eyes


async def main():
    """
    A loop!
    :return:
    """
    e = Eyes()

    verticals = ['both', 'top', 'bottom']
    horizontals = ['both', 'left', 'right']
    bugs = ['none', 'left', 'none', 'right', 'none', 'both', 'none']
    eyes = ['both', 'both', 'left', 'both', 'both', 'right', 'both', 'both']

    gc.collect()
    print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
    print("MEMORY FREE", gc.mem_free())  # noqa
    shut = False
    while True:
        try:
            if shut:  # If eyes are shut, open them.
                e.blink_L.x = -200
                e.blink_R.x = -200
                shut = False

            if not random.randint(0, 10):
                await e.squint(random.randint(0, 20), random.choice(verticals), random.choice(horizontals))

            if not random.randint(0, 10):
                await e.glance(
                    random.randint(-30, 30),
                    random.choice(verticals),
                    random.choice(horizontals),
                    random.choice(horizontals),
                    random.choice(bugs)
                )

            if not random.randint(0, 25):
                await e.eye_position(
                    random.randint(25, 71),
                    random.randint(25, 39),
                    random.choice(eyes)
                )

            if not random.randint(0, 2):
                await e.saccades(7, 7)

            if not random.randint(0, 50):  # Blink randomly.
                e.blink_L.x = 0
                e.blink_R.x = 0
                shut = True

            delay = random.randint(125, 500) / 1000
            await asyncio.sleep(delay)
        except KeyboardInterrupt:
            pass
            # TODO: Return expression params here.


asyncio.run(main())
