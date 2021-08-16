import logging
import os
from glob import glob
from subprocess import CalledProcessError, check_output
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import rasterio
import requests

from stactools.nrcan_landcover.constants import COLOUR_MAP, JSONLD_HREF
from stactools.nrcan_landcover.utils import get_metadata

logger = logging.getLogger(__name__)


def download_create_cog(
    output_directory: str,
    metadata_url: str = JSONLD_HREF,
    raise_on_fail: bool = True,
    dry_run: bool = False,
) -> str:
    if dry_run:
        logger.info("Would have downloaded TIF, created COG, and written COG")
        return output_directory

    metadata = get_metadata(JSONLD_HREF)
    access_url = metadata["tiff_metadata"]["dcat:accessURL"].get("@id")
    with TemporaryDirectory() as tmp_dir:
        # Extract filename from url
        tmp_file = os.path.join(tmp_dir, access_url.split('/').pop())

        resp = requests.get(access_url)

        with open(tmp_file, 'wb') as f:
            f.write(resp.content)
        if access_url.endswith(".zip"):
            with ZipFile(tmp_file, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
        print(os.listdir(tmp_dir))
        file_name = glob(f"{tmp_dir}/*.tif").pop()
        output_file = os.path.join(
            output_directory,
            os.path.basename(file_name).replace(".tif", "") + "_cog.tif")
        return create_cog(file_name, output_file, raise_on_fail, dry_run)


def create_cog(
    input_path: str,
    output_path: str,
    raise_on_fail: bool = True,
    dry_run: bool = False,
) -> str:
    """Create COG from a tif

    Args:
        input_path (str): Path to the Natural Resources Canada Land Cover data.
        output_path (str): The path to which the COG will be written.
        raise_on_fail (bool, optional): Whether to raise error on failure.
            Defaults to True.
        dry_run (bool, optional): Run without downloading tif, creating COG,
            and writing COG. Defaults to False.

    Returns:
        str: The path to the output COG.
    """

    output = None
    try:
        if dry_run:
            logger.info("Would have read TIF, created COG, and written COG")
        else:
            cmd = [
                "gdal_translate",
                "-of",
                "COG",
                "-co",
                "BLOCKSIZE=512",
                "-co",
                "compress=deflate",
                "-co",
                "predictor=yes",
                "-co",
                "OVERVIEWS=IGNORE_EXISTING",
                "-a_nodata",
                "0",
                input_path,
                output_path,
            ]

            try:
                output = check_output(cmd)
            except CalledProcessError as e:
                output = e.output
                raise
            finally:
                logger.info(f"output: {str(output)}")
            with rasterio.open(output_path, "r+") as dataset:
                dataset.write_colormap(1, COLOUR_MAP)

    except Exception:
        logger.error("Failed to process {}".format(output_path))

        if raise_on_fail:
            raise

    return output_path
