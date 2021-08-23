import logging
import os
from typing import Optional

import click

from stactools.nrcan_landcover import cog, extent, stac, utils
from stactools.nrcan_landcover.constants import JSONLD_HREF

logger = logging.getLogger(__name__)


def create_nrcanlandcover_command(cli: click.Group) -> click.Command:
    """Creates the nrcanlandcover command line utility."""
    @cli.group(
        "nrcanlandcover",
        short_help=(
            "Commands for working with Natural Resources Canada Land Cover data"
        ),
    )
    def nrcanlandcover() -> None:
        pass

    @nrcanlandcover.command(
        "create-collection",
        short_help="Creates a STAC collection from NRCan Landcover metadata",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC Collection json",
    )
    @click.option(
        "-m",
        "--metadata",
        help="The url to the metadata jsonld",
        default=JSONLD_HREF,
    )
    def create_collection_command(destination: str, metadata: str) -> None:
        """Creates a STAC Collection from NRCan Landcover metadata

        Args:
            destination (str): Directory used to store the collection json
            metadata (str): Path to a jsonld metadata file - provided by NRCan
        Returns:
            Callable
        """
        metadata_dict = utils.get_metadata(metadata)
        output_path = os.path.join(destination, "collection.json")
        collection = stac.create_collection(metadata_dict, metadata)
        collection.set_self_href(output_path)
        collection.make_all_asset_hrefs_relative()
        collection.save_object(dest_href=output_path)

    @nrcanlandcover.command(
        "create-cog",
        short_help="Transform Geotiff to Cloud-Optimized Geotiff.",
    )
    @click.option("-d",
                  "--destination",
                  required=True,
                  help="The output directory for the COG")
    @click.option("-s",
                  "--source",
                  required=False,
                  help="Path to an input GeoTiff")
    def create_cog_command(destination: str, source: Optional[str]) -> None:
        """Generate a COG from a GeoTiff. The COG will be saved in the desination
        with `_cog.tif` appended to the name.

        Args:
            destination (str): Local directory to save output COGs
            source (str): An input NRCAN Landcover GeoTiff
        """
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        if source is None:
            cog.download_create_cog(destination)

        else:
            output_path = os.path.join(
                destination,
                os.path.basename(source)[:-4] + "_cog.tif")
            cog.create_cog(source, output_path)

    @nrcanlandcover.command(
        "create-item",
        short_help="Create a STAC item using JSONLD metadata and a COG",
    )
    @click.option(
        "-d",
        "--destination",
        required=True,
        help="The output directory for the STAC json",
    )
    @click.option("-c", "--cog", required=True, help="COG href")
    @click.option(
        "-m",
        "--metadata",
        help="The url to the metadata description.",
        default=JSONLD_HREF,
    )
    def create_item_command(destination: str, cog: str, metadata: str) -> None:
        """Generate a STAC item using the metadata, with an asset url as provided.

        Args:
            destination (str): Local directory to save the STAC Item json
            cog (str): location of a COG asset for the item
            metadata (str): url containing the NRCAN Landcover JSONLD metadata
        """
        jsonld_metadata = utils.get_metadata(metadata)
        output_path = os.path.join(destination,
                                   os.path.basename(cog)[:-4] + ".json")
        item = stac.create_item(jsonld_metadata, metadata, cog)
        item.set_self_href(output_path)
        item.make_asset_hrefs_relative()
        item.save_object(dest_href=output_path)

    @nrcanlandcover.command(
        "create-extent-asset",
        short_help="Create extent asset for the STAC Item",
    )
    @click.option("-d",
                  "--destination",
                  required=True,
                  help="The output directory for the extent asset")
    @click.option(
        "-m",
        "--metadata",
        help="The url to the metadata description.",
        default=JSONLD_HREF,
    )
    def create_extent_asset_command(destination: str, metadata: str) -> None:
        """Generate a GeoJSON of the extent of the STAC Item.

        Args:
            destination (str): Local directory to save output COGs
        """
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        jsonld_metadata = utils.get_metadata(metadata)
        output_path = os.path.join(destination, "extent.geojson")
        extent.create_extent_asset(jsonld_metadata, output_path)

    return nrcanlandcover
