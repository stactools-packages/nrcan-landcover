import logging
import os
from glob import glob
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
        create_collection_command_fn(destination, metadata)

    def create_collection_command_fn(destination: str, metadata: str) -> None:
        metadata_dict = utils.get_metadata(metadata)
        output_path = os.path.join(destination, "collection.json")
        collection = stac.create_collection(metadata_dict, metadata)
        collection.set_self_href(output_path)
        collection.normalize_hrefs(destination)
        collection.save()
        collection.validate()

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
    @click.option(
        "-t",
        "--tile",
        help="Tile the tiff into many smaller files.",
        is_flag=True,
        default=False,
    )
    def create_cog_command(destination: str, source: Optional[str],
                           tile: bool) -> None:
        """Generate a COG from a GeoTiff. The COG will be saved in the desination
        with `_cog.tif` appended to the name.

        Args:
            destination (str): Local directory to save output COGs
            source (str, optional): An input NRCAN Landcover GeoTiff
            tile (bool, optional): Tile the tiff into many smaller files.
        """
        create_cog_command_fn(destination, source, tile)

    def create_cog_command_fn(destination: str, source: Optional[str],
                              tile: bool) -> None:
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        if source is None:
            cog.download_create_cog(destination, retile=tile)
        elif tile:
            cog.create_retiled_cogs(source, destination)
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
        "-e",
        "--extent-asset",
        required=False,
        help="An asset representing the extent of the STAC Item",
    )
    @click.option(
        "-m",
        "--metadata",
        help="The url to the metadata description.",
        default=JSONLD_HREF,
    )
    def create_item_command(destination: str, cog: str,
                            extent_asset: Optional[str],
                            metadata: str) -> None:
        """Generate a STAC item using the metadata, with an asset url as provided.

        Args:
            destination (str): Local directory to save the STAC Item json
            cog (str): location of a COG asset for the item
            extent_asset (str, optional): File containing a GeoJSON asset of the extent
            metadata (str): url containing the NRCAN Landcover JSONLD metadata
        """
        create_item_command_fn(destination, cog, extent_asset, metadata)

    def create_item_command_fn(destination: str, cog: str,
                               extent_asset: Optional[str],
                               metadata: str) -> None:
        jsonld_metadata = utils.get_metadata(metadata)
        output_path = os.path.join(destination,
                                   os.path.basename(cog)[:-4] + ".json")
        if extent_asset is None and os.path.exists(
                os.path.join(destination, "extent.geojson")):
            extent_asset = os.path.join(destination, "extent.geojson")
        item = stac.create_item(jsonld_metadata,
                                destination,
                                metadata,
                                cog,
                                extent_asset_path=extent_asset)
        item.set_self_href(output_path)
        item.make_asset_hrefs_relative()
        item.save_object()
        item.validate()

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
            metadata (str): URL to the metadata
        """
        create_extent_asset_command_fn(destination, metadata)

    def create_extent_asset_command_fn(destination: str,
                                       metadata: str) -> None:
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        jsonld_metadata = utils.get_metadata(metadata)
        output_path = os.path.join(destination, "extent.geojson")
        extent.create_extent_asset(jsonld_metadata, output_path)

    @nrcanlandcover.command(
        "build-full-collection",
        short_help="Creates a STAC collection with Items and Assets",
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
    def build_full_collection_command(destination: str, metadata: str) -> None:
        """Creates a STAC collection with Items and Assets

        Args:
            destination (str): Directory used to store the collection json
            metadata (str, optional): Path to a jsonld metadata file - provided by NRCan
        Returns:
            Callable
        """
        create_cog_command_fn(destination, None, tile=True)
        for cog_file in glob(f"{destination}/*.tif"):
            create_item_command_fn(destination,
                                   cog_file,
                                   None,
                                   metadata=metadata)
        create_collection_command_fn(destination, metadata)

    return nrcanlandcover
