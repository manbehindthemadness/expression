"""
A wild init file!
"""
try:
    from eyes import Eyes
    from example import test, screensaver
except ImportError:
    from .eyes import Eyes
    from .example import test, screensaver
