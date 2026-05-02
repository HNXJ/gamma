"""
Shim for backward compatibility. 
Redirects all imports to runtime_types.py to avoid shadowing the standard library 'types' module
while supporting legacy import sites.
"""
from .runtime_types import *
