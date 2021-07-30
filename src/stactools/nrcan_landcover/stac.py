from typing import Any, Dict, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import logging
import rasterio
from pystac.extensions.projection import ProjectionExtension
from stactools.nrcan_landcover.constants import (
    LANDCOVER_ID,
    LANDCOVER_EPSG,
    LANDCOVER_TITLE,
    DESCRIPTION,
    NRCAN_PROVIDER,
    LICENSE,
    LICENSE_LINK,
)

import pystac
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


def create_item(metadata: Dict[str, Any],
                metadata_url: str,
                cog_href: Optional[str] = None) -> pystac.Item:
    """Creates a STAC item for a Natural Resources Canada Land Cover dataset.

    Args:
        metadata_url (str): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.

    Returns:
        pystac.Item: STAC Item object.
    """

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

    bbox = Polygon(geometry.get("coordinates")[0]).bounds
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
    with rasterio.open(cog_href) as dataset:
        item_projection.bbox = dataset.bounds
        item_projection.transform = list(dataset.transform)
        item_projection.shape = [dataset.height, dataset.width]

    # Create metadata asset
    item.add_asset(
        "metadata",
        pystac.Asset(
            href=metadata_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="Land cover of Canada metadata",
        ),
    )

    if cog_href is not None:
        # Create COG asset if it exists.
        item.add_asset(
            "landcover",
            pystac.Asset(
                href=cog_href,
                media_type=pystac.MediaType.COG,
                roles=["data"],
                title="Land cover of Canada COGs",
            ),
        )

    item.set_self_href(metadata_url)

    item.save_object()

    return item


def create_collection(metadata: Dict[str, Any],
                      metadata_url: str) -> pystac.Collection:
    """Create a STAC Collection using a jsonld file provided by NRCan
    and save it to a destination.

    The metadata dict may be created using `utils.get_metadata`

    Args:
        metadata (dict): metadata parsed from jsonld
        metadata_url (str): Location to save the output STAC Collection json

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

    collection.set_self_href(metadata_url)

    collection.save_object()

    return collection
