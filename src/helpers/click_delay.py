import contextlib
import os
from playwright.sync_api import Locator

CLICK_DELAY_MS = int(os.getenv("CKG_CLICK_DELAY_MS", "1000"))
_delay_enabled = True

if CLICK_DELAY_MS > 0:
    _original_click = Locator.click

    def _patched_click(self, **kwargs):
        _original_click(self, **kwargs)
        if _delay_enabled:
            self.page.wait_for_timeout(CLICK_DELAY_MS)

    Locator.click = _patched_click


@contextlib.contextmanager
def no_click_delay():
    global _delay_enabled
    _delay_enabled = False
    try:
        yield
    finally:
        _delay_enabled = True
