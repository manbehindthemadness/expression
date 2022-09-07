"""
Lets give a drone some eyes...
"""
import gc
import random
import asyncio
try:
    from eyes import Eyes
except ImportError:
    from .eyes import Eyes


def test():
    """
    Runs the visual demonstration test.
    """
    async def main():
        """
        A loop!
        :return:
        """
        e = Eyes()

        directions = ['left', 'right']
        verticals = ['both', 'top', 'bottom']
        horizontals = ['both', 'left', 'right']
        bugs = ['none', 'left', 'none', 'right', 'none', 'both', 'none']
        eyes = ['both', 'both', 'left', 'both', 'both', 'right', 'both', 'both']

        gc.collect()
        print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
        print("MEMORY FREE", gc.mem_free())  # noqa
        while True:
            try:
                if not random.randint(0, 25):
                    await e.squint(
                        random.randint(0, 10),
                        random.choice(verticals),
                        random.choice(horizontals),
                        mask=True
                    )

                if not random.randint(0, 25):
                    await e.glance(
                        random.randint(-15, 15),
                        random.choice(verticals),
                        random.choice(horizontals),
                        random.choice(horizontals),
                        random.choice(bugs),
                        mask=True
                    )

                if not random.randint(0, 10):
                    await e.eye_position(
                        random.randint(25, 71),
                        random.randint(25, 39),
                        random.choice(eyes),
                        random.randint(1, 6)
                    )

                if not random.randint(0, 2):
                    await e.saccades(7, 7)

                if not random.randint(0, 25):
                    await e.blink()

                if not random.randint(0, 10):
                    await e.background_fill(
                        random.randint(0, 16777215),
                        random.choice(horizontals)
                    )

                # if not random.randint(0, 25):
                #     await e.eye_roll(
                #         random.randint(0, 10),
                #         random.choice(directions),
                #         random.randint(5, 20),
                #         random.choice(horizontals)
                #     )

                delay = random.randint(125, 500) / 1000
                await asyncio.sleep(delay)
            except KeyboardInterrupt:
                pass

    asyncio.run(main())
