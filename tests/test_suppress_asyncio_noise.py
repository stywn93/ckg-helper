import logging
import unittest

from src.helpers.suppress_asyncio_noise import (
    SuppressTargetClosedFilter,
    install_asyncio_exception_filter,
)


class TestSuppressTargetClosedFilter(unittest.TestCase):
    def _make_record(self, msg: str, exc_info=None) -> logging.LogRecord:
        return logging.LogRecord(
            name="asyncio",
            level=logging.ERROR,
            pathname=__file__,
            lineno=0,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )

    def test_suppresses_target_closed_error_message(self):
        """Log yang mengandung 'TargetClosedError' harus disaring."""
        flt = SuppressTargetClosedFilter()
        record = self._make_record(
            "Future exception was never retrieved\n"
            "playwright._impl._errors.TargetClosedError: Target page, context or browser has been closed"
        )
        self.assertFalse(flt.filter(record))

    def test_suppresses_target_page_closed_message(self):
        """Log yang mengandung kalimat 'Target page, context or browser has been closed' harus disaring."""
        flt = SuppressTargetClosedFilter()
        record = self._make_record("Target page, context or browser has been closed")
        self.assertFalse(flt.filter(record))

    def test_allows_other_error_messages(self):
        """Log error selain TargetClosedError harus tetap lolos."""
        flt = SuppressTargetClosedFilter()
        record = self._make_record("Some unexpected asyncio error that is not playwright-related")
        self.assertTrue(flt.filter(record))

    def test_allows_empty_message(self):
        """Log dengan pesan kosong harus tetap lolos."""
        flt = SuppressTargetClosedFilter()
        record = self._make_record("")
        self.assertTrue(flt.filter(record))


class TestInstallAsyncioExceptionFilter(unittest.TestCase):
    def setUp(self):
        """Bersihkan filter yang mungkin sudah terpasang dari test lain."""
        logger = logging.getLogger("asyncio")
        logger.filters = [
            f for f in logger.filters if not isinstance(f, SuppressTargetClosedFilter)
        ]

    def test_filter_installed(self):
        """install_asyncio_exception_filter() harus memasang filter ke asyncio logger."""
        install_asyncio_exception_filter()
        logger = logging.getLogger("asyncio")
        count = sum(1 for f in logger.filters if isinstance(f, SuppressTargetClosedFilter))
        self.assertEqual(count, 1)

    def test_install_is_idempotent(self):
        """Memanggil install_asyncio_exception_filter() berkali-kali tidak boleh menambahkan filter ganda."""
        install_asyncio_exception_filter()
        install_asyncio_exception_filter()
        install_asyncio_exception_filter()
        logger = logging.getLogger("asyncio")
        count = sum(1 for f in logger.filters if isinstance(f, SuppressTargetClosedFilter))
        self.assertEqual(count, 1)

    def tearDown(self):
        """Bersihkan filter setelah setiap test."""
        logger = logging.getLogger("asyncio")
        logger.filters = [
            f for f in logger.filters if not isinstance(f, SuppressTargetClosedFilter)
        ]


if __name__ == "__main__":
    unittest.main()
