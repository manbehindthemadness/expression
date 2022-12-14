"""
Lets give a drone some eyes...
"""
import gc
import random
import board
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
        e = Eyes(clock1=board.D0, mosi1=board.D1)

        verticals = ['both', 'top', 'bottom']
        horizontals = ['both', 'left', 'right']
        bugs = ['none', 'left', 'none', 'right', 'none', 'both', 'none']
        eyes = ['both', 'both', 'left', 'both', 'both', 'right', 'both', 'both']

        gc.collect()
        print("MEMORY ALLOCATED", gc.mem_alloc())  # noqa
        print("MEMORY FREE", gc.mem_free())  # noqa
        await e.start()
        while True:
            try:
                if not random.randint(0, 25):
                    await e.squint(  # Note that the squint sprites are in halves, top and bottom.
                        amount=random.randint(0, 100),  # Intensity of the expression.
                        top_bottom=random.choice(verticals),  # Top or bottom lid(s).
                        left_right=random.choice(horizontals),  # Left or right lid(s).
                        mask=True  # Mask the transition by blinking.
                    )

                if not random.randint(0, 25):
                    await e.glance(  # Note that the glance sprites are in quadrants.
                        amount=random.randint(0, 100),  # Intensity of the expression.
                        top_bottom=random.choice(verticals),  # Top or bottom lid(s).
                        left_right=random.choice(horizontals),  # Left or right lid(s).
                        right_left=random.choice(horizontals),  # Left or right lid-halves.
                        bug=random.choice(bugs),  # Go full-on bug-eyed.
                        mask=True  # Mask the transition by blinking.
                    )

                if not random.randint(0, 5):
                    await e.eye_position(
                        x=random.randint(-75, 75),
                        y=random.randint(-75, 75),
                        left_right=random.choice(eyes),  # Left, right, or both eyes.
                        rate=random.randint(1, 10)  # Speed of movement.
                    )

                if not random.randint(0, 2):
                    await e.saccades(  # Random eye twitch.
                        x=7,  # Allowed variance x.
                        y=7  # Allowed variance y.
                    )

                if not random.randint(0, 25):
                    await e.blink()  # Blink our eyes.

                if not random.randint(0, 10):
                    await e.background_fill(
                        fill=random.randint(0, 16777215),  # Choose a random color.
                        left_right=random.choice(horizontals)  # Left or right eye-backgrounds.
                    )

                if not random.randint(0, 75):
                    await e.iris_to_icon(  # Randomly display a sick-ass love, death and robots icon ;)
                        left_right=random.choice(horizontals)
                    )
                if not random.randint(0, 10):  # Change icons back into normal eyes.
                    await e.iris_to_icon()

                delay = random.randint(125, 500) / 1000  # Keep the cycle uneven enough to look convincing.
                await asyncio.sleep(delay)
            except KeyboardInterrupt:
                pass

    asyncio.run(main())


def screensaver():
    """
    Tests out the neat screensaver function.
    :return:
    """
    async def main():
        """
        Teh loop.
        :return:
        """
        e = Eyes()
        while True:
            await e.screensaver()

    asyncio.run(main())
