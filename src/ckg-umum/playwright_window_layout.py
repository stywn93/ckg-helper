import platform
import subprocess
import threading
import tkinter as tk
from dataclasses import dataclass


@dataclass(frozen=True)
class PlaywrightWindowLayout:
    browser_width: int
    inspector_width: int
    height: int
    browser_x: int = 0
    browser_y: int = 0

    @property
    def inspector_x(self) -> int:
        return self.browser_width

    @property
    def inspector_y(self) -> int:
        return 0

    @property
    def chromium_args(self) -> list[str]:
        return [
            f"--window-position={self.browser_x},{self.browser_y}",
            f"--window-size={self.browser_width},{self.height}",
        ]


def get_playwright_window_layout() -> PlaywrightWindowLayout:
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    browser_width = int(screen_width * 2 / 3)
    inspector_width = screen_width - browser_width

    return PlaywrightWindowLayout(
        browser_width=browser_width,
        inspector_width=inspector_width,
        height=screen_height,
    )


def launch_chromium_with_layout(playwright):
    layout = get_playwright_window_layout()
    browser = playwright.chromium.launch(
        headless=False,
        args=layout.chromium_args,
    )
    return browser, layout


def pause_with_inspector_layout(page, layout: PlaywrightWindowLayout) -> None:
    arrange_inspector_window_async(layout)
    page.pause()


def arrange_inspector_window_async(layout: PlaywrightWindowLayout) -> None:
    if platform.system() != "Darwin":
        return

    thread = threading.Thread(
        target=_arrange_macos_inspector_window,
        args=(layout,),
        daemon=True,
    )
    thread.start()


def _arrange_macos_inspector_window(layout: PlaywrightWindowLayout) -> None:
    script = """
on run argv
    set targetX to item 1 of argv as integer
    set targetY to item 2 of argv as integer
    set targetWidth to item 3 of argv as integer
    set targetHeight to item 4 of argv as integer

    tell application "System Events"
        repeat 30 times
            repeat with appProcess in application processes
                repeat with appWindow in windows of appProcess
                    try
                        set windowTitle to name of appWindow as text
                        if windowTitle contains "Playwright Inspector" then
                            set position of appWindow to {targetX, targetY}
                            set size of appWindow to {targetWidth, targetHeight}
                            return
                        end if
                    end try
                end repeat
            end repeat
            delay 0.2
        end repeat
    end tell
end run
"""
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                script,
                str(layout.inspector_x),
                str(layout.inspector_y),
                str(layout.inspector_width),
                str(layout.height),
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass
