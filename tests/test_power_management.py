import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.helpers.power_management import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    SleepPreventer,
)


class TestSleepPreventer(unittest.TestCase):
    @patch("sys.platform", "win32")
    def test_windows_acquire_and_release(self):
        mock_kernel32 = MagicMock()
        mock_kernel32.SetThreadExecutionState.return_value = 1

        mock_windll = MagicMock()
        mock_windll.kernel32 = mock_kernel32

        with patch("src.helpers.power_management.ctypes") as mock_ctypes:
            mock_ctypes.windll = mock_windll
            preventer = SleepPreventer()
            self.assertFalse(preventer.is_active)

            with preventer:
                self.assertTrue(preventer.is_active)
                mock_kernel32.SetThreadExecutionState.assert_called_with(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                )

            self.assertFalse(preventer.is_active)
            mock_kernel32.SetThreadExecutionState.assert_called_with(ES_CONTINUOUS)

    @patch("sys.platform", "darwin")
    @patch("src.helpers.power_management.subprocess.Popen")
    def test_darwin_acquire_and_release(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        preventer = SleepPreventer()
        with preventer:
            self.assertTrue(preventer.is_active)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "caffeinate")
            self.assertIn("-d", args[0])

        self.assertFalse(preventer.is_active)
        mock_proc.terminate.assert_called_once()

    @patch("sys.platform", "win32")
    def test_windows_exception_graceful_handling(self):
        with patch("src.helpers.power_management.ctypes") as mock_ctypes:
            mock_ctypes.windll.kernel32.SetThreadExecutionState.side_effect = RuntimeError("DLL failure")
            preventer = SleepPreventer()
            # Should not raise exception
            preventer.acquire()
            self.assertFalse(preventer.is_active)
            preventer.release()

    @patch("sys.platform", "darwin")
    @patch("src.helpers.power_management.subprocess.Popen")
    def test_darwin_exception_graceful_handling(self, mock_popen):
        mock_popen.side_effect = OSError("caffeinate not found")
        preventer = SleepPreventer()
        preventer.acquire()
        self.assertFalse(preventer.is_active)
        preventer.release()


if __name__ == "__main__":
    unittest.main()
