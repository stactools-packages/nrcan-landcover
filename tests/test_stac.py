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
            item = stac.create_item(metadata, tmp_dir, JSONLD_HREF, cog_path)
            item.set_self_href(json_path)
            item.save_object(dest_href=json_path)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            item_path = os.path.join(tmp_dir, jsons[0])

            item = pystac.read_file(item_path)
        asset = item.assets["landcover"]

        assert "metadata" in item.assets
        assert "thumbnail" in item.assets
        assert "data" in asset.roles

        # Projection Extension
        assert "proj:epsg" in item.properties
        assert "proj:bbox" in item.properties
        assert "proj:transform" in item.properties
        assert "proj:shape" in item.properties

        assert "proj:epsg" in asset.extra_fields
        assert "proj:bbox" in asset.extra_fields
        assert "proj:transform" in asset.extra_fields
        assert "proj:shape" in asset.extra_fields

        # File Extension
        assert "file:size" in asset.extra_fields
        assert "file:values" in asset.extra_fields
        assert len(asset.extra_fields["file:values"]) > 0

        # Raster Extension
        assert "raster:bands" in asset.extra_fields
        assert len(asset.extra_fields["raster:bands"]) == 1
        assert "nodata" in asset.extra_fields["raster:bands"][0]
        assert "sampling" in asset.extra_fields["raster:bands"][0]
        assert "data_type" in asset.extra_fields["raster:bands"][0]
        assert "spatial_resolution" in asset.extra_fields["raster:bands"][0]

        # Label Extension
        assert "labels" in asset.roles
        assert "labels-raster" in asset.roles

        assert "label:type" in item.properties
        assert "label:tasks" in item.properties
        assert "label:properties" in item.properties
        assert "label:description" in item.properties
        assert "label:classes" in item.properties

        assert "label:type" in asset.extra_fields
        assert "label:tasks" in asset.extra_fields
        assert "label:properties" in asset.extra_fields
        assert "label:description" in asset.extra_fields
        assert "label:classes" in asset.extra_fields

        item.validate()

    def test_create_collection(self):
        with TemporaryDirectory() as tmp_dir:
            metadata = utils.get_metadata(JSONLD_HREF)

            # Create stac collection
            json_path = os.path.join(tmp_dir, "test.json")
            collection = stac.create_collection(metadata, JSONLD_HREF)
            collection.set_self_href(json_path)
            collection.save_object(dest_href=json_path)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            self.assertEqual(len(jsons), 1)

            collection_path = os.path.join(tmp_dir, jsons[0])

            collection = pystac.read_file(collection_path)

            item_asset = collection.extra_fields["item_assets"]["landcover"]
            summaries = collection.summaries.to_dict()

            assert "metadata" in collection.assets
            assert "thumbnail" in collection.assets
            assert "data" in item_asset["roles"]

            # Projection Extension
            assert "proj:epsg" in item_asset
            assert "proj:epsg" in summaries

            # File Extension
            assert "file:values" in item_asset
            assert len(item_asset["file:values"]) > 0

            # Raster Extension
            assert "raster:bands" in item_asset
            assert "nodata" in item_asset["raster:bands"]
            assert "sampling" in item_asset["raster:bands"]
            assert "data_type" in item_asset["raster:bands"]
            assert "spatial_resolution" in item_asset["raster:bands"]

            # Label Extension
            assert "labels" in item_asset["roles"]
            assert "labels-raster" in item_asset["roles"]

            assert "label:type" in summaries
            assert "label:tasks" in summaries
            assert "label:classes" in summaries

            assert "label:type" in item_asset
            assert "label:tasks" in item_asset
            assert "label:properties" in item_asset
            assert "label:classes" in item_asset

            collection.validate()
