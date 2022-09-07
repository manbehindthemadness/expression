"""
A wild init file!
"""
try:
    from eyes import Eyes
    from example import test
except ImportError:
    from .eyes import Eyes
    from .example import test
