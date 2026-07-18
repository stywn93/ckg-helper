import os
from playwright.sync_api import Locator

CLICK_DELAY_MS = int(os.getenv("CKG_CLICK_DELAY_MS", "1000"))

if CLICK_DELAY_MS > 0:
    _original_click = Locator.click

    def _patched_click(self, **kwargs):
        _original_click(self, **kwargs)
        self.page.wait_for_timeout(CLICK_DELAY_MS)

    Locator.click = _patched_click
