import os

GMFI_ENV = os.environ.get("GMFI_ENV", None)

if GMFI_ENV == "local":
    from .local import *

elif GMFI_ENV == "production":
    from .production import *

else:
    from .local import *
