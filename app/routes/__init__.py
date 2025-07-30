# Import available routes
from . import admin

# Try to import optional routes
try:
    from . import blog
except ImportError:
    blog = None

try:
    from . import api
except ImportError:
    api = None

__all__ = ["admin"]
