import unittest

import stactools.nrcan_landcover


class TestModule(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(stactools.nrcan_landcover.__version__)
