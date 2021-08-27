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
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.label import (
    LabelClasses,
    LabelExtension,
    LabelTask,
    LabelType,
)
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import (
    DataType,
    RasterBand,
    RasterExtension,
    Sampling,
)
from shapely.geometry import Polygon

from stactools.nrcan_landcover.constants import (
    CLASSIFICATION_VALUES,
    DESCRIPTION,
    JSONLD_HREF,
    KEYWORDS,
    LANDCOVER_EPSG,
    LANDCOVER_ID,
    LANDCOVER_TITLE,
    LICENSE,
    LICENSE_LINK,
    NRCAN_PROVIDER,
    THUMBNAIL_HREF,
)
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
        metadata (dict): Parsed metadata.
        destination (str): Directory where the Item will be stored.
        metadata_url (str, optional): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.
        extent_asset_path (str, optional): Path to extent GeoJSON file.
        thumbnail_url (str, optional): URL for thumbnail image.

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

    item_label = LabelExtension.ext(item, add_if_missing=True)
    item_label.label_type = LabelType.RASTER
    item_label.label_tasks = [LabelTask.CLASSIFICATION]
    item_label.label_properties = None
    item_label.label_description = ""
    item_label.label_classes = [
        # TODO: The STAC Label extension JSON Schema is incorrect.
        # https://github.com/stac-extensions/label/pull/8
        # https://github.com/stac-utils/pystac/issues/611
        # When it is fixed, this should be None, not "None"
        LabelClasses.create(list(CLASSIFICATION_VALUES.values()), "None")
    ]

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
            roles=[
                "data",
                "labels",
                "labels-raster",
            ],
            title="Land cover of Canada COG",
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
        # Projection Extension
        cog_asset_projection = ProjectionExtension.ext(cog_asset,
                                                       add_if_missing=True)
        cog_asset_projection.epsg = item_projection.epsg
        cog_asset_projection.bbox = item_projection.bbox
        cog_asset_projection.transform = item_projection.transform
        cog_asset_projection.shape = item_projection.shape
        # Label Extension (doesn't seem to handle Assets properly)
        cog_asset.extra_fields["label:type"] = item_label.label_type
        cog_asset.extra_fields["label:tasks"] = item_label.label_tasks
        cog_asset.extra_fields[
            "label:properties"] = item_label.label_properties
        cog_asset.extra_fields[
            "label:description"] = item_label.label_description
        cog_asset.extra_fields["label:classes"] = [
            item_label.label_classes[0].to_dict()
        ]
    return item


def create_collection(
        metadata: Dict[str, Any],
        metadata_url: str = JSONLD_HREF,
        thumbnail_url: str = THUMBNAIL_HREF) -> pystac.Collection:
    """Create a STAC Collection using a jsonld file provided by NRCan.

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
        keywords=KEYWORDS,
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

    collection_label = LabelExtension.summaries(collection,
                                                add_if_missing=True)
    collection_label.label_type = [LabelType.RASTER]
    collection_label.label_tasks = [LabelTask.CLASSIFICATION]
    collection_label.label_properties = None
    collection_label.label_classes = [
        # TODO: The STAC Label extension JSON Schema is incorrect.
        # https://github.com/stac-extensions/label/pull/8
        # https://github.com/stac-utils/pystac/issues/611
        # When it is fixed, this should be None, not "None"
        LabelClasses.create(list(CLASSIFICATION_VALUES.values()), "None")
    ]

    collection_proj = ProjectionExtension.summaries(collection,
                                                    add_if_missing=True)
    collection_proj.epsg = [LANDCOVER_EPSG]

    collection_item_asset = ItemAssetsExtension.ext(collection,
                                                    add_if_missing=True)
    collection_item_asset.item_assets = {
        "metadata":
        AssetDefinition(
            dict(
                type=pystac.MediaType.JSON,
                roles=["metadata"],
                title="Land cover of Canada metadata",
            )),
        "thumbnail":
        AssetDefinition(
            dict(
                type=pystac.MediaType.JPEG,
                roles=["thumbnail"],
                title="Land cover of Canada thumbnail",
            )),
        "landcover":
        AssetDefinition({
            "type":
            pystac.MediaType.COG,
            "roles": [
                "data",
                "labels",
                "labels-raster",
            ],
            "title":
            "Land cover of Canada COG",
            "raster:bands":
            RasterBand.create(nodata=0,
                              sampling=Sampling.AREA,
                              data_type=DataType.UINT8,
                              spatial_resolution=30).to_dict(),
            "file:values": [{
                "values": [value],
                "summary": summary
            } for value, summary in CLASSIFICATION_VALUES.items()],
            "label:type":
            collection_label.label_type[0],
            "label:tasks":
            collection_label.label_tasks,
            "label:properties":
            None,
            "label:classes": [collection_label.label_classes[0].to_dict()],
        })
    }

    return collection
