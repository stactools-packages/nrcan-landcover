import click
import logging
import os

from stactools.nrcan_landcover import stac
from stactools.nrcan_landcover import cog
from stactools.nrcan_landcover import utils
from stactools.nrcan_landcover.constants import LANDCOVER_ID, JSONLD_HREF

logger = logging.getLogger(__name__)


def create_nrcanlandcover_command(cli):
    """Creates the nrcanlandcover command line utility."""

    @cli.group(
        "nrcanlandcover",
        short_help=(
            "Commands for working with Natural Resources Canada Land Cover data"
        ),
    )
    def nrcanlandcover():
        pass

    @nrcanlandcover.command(
        "create-catalog",
        short_help="Create a STAC catalog for NRCan 2015 Land Cover of Canada.",
    )
    @click.argument("destination")
    @click.option(
        "-s",
        "--source",
        help="The url to the metadata description.",
        default=JSONLD_HREF,
    )
    def create_catalog_command(destination: str, source: str):
        """Creates a STAC Catalog from Natural Resources Canada
        Land Cover metadata files.

        Args:
            destination (str): Path to output STAC catalog.
            source (str): Path to NRCan provided metadata - Currently only supports JSON-LD.

        Returns:
            Callable
        """

        json_path = source

        metadata = utils.get_metadata(json_path)

        asset_package_path = utils.download_asset_package(metadata)

        tif_path = os.path.join(
            asset_package_path,
            [i for i in os.listdir(asset_package_path) if i.endswith(".tif")][0],
        )

        output_path = destination.replace(".json", "_cog.tif")

        # Create cog asset
        cog_path = cog.create_cog(tif_path, output_path, dry_run=False)

        # Create stac item
        item = stac.create_item(metadata, json_path, cog_path, destination)
        item.collection_id = LANDCOVER_ID

        collection = stac.create_collection(metadata)
        collection.add_item(item)
        collection_dir = os.path.dirname(os.path.dirname(destination))

        collection.normalize_hrefs(collection_dir)
        collection.save()
        collection.validate()

    @nrcanlandcover.command(
        "create-cog", short_help="Transform Geotiff to Cloud-Optimized Geotiff.",
    )
    @click.option(
        "-d", "--destination", required=True, help="The output directory for the COG"
    )
    @click.option("-s", "--source", required=True, help="Path to an input GeoTiff")
    def create_cog_command(destination: str, source: str):
        """Generate a COG from a GeoTiff. The COG will be saved in the desination 
        with `_cog.tif` appended to the name.

        Args:
            destination (str): Local directory to save output COGs
            source (str): An input NRCAN Landcover GeoTiff
        """
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        output_path = os.path.join(
            destination, os.path.basename(source)[:-4] + "_cog.tif"
        )

        cog.create_cog(source, output_path)

    @nrcanlandcover.command(
        "create-item", short_help="Create a STAC item using JSONLD metadata and a COG",
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
    def create_item_command(destination: str, cog: str, metadata: str):
        """Generate a STAC item using the metadata, with an asset url as provided.

        Args:
            destination (str): Local directory to save the STAC Item json
            cog (str): location of a COG asset for the item
            metadata (str): url containing the NRCAN Landcover JSONLD metadata
        """
        jsonld_metadata = utils.get_metadata(metadata)

        output_path = os.path.join(destination, os.path.basename(cog)[:-4] + '.json')

        stac.create_item(jsonld_metadata, output_path, cog)

    return nrcanlandcover
