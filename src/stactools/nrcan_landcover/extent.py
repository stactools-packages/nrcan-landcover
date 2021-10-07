import json
import logging
from typing import Any, Dict, Optional

from pystac.stac_io import DefaultStacIO

from stactools.nrcan_landcover.stac import get_cog_geom

logger = logging.getLogger(__name__)


def create_extent_asset(metadata: Dict[str, Any], output_path: str,
                        cog_href: Optional[str]) -> None:
    # If cog_href is None it will use values from the metadata
    cog_geom = get_cog_geom(cog_href, metadata)
    DefaultStacIO().write_text_to_href(
        output_path,
        json.dumps({
            "type":
            "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": cog_geom['geometry'],
                "properties": {}
            }]
        }))
