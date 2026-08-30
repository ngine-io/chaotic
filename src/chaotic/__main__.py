"""Allow ``python -m chaotic``."""

from __future__ import annotations

import sys

from chaotic.cli import main

if __name__ == "__main__":
    sys.exit(main())
