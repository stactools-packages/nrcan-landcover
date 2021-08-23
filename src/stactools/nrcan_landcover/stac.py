import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import fsspec
import pystac
import pytz
import rasterio
from dateutil.relativedelta import relativedelta
from pystac.extensions.file import FileExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import (DataType, RasterBand, RasterExtension,
                                      Sampling)
from shapely.geometry import Polygon

from stactools.nrcan_landcover.constants import (CLASSIFICATION_VALUES,
                                                 DESCRIPTION, JSONLD_HREF,
                                                 LANDCOVER_EPSG, LANDCOVER_ID,
                                                 LANDCOVER_TITLE, LICENSE,
                                                 LICENSE_LINK, NRCAN_PROVIDER,
                                                 THUMBNAIL_HREF)
from stactools.nrcan_landcover.utils import uri_validator

logger = logging.getLogger(__name__)


def create_item(metadata: Dict[str, Any],
                destination: str,
                metadata_url: str = JSONLD_HREF,
                cog_href: Optional[str] = None,
                extent_asset_path: Optional[str] = None,
                thumbnail_url: str = THUMBNAIL_HREF) -> pystac.Item:
    """Creates a STAC item for a Natural Resources Canada Land Cover dataset.

    Args:
        metadata_url (str, optional): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

    cog_href_relative = None
    if cog_href and not uri_validator(cog_href):
        cog_href_relative = os.path.relpath(cog_href, destination)
    if extent_asset_path and not uri_validator(extent_asset_path):
        extent_asset_path = os.path.relpath(extent_asset_path, destination)

    title = metadata["tiff_metadata"]["dct:title"]
    description = metadata["description_metadata"]["dct:description"]

    utc = pytz.utc

    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(year, "%Y"))

    end_datetime = dataset_datetime + relativedelta(years=5)

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    id = title.replace(" ", "-")
    geometry = metadata["geom_metadata"]
    bbox = list(Polygon(geometry.get("coordinates")[0]).bounds)
    properties = {
        "title": title,
        "description": description,
    }

    # Create item
    item = pystac.Item(
        id=id,
        geometry=geometry,
        bbox=bbox,
        datetime=dataset_datetime,
        properties=properties,
        stac_extensions=[],
    )

    if start_datetime and end_datetime:
        item.common_metadata.start_datetime = start_datetime
        item.common_metadata.end_datetime = end_datetime

    item_projection = ProjectionExtension.ext(item, add_if_missing=True)
    item_projection.epsg = LANDCOVER_EPSG
    if cog_href is not None:
        with rasterio.open(cog_href) as dataset:
            item_projection.bbox = list(dataset.bounds)
            item_projection.transform = list(dataset.transform)
            item_projection.shape = [dataset.height, dataset.width]
    item.add_asset(
        "metadata",
        pystac.Asset(
            href=metadata_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="Land cover of Canada metadata",
        ),
    )
    item.add_asset(
        "thumbnail",
        pystac.Asset(
            href=thumbnail_url,
            media_type=pystac.MediaType.JPEG,
            roles=["thumbnail"],
            title="Land cover of Canada thumbnail",
        ),
    )
    if extent_asset_path:
        item.add_asset(
            "extent",
            pystac.Asset(
                href=extent_asset_path,
                media_type=pystac.MediaType.GEOJSON,
                roles=["extent"],
                title="Land cover of Canada extent",
            ),
        )

    if cog_href is not None:
        # Create COG asset if it exists.
        cog_asset = pystac.Asset(
            href=cog_href_relative or cog_href,
            media_type=pystac.MediaType.COG,
            roles=["data"],
            title="Land cover of Canada COGs",
        )
        item.add_asset("landcover", cog_asset)
        # File Extension
        cog_asset_file = FileExtension.ext(cog_asset, add_if_missing=True)
        # The following odd type annotation is needed
        mapping: List[Any] = [{
            "values": [value],
            "summary": summary
        } for value, summary in CLASSIFICATION_VALUES.items()]
        cog_asset_file.values = mapping
        with fsspec.open(cog_href) as file:
            size = file.size
            if size is not None:
                cog_asset_file.size = size
        # Raster Extension
        cog_asset_raster = RasterExtension.ext(cog_asset, add_if_missing=True)
        cog_asset_raster.bands = [
            RasterBand.create(nodata=0,
                              sampling=Sampling.AREA,
                              data_type=DataType.UINT8,
                              spatial_resolution=30)
        ]
    return item


def create_collection(
        metadata: Dict[str, Any],
        metadata_url: str = JSONLD_HREF,
        thumbnail_url: str = THUMBNAIL_HREF) -> pystac.Collection:
    """Create a STAC Collection using a jsonld file provided by NRCan
    and save it to a destination.

    The metadata dict may be created using `utils.get_metadata`

    Args:
        metadata (dict): metadata parsed from jsonld
        metadata_url (str, optional): Location to save the output STAC Collection json

    Returns:
        pystac.Collection: pystac collection object
    """
    # Creates a STAC collection for a Natural Resources Canada Land Cover dataset

    title = metadata["tiff_metadata"]["dct:title"]

    utc = pytz.utc
    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(year, "%Y"))

    start_datetime = dataset_datetime  # type: Optional[datetime]
    end_datetime = dataset_datetime + relativedelta(years=5)

    geometry = metadata["geom_metadata"]
    bbox = list(Polygon(geometry.get("coordinates")[0]).bounds)

    collection = pystac.Collection(
        id=LANDCOVER_ID,
        title=LANDCOVER_TITLE,
        description=DESCRIPTION,
        providers=[NRCAN_PROVIDER],
        license=LICENSE,
        extent=pystac.Extent(
            pystac.SpatialExtent([bbox]),
            # mypy insists that a datetime can't be used for Optional[datetime]
            # The type of the datetimes is overridden above
            pystac.TemporalExtent([[start_datetime, end_datetime]]),
        ),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED,
    )
    collection.add_link(LICENSE_LINK)
    collection.add_asset(
        "metadata",
        pystac.Asset(
            href=metadata_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="Land cover of Canada metadata",
        ),
    )
    collection.add_asset(
        "thumbnail",
        pystac.Asset(
            href=thumbnail_url,
            media_type=pystac.MediaType.JPEG,
            roles=["thumbnail"],
            title="Land cover of Canada thumbnail",
        ),
    )
    return collection
