import json
import logging
from typing import Any, Dict

from pystac.stac_io import DefaultStacIO

logger = logging.getLogger(__name__)


def create_extent_asset(metadata: Dict[str, Any], output_path: str) -> None:
    DefaultStacIO().write_text_to_href(
        output_path,
        json.dumps({
            "type":
            "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": metadata["geom_metadata"],
                "properties": {}
            }]
        }))
