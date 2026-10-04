import unittest
from unittest.mock import patch

import ckg_helper


class TestStopHandler(unittest.TestCase):
    @patch("ckg_helper.install_asyncio_exception_filter")
    @patch("ckg_helper.show_banner")
    @patch("ckg_helper.get_app_root")
    @patch("ckg_helper.load_app_env")
    @patch("ckg_helper.check_for_update", return_value=None)
    @patch("ckg_helper.run_selected_option", side_effect=KeyboardInterrupt)
    @patch("ckg_helper.pause")
    @patch("ckg_helper.select_menu", side_effect=["1", "q"])
    def test_keyboard_interrupt_does_not_pause(
        self,
        mock_select_menu,
        mock_pause,
        mock_run_selected_option,
        mock_check_update,
        mock_load_env,
        mock_get_app_root,
        mock_show_banner,
        mock_install_filter,
    ):
        ckg_helper.main()
        self.assertEqual(mock_select_menu.call_count, 2)
        mock_pause.assert_not_called()


if __name__ == "__main__":
    unittest.main()
