import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import fsspec
import pystac
import pytz
import rasterio
from dateutil.relativedelta import relativedelta
from pyproj import CRS, Proj
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
from pystac.extensions.scientific import ScientificExtension
from shapely.geometry import Polygon, box
from shapely.geometry import mapping as geojson_mapping
from stactools.core.io import ReadHrefModifier

from stactools.nrcan_landcover.constants import (
    CITATION,
    CLASSIFICATION_VALUES,
    DESCRIPTION,
    DOI,
    FULL_DATASET_BBOX,
    JSONLD_HREF,
    KEYWORDS,
    LANDCOVER_CRS_WKT,
    LANDCOVER_EPSG,
    LANDCOVER_ID,
    LANDCOVER_TITLE,
    LICENSE,
    LICENSE_LINK,
    NO_DATA_VALUE,
    NRCAN_PROVIDER,
    THUMBNAIL_HREF,
)
from stactools.nrcan_landcover.utils import uri_validator

logger = logging.getLogger(__name__)


def get_cog_geom(href: Optional[str], metadata: Dict[str,
                                                     Any]) -> Dict[str, Any]:
    if href is not None:
        with rasterio.open(href) as dataset:
            cog_bbox = list(dataset.bounds)
            cog_transform = list(dataset.transform)
            cog_shape = [dataset.height, dataset.width]

            # If cog is the full dataset, use the bbox from the metadata
            if cog_bbox == FULL_DATASET_BBOX:
                tiled = False
                geometry = metadata["geom_metadata"]
                bbox = list(Polygon(geometry.get("coordinates")[0]).bounds)
            else:
                tiled = True
                transformer = Proj.from_crs(CRS.from_epsg(LANDCOVER_EPSG),
                                            CRS.from_epsg(4326),
                                            always_xy=True)
                bbox = list(
                    transformer.transform_bounds(dataset.bounds.left,
                                                 dataset.bounds.bottom,
                                                 dataset.bounds.right,
                                                 dataset.bounds.top))
                geometry = geojson_mapping(box(*bbox, ccw=True))
    else:
        # Use values from the metadata
        geometry = metadata["geom_metadata"]
        bbox = list(Polygon(geometry.get("coordinates")[0]).bounds)
        tiled = False
        cog_bbox = []
        cog_transform = []
        cog_shape = []
    return {
        'bbox': bbox,
        'cog_bbox': cog_bbox,
        'geometry': geometry,
        'tiled': tiled,
        'transform': cog_transform,
        'shape': cog_shape,
    }


def create_item(metadata: Dict[str, Any],
                destination: str,
                metadata_url: str = JSONLD_HREF,
                cog_href: Optional[str] = None,
                cog_href_modifier: Optional[ReadHrefModifier] = None,
                extent_asset_href: Optional[str] = None,
                thumbnail_url: str = THUMBNAIL_HREF) -> pystac.Item:
    """Creates a STAC item for a Natural Resources Canada Land Cover dataset.

    Args:
        metadata (dict): Parsed metadata.
        destination (str): Directory where the Item will be stored.
        metadata_url (str, optional): Path to provider metadata.
        cog_href (str, optional): Path to COG asset.
        extent_asset_href (str, optional): Path to extent GeoJSON file.
        thumbnail_url (str, optional): URL for thumbnail image.

    Returns:
        pystac.Item: STAC Item object.
    """

    cog_href_relative = None
    if cog_href and not uri_validator(cog_href):
        cog_href_relative = os.path.relpath(cog_href, destination)
    if extent_asset_href and not uri_validator(extent_asset_href):
        extent_asset_href = os.path.relpath(extent_asset_href, destination)
    cog_access_href = cog_href  # Make sure cog_access_href exists, even if None
    if cog_href and cog_href_modifier:
        cog_access_href = cog_href_modifier(cog_href)

    title = metadata["tiff_metadata"]["dct:title"]
    description = metadata["description_metadata"]["dct:description"]

    utc = pytz.utc

    year = title.split(" ")[0]
    dataset_datetime = utc.localize(datetime.strptime(year, "%Y"))

    end_datetime = dataset_datetime + relativedelta(years=5)

    start_datetime = dataset_datetime
    end_datetime = end_datetime

    if cog_href is not None:
        id = os.path.basename(cog_href).replace("_cog", "").replace(".tif", "")
    else:
        id = title.replace(" ", "-")
    cog_geom = get_cog_geom(cog_access_href, metadata)
    bbox = cog_geom["bbox"]
    geometry = cog_geom["geometry"]
    tiled = cog_geom["tiled"]

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
    item_projection.wkt2 = LANDCOVER_CRS_WKT
    if cog_href is not None:
        item_projection.bbox = cog_geom["cog_bbox"]
        item_projection.transform = cog_geom["transform"]
        item_projection.shape = cog_geom["shape"]

    item_label = LabelExtension.ext(item, add_if_missing=True)
    item_label.label_type = LabelType.RASTER
    item_label.label_tasks = [LabelTask.CLASSIFICATION]
    item_label.label_properties = None
    item_label.label_description = ""
    item_label.label_classes = [
        # TODO: The STAC Label extension JSON Schema is incorrect.
        # https://github.com/stac-extensions/label/pull/8
        # https://github.com/stac-utils/pystac/issues/611
        # When it is fixed, this should be None, not the empty string.
        LabelClasses.create(list(CLASSIFICATION_VALUES.values()), "")
    ]

    item_sci = ScientificExtension.ext(item, add_if_missing=True)
    item_sci.doi = DOI
    item_sci.citation = CITATION

    item.add_asset(
        "metadata",
        pystac.Asset(
            href=metadata_url,
            media_type=pystac.MediaType.JSON,
            roles=["metadata"],
            title="Land cover of Canada metadata",
        ),
    )
    if not tiled:
        item.add_asset(
            "thumbnail",
            pystac.Asset(
                href=thumbnail_url,
                media_type=pystac.MediaType.PNG,
                roles=["thumbnail"],
                title="Land cover of Canada thumbnail",
            ),
        )
    if extent_asset_href:
        item.add_asset(
            "extent",
            pystac.Asset(
                href=extent_asset_href,
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
        with fsspec.open(cog_access_href) as file:
            size = file.size
            if size is not None:
                cog_asset_file.size = size
        # Raster Extension
        cog_asset_raster = RasterExtension.ext(cog_asset, add_if_missing=True)
        cog_asset_raster.bands = [
            RasterBand.create(nodata=NO_DATA_VALUE,
                              sampling=Sampling.AREA,
                              data_type=DataType.UINT8,
                              spatial_resolution=30)
        ]
        # Projection Extension
        cog_asset_projection = ProjectionExtension.ext(cog_asset,
                                                       add_if_missing=True)
        cog_asset_projection.epsg = item_projection.epsg
        cog_asset_projection.wkt2 = item_projection.wkt2
        cog_asset_projection.bbox = item_projection.bbox
        cog_asset_projection.transform = item_projection.transform
        cog_asset_projection.shape = item_projection.shape
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
        thumbnail_url (str, optional): URL to a thumbnail image for the Collection

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
            media_type=pystac.MediaType.PNG,
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
        # When it is fixed, this should be None, not the empty string.
        LabelClasses.create(list(CLASSIFICATION_VALUES.values()), "")
    ]

    collection_proj = ProjectionExtension.summaries(collection,
                                                    add_if_missing=True)
    collection_proj.epsg = [LANDCOVER_EPSG]

    collection_sci = ScientificExtension.ext(collection, add_if_missing=True)
    collection_sci.doi = DOI
    collection_sci.citation = CITATION

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
            "raster:bands": [
                RasterBand.create(nodata=NO_DATA_VALUE,
                                  sampling=Sampling.AREA,
                                  data_type=DataType.UINT8,
                                  spatial_resolution=30).to_dict()
            ],
            "file:values": [{
                "values": [value],
                "summary": summary
            } for value, summary in CLASSIFICATION_VALUES.items()],
            "proj:epsg":
            collection_proj.epsg[0]
        }),
        "extent":
        AssetDefinition(
            dict(
                type=pystac.MediaType.GEOJSON,
                roles=["extent"],
                title="Land cover of Canada extent",
            )),
    }

    return collection
