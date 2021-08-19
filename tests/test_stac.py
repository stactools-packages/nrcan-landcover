import os
import unittest
from tempfile import TemporaryDirectory

import pystac

from stactools.nrcan_landcover import cog, stac, utils
from stactools.nrcan_landcover.constants import JSONLD_HREF
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

            # Select a .tif data file
            test_path = test_data.get_path("data-files")
            cog_path = os.path.join(test_path, [
                d for d in os.listdir(test_path) if d.lower().endswith(".tif")
            ][0])

            # Create stac item
            json_path = os.path.join(tmp_dir, "test.json")
            item = stac.create_item(metadata, json_path, cog_path)
            item.save_object()

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item_path = os.path.join(tmp_dir, jsons[0])

            item = pystac.read_file(item_path)
        asset = item.assets["landcover"]

        # Projection Extension
        assert "proj:epsg" in item.properties
        assert "proj:bbox" in item.properties
        assert "proj:transform" in item.properties
        assert "proj:shape" in item.properties

        # File Extension
        assert "file:size" in asset.extra_fields
        assert "file:values" in asset.extra_fields
        assert len(asset.extra_fields["file:values"]) > 0
        assert "raster:bands" in asset.extra_fields

        # Raster Extension
        assert len(asset.extra_fields["raster:bands"]) == 1
        assert "nodata" in asset.extra_fields["raster:bands"][0]
        assert "sampling" in asset.extra_fields["raster:bands"][0]
        assert "data_type" in asset.extra_fields["raster:bands"][0]
        assert "spatial_resolution" in asset.extra_fields["raster:bands"][0]

    def test_create_collection(self):
        with TemporaryDirectory() as tmp_dir:
            metadata = utils.get_metadata(JSONLD_HREF)

            # Create stac collection
            json_path = os.path.join(tmp_dir, "test.json")
            collection = stac.create_collection(metadata, json_path)
            collection.save_object()

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection_path = os.path.join(tmp_dir, jsons[0])

            collection = pystac.read_file(collection_path)

            collection.validate()
