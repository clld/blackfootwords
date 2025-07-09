"""
Utility functions
"""


def log_or_raise(msg, log=None, level='error'):
    if log:
        getattr(log, level)(msg)
        return False
    raise ValueError(msg)
