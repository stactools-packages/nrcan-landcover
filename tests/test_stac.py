import os
from tempfile import TemporaryDirectory
import unittest

import pystac

from stactools.nrcan_landcover.constants import JSONLD_HREF
from stactools.nrcan_landcover import utils, cog, stac

from tests import test_data


class StacTest(unittest.TestCase):
    def test_create_cog(self):
        with TemporaryDirectory() as tmp_dir:
            test_path = test_data.get_path("data-files")
            paths = [
                os.path.join(test_path, d) for d in os.listdir(test_path)
                if d.lower().endswith(".tif")
            ]

            for path in paths:
                output_path = os.path.join(
                    tmp_dir,
                    os.path.basename(path)[:-4] + "_cog.tif")
                cog.create_cog(path, output_path)

                cogs = [
                    p for p in os.listdir(tmp_dir) if p.endswith("_cog.tif")
                ]
                self.assertEqual(len(cogs), 1)

    def test_create_item(self):
        with TemporaryDirectory() as tmp_dir:
            metadata = utils.get_metadata(JSONLD_HREF)

            # Create stac item
            json_path = os.path.join(tmp_dir, "test.json")
            stac.create_item(metadata, json_path, "mock.tif")

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item_path = os.path.join(tmp_dir, jsons[0])

            item = pystac.read_file(item_path)

        item.validate()

    def test_create_collection(self):
        with TemporaryDirectory() as tmp_dir:
            metadata = utils.get_metadata(JSONLD_HREF)

            # Create stac collection
            json_path = os.path.join(tmp_dir, "test.json")
            stac.create_collection(metadata, json_path)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection_path = os.path.join(tmp_dir, jsons[0])

            collection = pystac.read_file(collection_path)

            collection.validate()
