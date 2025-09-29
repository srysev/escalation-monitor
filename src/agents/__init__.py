# src/agents/__init__.py
from . import military
from . import diplomatic
from . import economic
from . import societal
from . import russians

AGENTS = {
    "military": military,
    "diplomatic": diplomatic,
    "economic": economic,
    "societal": societal,
    "russians": russians,
}