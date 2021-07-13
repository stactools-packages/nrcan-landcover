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
    def create_collection_command(destination: str, metadata: str):
        """Creates a STAC Collection from NRCan Landcover metadata

        Args:
            destination (str): Directory used to store the collection json
            metadata (str): Path to a jsonld metadata file - provided by NRCan
        Returns:
            Callable
        """
        metadata = utils.get_metadata(metadata)

        output_path = os.path.join(destination, f"{LANDCOVER_ID}.json")

        stac.create_collection(metadata, output_path)

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
                  required=True,
                  help="Path to an input GeoTiff")
    def create_cog_command(destination: str, source: str):
        """Generate a COG from a GeoTiff. The COG will be saved in the desination
        with `_cog.tif` appended to the name.

        Args:
            destination (str): Local directory to save output COGs
            source (str): An input NRCAN Landcover GeoTiff
        """
        if not os.path.isdir(destination):
            raise IOError(f'Destination folder "{destination}" not found')

        output_path = os.path.join(destination,
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
    def create_item_command(destination: str, cog: str, metadata: str):
        """Generate a STAC item using the metadata, with an asset url as provided.

        Args:
            destination (str): Local directory to save the STAC Item json
            cog (str): location of a COG asset for the item
            metadata (str): url containing the NRCAN Landcover JSONLD metadata
        """
        jsonld_metadata = utils.get_metadata(metadata)

        output_path = os.path.join(destination,
                                   os.path.basename(cog)[:-4] + ".json")

        stac.create_item(jsonld_metadata, output_path, cog)

    return nrcanlandcover
